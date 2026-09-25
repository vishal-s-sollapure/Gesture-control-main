"""
GestureControl AI - Configuration Module
Manages application defaults, gesture thresholds, settings persistence, and system constants.
"""

import json
import os
from pathlib import Path

# Application Metadata
APP_NAME = "GestureControl AI"
APP_VERSION = "1.0.0"

# Default File Paths
BASE_DIR = Path(__file__).resolve().parent
SETTINGS_FILE = BASE_DIR / "settings.json"

# Default Settings Schema
DEFAULT_SETTINGS = {
    # Camera settings
    "camera_index": 0,
    "camera_width": 640,
    "camera_height": 480,
    "camera_fps": 30,

    # Control Settings
    "control_enabled": False,
    "sensitivity": 1.4,         # Cursor movement multiplier
    "smoothing": 0.75,          # EMA smoothing factor (0.0 = raw, 0.95 = max smooth)
    "margin_x": 0.15,           # Active camera box margin (15% padding)
    "margin_y": 0.15,
    "dead_zone": 3.0,           # Pixel movement threshold to ignore jitter

    # Gesture Thresholds
    "pinch_threshold": 0.045,   # Distance between thumb and index tip (normalized)
    "double_click_interval": 0.4, # Seconds between two pinches for double click
    "scroll_sensitivity": 25.0, # Pixels scrolled per movement unit
    "scroll_deadzone": 0.02,    # Normalized Y distance to initiate scroll
    "swipe_threshold": 0.08,    # X movement delta for swipe detection
    "swipe_frames": 6,          # Frame history buffer for swipe detection
    "gesture_cooldown": 0.50,   # Seconds to wait between repeating discrete actions (0.5s default)
    "confidence_threshold": 0.7, # Minimum tracking confidence
    "debug_mode": False,        # Display detailed landmark debug overlay

    # Enabled Gestures Toggle
    "enabled_gestures": {
        "cursor_movement": True,
        "left_click": True,
        "right_click": True,
        "scroll": True,
        "drag_and_drop": True,
        "double_click": True,
        "media_play_pause": True,
        "next_track": True,
        "prev_track": True,
        "emergency_fist": True
    }
}

# Gesture Names and Descriptions
GESTURE_NAMES = {
    "CURSOR": "☝️ Cursor Movement",
    "PINCH": "🤏 Left Click",
    "RIGHT_CLICK": "✌️ Right Click",
    "OPEN_PALM": "✋ Scroll",
    "DRAG": "✊🤏 Drag & Drop",
    "DOUBLE_PINCH": "🤏🤏 Double Click",
    "THUMBS_UP": "👍 Play/Pause",
    "SWIPE_LEFT": "👈 Previous Track",
    "SWIPE_RIGHT": "👉 Next Track",
    "FIST": "✊ Emergency Pause",
    "IDLE": "🖐️ Neutral / Ready",
    "UNKNOWN": "❓ Unrecognized"
}


def load_settings() -> dict:
    """Loads settings from settings.json or returns default settings if missing/corrupt."""
    if not SETTINGS_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with default settings to ensure missing keys are populated
            settings = DEFAULT_SETTINGS.copy()
            settings.update(data)
            return settings
    except Exception as e:
        print(f"[Config] Error loading settings.json ({e}). Falling back to defaults.")
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> bool:
    """Saves dictionary settings to settings.json."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        print(f"[Config] Error saving settings: {e}")
        return False
