# GestureControl AI 🖐️💻
> **Touchless Desktop Computer Control using Computer Vision & AI Hand Tracking**

---

## 📌 Overview

**GestureControl AI** is a complete, real-time desktop application that allows users to interact with and control their laptop or desktop computer using intuitive hand gestures captured through a standard webcam.

It replaces standard physical mouse and keyboard inputs with computer vision algorithms, enabling **touchless navigation**, **mouse movements**, **clicking**, **scrolling**, **dragging & dropping**, **media playback controls**, and **safety pause mechanisms**.

Designed for accessibility, hygiene, presentations, and modern human-computer interaction, GestureControl AI works 100% locally and offline without requiring paid APIs or cloud dependencies.

---

## ✨ Features

- **10 Core Hand Gestures**: Fully mapped mouse, scroll, media, and system control actions.
- **Real-Time 3D Hand Tracking**: Uses MediaPipe 21-landmark tracking with high precision.
- **Exponential Motion Smoothing (EMA)**: Eliminates hand jitter and cursor shake for fluid mouse control.
- **Gesture State Machine & Cooldowns**: Prevents accidental actions and multi-click spam.
- **Safety First Architecture**:
  - **Master Enable/Disable Control Switch**.
  - **Emergency Keyboard Stop (`ESC` key)**.
  - **Closed Fist Emergency Pause Gesture (`✊`)**.
  - **Screen Boundary Clamping**.
- **Modern Desktop Dashboard UI**: Real-time webcam overlay, status cards, gesture reference guide, live activity log feed, and interactive settings tuning window.
- **Local Settings Persistence**: Customize sensitivity, smoothing, pinch thresholds, and individual gesture toggles saved to `settings.json`.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **OpenCV (`opencv-python`)** — Webcam capture, frame processing, and HUD annotations.
- **MediaPipe (`mediapipe`)** — Real-time 3D hand landmark detection and skeletal tracking.
- **PyAutoGUI (`pyautogui`)** — System-level mouse cursor movements, clicks, and keyboard inputs.
- **NumPy (`numpy`)** — Vector coordinate transformations, Euclidean distance, and angle calculations.
- **Tkinter & PIL (`Pillow`)** — Desktop dashboard GUI, status badges, and video streaming.

---

## 🏗️ Architecture

```text
       ┌────────────────────────┐
       │     Webcam Feed        │
       └───────────┬────────────┘
                   │ BGR Frames
                   ▼
       ┌────────────────────────┐
       │     OpenCV Camera      │
       └───────────┬────────────┘
                   │ OpenCV Frame
                   ▼
       ┌────────────────────────┐
       │ MediaPipe Hand Tracker │ ──► 21 3D Landmarks
       └───────────┬────────────┘
                   │ Landmark Coordinates
                   ▼
       ┌────────────────────────┐
       │   Gesture Recognizer   │ ──► Geometry & Vector Distances
       └───────────┬────────────┘
                   │ Raw Gesture & Confidence
                   ▼
       ┌────────────────────────┐
       │ Gesture State Machine  │ ──► Frame Filtering & Cooldown
       └───────────┬────────────┘
                   │ Confirmed Gesture Action
                   ▼
       ┌────────────────────────┐
       │  Gesture Controller    │ ──► Check Master Enable / Safety
       └───────────┬────────────┘
                   │ Screen Mapping & EMA Smoothing
                   ▼
       ┌────────────────────────────────────────────────────────┐
       │  System Action Dispatchers                             │
       │  ├── Mouse Controller (Move, Click, Drag, Scroll)      │
       │  ├── Keyboard Controller (Hotkeys, ESC Listener)       │
       │  └── Media Controller (Play/Pause, Next/Prev Track)    │
       └────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```text
GestureControlAI/
│
├── main.py                    # Application Entry Point
├── config.py                  # Settings defaults & local JSON storage
├── settings.json              # Saved user configuration parameters
├── requirements.txt           # Project dependencies
├── README.md                  # System documentation
│
├── core/
│   ├── __init__.py
│   ├── camera.py              # Threaded OpenCV video capture manager
│   ├── hand_tracker.py        # MediaPipe 3D landmark extraction & drawing
│   ├── gesture_recognizer.py  # Geometry, finger state & swipe detector
│   └── gesture_controller.py  # Central pipeline orchestrator & safety HUD
│
├── controls/
│   ├── __init__.py
│   ├── mouse_controller.py    # PyAutoGUI mouse actions & screen bounds
│   ├── keyboard_controller.py # Virtual keypresses & hotkey execution
│   └── media_controller.py    # OS media playback triggers
│
├── ui/
│   ├── __init__.py
│   ├── dashboard.py           # Tkinter desktop GUI dashboard
│   └── settings.py            # Settings configuration window
│
├── utils/
│   ├── __init__.py
│   ├── smoothing.py           # EMA smoother, ROI coordinate mapper & deadzone
│   └── logger.py              # Thread-safe logging & UI event queue
│
└── tests/
    ├── __init__.py
    ├── test_gestures.py       # Unit tests for gestures & state machine
    └── test_coordinates.py    # Unit tests for coordinate math & smoothing
