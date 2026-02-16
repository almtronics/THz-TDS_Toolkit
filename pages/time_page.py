"""
Time domain view page.

This page allows the user to:
- Load and clear datasets
- Plot time (ps) vs amplitude for all visible datasets
- Toggle visibility of each loaded dataset in the time plot
- Select a reference dataset for future normalization operations
"""
import tkinter as tk
from tkinter import ttk

from ui.base_page import ToolkitPage

class TimePage(ToolkitPage):
    # Page for plotting time-domain waveform
    def __init__(self, app) -> None:
        """
        Initialize Time Domain page.

        Args:
            app: Main application instance (THzToolkitApp).
        """
        super().__init__(app)
        self.name = "Time Domain"
        # One bool per dataset path (True = visible, False = hidden)
        self._visible_vars = {}
        # Selected reference dataset
        self._ref_var = tk.StringVar(master=self.app.root, value="")
        self._ref_name_var = tk.StringVar(master=self.app.root, value="Reference: (none)")

    
    def _sync_visibility_vars(self) -> None:
        """
        Ensure visibility flags exist for all loaded datasets.

        Add missing bool for new datasets and removes vars for cleared/unloaded datasets
        """
        datasets = self.app.data.get_all()
        current_paths = set()

        for ds in datasets:
            path = ds.get("path", ds.get("name", ""))
            current_paths.add(path)

            if path not in self._visible_vars:
                self._visible_vars[path] = tk.BooleanVar(value=True)

        for path in list(self._visible_vars.keys()):
            if path not in current_paths:
                del self._visible_vars[path]
        
    def _load_and_rebuild(self) -> None:
        """Load datasets via the app dialog and rebuild controls."""
        self.app.load_data_dialog()
        self.app.switch_to_page(self.name)

    def _clear_and_rebuild(self) -> None:
        """Clear all datasets and rebuild controls."""
        self.app.clear_data()
        self.app.switch_to_page(self.name)

    def _update_ref_label(self) -> None:
        """Update the label showing which dataset is currently selected as reference."""
        ref_path = self._ref_var.get().strip()
        if not ref_path:
            self._ref_name_var.set("Selected reference: (none)")
            return

        for ds in self.app.data.get_all():
            if ds.get("path") == ref_path:
                self._ref_name_var.set(f"Selected reference: {ds.get('name', 'Unnamed')}")
                return

        self._ref_name_var.set("Reference: (unknown)")

    def build_controls(self, parent) -> None:
        """
        Build the controls panel for the Time Domain page.

        Args:
            parent: Tkinter Frame that will contain this page's widgets.
        """
        self._sync_visibility_vars()
        tk.Label(parent, text="Data Management", bg="#f5f5f5", 
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0,5))

        btn_load = tk.Button(parent, text="📂 Load New Dataset", 
                            bg="#e1e1e1", relief=tk.GROOVE,
                            command=self._load_and_rebuild)
        btn_load.pack(fill=tk.X, pady=(0, 5))

        btn_clear = tk.Button(parent, text="❌ Clear All", 
                             bg="#e1e1e1", relief=tk.GROOVE,
                             command=self._clear_and_rebuild)
        btn_clear.pack(fill=tk.X, pady=(0, 20))

        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=10)

        tk.Label(parent, text="Datasets View Controls", bg="#f5f5f5",
                font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0,5))

        datasets = self.app.data.get_all()
        if not datasets:
            tk.Label(parent, text="No datasets loaded.", bg="#f5f5f5", fg="gray").pack(anchor="w")
            return
        
        if self.app.data.reference_path:
            self._ref_var.set(self.app.data.reference_path)
        else:
            self._ref_var.set("")

        for ds in datasets:
            name = ds.get("name", "Unnamed")
            path = ds.get("path", name)

            row = tk.Frame(parent, bg="#f5f5f5")
            row.pack(fill=tk.X, anchor="w")

            tk.Checkbutton(
                row,
                text=name,
                variable=self._visible_vars[path],
                bg="#f5f5f5",
                command=self.app.refresh_view
            ).pack(side=tk.LEFT, anchor="w")

            tk.Radiobutton(
                row,
                text="Ref",
                value=path,
                variable=self._ref_var,
                bg="#f5f5f5",
                command=lambda p=path: (
                    self.app.data.set_reference(p),
                    self._update_ref_label(),
                    self.app.refresh_view()
                )
            ).pack(side=tk.RIGHT)

        self._update_ref_label()
        tk.Label(parent, textvariable=self._ref_name_var, bg="#f5f5f5", fg="gray").pack(anchor="w", pady=(5, 0))


    def render_view(self, fig, ax) -> None:
        """
        Render the time-domain plot.

        Args:
            fig: Shared Matplotlib Figure.
            ax: Shared Matplotlib Axes to draw into.
        """
        self._sync_visibility_vars()

        ax.set_title("Time Domain")
        ax.set_xlabel("Time (ps)")
        ax.set_ylabel("Amplitude")
        datasets = self.app.data.get_all()

        if not datasets:
            ax.text(0.5, 0.5, "No Data Loaded\nClick 'Load New Dataset' to begin.", 
                   ha='center', va='center', transform=ax.transAxes, color="gray")
            return

        for ds in datasets:
            name = ds.get("name", "Unnamed")
            path = ds.get("path", name)

            if not self._visible_vars[path].get():
                continue

            df = ds["df"]
            ax.plot(df["time"], df["real"], label=name)
        
        ax.legend()
