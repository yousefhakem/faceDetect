# 🔒 Face Detection Security System

An intelligent face recognition security system that automatically monitors your computer using your webcam and takes security actions when unauthorized access is detected.

## ✨ Features

- **Real-time face detection** using your webcam
- **Face recognition** with pre-enrolled photos of authorized users
- **Automatic security responses** when unauthorized access detected:
  - No faces detected (user away)
  - Multiple faces detected (unauthorized person present)  
  - Unrecognized face detected
- **Fast performance** with optimized detection algorithms
- **Secure face enrollment** with encrypted photo storage
- **Systemd integration** for automatic startup
- **Comprehensive logging** for security audit trails

## 📋 Requirements

- **Ubuntu 18.04+** (Desktop or Server)
- **Python 3.6+**
- **Webcam** (USB camera or built-in)
- **sudo privileges** for installation

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yousefhakem/faceDetect.git
cd faceDetect
```

### 2. Run Installation
```bash
chmod +x install_presence_guard.sh
./install_presence_guard.sh
```

### 3. Setup Secure Face Enrollment
```bash
# Run the security setup script
chmod +x secure_face_setup.sh
./secure_face_setup.sh
```

### 4. Add Your Face Photos
```bash
# Copy clear photos of your face to the enrollment directory
cp ~/Pictures/your_face_photo1.jpg ~/.face_enroll/
cp ~/Pictures/your_face_photo2.jpg ~/.face_enroll/

# The photos will be automatically secured by the previous step
```

### 5. Test the System
```bash
# Test manually first
~/.local/bin/presence_guard.py

# If working correctly, start the service
systemctl --user start presence-guard.service
```

### 6. Enable Auto-start
```bash
# Enable automatic startup on boot
systemctl --user enable presence-guard.service

# Reboot to test
sudo reboot
```

## 📁 Project Structure

```
faceDetect/
├── .face_enroll/              # Secure directory for face photos
├── install_presence_guard.sh  # Main installation script
├── presence_guard.py          # Core face detection script
├── presence-guard.service     # Systemd service configuration
├── secure_face_setup.sh       # Security setup script
└── README.md                  # This file
```

## 🔒 Alternative: Security-First Installation

If you want to prioritize security setup, you can use the dedicated security script:

```bash
# 1. Clone repository
git clone https://github.com/yousefhakem/faceDetect.git
cd faceDetect

# 2. Setup security first
chmod +x secure_face_setup.sh
./secure_face_setup.sh

# 3. Add face photos (they'll be automatically secured)
cp ~/Pictures/your_face*.jpg ~/.face_enroll/

# 4. Run full installation
chmod +x install_presence_guard.sh
./install_presence_guard.sh

## 📸 Face Enrollment Tips

For best results when adding face photos:

1. **Use multiple photos** (3-5) with different:
   - Lighting conditions
   - Facial expressions
   - Head angles (slight left/right)

2. **Photo quality requirements:**
   - Clear, well-lit images
   - Face clearly visible
   - Minimal background clutter
   - Similar to webcam conditions

3. **File formats supported:**
   - JPEG (.jpg, .jpeg)
   - PNG (.png)
   - Other common image formats

## 🔧 Service Management

```bash
# Start the service
systemctl --user start presence-guard.service

# Stop the service
systemctl --user stop presence-guard.service

# Check service status
systemctl --user status presence-guard.service

# View real-time logs
journalctl --user -u presence-guard.service -f

# Disable auto-start
systemctl --user disable presence-guard.service
```

## 📊 Monitoring & Logs

### View Logs
```bash
# Real-time service logs
journalctl --user -u presence-guard.service -f

# Application logs
tail -f ~/presence_guard.log

# System security logs
sudo tail -f /var/log/auth.log | grep presence_guard
```

### Log Events
The system logs these events:
- Face detection results
- Authorization decisions
- Security actions taken
- System errors and warnings

## 🛠️ Troubleshooting

### Camera Issues
```bash
# Check available cameras
ls /dev/video*

# Test camera access
cheese  # or any camera app

# Check video group membership
groups | grep video
```

### Permission Issues
```bash
# Fix face enrollment permissions
chmod 700 ~/.face_enroll/
chmod 600 ~/.face_enroll/*

# Check current permissions
ls -la ~/.face_enroll/
```

### Service Issues
```bash
# Reload systemd configuration
systemctl --user daemon-reload

# Reset failed service
systemctl --user reset-failed presence-guard.service

# Manual test
~/.local/bin/presence_guard.py
```

### Face Recognition Issues
```bash
# Test face recognition manually
python3 -c "
import face_recognition
img = face_recognition.load_image_file('~/.face_enroll/your_photo.jpg')
print('✅ Face recognition working')
"
```

## 🔒 Security Considerations

- Face photos are stored with `600` permissions (readable only by you)
- Service runs with restricted privileges (`NoNewPrivileges=true`)
- Temporary files isolated (`PrivateTmp=true`)
- No network access required for core functionality
- All security events logged for audit

## 🐛 Common Issues

### 1. "Permission denied" errors
```bash
# Fix user permissions
sudo usermod -a -G video $USER
# Then logout/login or reboot
```

### 2. "No module named face_recognition"
```bash
# Reinstall Python packages
pip3 install --user --upgrade face_recognition opencv-python
```

### 3. "Cannot open webcam"
```bash
# Check camera permissions
ls -la /dev/video0
# Should be accessible by video group
```

### 4. Service won't start
```bash
# Check service logs
journalctl --user -u presence-guard.service --no-pager
```