"""Hit detection and position calculation for user interactions."""

import math
from typing import Optional, Dict, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..pod import Pod
    from ..relationship import Relationship


class HitDetection:
    """Handles all hit detection and position calculations for click events."""

    def __init__(self, app):
        """Initialize hit detection with reference to main app."""
        self.app = app

    def get_pod_at_position(self, x: float, y: float) -> Optional['Pod']:
        """Find the pod at the given canvas position."""
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        # Convert to world coordinates (accounting for zoom)
        world_x = (x - offset_x) / self.app.zoom_scale
        world_y = (y - offset_y) / self.app.zoom_scale

        # Check all pods (in reverse order to check top ones first)
        for pod in reversed(self.app.current_container.children):
            if pod.contains_point(world_x, world_y):
                return pod

        return None

    def get_relationship_at_position(self, x: float, y: float) -> Optional['Relationship']:
        """Find the relationship at the given canvas position."""
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        # Convert to world coordinates (accounting for zoom)
        world_x = (x - offset_x) / self.app.zoom_scale
        world_y = (y - offset_y) / self.app.zoom_scale

        # Check all relationships
        for rel in self.app.relationships:
            # Skip relationships where either end is the current container itself
            if rel.source == self.app.current_container or rel.target == self.app.current_container:
                continue

            # Only check relationships where at least one end is a child of the current container
            source_in_container = rel.source.parent == self.app.current_container
            target_in_container = rel.target.parent == self.app.current_container

            if not source_in_container and not target_in_container:
                continue

            x1, y1, x2, y2 = rel.get_endpoints()

            # Calculate distance from point to line segment
            distance = self.point_to_line_distance(world_x, world_y, x1, y1, x2, y2)

            # If within 5 pixels of the line, consider it a hit (scale threshold by zoom)
            if distance < 5 / self.app.zoom_scale:
                return rel

        return None

    def point_to_line_distance(self, px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate the distance from a point to a line segment."""
        # Calculate line length squared
        line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2

        if line_length_sq == 0:
            # Line is actually a point
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        # Calculate projection of point onto line (clamped to segment)
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))

        # Find closest point on line segment
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)

        # Return distance from point to closest point on segment
        return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

    def get_ghost_pod_at_position(self, x: float, y: float) -> Optional['Pod']:
        """Find the ghost pod at the given canvas position."""
        if not self.app.ghost_pods or not self.app.ghost_positions:
            return None

        # Convert canvas position to world coordinates
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y
        world_x = (x - offset_x) / self.app.zoom_scale
        world_y = (y - offset_y) / self.app.zoom_scale

        ghost_width = 100
        ghost_height = 50

        # Check all ghost pods in reverse order (top ones first)
        for pod in reversed(self.app.ghost_pods):
            key = (self.app.current_container.id, pod.id)
            if key not in self.app.ghost_positions:
                continue

            gx, gy = self.app.ghost_positions[key]

            # Check if click is within ghost bounds (in world coordinates)
            x1 = gx - ghost_width / 2
            y1 = gy - ghost_height / 2
            x2 = gx + ghost_width / 2
            y2 = gy + ghost_height / 2

            if x1 <= world_x <= x2 and y1 <= world_y <= y2:
                return pod

        return None

    def get_resize_handle_positions(self, pod: 'Pod', offset_x: float, offset_y: float) -> Dict[str, Tuple[float, float]]:
        """Get the positions of all resize handles for a pod."""
        x1, y1, x2, y2 = pod.get_bounds()

        # Apply zoom scaling
        x1 *= self.app.zoom_scale
        y1 *= self.app.zoom_scale
        x2 *= self.app.zoom_scale
        y2 *= self.app.zoom_scale

        # Apply offset
        x1 += offset_x
        y1 += offset_y
        x2 += offset_x
        y2 += offset_y

        cx = (x1 + x2) / 2  # Center X
        cy = (y1 + y2) / 2  # Center Y

        # Return handle positions: {direction: (x, y)}
        return {
            "nw": (x1, y1),      # Northwest (top-left)
            "n": (cx, y1),       # North (top-center)
            "ne": (x2, y1),      # Northeast (top-right)
            "e": (x2, cy),       # East (middle-right)
            "se": (x2, y2),      # Southeast (bottom-right)
            "s": (cx, y2),       # South (bottom-center)
            "sw": (x1, y2),      # Southwest (bottom-left)
            "w": (x1, cy),       # West (middle-left)
        }

    def get_relationship_button_positions(self, pod: 'Pod', offset_x: float, offset_y: float) -> Dict[str, Tuple[float, float]]:
        """Get the positions of relationship creation buttons (cardinal directions only)."""
        x1, y1, x2, y2 = pod.get_bounds()

        # Apply zoom scaling
        x1 *= self.app.zoom_scale
        y1 *= self.app.zoom_scale
        x2 *= self.app.zoom_scale
        y2 *= self.app.zoom_scale

        # Apply offset
        x1 += offset_x
        y1 += offset_y
        x2 += offset_x
        y2 += offset_y

        cx = (x1 + x2) / 2  # Center X
        cy = (y1 + y2) / 2  # Center Y

        # Distance to place buttons outside the pod border
        button_offset = 20

        # Return button positions: {direction: (x, y)}
        return {
            "n": (cx, y1 - button_offset),       # North
            "e": (x2 + button_offset, cy),       # East
            "s": (cx, y2 + button_offset),       # South
            "w": (x1 - button_offset, cy),       # West
        }

    def get_resize_handle_at_position(self, x: float, y: float, pod: 'Pod') -> Optional[str]:
        """Check if position is over a resize handle. Returns handle direction or None."""
        if not pod.selected:
            return None

        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        handles = self.get_resize_handle_positions(pod, offset_x, offset_y)
        half_size = self.app.resize_handle_size / 2

        # Check each handle
        for direction, (hx, hy) in handles.items():
            if (hx - half_size <= x <= hx + half_size and
                hy - half_size <= y <= hy + half_size):
                return direction

        return None

    def get_relationship_button_at_position(self, x: float, y: float, pod: 'Pod') -> Optional[str]:
        """Check if position is over a relationship button. Returns button direction or None."""
        if not pod.selected:
            return None

        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        buttons = self.get_relationship_button_positions(pod, offset_x, offset_y)
        half_size = self.app.relationship_button_size / 2

        # Check each button
        for direction, (bx, by) in buttons.items():
            # Use circular hit detection
            distance = math.sqrt((x - bx) ** 2 + (y - by) ** 2)
            if distance <= half_size:
                return direction

        return None
