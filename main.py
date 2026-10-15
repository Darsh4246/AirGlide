import os
import sys
import cv2
import time
import math
import ctypes
import pyautogui
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Direct Windows API for zero-latency mouse control
user32 = ctypes.windll.user32

def move_mouse(x, y):
    user32.SetCursorPos(int(x), int(y))

def mouse_down():
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN

def mouse_up():
    user32.mouse_event(0x0004, 0, 0, 0, 0)    # MOUSEEVENTF_LEFTUP

def right_click():
    user32.mouse_event(0x0008, 0, 0, 0, 0)  # MOUSEEVENTF_RIGHTDOWN
    user32.mouse_event(0x0010, 0, 0, 0, 0)  # MOUSEEVENTF_RIGHTUP

# ==========================
# CONFIG
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "hand_landmarker.task")
SHOW_PREVIEW = True  # Set to True to display camera feed with tracking visuals

CAM_W, CAM_H = 640, 360
DEADZONE = 2
EDGE_PADDING = 30

PINCH_DIST = 42
PINCH_FRAMES = 1     # Instant click/drag response
COOLDOWN = 0.4
FRAME_SKIP = 1       # Process every frame for maximum smoothness

fist_start_time = None
FIST_HOLD_TIME = 2.5  # seconds

# ==========================
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0
screen_w, screen_h = pyautogui.size()

# ==========================
# Validate Model
# ==========================
if not os.path.exists(MODEL_PATH):
    print(f"[ERROR] Hand landmarker model file not found at: {MODEL_PATH}")
    print("Please download hand_landmarker.task and place it in the project root.")
    sys.exit(1)

# ==========================
# MediaPipe Detector Setup
# ==========================
print("[INFO] Initializing MediaPipe HandLandmarker (optimized for low latency)...")
base = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base,
    num_hands=1,
    running_mode=vision.RunningMode.VIDEO,
    min_hand_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
detector = vision.HandLandmarker.create_from_options(options)

# ==========================
# Camera Setup (Auto-Detect)
# ==========================
def open_camera(indices=(0, 1)):
    for idx in indices:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"[INFO] Camera successfully opened at index {idx} (CAP_DSHOW).")
                return cap, idx
            cap.release()

        # Fallback to default backend
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"[INFO] Camera successfully opened at index {idx} (Default backend).")
                return cap, idx
            cap.release()
    return None, None

cap, active_cam_idx = open_camera([0, 1])
if cap is None:
    print("[ERROR] Could not open camera at index 0 or 1. Please verify your webcam is connected and not in use by another app.")
    sys.exit(1)

# Eliminate camera buffer lag and configure resolution
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
cap.set(cv2.CAP_PROP_FPS, 30)

prev_x, prev_y = screen_w // 2, screen_h // 2
last_action = 0
dragging = False
pinch_count = 0
start_time = time.time()

# ==========================
# Helpers
# ==========================
def cooldown():
    global last_action
    if time.time() - last_action > COOLDOWN:
        last_action = time.time()
        return True
    return False

def finger_up(lm, tip, pip):
    return lm[tip].y < lm[pip].y

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def palm_center(lm, w, h):
    ids = [0, 5, 9, 13, 17]
    x = sum(lm[i].x for i in ids) / 5
    y = sum(lm[i].y for i in ids) / 5
    return int(x * w), int(y * h)

def map_range(v, a, b, c, d):
    return max(c, min(d, (v - a) * (d - c) / (b - a) + c))

# ==========================
# MAIN LOOP
# ==========================
while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("[WARNING] Failed to grab frame from camera. Exiting loop.")
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # Use actual monotonic millisecond timestamp
    frame_ts = int((time.time() - start_time) * 1000)
    result = detector.detect_for_video(mp_image, frame_ts)

    if result.hand_landmarks:
        lm = result.hand_landmarks[0]

        # ----- CURSOR (PALM)
        palm_x, palm_y = palm_center(lm, w, h)

        sx = map_range(palm_x, EDGE_PADDING, w - EDGE_PADDING, 0, screen_w)
        sy = map_range(palm_y, EDGE_PADDING, h - EDGE_PADDING, 0, screen_h)

        dx, dy = sx - prev_x, sy - prev_y
        dist_moved = math.hypot(dx, dy)
        if dist_moved > DEADZONE:
            # Dynamic responsiveness: adapts smoothing to movement speed
            alpha = min(0.85, max(0.45, dist_moved / 80.0))
            prev_x += dx * alpha
            prev_y += dy * alpha
            move_mouse(prev_x, prev_y)

        def pt(i): return (int(lm[i].x * w), int(lm[i].y * h))
        index, thumb = pt(8), pt(4)

        fingers = {
            "index": finger_up(lm, 8, 6),
            "middle": finger_up(lm, 12, 10),
            "ring": finger_up(lm, 16, 14),
            "pinky": finger_up(lm, 20, 18)
        }

        # ----- LEFT CLICK / DRAG (FAST RESPONSE)
        if dist(index, thumb) < PINCH_DIST:
            pinch_count += 1
            if pinch_count >= PINCH_FRAMES and not dragging:
                mouse_down()
                dragging = True
        else:
            pinch_count = 0
            if dragging:
                mouse_up()
                dragging = False

        # ----- RIGHT CLICK
        if fingers["index"] and not any([fingers["middle"], fingers["ring"], fingers["pinky"]]) and cooldown():
            right_click()

        # ----- START MENU
        if fingers["ring"] and not any([fingers["index"], fingers["middle"], fingers["pinky"]]) and cooldown():
            pyautogui.press("win")

        # ----- ALT + F4
        if not any(fingers.values()):  # fist detected
            if fist_start_time is None:
                fist_start_time = time.time()
            elif time.time() - fist_start_time >= FIST_HOLD_TIME:
                pyautogui.hotkey("alt", "f4")
                fist_start_time = None  # reset after trigger
        else:
            fist_start_time = None

        # Visual feedback on frame if preview is enabled
        if SHOW_PREVIEW:
            cv2.circle(frame, (palm_x, palm_y), 8, (0, 255, 0), -1)  # Palm center
            cv2.circle(frame, index, 6, (255, 0, 0), -1)              # Index tip
            cv2.circle(frame, thumb, 6, (0, 0, 255), -1)              # Thumb tip
            cv2.line(frame, index, thumb, (255, 255, 0), 2)           # Pinch indicator
            state_text = f"Drag: {'ON' if dragging else 'OFF'} | Pinch: {dist(index, thumb):.0f}"
            cv2.putText(frame, state_text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            if fist_start_time is not None:
                remaining = max(0.0, FIST_HOLD_TIME - (time.time() - fist_start_time))
                cv2.putText(frame, f"Fist hold: {remaining:.1f}s", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    if SHOW_PREVIEW:
        cv2.imshow("DarshAI Cursor Navigation (Press ESC or Q to quit)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27 or key == ord('q'):
            print("[INFO] Exit requested by user.")
            break
        # Handle clicking window close 'X' button
        if cv2.getWindowProperty("DarshAI Cursor Navigation (Press ESC or Q to quit)", cv2.WND_PROP_VISIBLE) < 1:
            print("[INFO] Preview window closed.")
            break
    else:
        if cv2.waitKey(1) == 27:
            break

print("[INFO] Releasing camera and closing windows...")
cap.release()
cv2.destroyAllWindows()
