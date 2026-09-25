"""
GestureControl AI - Media Controller Module
Handles media playback keys: Play/Pause, Next Track, Previous Track.
"""

from utils.logger import setup_logger, log_ui

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    pyautogui = None
    HAS_PYAUTOGUI = False

logger = setup_logger("MediaController")


class MediaController:
    """
    Triggers OS-level media playback keys (play/pause, next track, prev track).
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run or not HAS_PYAUTOGUI
        logger.info(f"MediaController initialized (DryRun: {self.dry_run})")

    def play_pause(self):
        """Toggles media play/pause state."""
        if self.dry_run:
            logger.info("[DryRun] Media Play/Pause triggered")
            log_ui("Media Play/Pause [DryRun]", "MEDIA")
            return

        try:
            pyautogui.press("playpause")
            log_ui("Media Play/Pause", "MEDIA")
        except Exception as e:
            logger.warning(f"Default 'playpause' key failed ({e}), falling back to 'space'")
            try:
                pyautogui.press("space")
                log_ui("Media Play/Pause (Space)", "MEDIA")
            except Exception as ex:
                logger.error(f"Media play/pause fallback failed: {ex}")

    def next_track(self):
        """Skips to the next media track."""
        if self.dry_run:
            logger.info("[DryRun] Media Next Track triggered")
            log_ui("Next Track [DryRun]", "MEDIA")
            return

        try:
            pyautogui.press("nexttrack")
            log_ui("Next Track", "MEDIA")
        except Exception as e:
            logger.error(f"Error pressing nexttrack key: {e}")

    def previous_track(self):
        """Skips to the previous media track."""
        if self.dry_run:
            logger.info("[DryRun] Media Previous Track triggered")
            log_ui("Previous Track [DryRun]", "MEDIA")
            return

        try:
            pyautogui.press("prevtrack")
            log_ui("Previous Track", "MEDIA")
        except Exception as e:
            logger.error(f"Error pressing prevtrack key: {e}")
