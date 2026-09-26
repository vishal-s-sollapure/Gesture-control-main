"""
GestureControl AI - First-Run Calibration UI Window
Interactive modal dialog providing visual step instructions, hand boundary positioning,
and threshold sampling wizard without real mouse control.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
from utils.logger import log_ui


class CalibrationWindow:
    """
    Modal dialog window for guided hand tracking calibration.
    """

    def __init__(self, parent: tk.Tk, controller, on_finish_callback: Callable = None):
        self.parent = parent
        self.controller = controller
        self.on_finish_callback = on_finish_callback

        self.win = tk.Toplevel(parent)
        self.win.title("GestureControl AI — Calibration Wizard")
        self.win.geometry("540x380")
        self.win.resizable(False, False)
        self.win.configure(bg="#1A1A24")
        self.win.grab_set()

        self.calibration = controller.calibration
        self.calibration.start_calibration()

        self._build_ui()
        self._update_loop()

    def _build_ui(self):
        """Constructs UI layout."""
        header = tk.Frame(self.win, bg="#242432", padx=20, pady=12)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="🧭 FIRST-RUN HAND CALIBRATION",
            font=("Segoe UI", 14, "bold"),
            bg="#242432",
            fg="#00ADB5"
        )
        title.pack(anchor="w")

        sub = tk.Label(
            header,
            text="Calibrate comfortable reach area & pinch thresholds (Control strictly PAUSED)",
            font=("Segoe UI", 9),
            bg="#242432",
            fg="#A0A0B5"
        )
        sub.pack(anchor="w")

        body = tk.Frame(self.win, bg="#1A1A24", padx=25, pady=20)
        body.pack(fill=tk.BOTH, expand=True)

        self.lbl_step = tk.Label(
            body,
            text="Step 1 of 5 — Center Hand",
            font=("Segoe UI", 12, "bold"),
            bg="#1A1A24",
            fg="#FFFFFF"
        )
        self.lbl_step.pack(anchor="w", pady=(0, 10))

        self.lbl_instruction = tk.Label(
            body,
            text=self.calibration.get_instruction(),
            font=("Segoe UI", 10),
            bg="#242432",
            fg="#00E676",
            wraplength=480,
            justify="left",
            padx=15,
            pady=15,
            bd=1,
            relief="solid"
        )
        self.lbl_instruction.pack(fill=tk.X, pady=(0, 20))

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(body, variable=self.progress_var, maximum=1.0)
        self.progress_bar.pack(fill=tk.X, pady=(0, 20))

        btn_bar = tk.Frame(body, bg="#1A1A24")
        btn_bar.pack(fill=tk.X)

        btn_skip = tk.Button(
            btn_bar,
            text="Skip Calibration",
            command=self._on_skip,
            bg="#333345",
            fg="#FFFFFF",
            font=("Segoe UI", 10),
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2"
        )
        btn_skip.pack(side=tk.LEFT)

        btn_next = tk.Button(
            btn_bar,
            text="Next Step ➔",
            command=self._on_manual_next,
            bg="#00ADB5",
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=18,
            pady=6,
            cursor="hand2"
        )
        btn_next.pack(side=tk.RIGHT)

    def _update_loop(self):
        """Timer loop updating step instructions and progress bar."""
        if not self.win.winfo_exists():
            return

        step = self.calibration.get_current_step()
        self.lbl_step.config(text=f"Active Step: {step}")
        self.lbl_instruction.config(text=self.calibration.get_instruction())

        if step == "COMPLETE":
            messagebox.showinfo("Calibration Complete", "Hand calibration completed successfully!\nSettings updated.")
            if self.on_finish_callback:
                self.on_finish_callback()
            self.win.destroy()
            return

        self.win.after(100, self._update_loop)

    def _on_manual_next(self):
        """User manual advance step."""
        self.calibration.advance_step()

    def _on_skip(self):
        """User cancels calibration."""
        self.calibration.cancel_calibration()
        log_ui("Calibration skipped by user", "WARN")
        self.win.destroy()