```

---

## 📋 Supported Gestures Reference Table

| Gesture Icon | Gesture Name | Hand Pose Description | System Action |
| :--- | :--- | :--- | :--- |
| ☝️ | **Cursor Movement** | Index finger extended, other fingers folded | Moves mouse cursor smoothly |
| 🤏 | **Left Click** | Thumb tip & Index tip pinch together | Single left mouse click |
| ✌️ | **Right Click** | Index & Middle fingers extended (V sign) | Single right mouse click |
| ✋ | **Scroll** | Open palm moved vertically up/down | Scrolls page up / down |
| ✊🤏 | **Drag & Drop** | Thumb & Index pinch and hold | Mouse down (hold), release to drop |
| 🤏🤏 | **Double Click** | Two quick pinch gestures within 0.4s | Double left mouse click |
| 👍 | **Media Play/Pause** | Thumbs up (Thumb up, other fingers folded) | Play / Pause media playback |
| 👉 | **Next Track** | Horizontal swipe hand to the right | Skip to next media track |
| 👈 | **Previous Track** | Horizontal swipe hand to the left | Skip to previous media track |
| ✊ | **Emergency Pause** | Closed fist (all fingers folded) | Instantly pauses gesture control |

---

## 🚀 Installation & Quick Start

### 1. Clone or Open Project Directory

```bash
cd GestureControlAI
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Application

```bash
python main.py
```

*Optional Command-Line Arguments:*
- `--dry-run`: Runs in simulation mode (logs mouse/keyboard actions without physically moving system mouse).
- `--camera 1`: Specifies alternate webcam index.

---

## 🧪 Running Automated Unit Tests

Automated tests do **NOT** move your physical mouse or trigger real keystrokes. They use synthetic hand landmarks and mocked controllers:

```bash
python -m unittest discover tests
```

To run individual test files:
```bash
python -m unittest tests/test_gestures.py
python -m unittest tests/test_coordinates.py
```

---

## 🛡️ Safety & Master Controls

1. **Master Control Switch**: Click `ENABLE CONTROL` on the dashboard to start computer actions. Click `DISABLE CONTROL` anytime to pause.
2. **Emergency Keyboard Stop**: Pressing the `ESC` key at any point instantly revokes computer control.
3. **Closed Fist Pause**: Form a closed fist (`✊`) towards the webcam to pause gesture control automatically.
4. **Boundary Guard**: Mouse coordinates are clamped strictly within screen bounds to prevent off-screen cursor traps.

---

## ⚙️ Configuration & Tuning

Access settings via the **⚙ Settings** button on the dashboard:
- **Cursor Sensitivity**: Adjust cursor reach speed across screen boundaries.
- **Cursor Smoothing**: Change EMA smoothing factor (0.0 = raw, 0.95 = ultra-smooth).
- **Pinch Threshold**: Calibrate distance threshold for click detection.
- **Scroll Speed**: Tune vertical scroll sensitivity.
- **Gesture Cooldown**: Set minimum delay between repeated discrete actions.
- **Gesture Toggles**: Enable or disable specific gestures independently.

---

## ❓ Troubleshooting

- **Webcam Not Detected**:
  - Ensure no other application (Zoom, Teams, Skype) is using your webcam.
  - Change camera device index in Settings or run with `python main.py --camera 1`.
- **Media Keys Not Responding**:
  - Ensure media player (Spotify, YouTube, VLC) is active and focused.
- **Cursor Shaking**:
  - Increase **Cursor Smoothing** slider in Settings (e.g. set to `0.80`).
  - Ensure good room lighting for clear webcam video.

---

## 🔮 Future Improvements

- [ ] **Two-Hand Gestures**: Multi-hand gestures for zoom-in/out (pinch zoom) and window rotation.
- [ ] **Custom Gesture Recorder**: Record custom user hand poses for customized hotkey shortcuts.
- [ ] **Voice + Gesture Hybrid**: Combine voice commands ("click", "back") with hand pointing.
- [ ] **Presentation Mode**: Dedicated slide presentation profile (next slide, laser pointer).
- [ ] **App-Specific Profiles**: Custom gesture mappings per active application.

---

## 📄 License

MIT License — Free for educational, research, and personal use.
