"""
GestureControl AI — Main Entry Point
Launches the Touchless Computer Control desktop dashboard and gesture engine.
"""

import argparse
import sys
import tkinter as tk
from tkinter import messagebox

from config import APP_NAME, APP_VERSION
from ui.dashboard import DashboardApp
from utils.logger import setup_logger

logger = setup_logger("Main")


def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION} - Touchless Computer Control")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in simulation mode (log mouse/keyboard actions without executing them)"
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Specify webcam device index (default: 0)"
    )
    return parser.parse_args()


def main():
    """Main application execution sequence."""
    args = parse_args()
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} (DryRun: {args.dry_run}, CameraIdx: {args.camera})...")

    root = tk.Tk()

    # Set application icon / title if supported
    try:
        root.title(f"{APP_NAME} v{APP_VERSION}")
    except Exception:
        pass

    app = DashboardApp(root=root, dry_run=args.dry_run)

    # Clean window close handler
    root.protocol("WM_DELETE_WINDOW", app.on_close)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Application interrupted by terminal keyboard signal.")
        app.on_close()
    except Exception as e:
        logger.critical(f"Unhandled runtime exception: {e}", exc_info=True)
        messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n{e}")
        app.on_close()


if __name__ == "__main__":
    main()
