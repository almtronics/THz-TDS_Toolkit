"""
Base class for pages of the application.

Each page is responsible for:
- Building its own controls in the right side panel (build_controls)
- Redering its own plot into the shared Matplotlib (render_view)

THzToolkitApp switches between pages and calls these two methods, so every
page must implement them.
"""
class ToolkitPage:
    """
    Base class for all pages.
    """
    def __init__(self, app_context) -> None:
        """
        Initialize the page.

        Args:
            app_context (THzToolkitApp): Main application instance, used to 
            access shared states and request refreshes.
        """
        self.app = app_context
        self.name = "Unnamed Page"

    def build_controls(self, parent_frame) -> None:
        """
        Override to build the right side panel controls for this page.
        
        Args:
            parent_frame (tk.Frame): kinter Frame that will contain this page widgets
        """
        raise NotImplementedError("Pages must implement build_controls().")

    def render_view(self, figure, ax) -> None:
        """
        Override to render the plot for this page.
        
        Args:
            figure (matplotlib.figure.Figure): The shared Matplotlib Figure object.
            ax (matplotlib.axes.Axes): The shared Matplotlib Axes to draw into.
        """
        raise NotImplementedError("Pages must implement render_view().")
    
    def get_config(self) -> dict:
        """
        Return a JSON-serializable dict describing the page's processing configuration.
        """
        return {}
