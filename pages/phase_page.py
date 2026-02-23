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
from core.processing import compute_phase, unwrap_phase, unwrap_phase_informed

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
            values=["Blind", "Informed"],
            state="readonly"
        )
        cb_unwrap.pack(fill=tk.X, pady=(0, 15))
        cb_unwrap.bind("<<ComboboxSelected>>", lambda e: self._on_method_change())

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

        # Get the reference
        ref_ds = self.app.data.get_reference()
        ref_path = ref_ds.get("path") if ref_ds else None

        for ds in datasets:
            fft_res = ds.get("results", {}).get("fft")
            if fft_res is None:
                continue

            has_any_fft = True
            freqs = fft_res["Freqs"]

            # Phase view
            if self.preview_wrapped_phase.get() or view == "Phase":
                y = compute_phase(fft_res["FFT"])["Phase"]
                if self.preview_wrapped_phase.get():
                    ax.plot(freqs, y, linestyle="None", marker=".", markersize=2.5,
                            label=ds.get("name", "Unnamed"))
                else:
                    ax.plot(freqs, y, label=ds.get("name", "Unnamed"))
                any_plotted = True
            # Unwrapped Phase view
            elif view == "Unwrapped Phase":
                phase_res = ds.get("results", {}).get("phase")
                if phase_res is None or "Unwrapped Phase" not in phase_res:
                    continue
                ax.plot(freqs, phase_res["Unwrapped Phase"], label=ds.get("name", "Unnamed"))
                any_plotted = True

        if not has_any_fft:
            ax.text(0.5, 0.5, "Compute FFT in the Frequency Domain page first.",
                    ha="center", va="center", transform=ax.transAxes, color="gray")
            return

        if not any_plotted:
            ax.text(0.5, 0.5, "Press 'Unwrap phase' to compute the unwrapped phase.",
                    ha="center", va="center", transform=ax.transAxes, color="gray")
            return

        if self.preview_wrapped_phase.get():
            ax.set_ylim(-np.pi, np.pi)

        ax.legend(fontsize=8)

    def on_unwrap_phase(self) -> None:
        """
        Compute and cache unwrapped phase for all datasets that have an FFT.
        """
        datasets = self.app.data.get_all()
        if not datasets:
            self.app.refresh_view()
            return

        method = self.unwrap_method.get()
        is_informed = (method == "Informed")

        ref_ds = self.app.data.get_reference()
        ref_path = ref_ds.get("path") if ref_ds else None

        # For informed unwrapping, we need the reference's t_peak_ps
        ref_fft = ref_ds.get("results", {}).get("fft") if ref_ds else None
        t0_ref = ref_fft.get("t_peak_ps") if ref_fft else None

        # Compute unwrapped phase
        for ds in datasets:
            fft_res = ds.get("results", {}).get("fft")
            fft_norm = ds.get("results", {}).get("fft_normalized")

            if fft_res is None:  # FFT must be computed first
                continue

            # Informed unwrapping
            if is_informed:
                if ref_fft is None or t0_ref is None:
                    print("Informed unwrap: no reference FFT found, falling back to blind.")
                    phase_data = compute_phase(fft_res["FFT"])
                    unwrapped = unwrap_phase(phase_data["Phase"])
                    method_name = "Blind"

                elif ds.get("path") == ref_path:
                    # Skip the reference itself — its phase difference is 0 by definition
                    continue

                elif fft_norm is None:
                    print(f"Informed unwrap: no normalized FFT for {ds.get('name')}, skipping.")
                    continue

                else:
                    t0_sam = fft_res.get("t_peak_ps")
                    if t0_sam is None:
                        print(f"Informed unwrap: no t_peak_ps for {ds.get('name')}, skipping.")
                        continue

                    unwrapped = unwrap_phase_informed(
                        fft_norm["Freqs"],
                        fft_norm["FFT"],
                        t0_sam_ps=t0_sam,
                        t0_ref_ps=t0_ref,
                    )
                    phase_data = {"Phase": np.angle(fft_norm["FFT"])}
                    method_name = "Informed"
            # Otherwise, use blind unwrap
            else:
                phase_data = compute_phase(fft_res["FFT"])
                unwrapped = unwrap_phase(phase_data["Phase"])
                method_name = "Blind"

            ds.setdefault("results", {})
            ds["results"]["phase"] = {
                **phase_data,
                **unwrapped,
                "method": method_name,
            }

        self.app.refresh_view()


    def get_config(self) -> dict:
        """
        Return the processing configuration for this page (JSON-serializable).
        """
        return {
            "unwrap_method": self.unwrap_method.get(),
        }
    
    def _on_method_change(self) -> None:
        """Clear cached phase results when switching unwrap mode."""
        for ds in self.app.data.get_all():
            ds.get("results", {}).pop("phase", None)
        self.app.refresh_view()
