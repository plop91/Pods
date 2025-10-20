"""Rendering engine for visual elements."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pod import Pod
    from ..relationship import Relationship


class RenderManager:
    """Manages all rendering operations for the canvas."""

    def __init__(self, app):
        """Initialize render manager with reference to main app."""
        self.app = app

    def render(self):
        """Render the current view."""
        self.app.canvas.delete("all")

        # Get canvas dimensions
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()

        # Calculate offset to center the view, including pan offset
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        # Set canvas background based on dark mode
        bg_color = "#1E1E1E" if self.app.dark_mode else "white"
        self.app.canvas.config(bg=bg_color)

        # Render grid if enabled
        if self.app.show_grid:
            self.render_grid(canvas_width, canvas_height, offset_x, offset_y)

        # Detect and collect ghost pods (external pods with relationships to current container)
        self.app.ghost_pods = self.collect_ghost_pods()
        self.calculate_ghost_positions(canvas_width, canvas_height)  # Modifies self.app.ghost_positions in place

        # Render relationships first (so they appear behind pods)
        for rel in self.app.relationships:
            self.render_relationship(rel, offset_x, offset_y)

        # Render pods
        for pod in self.app.current_container.children:
            self.render_pod(pod, offset_x, offset_y)

        # Render ghost pods
        self.render_ghost_pods()

        # Update minimap if visible
        if self.app.minimap_manager.show_minimap and self.app.minimap_manager.minimap_window and self.app.minimap_manager.minimap_window.winfo_exists():
            self.app.minimap_manager.render_minimap()

        # Render relationship creation indicator if in creation mode
        if self.app.creating_relationship and self.app.relationship_source_pod:
            # Draw instruction text (not affected by zoom)
            text_color = "#4ADE80" if self.app.dark_mode else "#27AE60"  # Lighter green for dark mode
            self.app.canvas.create_text(
                offset_x, 20,
                text="Click on a pod to create a relationship",
                fill=text_color,
                font=("Arial", 12, "bold"),
                tags=("relationship_creation_hint",)
            )

            # Draw external link zone on the right side
            self.render_external_link_zone(canvas_width, canvas_height)

    def render_pod(self, pod: 'Pod', offset_x: float, offset_y: float):
        """Render a single pod on the canvas."""
        x1, y1, x2, y2 = pod.get_bounds()

        # Apply zoom scaling
        x1 *= self.app.zoom_scale
        y1 *= self.app.zoom_scale
        x2 *= self.app.zoom_scale
        y2 *= self.app.zoom_scale

        # Apply offset for centering
        x1 += offset_x
        y1 += offset_y
        x2 += offset_x
        y2 += offset_y

        # Determine colors based on state
        fill_color = pod.color
        outline_color = pod.border_color
        outline_width = 2

        if pod.selected:
            outline_color = "#3498DB"
            outline_width = 3
        elif pod.hovered:
            outline_color = "#5DADE2"

        # Draw shape (force rectangle if description is enabled)
        if pod.has_description or pod.shape == "rectangle":
            self.app.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                tags=("pod", pod.id)
            )
        else:  # oval
            self.app.canvas.create_oval(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                tags=("pod", pod.id)
            )

        # Draw text and description if enabled
        # Use smart contrast detection to ensure text is readable on any background
        text_color = self.get_contrast_text_color(pod.color)

        if pod.has_description:
            # Calculate separator position (30% from top for name section)
            separator_y = y1 + (y2 - y1) * 0.3
            name_y = y1 + (separator_y - y1) / 2
            desc_y = separator_y + (y2 - separator_y) / 2

            # Draw name in top section
            self.app.canvas.create_text(
                pod.x * self.app.zoom_scale + offset_x, name_y,
                text=pod.name,
                fill=text_color,
                font=("Arial", 10, "bold"),
                tags=("pod", pod.id)
            )

            # Draw separator line
            separator_color = "#666666" if self.app.dark_mode else "#95A5A6"
            self.app.canvas.create_line(
                x1 + 5, separator_y, x2 - 5, separator_y,
                fill=separator_color,
                width=1,
                tags=("pod", pod.id)
            )

            # Draw description in bottom section (word-wrapped if needed)
            if pod.description:
                # Simple word wrapping
                max_width = (pod.width - 10) * self.app.zoom_scale
                wrapped_text = self.wrap_text(pod.description, max_width, ("Arial", 8))
                self.app.canvas.create_text(
                    pod.x * self.app.zoom_scale + offset_x, desc_y,
                    text=wrapped_text,
                    fill=text_color,
                    font=("Arial", 8),
                    width=max_width,
                    tags=("pod", pod.id)
                )
        else:
            # Draw text normally
            self.app.canvas.create_text(
                pod.x * self.app.zoom_scale + offset_x, pod.y * self.app.zoom_scale + offset_y,
                text=pod.name,
                fill=text_color,
                font=("Arial", 10),
                tags=("pod", pod.id)
            )

        # Draw indicator if pod has children
        if pod.children:
            # Use same contrast logic for indicator
            indicator_color = self.get_contrast_text_color(pod.color)
            self.app.canvas.create_text(
                pod.x * self.app.zoom_scale + offset_x, y2 - 5,
                text="⋯",
                fill=indicator_color,
                font=("Arial", 8),
                tags=("pod", pod.id)
            )

        # Draw resize handles if pod is selected
        if pod.selected:
            self.render_resize_handles(pod, offset_x, offset_y)
            self.render_relationship_buttons(pod, offset_x, offset_y)

    def wrap_text(self, text: str, max_width: float, font) -> str:
        """Simple text wrapping helper."""
        # For simplicity, just return the text - tkinter Text widget handles wrapping
        # This could be enhanced with proper text measurement
        return text

    def get_luminance(self, hex_color: str) -> float:
        """Calculate relative luminance of a color (0-1 scale).

        Uses the formula from WCAG 2.0:
        https://www.w3.org/TR/WCAG20/#relativeluminancedef
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')

        # Convert hex to RGB (0-255)
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0

        # Apply gamma correction
        def adjust(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        r, g, b = adjust(r), adjust(g), adjust(b)

        # Calculate luminance
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def get_contrast_text_color(self, bg_color: str) -> str:
        """Return black or white text color based on background luminance.

        Returns white text for dark backgrounds, black for light backgrounds.
        """
        luminance = self.get_luminance(bg_color)
        # Use white text if background is dark (luminance < 0.5)
        return "#FFFFFF" if luminance < 0.5 else "#000000"

    def collect_ghost_pods(self) -> list:
        """Collect all external pods that have relationships to/from pods in current container.

        Returns a list of unique external pods that should be shown as ghosts.
        """
        ghost_pods = []
        seen_pod_ids = set()

        for rel in self.app.relationships:
            # Check if source is in current container and target is external
            source_in_container = rel.source.parent == self.app.current_container
            target_in_container = rel.target.parent == self.app.current_container

            # Don't include the current container itself
            if rel.source == self.app.current_container or rel.target == self.app.current_container:
                continue

            # If source is in container and target is external, add target as ghost
            if source_in_container and not target_in_container:
                if rel.target.id not in seen_pod_ids:
                    ghost_pods.append(rel.target)
                    seen_pod_ids.add(rel.target.id)

            # If target is in container and source is external, add source as ghost
            if target_in_container and not source_in_container:
                if rel.source.id not in seen_pod_ids:
                    ghost_pods.append(rel.source)
                    seen_pod_ids.add(rel.source.id)

        return ghost_pods

    def calculate_ghost_positions(self, canvas_width: float, canvas_height: float):
        """Initialize positions for ghost pods that don't have positions yet.

        Uses world coordinates. Only sets positions for new ghosts that haven't been positioned yet.
        """
        if not self.app.ghost_pods:
            return

        # Ensure ghost_positions is initialized
        if self.app.ghost_positions is None:
            self.app.ghost_positions = {}

        # Calculate positions for ghosts that don't have saved positions
        # Position them along the right edge of the canvas
        right_edge_x = canvas_width / 2 - 50  # World X coordinate for right edge
        spacing = 100
        start_y = -len(self.app.ghost_pods) * spacing / 2

        for i, ghost_pod in enumerate(self.app.ghost_pods):
            key = (self.app.current_container.id, ghost_pod.id)
            if key not in self.app.ghost_positions:
                # Assign default position (world coordinates)
                ghost_y = start_y + i * spacing
                self.app.ghost_positions[key] = (right_edge_x, ghost_y)

    def render_ghost_pods(self):
        """Render ghost pods (external pods with relationships to current container)."""
        if not self.app.ghost_pods:
            return

        # Get canvas dimensions for offset calculation
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        for ghost_pod in self.app.ghost_pods:
            # Get position from ghost_positions (world coordinates)
            key = (self.app.current_container.id, ghost_pod.id)
            if key not in self.app.ghost_positions:
                continue

            world_x, world_y = self.app.ghost_positions[key]

            # Convert world coordinates to canvas coordinates with zoom
            canvas_x = world_x * self.app.zoom_scale + offset_x
            canvas_y = world_y * self.app.zoom_scale + offset_y

            # Ghost pod dimensions (in world coordinates)
            ghost_width = 80
            ghost_height = 40

            # Calculate bounds in canvas coordinates
            x1 = canvas_x - (ghost_width / 2) * self.app.zoom_scale
            y1 = canvas_y - (ghost_height / 2) * self.app.zoom_scale
            x2 = canvas_x + (ghost_width / 2) * self.app.zoom_scale
            y2 = canvas_y + (ghost_height / 2) * self.app.zoom_scale

            # Determine color based on selection
            if self.app.selected_ghost == ghost_pod:
                fill_color = "#E8F4F8"  # Light blue for selected
                outline_color = "#3498DB"  # Blue outline
                outline_width = 2
            else:
                fill_color = "#F0F0F0"  # Light gray
                outline_color = "#999999"  # Gray outline
                outline_width = 1

            # Draw ghost pod rectangle with dashed outline
            self.app.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                dash=(4, 4),
                tags=("ghost_pod", ghost_pod.id)
            )

            # Draw ghost pod name
            self.app.canvas.create_text(
                canvas_x, canvas_y,
                text=ghost_pod.name,
                fill="#666666",
                font=("Arial", 8, "italic"),
                tags=("ghost_pod", ghost_pod.id)
            )

    def render_external_link_zone(self, canvas_width: float, canvas_height: float):
        """Render the external link zone on the right side during relationship creation."""
        zone_width = self.app.external_link_zone_width

        # Draw a highlighted zone on the right edge
        zone_color = "#E8F8E8" if not self.app.dark_mode else "#2A4A2A"  # Light/dark green
        border_color = "#4ADE80" if not self.app.dark_mode else "#27AE60"

        # Zone rectangle
        self.app.canvas.create_rectangle(
            canvas_width - zone_width, 0,
            canvas_width, canvas_height,
            fill=zone_color,
            outline=border_color,
            width=2,
            tags=("external_link_zone",)
        )

        # Draw text instruction
        text_color = "#27AE60" if not self.app.dark_mode else "#4ADE80"
        self.app.canvas.create_text(
            canvas_width - zone_width / 2, canvas_height / 2,
            text="Drop here\nfor external\nlink",
            fill=text_color,
            font=("Arial", 9, "bold"),
            justify="center",
            tags=("external_link_zone",)
        )

    def render_resize_handles(self, pod: 'Pod', offset_x: float, offset_y: float):
        """Render resize handles for a selected pod."""
        # Get handle positions from app.py to ensure consistency with hit detection
        handles = self.app.hit_detection.get_resize_handle_positions(pod, offset_x, offset_y)
        handle_size = self.app.resize_handle_size

        for handle_id, (hx, hy) in handles.items():
            self.app.canvas.create_rectangle(
                hx - handle_size, hy - handle_size,
                hx + handle_size, hy + handle_size,
                fill="#FFFFFF",
                outline="#3498DB",
                width=2,
                tags=("resize_handle", f"resize_handle_{handle_id}", pod.id)
            )

    def render_relationship_buttons(self, pod: 'Pod', offset_x: float, offset_y: float):
        """Render the relationship creation buttons (+ buttons on each side)."""
        # Get button positions from app.py to ensure consistency with hit detection
        buttons = self.app.hit_detection.get_relationship_button_positions(pod, offset_x, offset_y)
        button_size = self.app.relationship_button_size

        for direction, (bx, by) in buttons.items():
            # Draw button background
            self.app.canvas.create_oval(
                bx - button_size, by - button_size,
                bx + button_size, by + button_size,
                fill="#27AE60",
                outline="#FFFFFF",
                width=1,
                tags=("relationship_button", f"relationship_button_{direction}", pod.id)
            )

            # Draw + symbol
            self.app.canvas.create_text(
                bx, by,
                text="+",
                fill="#FFFFFF",
                font=("Arial", 10, "bold"),
                tags=("relationship_button", f"relationship_button_{direction}", pod.id)
            )

    def render_relationship(self, rel: 'Relationship', offset_x: float, offset_y: float):
        """Render a relationship line between two pods."""
        # Get source and target positions
        source_x = rel.source.x * self.app.zoom_scale + offset_x
        source_y = rel.source.y * self.app.zoom_scale + offset_y
        target_x = rel.target.x * self.app.zoom_scale + offset_x
        target_y = rel.target.y * self.app.zoom_scale + offset_y

        # Check if either endpoint is a ghost pod
        source_is_ghost = rel.source in self.app.ghost_pods
        target_is_ghost = rel.target in self.app.ghost_pods

        # If source is a ghost, use its ghost position
        if source_is_ghost:
            key = (self.app.current_container.id, rel.source.id)
            if key in self.app.ghost_positions:
                world_x, world_y = self.app.ghost_positions[key]
                source_x = world_x * self.app.zoom_scale + offset_x
                source_y = world_y * self.app.zoom_scale + offset_y

        # If target is a ghost, use its ghost position
        if target_is_ghost:
            key = (self.app.current_container.id, rel.target.id)
            if key in self.app.ghost_positions:
                world_x, world_y = self.app.ghost_positions[key]
                target_x = world_x * self.app.zoom_scale + offset_x
                target_y = world_y * self.app.zoom_scale + offset_y

        # Only draw if BOTH endpoints are visible (in container or shown as ghost)
        source_in_container = rel.source.parent == self.app.current_container
        target_in_container = rel.target.parent == self.app.current_container

        # Check if both endpoints are visible
        source_visible = source_in_container or source_is_ghost
        target_visible = target_in_container or target_is_ghost

        if not (source_visible and target_visible):
            return

        # Determine line color
        if self.app.selected_relationship == rel:
            line_color = "#E74C3C"  # Red for selected
            line_width = 3
        else:
            line_color = rel.color
            line_width = 2

        # Draw the line
        line_style = {"dash": (5, 5)} if (source_is_ghost or target_is_ghost) else {}
        self.app.canvas.create_line(
            source_x, source_y, target_x, target_y,
            fill=line_color,
            width=line_width,
            tags=("relationship", rel.id),
            **line_style
        )

        # Draw arrow at target end
        import math
        arrow_size = 10
        angle = math.atan2(target_y - source_y, target_x - source_x)

        # Calculate arrow points
        arrow_x1 = target_x - arrow_size * math.cos(angle - math.pi / 6)
        arrow_y1 = target_y - arrow_size * math.sin(angle - math.pi / 6)
        arrow_x2 = target_x - arrow_size * math.cos(angle + math.pi / 6)
        arrow_y2 = target_y - arrow_size * math.sin(angle + math.pi / 6)

        self.app.canvas.create_polygon(
            target_x, target_y,
            arrow_x1, arrow_y1,
            arrow_x2, arrow_y2,
            fill=line_color,
            outline=line_color,
            tags=("relationship", rel.id)
        )

        # Draw label if present
        if rel.label:
            # Position label at midpoint
            mid_x = (source_x + target_x) / 2
            mid_y = (source_y + target_y) / 2

            # Background for label
            bg_color = "#FFFFCC" if not self.app.dark_mode else "#3A3A3A"
            text_color = "#000000" if not self.app.dark_mode else "#FFFFFF"

            self.app.canvas.create_text(
                mid_x, mid_y,
                text=rel.label,
                fill=text_color,
                font=("Arial", 8),
                tags=("relationship", rel.id)
            )

    def render_grid(self, canvas_width: float, canvas_height: float, offset_x: float, offset_y: float):
        """Render a grid on the canvas."""
        grid_color = "#E0E0E0" if not self.app.dark_mode else "#2A2A2A"
        grid_size = self.app.grid_size * self.app.zoom_scale

        # Calculate grid starting position
        start_x = offset_x % grid_size
        start_y = offset_y % grid_size

        # Draw vertical lines
        x = start_x
        while x < canvas_width:
            self.app.canvas.create_line(
                x, 0, x, canvas_height,
                fill=grid_color,
                width=1,
                tags=("grid",)
            )
            x += grid_size

        # Draw horizontal lines
        y = start_y
        while y < canvas_height:
            self.app.canvas.create_line(
                0, y, canvas_width, y,
                fill=grid_color,
                width=1,
                tags=("grid",)
            )
            y += grid_size
