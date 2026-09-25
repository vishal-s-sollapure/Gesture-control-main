"""
GestureControl AI - Settings Panel Module
Provides interactive controls for tuning sensitivity, smoothing factors,
gesture activation toggles, debug mode toggle, and saving configurations locally.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config import save_settings, DEFAULT_SETTINGS


class SettingsWindow(tk.Toplevel):
    """
    Dedicated Toplevel window for modifying application settings.
    """

    def __init__(self, parent, current_settings: dict, on_save_callback):
        super().__init__(parent)
        self.title("GestureControl AI - Settings")
        self.geometry("520x720")
        self.resizable(False, False)
        self.configure(bg="#1E1E24")

        self.settings = current_settings.copy()
        self.on_save_callback = on_save_callback

        # Visual Styling Palette
        self.bg_dark = "#1E1E24"
        self.card_bg = "#2B2B36"
        self.accent_color = "#00ADB5"
        self.text_color = "#EEEEEE"

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        """Constructs settings UI widgets."""
        main_container = tk.Frame(self, bg=self.bg_dark, padx=20, pady=15)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Title Header
        title_label = tk.Label(
            main_container,
            text="⚙ Configuration & Tuning",
            font=("Segoe UI", 16, "bold"),
            bg=self.bg_dark,
            fg=self.accent_color
        )
        title_label.pack(anchor="w", pady=(0, 15))

        # Scrollable Notebook / Canvas container
        canvas = tk.Canvas(main_container, bg=self.bg_dark, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.bg_dark)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=460)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # SECTION 1: Sensitivity & Motion Tuning Card
        tuning_card = tk.LabelFrame(
            scroll_frame,
            text=" Cursor & Motion Sensitivity ",
            font=("Segoe UI", 11, "bold"),
            bg=self.card_bg,
            fg=self.text_color,
            bd=1,
            relief="solid",
            padx=15,
            pady=10
        )
        tuning_card.pack(fill=tk.X, pady=(0, 15))

        # 1. Cursor Sensitivity Slider
        self.sens_var = tk.DoubleVar(value=self.settings.get("sensitivity", 1.4))
        self._create_slider_row(
            tuning_card,
            "Cursor Sensitivity:",
            self.sens_var,
            from_=0.5,
            to=3.0,
            resolution=0.1
        )

        # 2. Smoothing Factor Slider
        self.smooth_var = tk.DoubleVar(value=self.settings.get("smoothing", 0.75))
        self._create_slider_row(
            tuning_card,
            "Cursor Smoothing (EMA):",
            self.smooth_var,
            from_=0.0,
            to=0.95,
            resolution=0.05
        )

        # 3. Pinch Threshold Slider
        self.pinch_var = tk.DoubleVar(value=self.settings.get("pinch_threshold", 0.045))
        self._create_slider_row(
            tuning_card,
            "Pinch Threshold Ratio:",
            self.pinch_var,
            from_=0.015,
            to=0.090,
            resolution=0.005
        )

        # 4. Scroll Sensitivity Slider
        self.scroll_var = tk.DoubleVar(value=self.settings.get("scroll_sensitivity", 25.0))
        self._create_slider_row(
            tuning_card,
            "Scroll Speed:",
            self.scroll_var,
            from_=5.0,
            to=60.0,
            resolution=5.0
        )

        # 5. Gesture Cooldown Slider
        self.cooldown_var = tk.DoubleVar(value=self.settings.get("gesture_cooldown", 0.50))
        self._create_slider_row(
            tuning_card,
            "Gesture Cooldown (sec):",
            self.cooldown_var,
            from_=0.1,
            to=1.0,
            resolution=0.05
        )

        # SECTION 2: Debug Mode & Diagnostics Card
        debug_card = tk.LabelFrame(
            scroll_frame,
            text=" Developer Diagnostics ",
            font=("Segoe UI", 11, "bold"),
            bg=self.card_bg,
            fg=self.accent_color,
            bd=1,
            relief="solid",
            padx=15,
            pady=10
        )
        debug_card.pack(fill=tk.X, pady=(0, 15))

        self.debug_var = tk.BooleanVar(value=self.settings.get("debug_mode", False))
        debug_chk = tk.Checkbutton(
            debug_card,
            text="🐞 Enable Debug Mode Overlay (Shows landmarks & ratios)",
            variable=self.debug_var,
            bg=self.card_bg,
            fg=self.text_color,
            selectcolor="#393E46",
            activebackground=self.card_bg,
            activeforeground=self.accent_color,
            font=("Segoe UI", 10, "bold")
        )
        debug_chk.pack(anchor="w")

        # SECTION 3: Individual Gestures Toggle Card
        gestures_card = tk.LabelFrame(
            scroll_frame,
            text=" Enable / Disable Gestures ",
            font=("Segoe UI", 11, "bold"),
            bg=self.card_bg,
            fg=self.text_color,
            bd=1,
            relief="solid",
            padx=15,
            pady=10
        )
        gestures_card.pack(fill=tk.X, pady=(0, 15))

        self.gesture_vars = {}
        enabled_map = self.settings.get("enabled_gestures", {})

        gesture_labels = {
            "cursor_movement": "☝️ Cursor Movement",
            "left_click": "🤏 Left Click (Pinch)",
            "right_click": "✌️ Right Click (2 Fingers)",
            "scroll": "✋ Scroll (Open Palm)",
            "drag_and_drop": "✊🤏 Drag & Drop",
            "double_click": "🤏🤏 Double Click",
            "media_play_pause": "👍 Play / Pause",
            "next_track": "👉 Next Track (Swipe Right)",
            "prev_track": "👈 Previous Track (Swipe Left)",
            "emergency_fist": "✊ Emergency Pause (Fist)"
        }

        for key, label_text in gesture_labels.items():
            var = tk.BooleanVar(value=enabled_map.get(key, True))
            self.gesture_vars[key] = var
            chk = tk.Checkbutton(
                gestures_card,
                text=label_text,
                variable=var,
                bg=self.card_bg,
                fg=self.text_color,
                selectcolor="#393E46",
                activebackground=self.card_bg,
                activeforeground=self.accent_color,
                font=("Segoe UI", 10)
            )
            chk.pack(anchor="w", pady=2)

        # Footer Action Buttons
        btn_frame = tk.Frame(self, bg=self.bg_dark, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20)

        reset_btn = tk.Button(
            btn_frame,
            text="Reset to Defaults",
            command=self._on_reset,
            bg="#393E46",
            fg="#EEEEEE",
            font=("Segoe UI", 10),
            relief="flat",
            padx=10,
            pady=6,
            cursor="hand2"
        )
        reset_btn.pack(side=tk.LEFT)

        save_btn = tk.Button(
            btn_frame,
            text="Save Settings",
            command=self._on_save,
            bg=self.accent_color,
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2"
        )
        save_btn.pack(side=tk.RIGHT)

    def _create_slider_row(self, parent, label_text: str, var: tk.DoubleVar, from_: float, to: float, resolution: float):
        """Helper to create a slider with live value display."""
        frame = tk.Frame(parent, bg=self.card_bg)
        frame.pack(fill=tk.X, pady=5)

        lbl_frame = tk.Frame(frame, bg=self.card_bg)
        lbl_frame.pack(fill=tk.X)

        lbl = tk.Label(lbl_frame, text=label_text, bg=self.card_bg, fg=self.text_color, font=("Segoe UI", 10))
        lbl.pack(side=tk.LEFT)

        val_lbl = tk.Label(lbl_frame, text=f"{var.get():.3f}", bg=self.card_bg, fg=self.accent_color, font=("Segoe UI", 10, "bold"))
        val_lbl.pack(side=tk.RIGHT)

        def update_val_label(val):
            val_lbl.config(text=f"{float(val):.3f}")

        slider = ttk.Scale(
            frame,
            from_=from_,
            to=to,
            variable=var,
            command=update_val_label
        )
        slider.pack(fill=tk.X, pady=(2, 0))

    def _on_save(self):
        """Gathers widget values, saves to file, triggers callback, and closes window."""
        self.settings["sensitivity"] = round(self.sens_var.get(), 2)
        self.settings["smoothing"] = round(self.smooth_var.get(), 2)
        self.settings["pinch_threshold"] = round(self.pinch_var.get(), 3)
        self.settings["scroll_sensitivity"] = round(self.scroll_var.get(), 1)
        self.settings["gesture_cooldown"] = round(self.cooldown_var.get(), 2)
        self.settings["debug_mode"] = self.debug_var.get()

        enabled_dict = {key: var.get() for key, var in self.gesture_vars.items()}
        self.settings["enabled_gestures"] = enabled_dict

        if save_settings(self.settings):
            self.on_save_callback(self.settings)
            messagebox.showinfo("Settings Saved", "Settings successfully updated!", parent=self)
            self.destroy()
        else:
            messagebox.showerror("Save Error", "Failed to write settings file.", parent=self)

    def _on_reset(self):
        """Resets sliders to default values."""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to original defaults?", parent=self):
            defaults = DEFAULT_SETTINGS.copy()
            self.sens_var.set(defaults["sensitivity"])
            self.smooth_var.set(defaults["smoothing"])
            self.pinch_var.set(defaults["pinch_threshold"])
            self.scroll_var.set(defaults["scroll_sensitivity"])
            self.cooldown_var.set(defaults["gesture_cooldown"])
            self.debug_var.set(defaults.get("debug_mode", False))

            for key, var in self.gesture_vars.items():
                var.set(defaults["enabled_gestures"].get(key, True))
