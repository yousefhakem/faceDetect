#!/bin/bash
# install_presence_guard.sh - Complete installation script for Ubuntu

set -e  # Exit on any error

USERNAME=$(whoami)
FACE_DIR="$HOME/.face_enroll"
SCRIPT_DIR="$HOME/.local/bin"
SCRIPT_PATH="$SCRIPT_DIR/presence_guard.py"
SERVICE_NAME="presence-guard@$USERNAME.service"

echo "=================================="
echo "Presence Guard Installation Script"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Do not run this script as root/sudo!"
    echo "Run as your regular user: ./install_presence_guard.sh"
    exit 1
fi

# Install system dependencies
echo "1. Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-dev cmake build-essential \
    libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev \
    pkg-config libavcodec-dev libavformat-dev libswscale-dev \
    libv4l-dev libxvidcore-dev libx264-dev libjpeg-dev \
    libpng-dev libtiff-dev gfortran openexr libatlas-base-dev \
    python3-numpy libtbb2 libtbb-dev libdc1394-22-dev \
    acl  # For advanced file permissions

echo ""
echo "2. Installing Python packages..."
pip3 install --user opencv-python numpy face_recognition

echo ""
echo "3. Setting up directories and permissions..."
mkdir -p "$FACE_DIR" "$SCRIPT_DIR"

# Secure the face enrollment directory
chmod 700 "$FACE_DIR"
# Set default ACL so new files are automatically secured
setfacl -d -m u::rw-,g::---,o::--- "$FACE_DIR" 2>/dev/null || true

echo ""
echo "4. Installing presence guard script..."
if [ ! -f "presence_guard.py" ]; then
    echo "Error: presence_guard.py not found in current directory!"
    echo "Make sure you have the script file here and run again."
    exit 1
fi

cp "presence_guard.py" "$SCRIPT_PATH"
chmod 755 "$SCRIPT_PATH"

echo ""
echo "5. Installing systemd service..."
# Create systemd user service
mkdir -p "$HOME/.config/systemd/user"

cat > "$HOME/.config/systemd/user/presence-guard.service" << EOF
[Unit]
Description=Presence Guard Face Recognition Security
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Environment="DISPLAY=:0"
Environment="XAUTHORITY=%h/.Xauthority"
ExecStart=/usr/bin/python3 %h/.local/bin/presence_guard.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=default.target
EOF

# Reload systemd and enable the service
systemctl --user daemon-reload
systemctl --user enable presence-guard.service

echo ""
echo "6. Adding user to video group (for camera access)..."
sudo usermod -a -G video "$USERNAME"

echo ""
echo "=================================="
echo "Installation Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Add your face photos to: $FACE_DIR"
echo "   Example: cp ~/Pictures/my_face*.jpg $FACE_DIR/"
echo ""
echo "2. Secure the photos:"
echo "   chmod 600 $FACE_DIR/*"
echo ""
echo "3. Test the script:"
echo "   $SCRIPT_PATH"
echo ""
echo "4. Start the service:"
echo "   systemctl --user start presence-guard.service"
echo ""
echo "5. Check service status:"
echo "   systemctl --user status presence-guard.service"
echo ""
echo "6. View logs:"
echo "   journalctl --user -u presence-guard.service -f"
echo ""
echo "7. REBOOT to ensure everything starts properly!"
echo ""
echo "Service will auto-start on login after reboot."
echo ""

# Show current face directory status
echo "Current face enrollment directory:"
ls -la "$FACE_DIR" 2>/dev/null || echo "No files found - add your photos!"

echo ""
echo "IMPORTANT: You may need to log out and back in (or reboot)"
echo "for the video group membership to take effect."