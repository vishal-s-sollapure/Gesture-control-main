"""
GestureControl AI - Safe Gesture Evaluation UI Window
Modal dialog for empirical gesture recognition evaluation, accuracy benchmarks,
and JSON report generation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from config import EVALUATION_FILE, GESTURE_NAMES


class EvaluationWindow:
    """
    Modal dialog window for safe empirical gesture evaluation.
    """

    def __init__(self, parent: tk.Tk, controller):
        self.parent = parent
        self.controller = controller

        self.win = tk.Toplevel(parent)
        self.win.title("GestureControl AI — Evaluation Benchmark")
        self.win.geometry("640x520")
        self.win.resizable(False, False)
        self.win.configure(bg="#1A1A24")
        self.win.grab_set()

        self.evaluation = controller.evaluation
        self.evaluation.start_evaluation()

        self._build_ui()
        self._update_loop()

    def _build_ui(self):
        """Constructs UI layout."""
        header = tk.Frame(self.win, bg="#242432", padx=20, pady=12)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="🧪 GESTURE RECOGNITION BENCHMARK",
            font=("Segoe UI", 14, "bold"),
            bg="#242432",
            fg="#00E676"
        )
        title.pack(anchor="w")

        sub = tk.Label(
            header,
            text="Safe evaluation mode (Mouse control disabled). Perform prompted gestures.",
            font=("Segoe UI", 9),
            bg="#242432",
            fg="#A0A0B5"
        )
        sub.pack(anchor="w")

        body = tk.Frame(self.win, bg="#1A1A24", padx=20, pady=15)
        body.pack(fill=tk.BOTH, expand=True)

        self.target_frame = tk.Frame(body, bg="#242432", padx=15, pady=15, bd=1, relief="solid")
        self.target_frame.pack(fill=tk.X, pady=(0, 15))

        self.lbl_target_title = tk.Label(
            self.target_frame,
            text="PROMPTED GESTURE:",
            font=("Segoe UI", 9, "bold"),
            bg="#242432",
            fg="#00ADB5"
        )
        self.lbl_target_title.pack(anchor="w")

        self.lbl_target_name = tk.Label(
            self.target_frame,
            text="☝️ Cursor Point",
            font=("Segoe UI", 16, "bold"),
            bg="#242432",
            fg="#FFFFFF"
        )
        self.lbl_target_name.pack(anchor="w", pady=(5, 0))

        # Trial results list table
        table_frame = tk.Frame(body, bg="#1A1A24")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        columns = ("expected", "detected", "match", "latency")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        self.tree.heading("expected", text="Expected Gesture")
        self.tree.heading("detected", text="Detected Gesture")
        self.tree.heading("match", text="Result")
        self.tree.heading("latency", text="Response Latency")

        self.tree.column("expected", width=160)
        self.tree.column("detected", width=160)
        self.tree.column("match", width=100)
        self.tree.column("latency", width=120)
        self.tree.pack(fill=tk.BOTH, expand=True)

        btn_bar = tk.Frame(body, bg="#1A1A24")
        btn_bar.pack(fill=tk.X)

        btn_cancel = tk.Button(
            btn_bar,
            text="Cancel Session",
            command=self._on_cancel,
            bg="#333345",
            fg="#FFFFFF",
            font=("Segoe UI", 10),
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2"
        )
        btn_cancel.pack(side=tk.LEFT)

        btn_finish = tk.Button(
            btn_bar,
            text="Complete Benchmark",
            command=self._on_finish,
            bg="#00E676",
            fg="#000000",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=18,
            pady=6,
            cursor="hand2"
        )
        btn_finish.pack(side=tk.RIGHT)

    def _update_loop(self):
        """Refreshes trial progress and table contents."""
        if not self.win.winfo_exists():
            return

        target_label = self.evaluation.get_target_label()
        self.lbl_target_name.config(text=target_label)

        # Refresh tree table
        for item in self.tree.get_children():
            self.tree.delete(item)

        for trial in self.evaluation.trials:
            match_str = "✓ PASS" if trial["match"] else "✗ FAIL"
            exp_label = GESTURE_NAMES.get(trial["expected_gesture"], trial["expected_gesture"])
            det_label = GESTURE_NAMES.get(trial["detected_gesture"], trial["detected_gesture"])
            lat_str = f"{trial['response_time_ms']} ms"
            self.tree.insert("", tk.END, values=(exp_label, det_label, match_str, lat_str))

        if not self.evaluation.is_active:
            report = self.evaluation.compute_report()
            acc = report.get("overall_accuracy_pct", "N/A")
            messagebox.showinfo(
                "Benchmark Results",
                f"Gesture Benchmark Completed!\n\n"
                f"Overall Accuracy: {acc}%\n"
                f"Total Trials: {report.get('total_trials', 0)}\n\n"
                f"Saved results to: evaluation_results.json"
            )
            self.win.destroy()
            return

        self.win.after(200, self._update_loop)

    def _on_finish(self):
        """Concludes evaluation session."""
        self.evaluation.finalize_evaluation()

    def _on_skip_step(self):
        """Skips current target."""
        self.evaluation.record_trial("SKIPPED", 0.0)

    def _on_cancel(self):
        """Cancels evaluation session."""
        self.evaluation.cancel_evaluation()
        self.win.destroy()
