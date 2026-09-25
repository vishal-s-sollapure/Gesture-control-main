"""
GestureControl AI - Keyboard Controller Module
Handles keyboard shortcuts, hotkeys, and system key events.
"""

from utils.logger import setup_logger, log_ui

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    pyautogui = None
    HAS_PYAUTOGUI = False

logger = setup_logger("KeyboardController")


class KeyboardController:
    """
    Handles virtual keyboard actions and shortcut invocations.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run or not HAS_PYAUTOGUI
        logger.info(f"KeyboardController initialized (DryRun: {self.dry_run})")

    def press_key(self, key_name: str):
        """Presses a single key (e.g. 'space', 'esc', 'tab')."""
        if self.dry_run:
            logger.info(f"[DryRun] Key Press: {key_name}")
            log_ui(f"Key Press ({key_name}) [DryRun]", "ACTION")
            return

        try:
            pyautogui.press(key_name)
            log_ui(f"Key Press: {key_name}", "ACTION")
        except Exception as e:
            logger.error(f"Error pressing key '{key_name}': {e}")

    def hotkey(self, *keys):
        """Triggers a key combination (e.g. 'alt', 'tab')."""
        key_str = "+".join(keys)
        if self.dry_run:
            logger.info(f"[DryRun] Hotkey: {key_str}")
            log_ui(f"Hotkey ({key_str}) [DryRun]", "ACTION")
            return

        try:
            pyautogui.hotkey(*keys)
            log_ui(f"Hotkey: {key_str}", "ACTION")
        except Exception as e:
            logger.error(f"Error executing hotkey '{key_str}': {e}")
