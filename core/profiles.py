"""
GestureControl AI - Configurable Gesture Profiles Module
Decouples raw gesture recognition from system action dispatches.
Supports Desktop, Presentation, Media, and Custom user profiles.
"""

from typing import Dict, Any


DEFAULT_PROFILE_MAPPINGS: Dict[str, Dict[str, str]] = {
    "Desktop": {
        "CURSOR": "Cursor Movement",
        "PINCH": "Left Mouse Click",
        "RIGHT_CLICK": "Right Mouse Click",
        "OPEN_PALM": "Scroll Up / Down",
        "THREE_FINGERS": "Unassigned",
        "DRAG": "Drag & Drop",
        "DOUBLE_PINCH": "Double Click",
        "THUMBS_UP": "Media Play / Pause",
        "SWIPE_LEFT": "Previous Track",
        "SWIPE_RIGHT": "Next Track",
        "FIST": "Emergency Pause"
    },
    "Presentation": {
        "CURSOR": "Laser Pointer Cursor",
        "PINCH": "Select Slide Element",
        "RIGHT_CLICK": "Presentation Context Menu",
        "OPEN_PALM": "Next Slide (Right Arrow)",
        "THREE_FINGERS": "Previous Slide (Left Arrow)",
        "DRAG": "Unassigned",
        "DOUBLE_PINCH": "Unassigned",
        "THUMBS_UP": "Toggle Presentation Blank",
        "SWIPE_LEFT": "Previous Slide",
        "SWIPE_RIGHT": "Next Slide",
        "FIST": "Emergency Pause"
    },
    "Media": {
        "CURSOR": "Cursor Movement",
        "PINCH": "Play / Pause Media",
        "RIGHT_CLICK": "Mute / Unmute",
        "OPEN_PALM": "Adjust Volume",
        "THREE_FINGERS": "Unassigned",
        "DRAG": "Seek Video Position",
        "DOUBLE_PINCH": "Toggle Fullscreen",
        "THUMBS_UP": "Play / Pause Media",
        "SWIPE_LEFT": "Previous Track",
        "SWIPE_RIGHT": "Next Track",
        "FIST": "Emergency Pause"
    },
    "Custom": {
        "CURSOR": "Cursor Movement",
        "PINCH": "Left Mouse Click",
        "RIGHT_CLICK": "Right Mouse Click",
        "OPEN_PALM": "Scroll Up / Down",
        "THREE_FINGERS": "Previous Slide",
        "DRAG": "Drag & Drop",
        "DOUBLE_PINCH": "Double Click",
        "THUMBS_UP": "Play / Pause Media",
        "SWIPE_LEFT": "Previous Track",
        "SWIPE_RIGHT": "Next Track",
        "FIST": "Emergency Pause"
    }
}


class ProfileManager:
    """
    Manages active profile settings and gesture-to-action mappings.
    """

    def __init__(self, active_profile: str = "Desktop", custom_mappings: Dict[str, str] = None):
        self.active_profile = active_profile if active_profile in DEFAULT_PROFILE_MAPPINGS else "Desktop"
        self.mappings = DEFAULT_PROFILE_MAPPINGS.copy()
        if custom_mappings:
            self.mappings["Custom"].update(custom_mappings)

    def set_profile(self, profile_name: str) -> bool:
        """Sets active profile if valid."""
        if profile_name in self.mappings:
            self.active_profile = profile_name
            return True
        return False

    def get_action_label(self, gesture_name: str) -> str:
        """Returns action description for active profile and given gesture."""
        profile_map = self.mappings.get(self.active_profile, self.mappings["Desktop"])
        return profile_map.get(gesture_name, "Unassigned")

    def get_active_mappings(self) -> Dict[str, str]:
        """Returns mapping dictionary for currently active profile."""
        return self.mappings.get(self.active_profile, self.mappings["Desktop"]).copy()

    def update_custom_mapping(self, gesture_name: str, action_description: str):
        """Updates custom profile gesture mapping."""
        self.mappings["Custom"][gesture_name] = action_description
