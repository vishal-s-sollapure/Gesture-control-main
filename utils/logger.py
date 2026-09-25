"""
GestureControl AI - Logging Utility
Provides structured logging for console output and thread-safe UI message buffers.
"""

import logging
import queue
import time

# Thread-safe queue for UI event feed
UI_LOG_QUEUE = queue.Queue(maxsize=100)


def setup_logger(name: str = "GestureControlAI", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a standard application logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def log_ui(message: str, level: str = "INFO"):
    """Pushes a user-facing event message to the UI log queue."""
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] [{level}] {message}"
    try:
        if UI_LOG_QUEUE.full():
            UI_LOG_QUEUE.get_nowait()
        UI_LOG_QUEUE.put_nowait(formatted_msg)
    except Exception:
        pass


def get_ui_logs():
    """Retrieves all pending messages from the UI queue without blocking."""
    messages = []
    while not UI_LOG_QUEUE.empty():
        try:
            messages.append(UI_LOG_QUEUE.get_nowait())
        except queue.Empty:
            break
    return messages
