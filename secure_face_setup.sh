#!/bin/bash
# secure_face_setup.sh - Secure the face enrollment directory

FACE_DIR="$HOME/.face_enroll"
SCRIPT_DIR="$HOME/.local/bin"
SCRIPT_PATH="$SCRIPT_DIR/presence_guard.py"

echo "Setting up secure face enrollment directory..."

# Create directories if they don't exist
mkdir -p "$FACE_DIR"
mkdir -p "$SCRIPT_DIR"

# Set restrictive permissions on face enrollment directory
# 700 = owner: read/write/execute, group: nothing, others: nothing
chmod 700 "$FACE_DIR"

# Make all existing files in the directory readable only by owner
find "$FACE_DIR" -type f -exec chmod 600 {} \;

# Set the directory to inherit these permissions for new files
# This ensures any new files added will be secure
setfacl -d -m u::rw-,g::---,o::--- "$FACE_DIR" 2>/dev/null || true

echo "Face enrollment directory secured:"
echo "Directory: $FACE_DIR"
echo "Permissions: $(ls -ld "$FACE_DIR")"
echo ""

# Install the presence guard script
if [ -f "presence_guard.py" ]; then
    cp "presence_guard.py" "$SCRIPT_PATH"
    chmod 755 "$SCRIPT_PATH"
    echo "Presence guard script installed to: $SCRIPT_PATH"
else
    echo "Warning: presence_guard.py not found in current directory"
    echo "You'll need to copy it manually to: $SCRIPT_PATH"
fi

echo ""
echo "Security setup complete!"
echo ""
echo "To add face photos securely:"
echo "1. Copy photos to: $FACE_DIR"
echo "2. Run: chmod 600 $FACE_DIR/*"
echo ""
echo "Current face enrollment files:"
ls -la "$FACE_DIR" 2>/dev/null || echo "No files found"