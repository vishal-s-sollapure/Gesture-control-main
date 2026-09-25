# GestureControl AI 🖐️💻
> **Touchless Desktop Computer Control using Computer Vision & AI Hand Tracking**

---

## 📌 Overview

**GestureControl AI** is a complete, real-time desktop application that allows users to interact with and control their laptop or desktop computer using intuitive hand gestures captured through a standard webcam.

It replaces standard physical mouse and keyboard inputs with computer vision algorithms, enabling **touchless navigation**, **mouse movements**, **clicking**, **scrolling**, **dragging & dropping**, **media playback controls**, and **safety pause mechanisms**.

Designed for accessibility, hygiene, presentations, and modern human-computer interaction, GestureControl AI works 100% locally and offline without requiring paid APIs or cloud dependencies.

---

## ✨ Key Features & Architectural Improvements

- **10 Core Hand Gestures**: Fully mapped mouse, scroll, media, and system control actions.
- **Strict Gesture Priority Chain**: Eliminates gesture conflicts (e.g. index cursor movement never accidentally triggers a media track swipe).
- **Scale-Invariant Hand Geometry**: Uses hand-scale ratios (`distance / hand_scale`) to ensure accurate gesture recognition at any distance from the camera.
- **Decoupled Double Click Timing**: Reliable double pinch detection without conflict with general action cooldown.
- **Exponential Motion Smoothing (EMA)**: Eliminates hand jitter and cursor shake for fluid mouse control.
- **Temporal State Machine & Cooldown**: Requires 3 consecutive frames before confirming discrete actions to prevent noisy accidental clicks.
- **Safety First Architecture**:
  - **Default Launch State**: `CONTROL: PAUSED` (user must explicitly enable control).
  - **Emergency Keyboard Stop**: `ESC` key in Dashboard UI.
  - **Closed Fist Emergency Pause Gesture**: (`✊`).
  - **Automatic Drag Release**: Mouse drag state is automatically released on emergency stop, camera failure, or application shutdown.
  - **Screen Boundary Guard**: Cursor clamped strictly to display dimensions `[0, W-1] x [0, H-1]`.
- **Modern Desktop Dashboard UI**: Real-time webcam overlay, visual status cards, gesture reference guide, live activity log feed, and interactive settings tuning window.
- **Developer Debug Mode**: On-screen overlay showing landmarks, finger extension states, scale ratios, raw/confirmed gestures, and cooldown timers.

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
       │   Gesture Recognizer   │ ──► Scale-Invariant Geometry & Vector Ratios
       └───────────┬────────────┘
                   │ Priority-Filtered Gesture & Genuine Confidence
                   ▼
       ┌────────────────────────┐
       │ Gesture State Machine  │ ──► Consecutive Frame Filtering & Cooldown
       └───────────┬────────────┘
                   │ Confirmed Gesture Action
                   ▼
       ┌────────────────────────┐
       │  Gesture Controller    │ ──► Safety Checks & Drag Guard
       └───────────┬────────────┘
                   │ Screen Mapping & EMA Smoothing
                   ▼
       ┌────────────────────────────────────────────────────────┐
       │  System Action Dispatchers                             │
       │  ├── Mouse Controller (Move, Click, Drag, Scroll)      │
       │  ├── Keyboard Controller (Virtual Keypresses)          │
       │  └── Media Controller (Play/Pause, Next/Prev Track)    │
       └────────────────────────────────────────────────────────┘
```

---

## 📋 Supported Gestures Reference Table

| Gesture Icon | Gesture Name | Hand Pose Description | System Action |
| :--- | :--- | :--- | :--- |
| ☝️ | **Cursor Movement** | Index finger extended, other fingers folded | Moves mouse cursor smoothly |
| 🤏 | **Left Click** | Thumb tip & Index tip pinch together | Single left mouse click |
| ✌️ | **Right Click** | Index & Middle fingers extended (V sign) | Single right mouse click |
| ✋ | **Scroll** | Open palm moved vertically up/down | Scrolls page up / down |
| ✊🤏 | **Drag & Drop** | Sustained Thumb & Index pinch | Mouse down (hold), release to drop |
| 🤏🤏 | **Double Click** | Two quick pinch gestures within 0.4s | Double left mouse click |
| 👍 | **Media Play/Pause** | Thumbs up (Thumb up, other fingers folded) | Play / Pause media playback |
| 👉 | **Next Track** | Rapid horizontal open-palm swipe to right | Skip to next media track |
| 👈 | **Previous Track** | Rapid horizontal open-palm swipe to left | Skip to previous media track |
| ✊ | **Emergency Pause** | Closed fist (all fingers folded) | Instantly pauses gesture control |

---

## 🚀 Installation & Quick Start

### 1. Open Project Directory

```bash
cd GestureControlAI
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --no-build-isolation -r requirements.txt
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

Automated tests run with mocked/dry-run controllers and do **NOT** execute real system mouse movements:

```bash
python -m unittest discover tests
```

To run individual test modules:
```bash
python -m unittest tests/test_gestures.py
python -m unittest tests/test_coordinates.py
```

---

## 🛡️ Safety & Master Controls

1. **Default Startup State**: The application launches in **`CONTROL: PAUSED`** state. You must explicitly click `ENABLE GESTURE CONTROL` to begin computer interaction.
2. **Emergency Keyboard Stop**: Pressing `ESC` while the Dashboard window is focused immediately pauses control.
3. **Emergency GUI Button**: Clicking the red `🚨 EMERGENCY STOP (ESC)` button on the dashboard immediately halts actions.
4. **Closed Fist Pause**: Form a closed fist (`✊`) towards the webcam to pause gesture control automatically.
5. **Automatic Drag Cleanup**: Any active mouse drag is automatically released if control is paused, emergency stop is triggered, camera disconnects, or the application is closed.
6. **Boundary Guard**: Mouse coordinates are clamped strictly within screen bounds `[0, Screen_Width-1] x [0, Screen_Height-1]`.

---

## ⚙️ Configuration & Tuning

Access settings via the **⚙ Settings** button on the dashboard:
- **Cursor Sensitivity**: Adjust cursor reach speed across screen boundaries.
- **Cursor Smoothing**: Change EMA smoothing factor (0.0 = raw, 0.95 = ultra-smooth).
- **Pinch Threshold Ratio**: Calibrate scale-relative distance threshold for click detection.
- **Scroll Speed**: Tune vertical scroll sensitivity.
- **Gesture Cooldown**: Set delay between repeated discrete actions (default 0.5s).
- **Double Click Interval**: Set maximum time allowed between pinches for double click (default 0.4s).
- **Developer Debug Mode**: Toggle on-screen landmark and state diagnostics overlay.
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

## 📄 License

MIT License — Free for educational, research, hackathon, and personal use.
