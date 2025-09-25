#!/usr/bin/env python3
"""
presence_guard.py
- Ensures ONLY the enrolled user is present.
- Locks the session if any condition fails.
- Does NOT attempt to unlock (use Howdy/fingerprint for unlocking).
"""

import os
import time
import subprocess
from datetime import datetime, timedelta
import face_recognition
import cv2
import numpy as np
import glob
import sys

# ===== CONFIG =====
ENROLL_DIR = os.path.expanduser("~/.face_enroll")
ALLOWED_TOLERANCE = 0.45    # face distance threshold (lower = stricter)
CHECK_INTERVAL = 2          # seconds between checks
LOCK_COOLDOWN = 5           # seconds to wait after locking before re-checking
LOGFILE = os.path.expanduser("~/presence_guard.log")
VIDEO_DEVICE = 0            # webcam device index
# ====================

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} - {msg}"
    print(line)
    try:
        with open(LOGFILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load_known_encodings(enroll_dir):
    files = glob.glob(os.path.join(enroll_dir, "*"))
    encodings = []
    for f in files:
        try:
            img = face_recognition.load_image_file(f)
            face_locs = face_recognition.face_locations(img, model="hog")
            if not face_locs:
                log(f"No face found in enroll image: {f}")
                continue
            enc = face_recognition.face_encodings(img, known_face_locations=face_locs)[0]
            encodings.append(enc)
            log(f"Loaded enrollment face from {os.path.basename(f)}")
        except Exception as e:
            log(f"Error loading {f}: {e}")
    return encodings


def lock_session():
    cmds = [
        ["loginctl", "lock-sessions"],
        ["gnome-screensaver-command", "--lock"],
        ["xdg-screensaver", "lock"],
        ["dm-tool", "lock"],
    ]
    for cmd in cmds:
        try:
            subprocess.run(cmd, check=True, timeout=5)
            log(f"Locked via: {' '.join(cmd)}")
            return True
        except FileNotFoundError:
            continue
        except subprocess.CalledProcessError:
            continue
        except Exception as e:
            log(f"Lock attempt error for {' '.join(cmd)}: {e}")
    log("All lock commands failed.")
    return False

def main():
    if not os.path.isdir(ENROLL_DIR):
        log(f"Enrollment dir {ENROLL_DIR} not found. Create it and add photos of your face.")
        sys.exit(1)

    known_encodings = load_known_encodings(ENROLL_DIR)
    if not known_encodings:
        log("No known face encodings loaded. Exiting.")
        sys.exit(1)

    # combine encodings into a numpy array for fast comparison
    known_encodings_np = np.array(known_encodings)

    log("Starting presence_guard")
    cap = cv2.VideoCapture(VIDEO_DEVICE)
    if not cap.isOpened():
        log("Cannot open webcam. Exiting.")
        sys.exit(1)

    last_lock_time = None

    try:
        while True:

            ret, frame = cap.read()
            if not ret:
                log("Failed to read from webcam, retrying...")
                time.sleep(CHECK_INTERVAL)
                continue

            small_frame = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
            rgb_frame = small_frame[:, :, ::-1]

            face_locations = face_recognition.face_locations(rgb_frame, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            n_faces = len(face_encodings)
            log(f"Detected {n_faces} face(s)")

            # If not exactly 1 face -> lock
            if n_faces != 1:
                log("Condition failed: not exactly one person present -> locking")
                lock_session()
                last_lock_time = datetime.now()
                time.sleep(LOCK_COOLDOWN)
                continue

            # Compare the single detected face to known encodings (use distance)
            dists = face_recognition.face_distance(known_encodings_np, face_encodings[0])
            best = float(np.min(dists))
            log(f"Best face distance: {best:.3f}")

            if best <= ALLOWED_TOLERANCE:
                log("Authorized face detected and only person present — all good.")
                # nothing to do; continue monitoring
            else:
                log("Unknown face detected (not authorized) -> locking")
                lock_session()
                last_lock_time = datetime.now()
                time.sleep(LOCK_COOLDOWN)
                continue

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        log("presence_guard stopped by user")
    except Exception as e:
        log(f"presence_guard crashed: {e}")
    finally:
        cap.release()

if __name__ == "__main__":
    main()