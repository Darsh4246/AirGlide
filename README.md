# AirGlide — Touchless AI Cursor Navigation

A low-latency, real-time AI hand-gesture cursor navigation and desktop control system powered by **Google MediaPipe Tasks API** and **OpenCV**, designed with direct Windows Native API integration for zero-delay mouse control.

---

## Features

- **Ultra-Low Latency Mouse Control**: Uses direct Windows Native API calls (`ctypes.windll.user32.SetCursorPos` and `mouse_event`) rather than high-overhead wrappers.
- **High Sensitivity Active Zone**: Maps a comfortable central camera box to the entire display so you can reach all four screen corners effortlessly without your hand dropping off the camera frame.
- **Pinch Click vs. Hold-to-Drag**: Quick pinch & release triggers a clean single click; holding the pinch for > 0.3s converts to smooth drag-and-drop.
- **Fatigue-Free "Air Click"**: Simply tap/bend your index finger down like clicking a real mouse button — no thumb pinching strain required!
- **Dynamic Velocity-Adaptive Smoothing**: Adapts cursor speed dynamically — fast hand movements track instantly for quick navigation, while slow motions are smoothed to eliminate hand tremors and jitter.
- **Buffer-Lag Free Video Pipeline**: Camera frame buffer is capped to 1 to eliminate internal video queue delays.
- **Camera Auto-Detection**: Automatically detects active webcams (indices `0` and `1`) with DirectShow (`CAP_DSHOW`) and fallback backends.
- **Visual Feedback HUD**: Displays active zone borders, palm centroid, pinch distance, real-time action states, and fist countdown.
- **Clean Exit Support**: Close easily using <kbd>ESC</kbd>, <kbd>Q</kbd>, or clicking the window close (`X`) button.

---

## Gesture Controls

| Gesture | Action | Description |
| :--- | :--- | :--- |
| **Open Palm Movement** | **Move Cursor** | Palm centroid moves the cursor inside the central **Active Zone**. |
| **Index Air Tap** | **Left Click** | Open hand, bend/tap your index finger down (like clicking a real mouse button). |
| **Pinch (Thumb + Index)** | **Drag & Drop** | Pinch thumb and index together to grab & drag; open fingers to release/drop. |
| **Index Finger Pointing Up** | **Right Click** | Keep only your index finger raised (middle, ring, pinky closed). |
| **Ring Finger Up Only** | **Windows Start Menu** | Raise only the ring finger to trigger the <kbd>Win</kbd> key. |
| **Closed Fist (Hold 2.5s)** | **Close Window (Alt + F4)** | Make a closed fist and hold for 2.5 seconds to close the active application. |

---

## Project Structure

```text
DarshAI_Cursor_Nav_py13/
├── .venv/                  # Python Virtual Environment
├── hand_landmarker.task    # MediaPipe HandLandmarker model file (~7.8 MB)
├── main.py                 # Core tracking and cursor navigation engine
├── requirements.txt        # Verified project dependencies
├── test.py                 # MediaPipe task verification script
└── README.md               # Documentation and user guide
```

---

## Installation & Setup

### 1. Prerequisites
- **Operating System**: Windows 10 / 11
- **Python**: Python 3.12 or 3.13 (64-bit)
- A connected webcam

### 2. Create and Activate Virtual Environment
Open PowerShell in the project directory:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

> **Note:** If script execution is restricted in PowerShell, run:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` before activating.

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Verify MediaPipe Model File
Ensure `hand_landmarker.task` is in the project root directory. If missing, it can be downloaded from:
```powershell
# Direct download via PowerShell (if needed):
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "hand_landmarker.task"
```

---

## Running the Application

Always run using `python` within your active virtual environment:

```powershell
python .\main.py
```

Or run directly using the `.venv` executable without activation:

```powershell
.\.venv\Scripts\python.exe main.py
```

> ⚠️ **Important on Windows:** Do not use `py .\main.py` or type `.\main.py` directly:
> - `py` bypasses the `.venv` and uses your global system Python.
> - `.\main.py` tells Windows to open the file in your default code editor (such as VS Code).

---

## Live Sensitivity & Tuning Controls

AirGlide features **interactive GUI drag bars** on top of the camera preview window for tuning settings on the fly:

- **Sensitivity Slider (1 to 100)**: Drag to instantly scale your cursor sensitivity. As you drag the bar, the green **Active Zone** box expands or contracts live on the video feed so you can see your exact full-screen hand boundaries.
- **Deadzone Slider (1 to 10)**: Drag to eliminate any minor hand tremors or jitter when holding your hand still.

You can also adjust default startup parameters in `main.py`:

```python
# ==========================
# CONFIG
# ==========================
SHOW_PREVIEW = True     # Set False to run headless in the background without a window
CAM_W, CAM_H = 640, 360 # Camera resolution (lower resolution = faster processing)
DEADZONE = 2            # Default movement threshold in pixels before cursor updates
PINCH_DIST = 40         # Distance in pixels between thumb & index to trigger Drag & Drop
COOLDOWN = 0.35         # Minimum cooldown seconds between discrete gesture triggers
FIST_HOLD_TIME = 2.5    # Seconds required to hold a fist to trigger Alt+F4
```

---

## Troubleshooting

- **AttributeError: module 'cv2' has no attribute '__version__'**:  
  Occurs when `opencv-python-headless` or multiple OpenCV packages were installed simultaneously. Run:
  ```powershell
  pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless
  pip install opencv-python==4.11.0.86
  ```

- **Camera not detected**:  
  Verify your camera is not being used by another application (Zoom, Teams, Discord, etc.). The script automatically tests indices `0` and `1`.

- **Cursor jitter when holding still**:  
  Increase `DEADZONE` (e.g. from `2` to `4` or `5`) in `main.py`.
