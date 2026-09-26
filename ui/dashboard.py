"""
GestureControl AI - Dashboard UI Module
Modern, sleek desktop application GUI displaying real-time video feed,
status cards, visual gesture feedback, gesture guide, control toggles, activity log feed, and settings access.
"""

import time
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk

from config import load_settings, GESTURE_NAMES
from core.gesture_controller import GestureController
from ui.settings import SettingsWindow
from utils.logger import get_ui_logs, setup_logger, log_ui

logger = setup_logger("Dashboard")


class DashboardApp:
    """
    Main Tkinter Desktop Dashboard Application.
    """

    def __init__(self, root: tk.Tk, dry_run: bool = False):
        self.root = root
        self.dry_run = dry_run

        self.root.title("GestureControl AI — Touchless Computer Control")
        self.root.geometry("1180x780")
        self.root.minsize(1020, 680)
        self.root.configure(bg="#1A1A24")

        # Load persisted config settings
        self.settings = load_settings()

        # Initialize core GestureController (defaults to CONTROL: PAUSED for safety)
        self.controller = GestureController(settings=self.settings, dry_run=self.dry_run)

        # Color Theme Palette
        self.bg_dark = "#1A1A24"
        self.card_bg = "#242432"
        self.card_border = "#333345"
        self.accent_teal = "#00ADB5"
        self.accent_green = "#00E676"
        self.accent_red = "#FF5252"
        self.text_primary = "#FFFFFF"
        self.text_secondary = "#A0A0B5"

        # Application state
        self.last_img_tk = None

        self._setup_key_bindings()
        self._build_ui()

        # Start gesture controller processing
        if not self.controller.start():
            messagebox.showwarning(
                "Camera Warning",
                "Could not connect to webcam. Please verify camera connection and permissions.\n"
                "The dashboard will start, but camera feed will remain offline."
            )

        # Start periodic GUI refresh timer loop (~30 FPS)
        self._schedule_gui_update()

    def _setup_key_bindings(self):
        """Global key bindings (ESC = Emergency Stop)."""
        self.root.bind("<Escape>", lambda event: self._on_emergency_stop())

    def _build_ui(self):
        """Constructs full dashboard widget hierarchy."""
        # Top App Bar / Header
        header_frame = tk.Frame(self.root, bg=self.card_bg, height=60, padx=20, pady=10)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_lbl = tk.Label(
            header_frame,
            text="GESTURECONTROL AI",
            font=("Segoe UI", 18, "bold"),
            bg=self.card_bg,
            fg=self.accent_teal
        )
        title_lbl.pack(side=tk.LEFT)

        sub_lbl = tk.Label(
            header_frame,
            text=" |  Touchless Computer Control Dashboard",
            font=("Segoe UI", 12),
            bg=self.card_bg,
            fg=self.text_secondary
        )
        sub_lbl.pack(side=tk.LEFT, padx=(0, 0))

        # Calibration & Evaluation Action Buttons
        eval_btn = tk.Button(
            header_frame,
            text="🧪 Benchmark",
            command=self._open_evaluation,
            bg="#333345",
            fg=self.accent_green,
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            activebackground=self.accent_green,
            activeforeground="#000000"
        )
        eval_btn.pack(side=tk.RIGHT, padx=(6, 0))

        cal_btn = tk.Button(
            header_frame,
            text="🧭 Calibrate",
            command=self._open_calibration,
            bg="#333345",
            fg=self.accent_teal,
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            activebackground=self.accent_teal,
            activeforeground="#FFFFFF"
        )
        cal_btn.pack(side=tk.RIGHT, padx=(6, 0))

        settings_btn = tk.Button(
            header_frame,
            text="⚙ Settings",
            command=self._open_settings,
            bg="#333345",
            fg=self.text_primary,
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=6,
            cursor="hand2",
            activebackground=self.accent_teal,
            activeforeground="#FFFFFF"
        )
        settings_btn.pack(side=tk.RIGHT, padx=(6, 0))

        # Active Profile Quick Selector
        prof_frame = tk.Frame(header_frame, bg=self.card_bg)
        prof_frame.pack(side=tk.RIGHT, padx=6)

        prof_lbl = tk.Label(prof_frame, text="Profile:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.accent_teal)
        prof_lbl.pack(side=tk.LEFT, padx=(0, 4))

        self.profile_var_gui = tk.StringVar(value=self.settings.get("active_profile", "Desktop"))
        profile_menu = ttk.OptionMenu(
            prof_frame,
            self.profile_var_gui,
            self.profile_var_gui.get(),
            "Desktop", "Media", "Presentation", "Custom",
            command=self._on_quick_profile_change
        )
        profile_menu.pack(side=tk.LEFT)

        # Main Layout Container (Left Video/Status, Right Reference/Log)
        main_body = tk.Frame(self.root, bg=self.bg_dark, padx=15, pady=15)
        main_body.pack(fill=tk.BOTH, expand=True)

        left_col = tk.Frame(main_body, bg=self.bg_dark)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_col = tk.Frame(main_body, bg=self.bg_dark, width=380)
        right_col.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_col.pack_propagate(False)

        # LEFT COLUMN COMPONENTS:
        # 1. Video Canvas Frame
        video_card = tk.Frame(left_col, bg=self.card_bg, bd=1, relief="solid", highlightbackground=self.card_border)
        video_card.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        self.video_label = tk.Label(video_card, bg="#0F0F14", text="Initializing Video Stream...", fg=self.text_secondary)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 2. Status Indicators Cards Bar (Section 12: Visual Gesture Feedback)
        status_bar = tk.Frame(left_col, bg=self.bg_dark)
        status_bar.pack(fill=tk.X, pady=(0, 12))

        # Status Pill 1: Camera & Hand Status
        self.card_cam = self._create_status_card(status_bar, "Camera / Hand", "● Connecting...", self.text_secondary)
        self.card_cam.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        # Status Pill 2: Control State
        self.card_ctrl = self._create_status_card(status_bar, "Gesture Control", "PAUSED", self.accent_red)
        self.card_ctrl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # Status Pill 3: Active Profile
        self.card_prof = self._create_status_card(status_bar, "Active Profile", "Desktop", self.accent_teal)
        self.card_prof.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # Status Pill 4: Current Gesture
        self.card_gest = self._create_status_card(status_bar, "Current Gesture", "🖐️ Ready", self.accent_teal)
        self.card_gest.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # Status Pill 5: Current Action
        self.card_act = self._create_status_card(status_bar, "Current Action", "Waiting...", self.text_primary)
        self.card_act.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        # Status Pill 6: Confidence & FPS
        self.card_fps = self._create_status_card(status_bar, "Conf / FPS", "-- | --", self.text_secondary)
        self.card_fps.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        # 3. Control Action Buttons Bar (Section 10 & 17)
        actions_bar = tk.Frame(left_col, bg=self.card_bg, padx=15, pady=12, bd=1, relief="solid")
        actions_bar.pack(fill=tk.X)

        self.btn_enable = tk.Button(
            actions_bar,
            text="▶ ENABLE GESTURE CONTROL",
            command=self._on_enable_control,
            bg=self.accent_green,
            fg="#000000",
            font=("Segoe UI", 11, "bold"),
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2"
        )
        self.btn_enable.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_disable = tk.Button(
            actions_bar,
            text="⏸ DISABLE GESTURE CONTROL",
            command=self._on_disable_control,
            bg="#444455",
            fg=self.text_primary,
            font=("Segoe UI", 11, "bold"),
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2"
        )
        self.btn_disable.pack(side=tk.LEFT, padx=10)

        self.btn_emergency = tk.Button(
            actions_bar,
            text="🚨 EMERGENCY STOP (ESC)",
            command=self._on_emergency_stop,
            bg=self.accent_red,
            fg="#FFFFFF",
            font=("Segoe UI", 11, "bold"),
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2"
        )
        self.btn_emergency.pack(side=tk.RIGHT)

        # RIGHT COLUMN COMPONENTS:
        # 1. Gesture Guide Reference Table
        guide_card = tk.LabelFrame(
            right_col,
            text=" 📜 Supported Gestures ",
            font=("Segoe UI", 11, "bold"),
            bg=self.card_bg,
            fg=self.accent_teal,
            bd=1,
            relief="solid",
            padx=10,
            pady=8
        )
        guide_card.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        gesture_list = [
            ("☝️ Cursor Point", "Move Mouse Cursor"),
            ("🤏 Thumb-Index Pinch", "Left Mouse Click"),
            ("✌️ Two Fingers Up", "Right Mouse Click"),
            ("✋ Open Palm Up/Down", "Scroll Up / Down"),
            ("✊🤏 Pinch & Hold", "Drag & Drop"),
            ("🤏🤏 Quick Double Pinch", "Double Click"),
            ("👍 Thumbs Up", "Media Play / Pause"),
            ("👉 Swipe Right", "Next Track"),
            ("👈 Swipe Left", "Previous Track"),
            ("✊ Closed Fist", "Emergency Pause Control")
        ]

        for icon_name, desc in gesture_list:
            row = tk.Frame(guide_card, bg=self.card_bg)
            row.pack(fill=tk.X, pady=3)

            lbl_icon = tk.Label(row, text=icon_name, font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg=self.text_primary, anchor="w")
            lbl_icon.pack(side=tk.LEFT)

            lbl_arrow = tk.Label(row, text="→", font=("Segoe UI", 9), bg=self.card_bg, fg=self.accent_teal)
            lbl_arrow.pack(side=tk.RIGHT, padx=4)

            lbl_desc = tk.Label(row, text=desc, font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_secondary, anchor="e")
            lbl_desc.pack(side=tk.RIGHT)

        # 2. Activity Event Log Listbox
        log_card = tk.LabelFrame(
            right_col,
            text=" 📝 Activity Log Feed ",
            font=("Segoe UI", 10, "bold"),
            bg=self.card_bg,
            fg=self.text_primary,
            bd=1,
            relief="solid",
            padx=8,
            pady=6,
            height=180
        )
        log_card.pack(fill=tk.X)
        log_card.pack_propagate(False)

        self.log_listbox = tk.Listbox(
            log_card,
            bg="#16161E",
            fg="#00E676",
            selectbackground="#2A2A38",
            font=("Consolas", 8),
            bd=0,
            highlightthickness=0
        )
        self.log_listbox.pack(fill=tk.BOTH, expand=True)

    def _create_status_card(self, parent, title: str, initial_val: str, color: str) -> tk.Frame:
        """Helper to construct uniform status indicator card."""
        card = tk.Frame(parent, bg=self.card_bg, bd=1, relief="solid", padx=10, pady=8)

        lbl_title = tk.Label(card, text=title, font=("Segoe UI", 8), bg=self.card_bg, fg=self.text_secondary)
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(card, text=initial_val, font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=color)
        lbl_val.pack(anchor="w", pady=(2, 0))

        # Attach reference to label widget inside frame for live updates
        card.val_label = lbl_val
        return card

    def _on_enable_control(self):
        """User enable click."""
        self.controller.enable_control()

    def _on_disable_control(self):
        """User disable click."""
        self.controller.disable_control("Dashboard button click")

    def _on_emergency_stop(self):
        """User emergency stop click or ESC key."""
        self.controller.emergency_stop()

    def _on_quick_profile_change(self, selected_profile: str):
        """Handler when user selects profile from dropdown menu."""
        self.settings["active_profile"] = selected_profile
        from config import save_settings
        save_settings(self.settings)
        self.controller.update_settings(self.settings)
        log_ui(f"Active Profile changed to: {selected_profile}", "CONFIG")

    def _open_calibration(self):
        """Opens first-run calibration wizard modal."""
        from ui.calibration_ui import CalibrationWindow
        CalibrationWindow(self.root, self.controller)

    def _open_evaluation(self):
        """Opens safe evaluation benchmark modal."""
        from ui.evaluation_ui import EvaluationWindow
        EvaluationWindow(self.root, self.controller)

    def _open_settings(self):
        """Opens modal settings window."""
        SettingsWindow(self.root, self.settings, self._on_settings_saved)

    def _on_settings_saved(self, new_settings: dict):
        """Callback when user saves settings in settings modal."""
        self.settings = new_settings
        self.profile_var_gui.set(new_settings.get("active_profile", "Desktop"))
        self.controller.update_settings(new_settings)
        log_ui("Settings updated and reloaded", "CONFIG")

    def _schedule_gui_update(self):
        """Periodic GUI refresh timer (~30 FPS)."""
        self._update_gui_state()
        self.root.after(33, self._schedule_gui_update)

    def _update_gui_state(self):
        """Updates video canvas, status pills, and log feed."""
        status = self.controller.get_status_info()

        # Update Camera & Hand Status Pill
        if status["connected"]:
            hand_str = "✓ Hand Detected" if status["hand_count"] > 0 else "No Hand"
            cam_color = self.accent_green if status["hand_count"] > 0 else self.text_secondary
            self.card_cam.val_label.config(text=f"● {hand_str}", fg=cam_color)
        else:
            self.card_cam.val_label.config(text="● Disconnected", fg=self.accent_red)

        # Update Gesture Control Pill
        if status["control_enabled"]:
            self.card_ctrl.val_label.config(text="ACTIVE", fg=self.accent_green)
            self.btn_enable.config(bg="#1F3D2B", fg="#A0A0A0")  # Dimmed active button
            self.btn_disable.config(bg=self.accent_teal, fg="#FFFFFF")
        else:
            self.card_ctrl.val_label.config(text="PAUSED", fg=self.accent_red)
            self.btn_enable.config(bg=self.accent_green, fg="#000000")
            self.btn_disable.config(bg="#333345", fg=self.text_secondary)

        # Update Active Profile Pill
        active_prof = status.get("active_profile", "Desktop")
        self.card_prof.val_label.config(text=active_prof, fg=self.accent_teal)

        # Update Current Gesture & Action Pills
        gest_label = status["gesture_label"]
        self.card_gest.val_label.config(text=gest_label, fg=self.accent_teal)

        action_name = status.get("action_name", "Waiting...")
        self.card_act.val_label.config(text=action_name, fg=self.text_primary)

        # Update Confidence & FPS Pill
        conf_pct = status.get("confidence_pct", "--")
        fps_val = status.get("fps", 0.0)
        self.card_fps.val_label.config(text=f"{conf_pct} | {fps_val} FPS", fg=self.accent_teal)

        # Render processed video frame onto GUI Tkinter canvas
        frame = self.controller.get_processed_frame()
        if frame is not None:
            h, w, _ = frame.shape
            canvas_w = max(320, self.video_label.winfo_width())
            canvas_h = max(240, self.video_label.winfo_height())

            if canvas_w > 10 and canvas_h > 10:
                frame_resized = cv2.resize(frame, (canvas_w, canvas_h), interpolation=cv2.INTER_AREA)
                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img_tk = ImageTk.PhotoImage(image=img)

                self.video_label.configure(image=img_tk, text="")
                self.video_label.image = img_tk
                self.last_img_tk = img_tk

        # Update Activity Log Feed
        new_logs = get_ui_logs()
        for msg in new_logs:
            self.log_listbox.insert(tk.END, msg)
            self.log_listbox.see(tk.END)
            if self.log_listbox.size() > 100:
                self.log_listbox.delete(0)

    def on_close(self):
        """Clean shutdown handler on window exit (releases drag, stops threads)."""
        logger.info("Closing GestureControl AI Dashboard...")
        self.controller.stop()
        self.root.destroy()
