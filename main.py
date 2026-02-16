"""
Application entry point for the THz-TDS Toolkit GUI.

- Creates Tkinter root window
- Initializes shared DataManager
- Builds main application shell
- Registers pages/tools
- Start the Tk event loop
"""
import tkinter as tk

from core.data_manager import DataManager
from ui.app_window import THzToolkitApp

from pages.time_page import TimePage
from pages.magnitude_page import MagnitudePage
from pages.phase_page import PhasePage

def main() -> None:
    """Launch the application."""
    root = tk.Tk()
    data_mgr = DataManager()
    app = THzToolkitApp(root, data_mgr)
    # Register Pages
    app.register_page(TimePage)
    app.register_page(MagnitudePage)
    app.register_page(PhasePage)
    # Set initial view and start
    app.switch_to_page("Time Domain")
    root.mainloop()

if __name__ == "__main__":
    main()
