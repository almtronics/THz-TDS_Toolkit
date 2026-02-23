"""
Frequency spectrum page.

This page allows the user to:
- Compute the FFT.
- Computes and plot the magnitude for all loaded datasets
- Choose a type of magnitude plot type
- Apply a time-domain window
- Optionally preview the time domain window
"""
import tkinter as tk
from tkinter import ttk

import numpy as np

from core.processing import compute_fft, compute_mag, apply_window, normalize_fft
from ui.base_page import ToolkitPage

WINDOW_SPECS = {
    "None":    {"nargs": 0, "help": "No window, args ignored.", "defaults": []},
    "hann":    {"nargs": 0, "help": "No args needed.", "defaults": []},
    "hamming": {"nargs": 0, "help": "No args needed.", "defaults": []},
    "blackman": {"nargs": 0, "help": "No args needed.", "defaults": []},
    "tukey":   {"nargs": 1, "help": "Enter alpha [0, 1].", "defaults": [0.5]},
}
WINDOW_CHOICES = list(WINDOW_SPECS.keys())

class FrequencyPage(ToolkitPage):
    # Page for plotting frequency-domain magnitude waveform
    def __init__(self, app) -> None:
        """
        Initialize Frequency Domain page.

        Args:
            app: Main application instance (THzToolkitApp).
        """
        super().__init__(app)
        self.name = "Frequency Domain"
        # Plot configuration
        self.plot_type = tk.StringVar(value="Magnitude")
        # Windowing / preview
        self.show_time_preview = tk.BooleanVar(value=False)
        self.window_type = tk.StringVar(value="None")
        self.window_args_text = tk.StringVar(value="")
        self.window_args_help = tk.StringVar(value=WINDOW_SPECS["None"]["help"])
        # User input time bounds
        self.start_time_ps = tk.StringVar(value="")
        self.stop_time_ps  = tk.StringVar(value="")
        # Snapped indices (read-only)
        self.start_idx_text = tk.StringVar(value="Start idx: -")
        self.stop_idx_text  = tk.StringVar(value="Stop idx: -")

    def _sync_window_args_ui(self):
        """
        Sync the window-argument UI elements with the currently selected window.
        """
        w = self.window_type.get()
        spec = WINDOW_SPECS.get(w, WINDOW_SPECS["None"])
        self.window_args_help.set(spec["help"])

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
    
    def _parse_window_args(self, window_type: str) -> list[float]:
        """
        Parse the Window args entry for the given window type using WINDOW_SPECS.

        Args:
            window_type: Selected window name from the combobox
        Returns:
            A list of floats representing parsed window parameters.
        Raises:
            ValueError: If user-entered args cannot be parsed.
        """
        spec = WINDOW_SPECS.get(window_type, WINDOW_SPECS["None"])
        raw = self.window_args_text.get().strip()

        if spec["nargs"] == 0:
            return []

        if raw == "":
            return list(spec["defaults"])

        parts = [p.strip() for p in raw.split(",") if p.strip() != ""]
        if len(parts) != spec["nargs"]:
            raise ValueError(f"{window_type} expects {spec['nargs']} arg(s)")

        return [float(p) for p in parts]


    def _build_window_spec(self) -> str | tuple:
        """
        Build a SciPy-compatible window spec from the selected window and parsed args.

        Returns:
            A window spec suitable for scipy.signal.get_window
        Raises:
            ValueError: If the selected window expects args and parsing fails.
        """
        wtype = self.window_type.get()
        if wtype == "None":
            return "None"

        args = self._parse_window_args(wtype)
        return wtype if len(args) == 0 else (wtype, *args)


    def build_controls(self, parent) -> None:
        """
        Build the controls panel for the Magnitude page.

        Args:
            parent: Tkinter Frame that will contain this page's widgets.
        """
        ttk.Button(parent, text="Compute FFT", command=self.on_compute_fft).pack(fill=tk.X, pady=(10, 0))
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)

        tk.Label(parent, text="Plot Type:", bg="#f5f5f5", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0,5))
        plot_opts = ["Magnitude", "Magnitude (dB)", "Normalized Magnitude", "Normalized Magnitude (dB)"]
        cb_plot = ttk.Combobox(parent, textvariable=self.plot_type, values=plot_opts, state="readonly")
        cb_plot.pack(fill=tk.X, pady=(0, 15))
        cb_plot.bind("<<ComboboxSelected>>", lambda e: self.app.refresh_view())

        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)

        tk.Label(parent, text="Window Function:", bg="#f5f5f5", font=("Segoe UI", 9, "bold")).pack(anchor="w")

        tk.Checkbutton(parent, text="Show time preview (window)",
               variable=self.show_time_preview, bg="#f5f5f5",
               command=self.app.refresh_view).pack(anchor="w", pady=(10, 0))
        cb_win = ttk.Combobox(parent, textvariable=self.window_type,
                      values=WINDOW_CHOICES, state="readonly")
        cb_win.pack(fill=tk.X, pady=5)

        tk.Label(parent, text="Window args:", bg="#f5f5f5", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5, 0))
        ent_args = tk.Entry(parent, textvariable=self.window_args_text)
        ent_args.pack(fill=tk.X, pady=(0, 2))
        ent_args.bind("<Return>", lambda e: self.app.refresh_view())
        tk.Label(parent, textvariable=self.window_args_help, bg="#f5f5f5", fg="gray").pack(anchor="w", pady=(0, 10))

        cb_win.bind("<<ComboboxSelected>>", lambda e: (self._sync_window_args_ui(), self.app.refresh_view()))

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
        self._sync_window_args_ui()

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
                color="gray"
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

        # Get reference and plot type
        ref_ds = self.app.data.get_reference()
        ref_path = ref_ds.get("path") if ref_ds else None
        is_normalized = self.plot_type.get().startswith("Normalized ")

        for ds in datasets:
            t = ds["df"]["time"].to_numpy()
            x = ds["df"]["complex"].to_numpy()

            if self.show_time_preview.get():
                ax.plot(t, x.real, alpha=0.8, label=ds.get("name", "Unnamed"))
            else:
                # Skip plotting the reference
                if is_normalized and ds.get("path") == ref_path:
                    continue

                res = ds.get("results", {})
                fft_res = res.get("fft_normalized" if is_normalized else "fft")

                if fft_res is None:
                    if is_normalized:
                        msg = "No normalized data.\nSet a reference in Time Domain, then click 'Compute FFT'."
                    else:
                        msg = "Press 'Compute FFT' to generate spectrum."
                    ax.text(0.5, 0.5, msg, ha="center", va="center", transform=ax.transAxes, color="gray")
                    return

                mag_key = self.plot_type.get().replace("Normalized ", "")
                mag_res = compute_mag(fft_res["FFT"])
                y = mag_res[mag_key]
                ax.plot(fft_res["Freqs"], y, label=ds.get("name", "Unnamed"))

        # Draw the window overlay
        if self.show_time_preview.get():
            t0 = datasets[0]["df"]["time"].to_numpy()
            x0 = datasets[0]["df"]["complex"].to_numpy()

            wtype = self.window_type.get()
            spec_meta = WINDOW_SPECS.get(wtype, WINDOW_SPECS["None"])

            try:
                window_args = self._parse_window_args(wtype)
            except ValueError:
                window_args = list(spec_meta["defaults"])

            _xw, w, s0, s1 = apply_window(
                t0,
                x0,
                window_type=wtype,
                window_args=window_args,
                start_idx=start_idx,
                stop_idx=stop_idx,
            )

            w_full = (t0 * 0.0)
            w_full[s0:s1] = w
            ax.plot(t0, w_full * global_scale, "--", linewidth=1.5, label="Window")

        ax.legend()

    def on_compute_fft(self) -> None:
        """
        Compute and cache the half-spectrum FFT for all loaded datasets.
        Stored under ds["results"]["fft"] with:
            - "Freqs": frequency axis
            - "FFT": complex FFT values
        """
        datasets = self.app.data.get_all()
        if not datasets:
            self.app.refresh_view()
            return

        try:
            start_idx, stop_idx = self._parse_window_indices(datasets)
        except ValueError:
            self.start_idx_text.set("Start idx: (invalid time)")
            self.stop_idx_text.set("Stop idx: (invalid time)")
            self.app.refresh_view()
            return

        for ds in datasets:
            t = ds["df"]["time"].to_numpy()
            x = ds["df"]["complex"].to_numpy()

            wtype = self.window_type.get()
            spec_meta = WINDOW_SPECS.get(wtype, WINDOW_SPECS["None"])

            try:
                window_args = self._parse_window_args(wtype)
            except ValueError:
                window_args = list(spec_meta["defaults"])

            spec = compute_fft(
                t,
                x,
                window_type=wtype,
                window_args=window_args,
                start_idx=start_idx,
                stop_idx=stop_idx,
            )

            ds.setdefault("results", {})
            ds["results"]["fft"] = spec

            # FFT changed, any cached phase/unwrap is now wrong
            ds["results"].pop("phase", None)
            ds["results"].pop("fft_normalized", None)

        # Compute normalized FFT if a reference is selected
        ref_ds = self.app.data.get_reference()
        if ref_ds and "fft" in ref_ds.get("results", {}):
            ref_fft = ref_ds["results"]["fft"]
            for ds in datasets:
                ds["results"]["fft_normalized"] = normalize_fft(ds["results"]["fft"], ref_fft)


        self.app.refresh_view()

    def get_config(self) -> dict:
        """
        Return the processing configuration for this page (JSON-serializable).
        """
        return {
            "window_type": self.window_type.get(),
            "window_args": self.window_args_text.get(),
            "start_time_ps": self.start_time_ps.get(),
            "stop_time_ps": self.stop_time_ps.get(),
        }