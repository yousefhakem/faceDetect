#!/usr/bin/env python3
"""
presence_guard.py (fast version)
- Locks the session unless EXACTLY ONE authorized face is present.
- Faster detection: small resolution, buffer flush, HOG+upsample, optional CNN fallback.
- Does NOT attempt to unlock (use PAM methods like Howdy/fingerprint).
"""

import os, sys, time, glob, subprocess
from datetime import datetime, timedelta
import numpy as np
import cv2
import face_recognition

# ===== CONFIG (tune as needed) =====
ENROLL_DIR = os.path.expanduser("~/.face_enroll")
ALLOWED_TOLERANCE = 0.65      # lower = stricter match
CHECK_INTERVAL = 0.35         # seconds between checks (fast)
LOCK_COOLDOWN = 4             # seconds to wait after locking before re-checking
ABSENCE_TIMEOUT = 6           # if 0 faces for this long -> lock (seconds)
USE_BLUETOOTH = False         # optional 2nd factor
PHONE_MAC = "AA:BB:CC:11:22:33"

VIDEO_DEVICE = None           # None = auto-detect 0..3 ; or set to an int like 0
FRAME_WIDTH = 640             # 640x480 is a good speed/accuracy balance
FRAME_HEIGHT = 480
HOG_UPSAMPLE = 1              # 0..2 ; higher = more recall, slower
USE_CNN_FALLBACK = True       # try 'cnn' first if HOG finds nothing (slower but robust)
ENCODING_EVERY_N = 1          # run face-ID every N frames (speed boost)
LOGFILE = os.path.expanduser("~/presence_guard.log")
# ===================================

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} - {msg}"
    print(line, flush=True)
    try:
        with open(LOGFILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def is_phone_present(mac):
    try:
        proc = subprocess.run(["bluetoothctl", "info", mac],
                              capture_output=True, text=True, timeout=6)
        out = (proc.stdout or "") + (proc.stderr or "")
        return "Connected: yes" in out
    except Exception as e:
        log(f"bluetooth check error: {e}")
        return False

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
        except Exception:
            continue
    log("All lock commands failed.")
    return False

def open_camera():
    """Open specific device or auto-detect 0..3. Set size and small buffer."""
    indices = [VIDEO_DEVICE] if isinstance(VIDEO_DEVICE, int) else [0,1,2,3]
    for idx in indices:
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if cap.isOpened():
            # set resolution + try to reduce buffering/latency
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            # warmup: read a few frames
            for _ in range(8):
                cap.read()
            return cap, idx
        if cap:
            cap.release()
    return None, None

def latest_frame(cap):
    """Flush stale frames then retrieve the freshest."""
    # some drivers honor grab()+retrieve() for fresher frames
    for _ in range(3):
        cap.grab()
    ok, f = cap.retrieve()
    if not ok:
        ok, f = cap.read()
    return f if ok else None

def load_known_encodings(enroll_dir):
    files = [p for p in glob.glob(os.path.join(enroll_dir, "*")) if os.path.isfile(p)]
    encodings = []
    for f in files:
        try:
            img = face_recognition.load_image_file(f)
            # detect with HOG for enrollment (fast)
            locs = face_recognition.face_locations(img, number_of_times_to_upsample=1, model="hog")
            if not locs:
                log(f"No face found in enroll image: {f}")
                continue
            enc = face_recognition.face_encodings(img, known_face_locations=locs)
            if enc:
                encodings.append(enc[0])
                log(f"Loaded enrollment face from {os.path.basename(f)}")
        except Exception as e:
            log(f"Error loading {f}: {e}")
    return np.array(encodings) if encodings else None

def detect_faces_rgb(rgb):
    """Return face locations using fast HOG; optional CNN fallback."""
    locs = face_recognition.face_locations(
        rgb, number_of_times_to_upsample=HOG_UPSAMPLE, model="hog"
    )
    if not locs and USE_CNN_FALLBACK:
        # One pass of CNN with mild upsample for hard angles/low light
        locs = face_recognition.face_locations(
            rgb, number_of_times_to_upsample=1, model="cnn"
        )
    return locs

def main():
    # Enrollment
    if not os.path.isdir(ENROLL_DIR):
        log(f"Enrollment dir {ENROLL_DIR} not found. Create it and add photos of your face.")
        sys.exit(1)

    known = load_known_encodings(ENROLL_DIR)
    if known is None or len(known) == 0:
        log("No known face encodings loaded. Exiting.")
        sys.exit(1)

    # Camera
    cap, cam_idx = open_camera()
    if not cap:
        log("Cannot open webcam (/dev/video0..3). Exiting.")
        sys.exit(1)
    log(f"Opened camera /dev/video{cam_idx} at {FRAME_WIDTH}x{FRAME_HEIGHT}")

    log("Starting presence_guard")
    last_seen_someone = datetime.now()
    frame_i = 0

    try:
        while True:
            # optional BT presence
            if USE_BLUETOOTH and not is_phone_present(PHONE_MAC):
                log("Phone not present; locking for safety.")
                lock_session()
                time.sleep(LOCK_COOLDOWN)
                continue

            frame = latest_frame(cap)
            if frame is None:
                log("Failed to read from webcam, retrying...")
                time.sleep(CHECK_INTERVAL)
                continue

            rgb = frame[:, :, ::-1]  # BGR -> RGB (no downscale; already 640x480)
            rgb = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
            # Fast face count
            face_locations = detect_faces_rgb(rgb)
            n_faces = len(face_locations)
            log(f"Detected {n_faces} face(s)")

            now = datetime.now()

            # Lock immediately if not exactly one face
            if n_faces != 1:
                # If nobody is here for ABSENCE_TIMEOUT, lock.
                # If more than one face, lock immediately.
                if n_faces == 0:
                    if (now - last_seen_someone).total_seconds() >= ABSENCE_TIMEOUT:
                        log("No faces for timeout -> locking")
                        lock_session()
                        time.sleep(LOCK_COOLDOWN)
                        # don't update last_seen_someone here; we stay in "absent" state
                    else:
                        log("No face seen yet; waiting for timeout...")
                else:
                    log("Multiple faces detected -> locking")
                    lock_session()
                    time.sleep(LOCK_COOLDOWN)
                time.sleep(CHECK_INTERVAL)
                continue

            # Exactly one face: occasionally verify identity (every N frames)
            authorized = False
            if frame_i % ENCODING_EVERY_N == 0:
                encs = face_recognition.face_encodings(rgb, face_locations)
                if encs:
                    dists = np.linalg.norm(known - encs[0], axis=1)
                    best = float(np.min(dists))
                    log(f"Best face distance: {best:.3f}")
                    authorized = (best <= ALLOWED_TOLERANCE)
                else:
                    log("Could not compute encoding on this frame; treating as unauthorized.")

            # Presence & lock decisions
            if authorized:
                last_seen_someone = now
                log("Authorized face present — all good.")
            else:
                # exactly one face but not (yet) authorized: be strict and lock
                log("Single face not authorized -> locking")
                lock_session()
                time.sleep(LOCK_COOLDOWN)

            frame_i += 1
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        log("presence_guard stopped by user")
    except Exception as e:
        log(f"presence_guard crashed: {e}")
    finally:
        cap.release()

if __name__ == "__main__":
    main()