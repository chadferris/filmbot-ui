"""
Video preview widget for Filmbot appliance.
Displays live feed from ATEM Mini via /dev/video5.
"""

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class VideoThread(QThread):
    """Thread for capturing video frames from ATEM."""
    
    frame_ready = Signal(np.ndarray)
    error_occurred = Signal(str)
    
    def __init__(self, device_path: str = "/dev/video5", fps: int = 30):
        """Initialize video capture thread.
        
        Args:
            device_path: Path to video device
            fps: Target frame rate for preview
        """
        super().__init__()
        self.device_path = device_path
        self.fps = fps
        self.running = False
        self.capture = None
    
    def run(self):
        """Main thread loop - captures and emits frames."""
        self.running = True
        
        # Try to open video device
        try:
            self.capture = cv2.VideoCapture(self.device_path, cv2.CAP_V4L2)
            
            if not self.capture.isOpened():
                self.error_occurred.emit(f"Cannot open video device: {self.device_path}")
                return
            
            # Set capture properties for MJPEG
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.capture.set(cv2.CAP_PROP_FPS, 60)
            
            frame_delay = int(1000 / self.fps)  # ms between frames
            
            while self.running:
                ret, frame = self.capture.read()
                
                if ret:
                    self.frame_ready.emit(frame)
                else:
                    self.error_occurred.emit("Failed to read frame")
                    break
                
                # Throttle to target FPS
                self.msleep(frame_delay)
        
        except Exception as e:
            self.error_occurred.emit(f"Video capture error: {str(e)}")
        
        finally:
            if self.capture:
                self.capture.release()
    
    def stop(self):
        """Stop the video capture thread."""
        self.running = False
        self.wait()


class VideoPreviewWidget(QWidget):
    """Widget that displays live video preview from ATEM."""
    
    def __init__(self, device_path: str = "/dev/video5", parent=None):
        """Initialize video preview widget.
        
        Args:
            device_path: Path to video device
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.device_path = device_path
        self.video_thread = None
        self.recording = False
        
        # Create UI
        self.setup_ui()
        
        # Start video capture
        self.start_preview()
    
    def setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Video display label
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.setText("Connecting to video source...")
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: black;
                color: white;
                font-size: 16px;
            }
        """)
        
        layout.addWidget(self.video_label)
    
    def start_preview(self):
        """Start video preview."""
        if self.video_thread and self.video_thread.isRunning():
            return
        
        self.video_thread = VideoThread(self.device_path, fps=30)
        self.video_thread.frame_ready.connect(self.update_frame)
        self.video_thread.error_occurred.connect(self.handle_error)
        self.video_thread.start()
    
    def stop_preview(self):
        """Stop video preview."""
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread = None
    
    def update_frame(self, frame: np.ndarray):
        """Update the displayed frame.
        
        Args:
            frame: OpenCV frame (BGR format)
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get widget size for scaling
        widget_size = self.video_label.size()
        
        # Scale frame to fit widget while maintaining aspect ratio
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # Create QImage
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale to widget size
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            widget_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
    
    def handle_error(self, error_msg: str):
        """Handle video capture errors.
        
        Args:
            error_msg: Error message
        """
        print(f"Video error: {error_msg}")
        self.video_label.setText(f"No video source\n{error_msg}")
    
    def set_recording(self, recording: bool):
        """Set recording indicator state.
        
        Args:
            recording: True if recording is active
        """
        self.recording = recording
        # TODO: Add visual recording indicator overlay
    
    def closeEvent(self, event):
        """Handle widget close event."""
        self.stop_preview()
        super().closeEvent(event)

