"""Minimap functionality for overview navigation."""

import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pod import Pod


class MinimapManager:
    """Manages minimap window and navigation functionality."""

    def __init__(self, app):
        """Initialize minimap manager with reference to main app."""
        self.app = app
        self.minimap_window = None
        self.minimap_canvas = None
        self.show_minimap = False

    def toggle_minimap(self):
        """Toggle minimap window visibility."""
        if self.minimap_window and self.minimap_window.winfo_exists():
            self.minimap_window.destroy()
            self.minimap_window = None
            self.show_minimap = False
        else:
            self.show_minimap_window()

    def show_minimap_window(self):
        """Create and show the minimap window."""
        self.minimap_window = tk.Toplevel(self.app.root)
        self.minimap_window.title("Minimap")
        self.minimap_window.geometry("250x250")
        self.minimap_window.attributes('-topmost', True)

        # Position at bottom-right of main window
        self.minimap_window.update_idletasks()
        x = self.app.root.winfo_x() + self.app.root.winfo_width() - 270
        y = self.app.root.winfo_y() + self.app.root.winfo_height() - 300
        self.minimap_window.geometry(f"+{x}+{y}")

        # Create canvas for minimap
        self.minimap_canvas = tk.Canvas(self.minimap_window, bg="white", highlightthickness=1, highlightbackground="#999")
        self.minimap_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Render minimap
        self.render_minimap()

        # Bind click to navigate
        self.minimap_canvas.bind("<Button-1>", self.on_minimap_click)

        # Update minimap when main canvas is rendered
        self.show_minimap = True

    def render_minimap(self):
        """Render the minimap showing all pods in current container."""
        if not self.minimap_window or not self.minimap_window.winfo_exists():
            return

        self.minimap_canvas.delete("all")

        if not self.app.current_container.children:
            return

        # Get minimap canvas size
        mm_width = self.minimap_canvas.winfo_width()
        mm_height = self.minimap_canvas.winfo_height()

        if mm_width < 10 or mm_height < 10:
            return

        # Calculate bounding box of all pods
        min_x = min(pod.x - pod.width / 2 for pod in self.app.current_container.children)
        max_x = max(pod.x + pod.width / 2 for pod in self.app.current_container.children)
        min_y = min(pod.y - pod.height / 2 for pod in self.app.current_container.children)
        max_y = max(pod.y + pod.height / 2 for pod in self.app.current_container.children)

        # Add padding
        padding = 50
        min_x -= padding
        max_x += padding
        min_y -= padding
        max_y += padding

        # Calculate scale to fit everything
        world_width = max_x - min_x
        world_height = max_y - min_y

        if world_width == 0 or world_height == 0:
            return

        scale_x = mm_width / world_width
        scale_y = mm_height / world_height
        scale = min(scale_x, scale_y) * 0.9  # Use 90% to leave some margin

        # Transform function
        def world_to_minimap(wx, wy):
            mx = (wx - min_x) * scale
            my = (wy - min_y) * scale
            return mx, my

        # Draw relationships
        for rel in self.app.relationships:
            # Only draw relationships in current container
            if rel.source.parent == self.app.current_container and rel.target.parent == self.app.current_container:
                x1, y1 = world_to_minimap(rel.source.x, rel.source.y)
                x2, y2 = world_to_minimap(rel.target.x, rel.target.y)
                self.minimap_canvas.create_line(x1, y1, x2, y2, fill="#999", width=1)

        # Draw pods
        for pod in self.app.current_container.children:
            x1, y1, x2, y2 = pod.get_bounds()
            mx1, my1 = world_to_minimap(x1, y1)
            mx2, my2 = world_to_minimap(x2, y2)

            # Use pod color but slightly darker
            color = pod.color if not pod.selected else "#3498DB"
            self.minimap_canvas.create_rectangle(
                mx1, my1, mx2, my2,
                fill=color,
                outline="#666",
                width=1
            )

        # Draw viewport indicator
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()

        # Calculate viewport in world coordinates
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        viewport_world_x1 = -offset_x / self.app.zoom_scale
        viewport_world_y1 = -offset_y / self.app.zoom_scale
        viewport_world_x2 = (canvas_width - offset_x) / self.app.zoom_scale
        viewport_world_y2 = (canvas_height - offset_y) / self.app.zoom_scale

        # Transform to minimap coordinates
        vp_x1, vp_y1 = world_to_minimap(viewport_world_x1, viewport_world_y1)
        vp_x2, vp_y2 = world_to_minimap(viewport_world_x2, viewport_world_y2)

        # Draw viewport rectangle
        self.minimap_canvas.create_rectangle(
            vp_x1, vp_y1, vp_x2, vp_y2,
            outline="#FF0000",
            width=2,
            tags=("viewport",)
        )

    def on_minimap_click(self, event):
        """Handle click on minimap to pan viewport."""
        if not self.app.current_container.children:
            return

        mm_width = self.minimap_canvas.winfo_width()
        mm_height = self.minimap_canvas.winfo_height()

        # Calculate bounding box (same as in render_minimap)
        min_x = min(pod.x - pod.width / 2 for pod in self.app.current_container.children)
        max_x = max(pod.x + pod.width / 2 for pod in self.app.current_container.children)
        min_y = min(pod.y - pod.height / 2 for pod in self.app.current_container.children)
        max_y = max(pod.y + pod.height / 2 for pod in self.app.current_container.children)

        padding = 50
        min_x -= padding
        max_x += padding
        min_y -= padding
        max_y += padding

        world_width = max_x - min_x
        world_height = max_y - min_y

        if world_width == 0 or world_height == 0:
            return

        scale_x = mm_width / world_width
        scale_y = mm_height / world_height
        scale = min(scale_x, scale_y) * 0.9

        # Convert minimap click to world coordinates
        world_x = (event.x / scale) + min_x
        world_y = (event.y / scale) + min_y

        # Center viewport on this world position
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()

        # Calculate pan offset to center on clicked position
        self.app.pan_offset_x = -(world_x * self.app.zoom_scale - canvas_width / 2)
        self.app.pan_offset_y = -(world_y * self.app.zoom_scale - canvas_height / 2)

        self.app.render()
        if self.show_minimap:
            self.render_minimap()
