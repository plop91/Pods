"""Main application window with canvas and interaction handling."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict
import math
import json

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
        self.selected_relationship: Optional[Relationship] = None
        self.dragging = False
        self.panning = False
        self.resizing = False
        self.resize_handle = None  # Which handle is being dragged (e.g., "nw", "n", "ne", etc.)
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.resize_handle_size = 6  # Size of resize handles in pixels

        # Pan/zoom state
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.zoom_scale = 1.0  # 1.0 = 100%, 2.0 = 200%, 0.5 = 50%

        # Relationship creation state
        self.creating_relationship = False
        self.relationship_source_pod: Optional[Pod] = None
        self.relationship_source_direction: Optional[str] = None  # "n", "s", "e", "w"
        self.relationship_button_size = 10  # Size of plus buttons
        self.external_link_zone_width = 40  # Width of the external link zone on right side

        # Navigation history for back button
        self.navigation_history = []

        # Current file path for save/load
        self.current_file_path: Optional[str] = None

        # Setup UI
        self.setup_ui()

        # Create some example pods
        self.create_example_data()

        # Delay initial render until window is fully displayed and canvas has correct dimensions
        self.root.after(10, self.render)

    def setup_ui(self):
        """Setup the user interface."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.load_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Bind keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.new_project())
        self.root.bind("<Control-o>", lambda e: self.load_project())
        self.root.bind("<Control-s>", lambda e: self.save_project())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_project_as())

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
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # Right-click
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows/macOS
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux scroll down
        self.root.bind("<Escape>", self.on_escape_key)

    def create_example_data(self):
        """Create some example pods and relationships for demonstration."""
        # Create some example pods in the main container
        pod1 = Pod("Project Ideas", x=200, y=200, width=120, height=70, shape="oval")
        pod2 = Pod("Team Members", x=450, y=200, width=120, height=70, shape="oval")
        pod3 = Pod("Resources", x=200, y=400, width=120, height=70, shape="oval")
        pod4 = Pod("Timeline", x=450, y=400, width=120, height=70, shape="oval")

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

        # Calculate offset to center the view, including pan offset
        offset_x = canvas_width / 2 + self.pan_offset_x
        offset_y = canvas_height / 2 + self.pan_offset_y

        # Render relationships first (so they appear behind pods)
        for rel in self.relationships:
            self.render_relationship(rel, offset_x, offset_y)

        # Render pods
        for pod in self.current_container.children:
            self.render_pod(pod, offset_x, offset_y)

        # Render relationship creation indicator if in creation mode
        if self.creating_relationship and self.relationship_source_pod:
            # Draw instruction text (not affected by zoom)
            self.canvas.create_text(
                offset_x, 20,
                text="Click on a pod to create a relationship",
                fill="#27AE60",
                font=("Arial", 12, "bold"),
                tags=("relationship_creation_hint",)
            )

            # Draw external link zone on the right side
            self.render_external_link_zone(canvas_width, canvas_height)

    def render_pod(self, pod: Pod, offset_x: float, offset_y: float):
        """Render a single pod on the canvas."""
        x1, y1, x2, y2 = pod.get_bounds()

        # Apply zoom scaling
        x1 *= self.zoom_scale
        y1 *= self.zoom_scale
        x2 *= self.zoom_scale
        y2 *= self.zoom_scale

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
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                tags=("pod", pod.id)
            )
        else:  # oval
            self.canvas.create_oval(
                x1, y1, x2, y2,
                fill=fill_color,
                outline=outline_color,
                width=outline_width,
                tags=("pod", pod.id)
            )

        # Draw text and description if enabled
        if pod.has_description:
            # Calculate separator position (30% from top for name section)
            separator_y = y1 + (y2 - y1) * 0.3
            name_y = y1 + (separator_y - y1) / 2
            desc_y = separator_y + (y2 - separator_y) / 2

            # Draw name in top section
            self.canvas.create_text(
                pod.x * self.zoom_scale + offset_x, name_y,
                text=pod.name,
                fill=pod.text_color,
                font=("Arial", 10, "bold"),
                tags=("pod", pod.id)
            )

            # Draw separator line
            self.canvas.create_line(
                x1 + 5, separator_y, x2 - 5, separator_y,
                fill="#95A5A6",
                width=1,
                tags=("pod", pod.id)
            )

            # Draw description in bottom section (word-wrapped if needed)
            if pod.description:
                # Simple word wrapping
                max_width = (pod.width - 10) * self.zoom_scale
                wrapped_text = self.wrap_text(pod.description, max_width, ("Arial", 8))
                self.canvas.create_text(
                    pod.x * self.zoom_scale + offset_x, desc_y,
                    text=wrapped_text,
                    fill=pod.text_color,
                    font=("Arial", 8),
                    width=max_width,
                    tags=("pod", pod.id)
                )
        else:
            # Draw text normally
            self.canvas.create_text(
                pod.x * self.zoom_scale + offset_x, pod.y * self.zoom_scale + offset_y,
                text=pod.name,
                fill=pod.text_color,
                font=("Arial", 10),
                tags=("pod", pod.id)
            )

        # Draw indicator if pod has children
        if pod.children:
            self.canvas.create_text(
                pod.x * self.zoom_scale + offset_x, y2 - 5,
                text="⋯",
                fill="#7F8C8D",
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

    def render_external_link_zone(self, canvas_width: float, canvas_height: float):
        """Render the external link zone on the right side of the canvas."""
        zone_x = canvas_width - self.external_link_zone_width

        # Draw the zone background
        self.canvas.create_rectangle(
            zone_x, 0,
            canvas_width, canvas_height,
            fill="#E8F4F8",
            outline="#3498DB",
            width=2,
            tags=("external_link_zone",)
        )

        # Draw icon/text in the zone
        mid_y = canvas_height / 2
        self.canvas.create_text(
            zone_x + self.external_link_zone_width / 2, mid_y - 20,
            text="Link to",
            fill="#2C3E50",
            font=("Arial", 9, "bold"),
            tags=("external_link_zone",)
        )
        self.canvas.create_text(
            zone_x + self.external_link_zone_width / 2, mid_y,
            text="External",
            fill="#2C3E50",
            font=("Arial", 9, "bold"),
            tags=("external_link_zone",)
        )
        self.canvas.create_text(
            zone_x + self.external_link_zone_width / 2, mid_y + 20,
            text="Pod",
            fill="#2C3E50",
            font=("Arial", 9, "bold"),
            tags=("external_link_zone",)
        )

    def get_resize_handle_positions(self, pod: Pod, offset_x: float, offset_y: float):
        """Get the positions of all resize handles for a pod."""
        x1, y1, x2, y2 = pod.get_bounds()

        # Apply zoom scaling
        x1 *= self.zoom_scale
        y1 *= self.zoom_scale
        x2 *= self.zoom_scale
        y2 *= self.zoom_scale

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

    def get_relationship_button_positions(self, pod: Pod, offset_x: float, offset_y: float):
        """Get the positions of relationship creation buttons (cardinal directions only)."""
        x1, y1, x2, y2 = pod.get_bounds()

        # Apply zoom scaling
        x1 *= self.zoom_scale
        y1 *= self.zoom_scale
        x2 *= self.zoom_scale
        y2 *= self.zoom_scale

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

    def render_relationship_buttons(self, pod: Pod, offset_x: float, offset_y: float):
        """Render plus buttons for creating relationships at cardinal directions."""
        buttons = self.get_relationship_button_positions(pod, offset_x, offset_y)
        half_size = self.relationship_button_size / 2

        for direction, (bx, by) in buttons.items():
            # Draw circle background
            self.canvas.create_oval(
                bx - half_size, by - half_size,
                bx + half_size, by + half_size,
                fill="#27AE60",
                outline="#1E8449",
                width=1,
                tags=("rel_button", f"rel_btn_{direction}", pod.id)
            )
            # Draw plus sign
            self.canvas.create_text(
                bx, by,
                text="+",
                fill="white",
                font=("Arial", 10, "bold"),
                tags=("rel_button", f"rel_btn_{direction}", pod.id)
            )

    def render_relationship(self, rel: Relationship, offset_x: float, offset_y: float):
        """Render a relationship line between pods."""
        # Check if source is in current container
        source_in_container = (rel.source.parent == self.current_container or rel.source == self.current_container)
        target_in_container = (rel.target.parent == self.current_container or rel.target == self.current_container)

        # Only render if at least one end is in the current container
        if not source_in_container and not target_in_container:
            return

        x1, y1, x2, y2 = rel.get_endpoints()

        # Apply zoom scaling
        x1 *= self.zoom_scale
        y1 *= self.zoom_scale
        x2 *= self.zoom_scale
        y2 *= self.zoom_scale

        # Apply offset
        x1 += offset_x
        y1 += offset_y
        x2 += offset_x
        y2 += offset_y

        # If target is external, draw line to edge of canvas
        if not target_in_container:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Calculate direction vector
            dx = x2 - x1
            dy = y2 - y1

            # Find intersection with canvas edge
            # Check right edge first (most common for external links)
            if dx > 0:
                t = (canvas_width - self.external_link_zone_width - x1) / dx if dx != 0 else float('inf')
                if 0 < t < 1:
                    x2 = canvas_width - self.external_link_zone_width
                    y2 = y1 + t * dy

        # If source is external (less common but possible)
        if not source_in_container:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Calculate direction vector
            dx = x1 - x2
            dy = y1 - y2

            # Find intersection with canvas edge
            if dx > 0:
                t = (canvas_width - self.external_link_zone_width - x2) / dx if dx != 0 else float('inf')
                if 0 < t < 1:
                    x1 = canvas_width - self.external_link_zone_width
                    y1 = y2 + t * dy

        # Draw line
        color = "#3498DB" if rel.selected else rel.color
        width = rel.line_width + 1 if rel.selected else rel.line_width
        self.canvas.create_line(
            x1, y1, x2, y2,
            fill=color,
            width=width,
            arrow=tk.LAST if rel.arrow else None,
            tags=("relationship", rel.id)
        )

        # Calculate midpoint for labels
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        # Draw label if present
        if rel.label:
            self.canvas.create_text(
                mid_x, mid_y - 10,
                text=rel.label,
                fill="#2C3E50" if rel.selected else "#7F8C8D",
                font=("Arial", 8, "bold" if rel.selected else "normal"),
                tags=("relationship", rel.id)
            )

        # Draw description if selected and present
        if rel.selected and rel.description:
            # Draw description box below the label
            desc_y_offset = 10 if rel.label else 5

            # Create a semi-transparent background for the description
            desc_lines = rel.description.split('\n')
            max_line_length = max(len(line) for line in desc_lines) if desc_lines else 0
            box_width = min(max_line_length * 6, 200)  # Approximate width
            box_height = len(desc_lines) * 12 + 10

            # Draw background box
            self.canvas.create_rectangle(
                mid_x - box_width / 2, mid_y + desc_y_offset,
                mid_x + box_width / 2, mid_y + desc_y_offset + box_height,
                fill="#ECF0F1",
                outline="#3498DB",
                width=1,
                tags=("relationship", rel.id)
            )

            # Draw description text
            self.canvas.create_text(
                mid_x, mid_y + desc_y_offset + box_height / 2,
                text=rel.description,
                fill="#2C3E50",
                font=("Arial", 8),
                width=box_width - 10,
                tags=("relationship", rel.id)
            )

    def get_pod_at_position(self, x: float, y: float) -> Optional[Pod]:
        """Find the pod at the given canvas position."""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.pan_offset_x
        offset_y = canvas_height / 2 + self.pan_offset_y

        # Convert to world coordinates (accounting for zoom)
        world_x = (x - offset_x) / self.zoom_scale
        world_y = (y - offset_y) / self.zoom_scale

        # Check all pods (in reverse order to check top ones first)
        for pod in reversed(self.current_container.children):
            if pod.contains_point(world_x, world_y):
                return pod

        return None

    def get_relationship_at_position(self, x: float, y: float) -> Optional[Relationship]:
        """Find the relationship at the given canvas position."""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.pan_offset_x
        offset_y = canvas_height / 2 + self.pan_offset_y

        # Convert to world coordinates (accounting for zoom)
        world_x = (x - offset_x) / self.zoom_scale
        world_y = (y - offset_y) / self.zoom_scale

        # Check all relationships
        for rel in self.relationships:
            # Only check relationships in the current container
            if (rel.source.parent != self.current_container and rel.source != self.current_container):
                continue
            if (rel.target.parent != self.current_container and rel.target != self.current_container):
                continue

            x1, y1, x2, y2 = rel.get_endpoints()

            # Calculate distance from point to line segment
            distance = self.point_to_line_distance(world_x, world_y, x1, y1, x2, y2)

            # If within 5 pixels of the line, consider it a hit (scale threshold by zoom)
            if distance < 5 / self.zoom_scale:
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

    def get_resize_handle_at_position(self, x: float, y: float, pod: Pod) -> Optional[str]:
        """Check if position is over a resize handle. Returns handle direction or None."""
        if not pod.selected:
            return None

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.pan_offset_x
        offset_y = canvas_height / 2 + self.pan_offset_y

        handles = self.get_resize_handle_positions(pod, offset_x, offset_y)
        half_size = self.resize_handle_size / 2

        # Check each handle
        for direction, (hx, hy) in handles.items():
            if (hx - half_size <= x <= hx + half_size and
                hy - half_size <= y <= hy + half_size):
                return direction

        return None

    def get_relationship_button_at_position(self, x: float, y: float, pod: Pod) -> Optional[str]:
        """Check if position is over a relationship button. Returns button direction or None."""
        if not pod.selected:
            return None

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.pan_offset_x
        offset_y = canvas_height / 2 + self.pan_offset_y

        buttons = self.get_relationship_button_positions(pod, offset_x, offset_y)
        half_size = self.relationship_button_size / 2

        # Check each button
        for direction, (bx, by) in buttons.items():
            # Use circular hit detection
            distance = math.sqrt((x - bx) ** 2 + (y - by) ** 2)
            if distance <= half_size:
                return direction

        return None

    def resize_pod(self, mouse_x: float, mouse_y: float):
        """Resize the selected pod based on the resize handle being dragged."""
        if not self.selected_pod or not self.resize_handle:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.pan_offset_x
        offset_y = canvas_height / 2 + self.pan_offset_y

        # Convert mouse position to world coordinates (accounting for zoom)
        world_x = (mouse_x - offset_x) / self.zoom_scale
        world_y = (mouse_y - offset_y) / self.zoom_scale

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
        # If in relationship creation mode, complete the relationship
        if self.creating_relationship:
            # Check if clicking in external link zone
            canvas_width = self.canvas.winfo_width()
            zone_x = canvas_width - self.external_link_zone_width
            if event.x >= zone_x:
                # Show external pod selector
                self.show_external_pod_selector()
                return

            target_pod = self.get_pod_at_position(event.x, event.y)
            if target_pod and target_pod != self.relationship_source_pod:
                # Create the relationship
                new_rel = Relationship(
                    self.relationship_source_pod,
                    target_pod,
                    label="",
                    relationship_type="default"
                )
                self.relationships.append(new_rel)

            # Exit relationship creation mode
            self.creating_relationship = False
            self.relationship_source_pod = None
            self.relationship_source_direction = None
            self.canvas.config(cursor="arrow")
            self.render()
            return

        # Check if clicking on a relationship button of the selected pod
        if self.selected_pod:
            rel_button = self.get_relationship_button_at_position(event.x, event.y, self.selected_pod)
            if rel_button:
                # Start relationship creation mode
                self.creating_relationship = True
                self.relationship_source_pod = self.selected_pod
                self.relationship_source_direction = rel_button
                self.canvas.config(cursor="crosshair")
                return

            # Check if clicking on a resize handle of the selected pod
            handle = self.get_resize_handle_at_position(event.x, event.y, self.selected_pod)
            if handle:
                # Start resizing
                self.resizing = True
                self.resize_handle = handle
                self.drag_start_x = event.x
                self.drag_start_y = event.y
                return

        pod = self.get_pod_at_position(event.x, event.y)

        # Deselect previous pod selection
        if self.selected_pod:
            self.selected_pod.selected = False

        # Deselect previous relationship selection
        if self.selected_relationship:
            self.selected_relationship.selected = False
            self.selected_relationship = None

        if pod:
            pod.selected = True
            self.selected_pod = pod
            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
        else:
            # Check if clicking on a relationship
            relationship = self.get_relationship_at_position(event.x, event.y)
            if relationship:
                relationship.selected = True
                self.selected_relationship = relationship
                self.selected_pod = None
            else:
                # Clicking on empty space - start panning
                self.selected_pod = None
                self.panning = True
                self.drag_start_x = event.x
                self.drag_start_y = event.y
                self.canvas.config(cursor="fleur")  # Hand/move cursor

        self.render()

    def on_canvas_double_click(self, event):
        """Handle double click - enter pod to view/create children."""
        pod = self.get_pod_at_position(event.x, event.y)

        if pod:
            self.navigate_into(pod)

    def on_canvas_drag(self, event):
        """Handle dragging a pod, panning, or resizing."""
        # Don't allow dragging when in relationship creation mode
        if self.creating_relationship:
            return

        if self.resizing and self.selected_pod and self.resize_handle:
            # Handle resizing
            self.resize_pod(event.x, event.y)
            self.render()
        elif self.panning:
            # Handle panning
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y

            # Update pan offset
            self.pan_offset_x += dx
            self.pan_offset_y += dy

            # Update drag start position
            self.drag_start_x = event.x
            self.drag_start_y = event.y

            self.render()
        elif self.dragging and self.selected_pod:
            # Calculate drag delta (account for zoom)
            dx = (event.x - self.drag_start_x) / self.zoom_scale
            dy = (event.y - self.drag_start_y) / self.zoom_scale

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
        self.panning = False
        self.resizing = False
        self.resize_handle = None

        # Reset cursor if we were panning
        if not self.creating_relationship:
            self.canvas.config(cursor="arrow")

    def on_canvas_motion(self, event):
        """Handle mouse motion for hover effects and cursor updates."""
        # Don't change cursor during relationship creation mode (it's set to crosshair)
        if self.creating_relationship:
            # Highlight pods when hovering in relationship creation mode
            pod = self.get_pod_at_position(event.x, event.y)
            changed = False
            for p in self.current_container.children:
                old_hover = p.hovered
                # Hover only if it's a different pod from the source
                p.hovered = (p == pod and p != self.relationship_source_pod)
                if old_hover != p.hovered:
                    changed = True
            if changed:
                self.render()
            return

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

    def on_escape_key(self, event):
        """Handle escape key press - cancel relationship creation."""
        if self.creating_relationship:
            self.creating_relationship = False
            self.relationship_source_pod = None
            self.relationship_source_direction = None
            self.canvas.config(cursor="arrow")
            self.render()

    def on_mouse_wheel(self, event):
        """Handle mouse wheel zoom."""
        # Determine zoom direction
        if event.num == 5 or event.delta < 0:  # Scroll down (zoom out)
            zoom_factor = 0.9
        elif event.num == 4 or event.delta > 0:  # Scroll up (zoom in)
            zoom_factor = 1.1
        else:
            return

        # Apply zoom limits
        new_zoom = self.zoom_scale * zoom_factor
        if 0.1 <= new_zoom <= 5.0:  # Limit zoom between 10% and 500%
            # Get mouse position relative to canvas
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            # Calculate world coordinates at mouse position before zoom
            mouse_world_x = (event.x - canvas_width / 2 - self.pan_offset_x) / self.zoom_scale
            mouse_world_y = (event.y - canvas_height / 2 - self.pan_offset_y) / self.zoom_scale

            # Apply zoom
            self.zoom_scale = new_zoom

            # Calculate world coordinates at mouse position after zoom
            new_mouse_world_x = (event.x - canvas_width / 2 - self.pan_offset_x) / self.zoom_scale
            new_mouse_world_y = (event.y - canvas_height / 2 - self.pan_offset_y) / self.zoom_scale

            # Adjust pan offset to keep mouse position fixed
            self.pan_offset_x += (new_mouse_world_x - mouse_world_x) * self.zoom_scale
            self.pan_offset_y += (new_mouse_world_y - mouse_world_y) * self.zoom_scale

            self.render()

    def on_canvas_right_click(self, event):
        """Handle right-click on canvas - show context menu for pods or relationships."""
        pod = self.get_pod_at_position(event.x, event.y)

        if pod:
            # Create context menu for pods
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Edit Name", command=lambda: self.edit_pod_name(pod))
            menu.add_separator()

            # Add checkbox for description
            desc_var = tk.BooleanVar(value=pod.has_description)
            menu.add_checkbutton(
                label="Show Description",
                variable=desc_var,
                command=lambda: self.toggle_pod_description(pod, desc_var.get())
            )

            if pod.has_description:
                menu.add_command(label="Edit Description", command=lambda: self.edit_pod_description(pod))

            # Display menu at cursor position
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        else:
            # Check if right-clicking on a relationship
            relationship = self.get_relationship_at_position(event.x, event.y)
            if relationship:
                # Create context menu for relationships
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="Edit Label", command=lambda: self.edit_relationship_label(relationship))
                menu.add_command(label="Edit Description", command=lambda: self.edit_relationship_description(relationship))

                # Display menu at cursor position
                try:
                    menu.tk_popup(event.x_root, event.y_root)
                finally:
                    menu.grab_release()

    def edit_pod_name(self, pod: Pod):
        """Open dialog to edit pod name."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Pod Name")
        dialog.geometry("400x120")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Name entry
        tk.Label(dialog, text="Pod Name:").pack(pady=(10, 5))
        name_entry = tk.Entry(dialog, width=40)
        name_entry.insert(0, pod.name)
        name_entry.pack(pady=5)
        name_entry.focus()
        name_entry.select_range(0, tk.END)

        def save_name():
            pod.name = name_entry.get()
            dialog.destroy()
            self.render()

        def cancel():
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Save", command=save_name, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel, width=10).pack(side=tk.LEFT, padx=5)

        # Bind Enter key to save
        name_entry.bind("<Return>", lambda e: save_name())
        dialog.bind("<Escape>", lambda e: cancel())

    def edit_pod_description(self, pod: Pod):
        """Open dialog to edit pod description."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Pod Description")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Description text area
        tk.Label(dialog, text="Description:").pack(pady=(10, 5))
        text_frame = tk.Frame(dialog)
        text_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        desc_text = tk.Text(text_frame, width=60, height=10, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        desc_text.insert("1.0", pod.description)
        desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=desc_text.yview)
        desc_text.focus()

        def save_description():
            pod.description = desc_text.get("1.0", tk.END).strip()
            dialog.destroy()
            self.render()

        def cancel():
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Save", command=save_description, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel, width=10).pack(side=tk.LEFT, padx=5)

        dialog.bind("<Escape>", lambda e: cancel())

    def toggle_pod_description(self, pod: Pod, enabled: bool):
        """Toggle description visibility for a pod."""
        pod.has_description = enabled
        if enabled and not pod.description:
            # If enabling description for the first time, open edit dialog
            self.edit_pod_description(pod)
        else:
            self.render()

    def edit_relationship_label(self, relationship: Relationship):
        """Open dialog to edit relationship label."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Relationship Label")
        dialog.geometry("400x120")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Label entry
        tk.Label(dialog, text="Relationship Label:").pack(pady=(10, 5))
        label_entry = tk.Entry(dialog, width=40)
        label_entry.insert(0, relationship.label)
        label_entry.pack(pady=5)
        label_entry.focus()
        label_entry.select_range(0, tk.END)

        def save_label():
            relationship.label = label_entry.get()
            dialog.destroy()
            self.render()

        def cancel():
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Save", command=save_label, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel, width=10).pack(side=tk.LEFT, padx=5)

        # Bind Enter key to save
        label_entry.bind("<Return>", lambda e: save_label())
        dialog.bind("<Escape>", lambda e: cancel())

    def edit_relationship_description(self, relationship: Relationship):
        """Open dialog to edit relationship description."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Relationship Description")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Description text area
        tk.Label(dialog, text="Description (visible when relationship is selected):").pack(pady=(10, 5))
        text_frame = tk.Frame(dialog)
        text_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        desc_text = tk.Text(text_frame, width=60, height=10, yscrollcommand=scrollbar.set, wrap=tk.WORD)
        desc_text.insert("1.0", relationship.description)
        desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=desc_text.yview)
        desc_text.focus()

        def save_description():
            relationship.description = desc_text.get("1.0", tk.END).strip()
            dialog.destroy()
            self.render()

        def cancel():
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Save", command=save_description, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel, width=10).pack(side=tk.LEFT, padx=5)

        dialog.bind("<Escape>", lambda e: cancel())

    def show_external_pod_selector(self):
        """Show dialog to select an external pod for creating a relationship."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select External Pod")
        dialog.geometry("400x500")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Select a pod to link to:", font=("Arial", 10, "bold")).pack(pady=(10, 5))

        # Create a frame with scrollbar for the pod list
        list_frame = tk.Frame(dialog)
        list_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create listbox
        pod_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        pod_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=pod_listbox.yview)

        # Collect all pods with their paths
        pod_list = []
        def collect_pods(pod: Pod, path: str = ""):
            current_path = f"{path}/{pod.name}" if path else pod.name
            if pod != self.main_pod:  # Don't include the main pod itself
                pod_list.append((pod, current_path))
            for child in pod.children:
                collect_pods(child, current_path)

        collect_pods(self.main_pod)

        # Sort by path for better organization
        pod_list.sort(key=lambda x: x[1])

        # Populate listbox
        for pod, path in pod_list:
            # Don't allow linking to self
            if pod != self.relationship_source_pod:
                display_text = path
                pod_listbox.insert(tk.END, display_text)

        # Store pod references
        pod_objects = [pod for pod, path in pod_list if pod != self.relationship_source_pod]

        def on_select():
            selection = pod_listbox.curselection()
            if selection:
                idx = selection[0]
                target_pod = pod_objects[idx]

                # Create the relationship
                new_rel = Relationship(
                    self.relationship_source_pod,
                    target_pod,
                    label="",
                    relationship_type="default"
                )
                self.relationships.append(new_rel)

                # Exit relationship creation mode
                self.creating_relationship = False
                self.relationship_source_pod = None
                self.relationship_source_direction = None
                self.canvas.config(cursor="arrow")

                dialog.destroy()
                self.render()

        def cancel():
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Link", command=on_select, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=cancel, width=10).pack(side=tk.LEFT, padx=5)

        # Double-click to select
        pod_listbox.bind("<Double-Button-1>", lambda e: on_select())
        dialog.bind("<Escape>", lambda e: cancel())

    def navigate_into(self, pod: Pod):
        """Navigate into a pod, making it the current container."""
        self.navigation_history.append(self.current_container)
        self.current_container = pod
        self.back_button.config(state=tk.NORMAL)
        self.nav_label.config(text=f"Current: {pod.name}")
        self.selected_pod = None

        # Reset pan offset and zoom when entering a new container
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.zoom_scale = 1.0

        self.render()

    def navigate_back(self):
        """Navigate back to the previous container."""
        if self.navigation_history:
            self.current_container = self.navigation_history.pop()
            self.nav_label.config(text=f"Current: {self.current_container.name}")
            self.selected_pod = None

            # Reset pan offset and zoom when going back
            self.pan_offset_x = 0
            self.pan_offset_y = 0
            self.zoom_scale = 1.0

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

    def build_pod_lookup(self, pod: Pod, lookup: Dict[str, Pod]):
        """Recursively build a lookup dictionary of pod ID -> pod object."""
        lookup[pod.id] = pod
        for child in pod.children:
            self.build_pod_lookup(child, lookup)

    def new_project(self):
        """Create a new empty project."""
        # Confirm if there are unsaved changes
        if self.main_pod.children or self.relationships:
            response = messagebox.askyesno(
                "New Project",
                "Are you sure you want to create a new project? Any unsaved changes will be lost."
            )
            if not response:
                return

        # Reset to empty project
        self.main_pod = Pod("Main", x=0, y=0, width=0, height=0)
        self.current_container = self.main_pod
        self.relationships = []
        self.navigation_history = []
        self.selected_pod = None
        self.selected_relationship = None
        self.current_file_path = None
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.zoom_scale = 1.0

        # Update UI
        self.nav_label.config(text="Current: Main")
        self.back_button.config(state=tk.DISABLED)
        self.root.title("Pods - Visual Idea Organization")

        self.render()

    def save_project_as(self):
        """Save the project to a new file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Pods Project", "*.json"), ("All Files", "*.*")],
            title="Save Project As"
        )

        if file_path:
            self.current_file_path = file_path
            self._save_to_file(file_path)

    def save_project(self):
        """Save the project to the current file, or prompt for location if new."""
        if self.current_file_path:
            self._save_to_file(self.current_file_path)
        else:
            self.save_project_as()

    def _save_to_file(self, file_path: str):
        """Internal method to save project to a specific file."""
        try:
            # Build the project data structure
            project_data = {
                "version": "1.0",
                "main_pod": self.main_pod.to_dict(),
                "relationships": [rel.to_dict() for rel in self.relationships]
            }

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2)

            # Update window title
            import os
            filename = os.path.basename(file_path)
            self.root.title(f"Pods - {filename}")

            messagebox.showinfo("Save Successful", f"Project saved to {file_path}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save project:\n{str(e)}")

    def load_project(self):
        """Load a project from a file."""
        # Confirm if there are unsaved changes
        if self.main_pod.children or self.relationships:
            response = messagebox.askyesno(
                "Load Project",
                "Are you sure you want to load a project? Any unsaved changes will be lost."
            )
            if not response:
                return

        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("Pods Project", "*.json"), ("All Files", "*.*")],
            title="Open Project"
        )

        if file_path:
            self._load_from_file(file_path)

    def _load_from_file(self, file_path: str):
        """Internal method to load project from a specific file."""
        try:
            # Read from file
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # Deserialize main pod
            self.main_pod = Pod.from_dict(project_data["main_pod"])

            # Build pod lookup dictionary
            pod_lookup: Dict[str, Pod] = {}
            self.build_pod_lookup(self.main_pod, pod_lookup)

            # Deserialize relationships
            self.relationships = [
                Relationship.from_dict(rel_data, pod_lookup)
                for rel_data in project_data.get("relationships", [])
            ]

            # Reset state
            self.current_container = self.main_pod
            self.navigation_history = []
            self.selected_pod = None
            self.selected_relationship = None
            self.current_file_path = file_path
            self.pan_offset_x = 0
            self.pan_offset_y = 0
            self.zoom_scale = 1.0

            # Update UI
            self.nav_label.config(text="Current: Main")
            self.back_button.config(state=tk.DISABLED)

            # Update window title
            import os
            filename = os.path.basename(file_path)
            self.root.title(f"Pods - {filename}")

            self.render()

            messagebox.showinfo("Load Successful", f"Project loaded from {file_path}")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load project:\n{str(e)}")
