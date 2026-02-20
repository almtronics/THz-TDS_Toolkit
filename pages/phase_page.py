"""
Phase analysis Page.

This page allows the user to:
- Computes and plot phase for all loaded datasets
- Select unwrapping method
- Apply a time-domain window
- Optionally preview the time domain window
"""
import tkinter as tk
from tkinter import ttk
import numpy as np

from ui.base_page import ToolkitPage
from core.processing import compute_phase, unwrap_phase

class PhasePage(ToolkitPage):
    # Page for plotting frequency-domain phase waveform
    def __init__(self, app) -> None:
        """
        Initialize the Phase page.

        Args:
            app: Main application instance (THzToolkitApp).
        """        
        super().__init__(app)
        self.name = "Phase Analysis"
        # View state
        self.phase_view = tk.StringVar(value="Phase")
        # Unwrap
        self.unwrap_method = tk.StringVar(value="Blind")
        self.preview_wrapped_phase = tk.BooleanVar(value=False)

    def build_controls(self, parent) -> None:
        """
        Build the controls panel for the Phase page.

        Args:
            parent: Tkinter Frame that will contain this page's widgets.
        """
        tk.Label(parent, text="Phase View:", bg="#f5f5f5", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        cb_view = ttk.Combobox(
            parent,
            textvariable=self.phase_view,
            values=["Phase", "Unwrapped Phase"],
            state="readonly"
        )
        cb_view.pack(fill=tk.X, pady=(0, 15))
        cb_view.bind("<<ComboboxSelected>>", lambda e: self.app.refresh_view())

        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)
        tk.Label(parent, text="Unwrapping:", bg="#f5f5f5", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))

        ttk.Button(
            parent,
            text="Unwrap phase",
            command=self.on_unwrap_phase,
        ).pack(fill=tk.X, pady=(10, 0))

        cb_unwrap = ttk.Combobox(
            parent,
            textvariable=self.unwrap_method,
            values=["Blind", "Informed (soon)"],
            state="readonly"
        )
        cb_unwrap.pack(fill=tk.X, pady=(0, 15))
        cb_unwrap.bind("<<ComboboxSelected>>", lambda e: self.app.refresh_view())

        tk.Checkbutton(
            parent,
            text="Preview [-π, π]",
            variable=self.preview_wrapped_phase,
            bg="#f5f5f5",
            command=self.app.refresh_view
        ).pack(anchor="w", pady=(0, 10))

    def render_view(self, fig, ax) -> None:
        """
        Render the phase plot.

        Args:
            fig: Shared Matplotlib Figure.
            ax: Shared Matplotlib Axes to draw into.
        """
        datasets = self.app.data.get_all()
        if not datasets:
            ax.text(0.5, 0.5, "No Data Loaded\n Go to Time Domain Page and Click 'Load New Dataset' to begin.", 
                   ha='center', va='center', transform=ax.transAxes, color="gray")
            return
        view = self.phase_view.get()
        ax.set_title(f"Frequency Domain - {view}")
        ax.set_xlabel("Frequency (THz)")
        ax.set_ylabel(view)

        has_any_fft = False
        any_plotted = False

        for ds in datasets:
            fft_res = ds.get("results", {}).get("fft")
            if fft_res is None:
                continue

            has_any_fft = True
            freqs = fft_res["Freqs"]
            fft_c = fft_res["FFT"]

            # Wrapped phase view
            if self.preview_wrapped_phase.get() or view == "Phase":
                y = compute_phase(fft_c)["Phase"]
                if self.preview_wrapped_phase.get():
                    ax.plot(
                        freqs, y,
                        linestyle="None", marker=".", markersize=2.5,
                        label=ds.get("name", "Unnamed"),
                    )
                else:
                    ax.plot(freqs, y, label=ds.get("name", "Unnamed"))
                any_plotted = True
                continue

            # Unwrapped Phase view
            phase_res = ds.get("results", {}).get("phase")
            if phase_res is None or "Unwrapped Phase" not in phase_res:
                continue

            ax.plot(freqs, phase_res["Unwrapped Phase"], label=ds.get("name", "Unnamed"))
            any_plotted = True

        if not has_any_fft:
            ax.text(
                0.5, 0.5,
                "Compute FFT in the Frequency Domain page first.",
                ha="center", va="center",
                transform=ax.transAxes, color="gray",
            )
            return

        if not any_plotted:
            ax.text(
                0.5, 0.5,
                "Press 'Unwrap phase' to compute the unwrapped phase.",
                ha="center", va="center",
                transform=ax.transAxes, color="gray",
            )
            return

        if self.preview_wrapped_phase.get():
            ax.set_ylim(-np.pi, np.pi)

        ax.legend(fontsize=8)

    def on_unwrap_phase(self) -> None:
        """
        Compute and cache unwrapped phase for all datasets that have an FFT.
        Stored under ds["results"]["phase"] with:
            - "Phase": wrapped phase in radians
            - "Unwrapped Phase": continuous phase
            - "method": unwrap method used
        """
        datasets = self.app.data.get_all()
        if not datasets:
            self.app.refresh_view()
            return

        method = self.unwrap_method.get()
        if method.startswith("Informed"):
            self.app._placeholder("Informed unwrap")
            return

        for ds in datasets:
            fft_res = ds.get("results", {}).get("fft")
            if fft_res is None: # FFT must be computed first
                continue

            phase = compute_phase(fft_res["FFT"])
            unwrapped = unwrap_phase(phase["Phase"])

            ds.setdefault("results", {})
            ds["results"]["phase"] = {
                **phase,
                **unwrapped,
                "method": "Blind",
            }

        self.app.refresh_view()