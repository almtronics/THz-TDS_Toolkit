"""
Magnitude spectrum page.

This page allows the user to:
- Computes and plot the magnitude for all loaded datasets
- Choose a type of magnitude plot type
- Apply a time-domain window
- Optionally preview the time domain window
"""
import tkinter as tk
from tkinter import ttk

import numpy as np

from core.processing import compute_fft, apply_window
from ui.base_page import ToolkitPage

class MagnitudePage(ToolkitPage):
    # Page for plotting frequency-domain magnitude waveform
    def __init__(self, app) -> None:
        """
        Initialize Magnitude page.

        Args:
            app: Main application instance (THzToolkitApp).
        """
        super().__init__(app)
        self.name = "Magnitude"
        # Plot configuration
        self.plot_type = tk.StringVar(value="Magnitude (dB)")
        # Windowing / preview
        self.show_time_preview = tk.BooleanVar(value=False)
        self.window_type = tk.StringVar(value="None")
        self.tukey_alpha = tk.DoubleVar(value=0.5)
        # User input time bounds
        self.start_time_ps = tk.StringVar(value="")
        self.stop_time_ps  = tk.StringVar(value="")
        # Snapped indices (read-only)
        self.start_idx_text = tk.StringVar(value="Start idx: -")
        self.stop_idx_text  = tk.StringVar(value="Stop idx: -")

    def _snap_time_to_index(self, t, t_ps, side="left") -> int:
        """
        Snap a time value (ps) to the closest valid index in a reference time axis.

        Args:
            t: Reference time axis array.
            t_ps: Time value in ps to snap.
            side: Passed to numpy.searchsorted ("left" or "right").

        Returns:
            Index in the inclusive range [0, len(t)].
        """
        idx = int(np.searchsorted(t, t_ps, side=side))
        return max(0, min(len(t), idx))
    
    def _parse_window_indices(self, datasets) -> tuple[int, int | None]:
        """
        Parse start/stop times and convert them into indices using the reference time axis.

        Args:
            datasets: List of dataset dicts from DataManager.

        Returns:
            (start_idx, stop_idx). stop_idx is None when the stop time is blank.

        Raises:
            ValueError: If user-entered start/stop times cannot be converted to float.
        """
        t_ref = datasets[0]["df"]["time"].to_numpy()

        start_txt = self.start_time_ps.get().strip()
        stop_txt = self.stop_time_ps.get().strip()

        start_idx = 0
        stop_idx = None

        if start_txt != "":
            start_idx = self._snap_time_to_index(t_ref, float(start_txt), side="left")

        if stop_txt != "":
            stop_idx = self._snap_time_to_index(t_ref, float(stop_txt), side="right")

        self.start_idx_text.set(f"Start idx: {start_idx}")
        self.stop_idx_text.set(f"Stop idx: {len(t_ref) if stop_idx is None else stop_idx}")
        return start_idx, stop_idx

    def build_controls(self, parent) -> None:
        """
        Build the controls panel for the Magnitude page.

        Args:
            parent: Tkinter Frame that will contain this page's widgets.
        """
        tk.Label(parent, text="Plot Type:", bg="#f5f5f5", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0,5))
        plot_opts = ["Magnitude", "Magnitude (dB)"]
        cb_plot = ttk.Combobox(parent, textvariable=self.plot_type, values=plot_opts, state="readonly")
        cb_plot.pack(fill=tk.X, pady=(0, 15))
        cb_plot.bind("<<ComboboxSelected>>", lambda e: self.app.refresh_view())

        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)

        tk.Label(parent, text="Window Function:", bg="#f5f5f5", font=("Segoe UI", 9, "bold")).pack(anchor="w")

        tk.Checkbutton(parent, text="Show time preview (window)",
               variable=self.show_time_preview, bg="#f5f5f5",
               command=self.app.refresh_view).pack(anchor="w", pady=(10, 0))
        cb_win = ttk.Combobox(parent, textvariable=self.window_type, 
                             values=["None", "hann", "hamming", "tukey"], state="readonly")
        cb_win.pack(fill=tk.X, pady=5)
        cb_win.bind("<<ComboboxSelected>>", lambda e: self.app.refresh_view())

        tk.Label(parent, text="Window times (ps):", bg="#f5f5f5", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(10, 0))

        row = tk.Frame(parent, bg="#f5f5f5")
        row.pack(fill=tk.X, pady=(5, 0))

        tk.Label(row, text="Start", bg="#f5f5f5").pack(side=tk.LEFT)
        ent_t0 = tk.Entry(row, textvariable=self.start_time_ps, width=10)
        ent_t0.pack(side=tk.LEFT, padx=(5, 15))

        tk.Label(row, text="Stop", bg="#f5f5f5").pack(side=tk.LEFT)
        ent_t1 = tk.Entry(row, textvariable=self.stop_time_ps, width=10)
        ent_t1.pack(side=tk.LEFT, padx=(5, 0))

        ent_t0.bind("<Return>", lambda e: self.app.refresh_view())
        ent_t1.bind("<Return>", lambda e: self.app.refresh_view())

        idx_row = tk.Frame(parent, bg="#f5f5f5")
        idx_row.pack(fill=tk.X, pady=(4, 0))

        tk.Label(idx_row, textvariable=self.start_idx_text, bg="#f5f5f5", fg="gray").pack(side=tk.LEFT)
        tk.Label(idx_row, textvariable=self.stop_idx_text,  bg="#f5f5f5", fg="gray").pack(side=tk.LEFT, padx=(15, 0))

    def render_view(self, fig, ax) -> None:
        """
        Render the Magnitude plot.

        Args:
            fig: Shared Matplotlib Figure.
            ax: Shared Matplotlib Axes to draw into.
        """
        datasets = self.app.data.get_all()
        if not datasets:
            ax.text(0.5, 0.5, "No Data Loaded\n Go to Time Domain Page and Click 'Load New Dataset' to begin.", 
                   ha='center', va='center', transform=ax.transAxes, color="gray")
            return

        try:
            start_idx, stop_idx = self._parse_window_indices(datasets)
        except ValueError:
            self.start_idx_text.set("Start idx: (invalid time)")
            self.stop_idx_text.set("Stop idx: (invalid time)")
            ax.set_title("Magnitude")
            ax.text(
                0.5,
                0.5,
                "Invalid start/stop time.",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color="gray",
            )
            return

        if self.show_time_preview.get():
            ax.set_title("Time-domain preview (window)")
            ax.set_xlabel("Time (ps)")
            ax.set_ylabel("Amplitude")
        else:
            current_plot = self.plot_type.get()
            ax.set_title(f"Frequency Domain - {current_plot}")
            ax.set_xlabel("Frequency (THz)")
            ax.set_ylabel(current_plot)

        # If previewing the time window, scale the window overlay to the largest signal.
        global_scale = 1e-12
        if self.show_time_preview.get():
            for ds in datasets:
                x_all = ds["df"]["complex"].to_numpy()
                global_scale = max(global_scale, float(abs(x_all.real).max()))

        for ds in datasets:
            t = ds["df"]["time"].to_numpy()
            x = ds["df"]["complex"].to_numpy()

            results = compute_fft(
                t,
                x,
                window_type=self.window_type.get(),
                start_idx=start_idx,
                stop_idx=stop_idx,
                tukey_alpha=self.tukey_alpha.get(),
            )

            ds.setdefault("results", {})
            ds["results"]["fft"] = results

            if self.show_time_preview.get():
                ax.plot(t, x.real, alpha=0.8, label=ds.get("name", "Unnamed"))
            else:
                ax.plot(results["Freqs"], results[self.plot_type.get()], label=ds.get("name", "Unnamed"))

        # Draw the window overlay
        if self.show_time_preview.get():
            t0 = datasets[0]["df"]["time"].to_numpy()
            x0 = datasets[0]["df"]["complex"].to_numpy()

            _xw, w, s0, s1 = apply_window(
                t0,
                x0,
                window_type=self.window_type.get(),
                start_idx=start_idx,
                stop_idx=stop_idx,
                tukey_alpha=self.tukey_alpha.get(),
            )

            w_full = (t0 * 0.0)
            w_full[s0:s1] = w
            ax.plot(t0, w_full * global_scale, "--", linewidth=1.5, label="Window")

        ax.legend()