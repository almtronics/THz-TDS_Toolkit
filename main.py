"""
Application entry point for the THz-TDS Toolkit GUI.

- Creates Tkinter root window
- Initializes shared DataManager
- Builds main application shell
- Registers pages/tools
- Start the Tk event loop
"""
import tkinter as tk
import os
import sys

from core.data_manager import DataManager
from ui.app_window import THzToolkitApp

from pages.time_page import TimePage
from pages.frequency_page import FrequencyPage
from pages.phase_page import PhasePage

def resource_path(relative_path):
    """ Get absolute path to resource """
    try: # PyInstaller temp folder at runtime
        base_path = sys._MEIPASS
    except Exception: # Not runtime, use standard path
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main() -> None:
    """Launch the application."""
    root = tk.Tk()
    icon_path = resource_path(os.path.join("img", "TTT.ico"))
    root.iconbitmap(icon_path)

    data_mgr = DataManager()
    app = THzToolkitApp(root, data_mgr)
    # Register Pages
    app.register_page(TimePage)
    app.register_page(FrequencyPage)
    app.register_page(PhasePage)
    # Set initial view and start
    app.switch_to_page("Time Domain")
    root.mainloop()

if __name__ == "__main__":
    main()
