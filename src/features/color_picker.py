"""Color picker functionality for changing pod colors."""

from tkinter import colorchooser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pod import Pod


class ColorPickerManager:
    """Manages color selection and pod color changes."""

    def __init__(self, app):
        """Initialize color picker manager with reference to main app."""
        self.app = app

    def set_pod_color(self, pod: 'Pod', color: str):
        """Set pod color to a specific color."""
        # Save state for undo
        self.app.state_manager.save_state()

        # Update pod color
        pod.color = color
        self.app.render()

    def change_pod_color(self, pod: 'Pod'):
        """Open color picker to change pod color."""
        # Open color chooser with current color
        color = colorchooser.askcolor(
            color=pod.color,
            title="Choose Pod Color",
            parent=self.app.root
        )

        if color and color[1]:  # color is ((r,g,b), '#RRGGBB')
            # Save state for undo
            self.app.state_manager.save_state()

            # Update pod color
            pod.color = color[1]
            self.app.render()
