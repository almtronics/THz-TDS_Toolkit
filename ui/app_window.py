"""
Main Application window (Tkinter + Matplotlib).

This module defines the top level GUI shell:
- Menu bar (File / Pages / Tools / Help)
- Page navigation tab strip
- Split workspace (left: plot, right: controls)
"""
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

import json

# Theme constants
COLOR_NAV_BG = "#d0d0d0"
COLOR_TAB_INACTIVE = "#e0e0e0"
COLOR_TAB_ACTIVE = "#ffffff"
COLOR_TAB_HOVER = "#f0f0f0"
COLOR_ACCENT = "#0078d7"

class THzToolkitApp:
    """Top level GUI controller that hosts pages and shared application state."""
    def __init__(self, root, data_manager) -> None:
        """
        Initialize the main application window.
        
        Args:
            root (tk.Tk): Root Tkinter window.
            data_manager (DataManager): Shared data state.
        """
        self.root = root
        self.data = data_manager

        self.root.title("THz-TDS Toolkit")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLOR_NAV_BG)

        self._setup_menu()
        self._setup_nav_bar()
        self._setup_split_pane()

        # Page registry and UI state
        self.pages = {}
        self.nav_buttons = {}
        self.current_page = None

    def export_config_dialog(self):
        """
        Export processing configuration for the currently active page to JSON.
        """
        if not self.current_page:
            return

        path = filedialog.asksaveasfilename(
            title="Export Config",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return

        try:
            cfg = {
                "app": {"name": "THz-TDS Toolkit", "version": "0.0.1-alpha"},
                "page": self.current_page.name,
                "config": self.current_page.get_config(),  # you will add this
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            messagebox.showerror("Export Config Error", str(e))

    def register_page(self, page_class) -> None:
        """
        Instantiates and registers a apge/tab.
        
        Args:
            page_class: Class implementing the page interface (ToolkitPage subclass).
        """
        page = page_class(self)
        self.pages[page.name] = page
        
        btn = tk.Button(
            self.nav_frame, 
            text=page.name, 
            font=("Segoe UI", 10),
            bg=COLOR_TAB_INACTIVE,
            fg="black",
            relief=tk.FLAT,
            bd=0,
            padx=20, pady=8,
            command=lambda p=page.name: self.switch_to_page(p)
        )
        btn.pack(side=tk.LEFT, padx=(0, 2))
        
        btn.bind("<Enter>", lambda e, b=btn: self._on_hover(b, True))
        btn.bind("<Leave>", lambda e, b=btn: self._on_hover(b, False))

        self.nav_buttons[page.name] = btn
        
        # Keep Pages menu in sync with tab strip
        self.pages_menu.add_command(
            label=page.name, 
            command=lambda p=page.name: self.switch_to_page(p)
        )

    def switch_to_page(self, page_name) -> None:
        """
        Switch the active page and rebuild the control panel.

        Args:
            page_name: Name of a registered page.
        """
        self.current_page = self.pages[page_name]

        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.config(bg=COLOR_TAB_ACTIVE, fg=COLOR_ACCENT, font=("Segoe UI", 10, "bold"))
            else:
                btn.config(bg=COLOR_TAB_INACTIVE, fg="black", font=("Segoe UI", 10))

        for widget in self.controls_frame.winfo_children():
            widget.destroy()

        header = tk.Label(self.controls_frame, text=page_name, 
                         font=("Segoe UI Semilight", 18), 
                         fg="#333", bg="#f5f5f5")
        header.pack(pady=(0, 20), anchor="w")

        self.current_page.build_controls(self.controls_frame)
        self.refresh_view()

    def refresh_view(self) -> None:
        """Clear the axes and ask active page to redraw."""
        if not self.current_page: return
        self.ax.clear()
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.current_page.render_view(self.fig, self.ax)
        self.canvas.draw()

    def load_data_dialog(self) -> None:
        """Opens file dialog and loads selected CSVs into DataManager."""
        paths = filedialog.askopenfilenames(filetypes=[("CSV files", "*.csv")])
        if paths:
            skipped = self.data.load_files(paths)
            self.refresh_view()

            if skipped:
                msg = "Some files were not loaded:\n\n" + "\n".join(
                    f"- {p}: {reason}" for p, reason in skipped
                )
                messagebox.showwarning("Import warning", msg)

    def clear_data(self) -> None:
        """Remove all datasets and refreshes plot."""
        self.data.clear()
        self.refresh_view()

    def save_figure(self) -> None:
        """Export the current Matplotlib figure."""
        path = filedialog.asksaveasfilename(
            title="Save Graph",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png"), ("PDF", "*.pdf"), ("SVG", "*.svg")]
        )
        if path:
            try:
                self.fig.savefig(path, dpi=300, bbox_inches="tight")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))
    
    def launch_calculator(self) -> None:
        """Attempts to launch the system calculator."""
        try:
            if platform.system() == "Windows":
                subprocess.Popen("calc.exe")
            elif platform.system() == "Darwin": # macOS
                subprocess.Popen(["open", "-a", "Calculator"])
            else: # Linux
                subprocess.Popen(["gnome-calculator"])
        except Exception:
            self._placeholder("Calculator (System utility not found)")

    def launch_notepad(self) -> None:
        """Attempts to launch the system text editor."""
        try:
            if platform.system() == "Windows":
                subprocess.Popen("notepad.exe")
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-a", "TextEdit"])
            else:
                subprocess.Popen(["gedit"])
        except Exception:
            self._placeholder("Notepad (System utility not found)")


    def show_about(self) -> None:
        """Displays application information."""
        messagebox.showinfo("About", "Terahertz Time-domain Toolkit (TTT)\nVersion 0.0.1-alpha\n© 2026")

    def _setup_menu(self) -> None:
        """Creates the top menu bar"""
        self.menubar = tk.Menu(self.root)

        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Export Config", command=self.export_config_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Print Graph (Save)", command=self.save_figure)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        self.pages_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Pages", menu=self.pages_menu)

        tools_menu = tk.Menu(self.menubar, tearoff=0)
        tools_menu.add_command(label="Calculator", command=self.launch_calculator)
        tools_menu.add_command(label="Notepad", command=self.launch_notepad)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
    
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=self.menubar)

    def _setup_nav_bar(self) -> None:
        """Creates the container for the pages tab strip."""
        self.nav_frame = tk.Frame(self.root, bg=COLOR_NAV_BG, pady=5, padx=5)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)

    def _setup_split_pane(self) -> None:
        """Creates the main resizeable split-pane. (left: plot, right: controls)"""
        self.main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=4, bg=COLOR_NAV_BG)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.plot_frame = tk.Frame(self.main_pane, bg="white", bd=0)
        self.main_pane.add(self.plot_frame, minsize=400, stretch="always")

        self.controls_frame = tk.Frame(self.main_pane, bg="#f5f5f5", padx=15, pady=15)
        self.main_pane.add(self.controls_frame, minsize=300, stretch="never")

        # Shared matplotlib canvas (all pages draw into this)
        self.fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _on_hover(self, btn, is_hovering) -> None:
        """Changes tab color on hover (unless active)."""
        if btn['bg'] != COLOR_TAB_ACTIVE:
            btn.config(bg=COLOR_TAB_HOVER if is_hovering else COLOR_TAB_INACTIVE)

    def _placeholder(self, name) -> None:
        """
        Show a generic message for unimplemented features.

        Args:
            name: Feature name shown to the user.
        """
        messagebox.showinfo("Feature Pending", f"'{name}' functionality is coming soon!")