"""
GestureControl AI - Mouse Controller Module
Handles system mouse cursor movement, clicks, dragging, and scrolling via PyAutoGUI.
Includes dry-run support for automated testing and screen boundary clamping.
"""

import logging

try:
    import pyautogui
    # Configure pyautogui for real-time smoothness
    pyautogui.PAUSE = 0.001
    pyautogui.FAILSAFE = True
    HAS_PYAUTOGUI = True
except ImportError:
    pyautogui = None
    HAS_PYAUTOGUI = False

from utils.logger import setup_logger, log_ui

logger = setup_logger("MouseController")


class MouseController:
    """
    Wrapper for system mouse actions with safety bounds, drag state tracking,
    and mock/dry-run capabilities.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run or not HAS_PYAUTOGUI
        self.is_dragging = False

        if HAS_PYAUTOGUI and not self.dry_run:
            self.screen_width, self.screen_height = pyautogui.size()
        else:
            self.screen_width, self.screen_height = 1920, 1080

        logger.info(
            f"MouseController initialized (Screen: {self.screen_width}x{self.screen_height}, DryRun: {self.dry_run})"
        )

    def get_screen_size(self):
        """Returns (width, height) of primary display."""
        return self.screen_width, self.screen_height

    def move_to(self, x: float, y: float):
        """
        Moves cursor to specified target coordinates safely clamped inside screen bounds.
        """
        clamped_x = max(0, min(self.screen_width - 1, int(x)))
        clamped_y = max(0, min(self.screen_height - 1, int(y)))

        if self.dry_run:
            logger.debug(f"[DryRun] Move mouse to ({clamped_x}, {clamped_y})")
            return

        try:
            pyautogui.moveTo(clamped_x, clamped_y, _pause=False)
        except Exception as e:
            logger.error(f"Error moving mouse to ({clamped_x}, {clamped_y}): {e}")

    def left_click(self):
        """Triggers a single left mouse click."""
        if self.dry_run:
            logger.info("[DryRun] Left Click executed")
            log_ui("Left Click [DryRun]", "ACTION")
            return

        try:
            pyautogui.click(button="left")
            log_ui("Left Click", "ACTION")
        except Exception as e:
            logger.error(f"Error executing left click: {e}")

    def right_click(self):
        """Triggers a single right mouse click."""
        if self.dry_run:
            logger.info("[DryRun] Right Click executed")
            log_ui("Right Click [DryRun]", "ACTION")
            return

        try:
            pyautogui.click(button="right")
            log_ui("Right Click", "ACTION")
        except Exception as e:
            logger.error(f"Error executing right click: {e}")

    def double_click(self):
        """Triggers a double left click."""
        if self.dry_run:
            logger.info("[DryRun] Double Click executed")
            log_ui("Double Click [DryRun]", "ACTION")
            return

        try:
            pyautogui.doubleClick()
            log_ui("Double Click", "ACTION")
        except Exception as e:
            logger.error(f"Error executing double click: {e}")

    def start_drag(self):
        """Presses and holds the left mouse button down for dragging."""
        if not self.is_dragging:
            self.is_dragging = True
            if self.dry_run:
                logger.info("[DryRun] Start Drag")
                log_ui("Drag Started [DryRun]", "ACTION")
                return

            try:
                pyautogui.mouseDown(button="left")
                log_ui("Drag Started", "ACTION")
            except Exception as e:
                logger.error(f"Error starting drag: {e}")

    def stop_drag(self):
        """Releases the left mouse button to complete drag-and-drop."""
        if self.is_dragging:
            self.is_dragging = False
            if self.dry_run:
                logger.info("[DryRun] Stop Drag")
                log_ui("Drag Released [DryRun]", "ACTION")
                return

            try:
                pyautogui.mouseUp(button="left")
                log_ui("Drag Released", "ACTION")
            except Exception as e:
                logger.error(f"Error releasing drag: {e}")

    def scroll(self, clicks: int):
        """
        Scrolls vertically. Positive clicks = scroll up, negative clicks = scroll down.
        """
        if clicks == 0:
            return

        if self.dry_run:
            logger.debug(f"[DryRun] Scroll {clicks} units")
            log_ui(f"Scroll {'Up' if clicks > 0 else 'Down'} ({clicks}) [DryRun]", "ACTION")
            return

        try:
            pyautogui.scroll(clicks)
            log_ui(f"Scroll {'Up' if clicks > 0 else 'Down'}", "ACTION")
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
