"""
GestureControl AI - Unit Tests for Configurable Gesture Profiles
"""

import unittest
from core.profiles import ProfileManager, DEFAULT_PROFILE_MAPPINGS


class TestProfiles(unittest.TestCase):

    def setUp(self):
        self.pm = ProfileManager(active_profile="Desktop")

    def test_default_profile_mappings(self):
        """Desktop profile maps PINCH to Left Mouse Click."""
        label = self.pm.get_action_label("PINCH")
        self.assertEqual(label, "Left Mouse Click")

    def test_presentation_profile_mappings(self):
        """Presentation profile maps OPEN_PALM to Next Slide."""
        self.pm.set_profile("Presentation")
        label = self.pm.get_action_label("OPEN_PALM")
        self.assertIn("Next Slide", label)

    def test_media_profile_mappings(self):
        """Media profile maps THUMBS_UP to Play / Pause Media."""
        self.pm.set_profile("Media")
        label = self.pm.get_action_label("THUMBS_UP")
        self.assertIn("Play / Pause", label)

    def test_custom_profile_update(self):
        """Custom profile allows updating mappings."""
        self.pm.set_profile("Custom")
        self.pm.update_custom_mapping("THREE_FINGERS", "Volume Up")
        label = self.pm.get_action_label("THREE_FINGERS")
        self.assertEqual(label, "Volume Up")


if __name__ == "__main__":
    unittest.main()
