#!/usr/bin/env python3
"""ProPresenter listener service.

Watches ProPresenter 6 (Stage Display WebSocket) or ProPresenter 7 (REST
polling) for slide notes containing [START_RECORD] / [STOP_RECORD] tags and
triggers the Filmbot ATEM recording script accordingly.
"""

import json
import logging
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config_manager import ConfigManager  # noqa: E402

RECORD_SCRIPT = "/opt/filmbot-appliance/record-atem.sh"
PID_FILE = "/tmp/filmbot-recording.pid"
LOG_FILE = "/var/log/filmbot-propresenter.log"
START_TAG = "[START_RECORD]"
STOP_TAG = "[STOP_RECORD]"
PP7_POLL_SECONDS = 0.5
RECONNECT_SECONDS = 5

logger = logging.getLogger("propresenter_listener")


class RecordingController:
    """Starts/stops the ATEM recording based on tag events."""

    def start(self) -> None:
        if os.path.exists(PID_FILE):
            logger.info("Recording already active; ignoring START_RECORD")
            return
        if not os.path.exists(RECORD_SCRIPT):
            logger.error("Record script not found at %s", RECORD_SCRIPT)
            return
        logger.info("Launching recording script: %s", RECORD_SCRIPT)
        try:
            subprocess.Popen(
                [RECORD_SCRIPT],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            logger.error("Failed to launch recording script: %s", exc)

    def stop(self) -> None:
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
        except (OSError, ValueError):
            logger.info("No active recording PID; ignoring STOP_RECORD")
            return
        logger.info("Sending SIGINT to ffmpeg PID %s", pid)
        try:
            os.kill(pid, signal.SIGINT)
        except ProcessLookupError:
            logger.warning("PID %s not running; removing stale PID file", pid)
            try:
                os.remove(PID_FILE)
            except OSError:
                pass
        except OSError as exc:
            logger.error("Failed to signal PID %s: %s", pid, exc)


class TagDispatcher:
    """Fires start/stop only on transitions to a new active slide.

    Notes may contain both tags. We treat each new (slide_key, notes) pair as
    an edge trigger so repeated events for the same slide don't retrigger.
    """

    def __init__(self, controller: RecordingController) -> None:
        self.controller = controller
        self._last_key: Optional[str] = None
        self._last_notes: str = ""

    def handle(self, slide_key: str, notes: str) -> None:
        notes = notes or ""
        if slide_key == self._last_key and notes == self._last_notes:
            return
        logger.debug("Slide changed: key=%s notes=%r", slide_key, notes)
        self._last_key = slide_key
        self._last_notes = notes
        if START_TAG in notes:
            self.controller.start()
        if STOP_TAG in notes:
            self.controller.stop()


class PP6Listener:
    """ProPresenter 6 Stage Display WebSocket client."""

    def __init__(self, host: str, port: int, password: str,
                 dispatcher: TagDispatcher) -> None:
        self.host = host
        self.port = port
        self.password = password
        self.dispatcher = dispatcher

    def run(self) -> None:
        try:
            import websocket  # type: ignore
        except ImportError:
            logger.error(
                "websocket-client is required for PP6 support "
                "(install with: pip install websocket-client)"
            )
            return
        url = f"ws://{self.host}:{self.port}/stagedisplay"
        while True:
            try:
                logger.info("Connecting to PP6 Stage Display: %s", url)
                ws = websocket.create_connection(url, timeout=10)
                ws.send(json.dumps(
                    {"pwd": self.password, "ptl": 610, "acn": "ath"}
                ))
                while True:
                    self._on_message(ws.recv())
            except Exception as exc:
                logger.warning(
                    "PP6 connection error: %s (retry in %ss)",
                    exc, RECONNECT_SECONDS,
                )
                time.sleep(RECONNECT_SECONDS)

    def _on_message(self, raw) -> None:
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            return
        acn = data.get("acn")
        if acn == "ath":
            if data.get("ath") in (True, 1, "1"):
                logger.info("PP6 authenticated")
            else:
                logger.error("PP6 authentication rejected: %s", data.get("err"))
            return
        if acn == "fv":
            # Frame Value payload: iterate elements looking for Current
            # Slide Notes (csn) and its uid (used as slide identity key).
            uid = None
            notes = ""
            for el in data.get("ary") or []:
                if el.get("acn") == "csn":
                    uid = el.get("uid") or uid
                    notes = el.get("txt") or ""
            if uid is not None:
                self.dispatcher.handle(f"pp6:{uid}", notes)


class PP7Listener:
    """ProPresenter 7 REST poller for the currently active slide."""

    def __init__(self, host: str, port: int, dispatcher: TagDispatcher,
                 poll_seconds: float = PP7_POLL_SECONDS) -> None:
        self.base = f"http://{host}:{port}"
        self.dispatcher = dispatcher
        self.poll_seconds = poll_seconds

    def run(self) -> None:
        logger.info("Polling PP7 REST API at %s", self.base)
        while True:
            try:
                self._poll_once()
            except urllib.error.URLError as exc:
                logger.warning("PP7 connection error: %s", exc)
            except Exception as exc:
                logger.exception("PP7 poll error: %s", exc)
            time.sleep(self.poll_seconds)

    def _get_json(self, path: str) -> Optional[dict]:
        with urllib.request.urlopen(f"{self.base}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _poll_once(self) -> None:
        # /v1/presentation/slide_index reports the currently displayed slide
        # index and presentation identity (PP7.9+).
        idx = self._get_json("/v1/presentation/slide_index") or {}
        pi = idx.get("presentation_index") or {}
        presentation = pi.get("presentation") or {}
        pres_uuid = presentation.get("uuid") or presentation.get("index")
        slide_index = pi.get("index")
        if pres_uuid is None or slide_index is None:
            return
        pres = self._get_json("/v1/presentation/active") or {}
        notes = _extract_pp7_notes(pres, slide_index)
        self.dispatcher.handle(f"pp7:{pres_uuid}:{slide_index}", notes)


def _extract_pp7_notes(presentation: dict, slide_index: int) -> str:
    """Walk PP7's active-presentation JSON to find notes for slide_index."""
    root = presentation.get("presentation") or presentation
    groups = root.get("groups") or []
    counter = 0
    for group in groups:
        for slide in group.get("slides") or []:
            if counter == slide_index:
                notes = slide.get("notes") or ""
                if isinstance(notes, dict):
                    return notes.get("text") or notes.get("plain") or ""
                return notes
            counter += 1
    return ""


def _configure_logging() -> None:
    handlers: list = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler(LOG_FILE))
    except OSError:
        pass
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> int:
    _configure_logging()
    config = ConfigManager()
    pp = config.get_propresenter_config()
    version = (pp.get("version") or "disabled").lower()
    host = pp.get("ip") or ""
    port = int(pp.get("port") or 0)
    password = pp.get("password") or ""

    if version == "disabled":
        logger.info("ProPresenter integration disabled; exiting")
        return 0
    if not host or not port:
        logger.error("ProPresenter host/port not configured")
        return 1

    dispatcher = TagDispatcher(RecordingController())
    if version == "6":
        PP6Listener(host, port, password, dispatcher).run()
    elif version == "7":
        PP7Listener(host, port, dispatcher).run()
    else:
        logger.error("Unknown ProPresenter version: %s", version)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

