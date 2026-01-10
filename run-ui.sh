#!/bin/bash
# Run Filmbot UI for testing (without systemd service)

cd "$(dirname "$0")"

# Check if running from install directory or /opt/filmbot-appliance
if [ -f "venv/bin/python" ]; then
    PYTHON="./venv/bin/python"
    MAIN="./main.py"
elif [ -f "/opt/filmbot-appliance/ui/venv/bin/python" ]; then
    PYTHON="/opt/filmbot-appliance/ui/venv/bin/python"
    MAIN="/opt/filmbot-appliance/ui/main.py"
else
    echo "Error: Cannot find Python virtual environment"
    echo "Run ./install.sh first"
    exit 1
fi

echo "Starting Filmbot UI..."
echo "Press Ctrl+C to stop"
echo ""

# Run in windowed mode (not fullscreen EGLFS)
export QT_QPA_PLATFORM=xcb  # Use X11 instead of EGLFS for testing

$PYTHON $MAIN

