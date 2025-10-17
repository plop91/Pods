"""Main application window with canvas and interaction handling."""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional
import math

from .pod import Pod
from .relationship import Relationship


class PodsApp:
    """Main application for the Pods visual idea organization tool."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Pods - Visual Idea Organization")
        self.root.geometry("1200x800")

        # Initialize the main pod (root container)
        self.main_pod = Pod("Main", x=0, y=0, width=0, height=0)
        self.current_container = self.main_pod

        # All relationships in the project
        self.relationships: List[Relationship] = []

        # Interaction state
        self.selected_pod: Optional[Pod] = None
        self.dragging = False
        self.resizing = False
        self.resize_handle = None  # Which handle is being dragged (e.g., "nw", "n", "ne", etc.)
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.resize_handle_size = 6  # Size of resize handles in pixels

        # Navigation history for back button
        self.navigation_history = []

        # Setup UI
        self.setup_ui()

        # Create some example pods
        self.create_example_data()

        # Initial render
        self.render()

    def setup_ui(self):
        """Setup the user interface."""
        # Top toolbar
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Navigation info
        self.nav_label = ttk.Label(toolbar, text="Current: Main")
        self.nav_label.pack(side=tk.LEFT, padx=5)

        # Back button
        self.back_button = ttk.Button(toolbar, text="← Back", command=self.navigate_back)
        self.back_button.pack(side=tk.LEFT, padx=5)
        self.back_button.config(state=tk.DISABLED)

        # Add pod button
        add_button = ttk.Button(toolbar, text="+ Add Pod", command=self.add_new_pod)
        add_button.pack(side=tk.LEFT, padx=5)

        # Canvas
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Event bindings
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_canvas_motion)

    def create_example_data(self):
        """Create some example pods and relationships for demonstration."""
        # Create some example pods in the main container
        pod1 = Pod("Project Ideas", x=200, y=200, width=120, height=70, shape="oval")
        pod2 = Pod("Team Members", x=450, y=200, width=120, height=70, shape="rectangle")
        pod3 = Pod("Resources", x=200, y=400, width=120, height=70, shape="oval")
        pod4 = Pod("Timeline", x=450, y=400, width=120, height=70, shape="rectangle")

        self.main_pod.add_child(pod1)
        self.main_pod.add_child(pod2)
        self.main_pod.add_child(pod3)
        self.main_pod.add_child(pod4)

        # Create some relationships
        rel1 = Relationship(pod1, pod2, label="worked on by")
        rel2 = Relationship(pod2, pod3, label="uses")
        rel3 = Relationship(pod3, pod4, label="scheduled in")

        self.relationships.extend([rel1, rel2, rel3])

        # Add some child pods to demonstrate hierarchy
        sub_pod1 = Pod("Feature A", x=150, y=150, width=100, height=60, shape="oval")
        sub_pod2 = Pod("Feature B", x=350, y=150, width=100, height=60, shape="oval")
        pod1.add_child(sub_pod1)
        pod1.add_child(sub_pod2)

    def render(self):
        """Render the current view."""
        self.canvas.delete("all")

        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate offset to center the view
        offset_x = canvas_width / 2
        offset_y = canvas_height / 2

        # Render relationships first (so they appear behind pods)
        for rel in self.relationships:
            self.render_relationship(rel, offset_x, offset_y)

        # Render pods
        for pod in self.current_container.children:
            self.render_pod(pod, offset_x, offset_y)

    def render_pod(self, pod: Pod, offset_x: float, offset_y: float):
        """Render a single pod on the canvas."""
        x1, y1, x2, y2 = pod.get_bounds()

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

        # Draw shape
        if pod.shape == "oval":
            self.canvas.create_oval(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                tags=("pod", pod.id)
            )
        else:  # rectangle
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                tags=("pod", pod.id)
            )

        # Draw text
        self.canvas.create_text(
            pod.x + offset_x, pod.y + offset_y,
            text=pod.name,
            fill=pod.text_color,
            font=("Arial", 10),
            tags=("pod", pod.id)
        )

        # Draw indicator if pod has children
        if pod.children:
            self.canvas.create_text(
                pod.x + offset_x, y2 - 5,
                text="⋯",
                fill="#7F8C8D",
                font=("Arial", 8),
                tags=("pod", pod.id)
            )

        # Draw resize handles if pod is selected
        if pod.selected:
            self.render_resize_handles(pod, offset_x, offset_y)

    def get_resize_handle_positions(self, pod: Pod, offset_x: float, offset_y: float):
        """Get the positions of all resize handles for a pod."""
        x1, y1, x2, y2 = pod.get_bounds()

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

    def render_resize_handles(self, pod: Pod, offset_x: float, offset_y: float):
        """Render resize handles around a selected pod."""
        handles = self.get_resize_handle_positions(pod, offset_x, offset_y)
        half_size = self.resize_handle_size / 2

        for direction, (hx, hy) in handles.items():
            # Draw a small rectangle for each handle
            self.canvas.create_rectangle(
                hx - half_size, hy - half_size,
                hx + half_size, hy + half_size,
                fill="white",
                outline="#3498DB",
                width=2,
                tags=("resize_handle", f"handle_{direction}", pod.id)
            )

    def render_relationship(self, rel: Relationship, offset_x: float, offset_y: float):
        """Render a relationship line between pods."""
        # Only render if both pods are in the current container
        if (rel.source.parent != self.current_container and rel.source != self.current_container):
            return
        if (rel.target.parent != self.current_container and rel.target != self.current_container):
            return

        x1, y1, x2, y2 = rel.get_endpoints()

        # Apply offset
        x1 += offset_x
        y1 += offset_y
        x2 += offset_x
        y2 += offset_y

        # Draw line
        color = "#3498DB" if rel.selected else rel.color
        self.canvas.create_line(
            x1, y1, x2, y2,
            fill=color,
            width=rel.line_width,
            arrow=tk.LAST if rel.arrow else None,
            tags=("relationship", rel.id)
        )

        # Draw label if present
        if rel.label:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            self.canvas.create_text(
                mid_x, mid_y - 10,
                text=rel.label,
                fill="#7F8C8D",
                font=("Arial", 8),
                tags=("relationship", rel.id)
            )

    def get_pod_at_position(self, x: float, y: float) -> Optional[Pod]:
        """Find the pod at the given canvas position."""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = canvas_width / 2
        offset_y = canvas_height / 2

        # Convert to world coordinates
        world_x = x - offset_x
        world_y = y - offset_y

        # Check all pods (in reverse order to check top ones first)
        for pod in reversed(self.current_container.children):
            if pod.contains_point(world_x, world_y):
                return pod

        return None

    def get_resize_handle_at_position(self, x: float, y: float, pod: Pod) -> Optional[str]:
        """Check if position is over a resize handle. Returns handle direction or None."""
        if not pod.selected:
            return None

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = canvas_width / 2
        offset_y = canvas_height / 2

        handles = self.get_resize_handle_positions(pod, offset_x, offset_y)
        half_size = self.resize_handle_size / 2

        # Check each handle
        for direction, (hx, hy) in handles.items():
            if (hx - half_size <= x <= hx + half_size and
                hy - half_size <= y <= hy + half_size):
                return direction

        return None

    def resize_pod(self, mouse_x: float, mouse_y: float):
        """Resize the selected pod based on the resize handle being dragged."""
        if not self.selected_pod or not self.resize_handle:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = canvas_width / 2
        offset_y = canvas_height / 2

        # Convert mouse position to world coordinates
        world_x = mouse_x - offset_x
        world_y = mouse_y - offset_y

        # Get current bounds in world coordinates
        x1, y1, x2, y2 = self.selected_pod.get_bounds()

        # Minimum size constraints
        min_width = 40
        min_height = 30

        # Adjust bounds based on which handle is being dragged
        handle = self.resize_handle

        # Handle vertical resizing
        if 'n' in handle:  # North handles (top)
            y1 = world_y
        if 's' in handle:  # South handles (bottom)
            y2 = world_y

        # Handle horizontal resizing
        if 'w' in handle:  # West handles (left)
            x1 = world_x
        if 'e' in handle:  # East handles (right)
            x2 = world_x

        # Ensure minimum size
        if x2 - x1 < min_width:
            if 'w' in handle:
                x1 = x2 - min_width
            else:
                x2 = x1 + min_width

        if y2 - y1 < min_height:
            if 'n' in handle:
                y1 = y2 - min_height
            else:
                y2 = y1 + min_height

        # Calculate new center position and dimensions
        new_x = (x1 + x2) / 2
        new_y = (y1 + y2) / 2
        new_width = x2 - x1
        new_height = y2 - y1

        # Update pod
        self.selected_pod.x = new_x
        self.selected_pod.y = new_y
        self.selected_pod.width = new_width
        self.selected_pod.height = new_height

    def on_canvas_click(self, event):
        """Handle single click on canvas."""
        # Check if clicking on a resize handle of the selected pod
        if self.selected_pod:
            handle = self.get_resize_handle_at_position(event.x, event.y, self.selected_pod)
            if handle:
                # Start resizing
                self.resizing = True
                self.resize_handle = handle
                self.drag_start_x = event.x
                self.drag_start_y = event.y
                return

        pod = self.get_pod_at_position(event.x, event.y)

        # Deselect previous selection
        if self.selected_pod:
            self.selected_pod.selected = False

        if pod:
            pod.selected = True
            self.selected_pod = pod
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
        else:
            self.selected_pod = None

        self.render()

    def on_canvas_double_click(self, event):
        """Handle double click - enter pod if it has children."""
        pod = self.get_pod_at_position(event.x, event.y)

        if pod and pod.children:
            self.navigate_into(pod)

    def on_canvas_drag(self, event):
        """Handle dragging a pod or resizing."""
        if self.resizing and self.selected_pod and self.resize_handle:
            # Handle resizing
            self.resize_pod(event.x, event.y)
            self.render()
        elif self.dragging and self.selected_pod:
            # Calculate drag delta
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y

            # Move pod
            self.selected_pod.move_to(
                self.selected_pod.x + dx,
                self.selected_pod.y + dy
            )

            # Update drag start position
            self.drag_start_x = event.x
            self.drag_start_y = event.y

            self.render()

    def on_canvas_release(self, event):
        """Handle mouse button release."""
        self.dragging = False
        self.resizing = False
        self.resize_handle = None

    def on_canvas_motion(self, event):
        """Handle mouse motion for hover effects and cursor updates."""
        # Check if hovering over a resize handle
        if self.selected_pod:
            handle = self.get_resize_handle_at_position(event.x, event.y, self.selected_pod)
            if handle:
                # Set cursor based on resize direction
                cursor_map = {
                    "nw": "size_nw_se",
                    "n": "size_ns",
                    "ne": "size_ne_sw",
                    "e": "size_we",
                    "se": "size_nw_se",
                    "s": "size_ns",
                    "sw": "size_ne_sw",
                    "w": "size_we",
                }
                self.canvas.config(cursor=cursor_map.get(handle, "arrow"))
            else:
                self.canvas.config(cursor="arrow")
        else:
            self.canvas.config(cursor="arrow")

        pod = self.get_pod_at_position(event.x, event.y)

        # Update hover state
        changed = False
        for p in self.current_container.children:
            old_hover = p.hovered
            p.hovered = (p == pod)
            if old_hover != p.hovered:
                changed = True

        if changed:
            self.render()

    def navigate_into(self, pod: Pod):
        """Navigate into a pod, making it the current container."""
        self.navigation_history.append(self.current_container)
        self.current_container = pod
        self.back_button.config(state=tk.NORMAL)
        self.nav_label.config(text=f"Current: {pod.name}")
        self.selected_pod = None
        self.render()

    def navigate_back(self):
        """Navigate back to the previous container."""
        if self.navigation_history:
            self.current_container = self.navigation_history.pop()
            self.nav_label.config(text=f"Current: {self.current_container.name}")
            self.selected_pod = None

            if not self.navigation_history:
                self.back_button.config(state=tk.DISABLED)

            self.render()

    def add_new_pod(self):
        """Add a new pod to the current container."""
        # Find a good position (offset from center)
        import random
        x = random.randint(-200, 200)
        y = random.randint(-200, 200)

        new_pod = Pod(
            f"New Pod {len(self.current_container.children) + 1}",
            x=x, y=y,
            width=120, height=70,
            shape="oval"
        )

        self.current_container.add_child(new_pod)
        self.render()
