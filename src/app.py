"""Main application window with canvas and interaction handling."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict
import math
import json
import uuid

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
        self.selected_pods: List[Pod] = []  # For multi-select
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

        # Undo/Redo stacks
        self.undo_stack: List[dict] = []
        self.redo_stack: List[dict] = []
        self.max_undo_levels = 50

        # Clipboard for copy/paste
        self.clipboard: Optional[dict] = None

        # Grid and snap settings
        self.show_grid = False
        self.snap_to_grid = False
        self.grid_size = 20  # Grid spacing in pixels

        # Search state
        self.search_dialog: Optional[tk.Toplevel] = None
        self.search_results: List[tuple] = []  # List of (pod, path_string) tuples
        self.search_result_index = 0

        # Setup UI
        self.setup_ui()

        # Create some example pods
        self.create_example_data()

        # Delay initial render until window is fully displayed and canvas has correct dimensions
        self.root.after(100, self.initial_render)

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

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy Pod", command=self.copy_pod, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste Pod", command=self.paste_pod, accelerator="Ctrl+V")

        # Bind keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.new_project())
        self.root.bind("<Control-o>", lambda e: self.load_project())
        self.root.bind("<Control-s>", lambda e: self.save_project())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_project_as())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-c>", lambda e: self.copy_pod())
        self.root.bind("<Control-v>", lambda e: self.paste_pod())
        self.root.bind("<Delete>", lambda e: self.delete_selected())
        self.root.bind("<BackSpace>", lambda e: self.delete_selected())
        self.root.bind("<Control-f>", lambda e: self.open_search_dialog())

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

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Alignment tools
        ttk.Label(toolbar, text="Align:").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(toolbar, text="Left", width=5, command=lambda: self.align_pods("left")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Center", width=6, command=lambda: self.align_pods("center")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Right", width=5, command=lambda: self.align_pods("right")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Top", width=4, command=lambda: self.align_pods("top")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Middle", width=6, command=lambda: self.align_pods("middle")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Bottom", width=6, command=lambda: self.align_pods("bottom")).pack(side=tk.LEFT, padx=1)

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Grid and snap checkboxes
        self.grid_var = tk.BooleanVar(value=False)
        self.snap_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="Show Grid", variable=self.grid_var, command=self.toggle_grid).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(toolbar, text="Snap to Grid", variable=self.snap_var, command=self.toggle_snap).pack(side=tk.LEFT, padx=2)

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

    def initial_render(self):
        """Perform initial render after ensuring canvas has correct dimensions."""
        # Force the window to update and calculate proper sizes
        self.root.update_idletasks()

        # Check if canvas has reasonable dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # If canvas is still too small, wait a bit longer
        if canvas_width < 100 or canvas_height < 100:
            self.root.after(50, self.initial_render)
            return

        # Now render with proper dimensions
        self.render()

    def render(self):
        """Render the current view."""
        self.canvas.delete("all")

        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate offset to center the view, including pan offset
        offset_x = canvas_width / 2 + self.pan_offset_x
        offset_y = canvas_height / 2 + self.pan_offset_y

        # Render grid if enabled
        if self.show_grid:
            self.render_grid(canvas_width, canvas_height, offset_x, offset_y)

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
        # Don't render relationships where either end is the current container itself
        # (we're inside that container, so we don't want to see its connections to the outside)
        if rel.source == self.current_container or rel.target == self.current_container:
            return

        # Check if source is a child of the current container
        source_in_container = rel.source.parent == self.current_container
        # Check if target is a child of the current container
        target_in_container = rel.target.parent == self.current_container

        # Only render if at least one end is a child of the current container
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
            # Skip relationships where either end is the current container itself
            if rel.source == self.current_container or rel.target == self.current_container:
                continue

            # Only check relationships where at least one end is a child of the current container
            source_in_container = rel.source.parent == self.current_container
            target_in_container = rel.target.parent == self.current_container

            if not source_in_container and not target_in_container:
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
                # Save state for undo
                self.save_state()

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
                self.render()  # Re-render to show external link zone and hint
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

        # Check if Ctrl is held for multi-select
        ctrl_held = (event.state & 0x4) != 0

        if pod:
            if ctrl_held:
                # Multi-select mode
                if pod in self.selected_pods:
                    # Deselect this pod
                    pod.selected = False
                    self.selected_pods.remove(pod)
                    self.selected_pod = self.selected_pods[0] if self.selected_pods else None
                else:
                    # Add to selection
                    pod.selected = True
                    self.selected_pods.append(pod)
                    self.selected_pod = pod
            else:
                # Single select mode - clear all previous selections
                for p in self.selected_pods:
                    p.selected = False
                self.selected_pods.clear()

                # Deselect previous relationship selection
                if self.selected_relationship:
                    self.selected_relationship.selected = False
                    self.selected_relationship = None

                pod.selected = True
                self.selected_pod = pod
                self.selected_pods = [pod]

            self.dragging = True
            self.drag_start_x = event.x
            self.drag_start_y = event.y
        else:
            # Check if clicking on a relationship
            relationship = self.get_relationship_at_position(event.x, event.y)
            if relationship:
                # Clear pod selections
                for p in self.selected_pods:
                    p.selected = False
                self.selected_pods.clear()
                self.selected_pod = None

                relationship.selected = True
                self.selected_relationship = relationship
            else:
                # Clicking on empty space
                if not ctrl_held:
                    # Clear all selections and start panning
                    for p in self.selected_pods:
                        p.selected = False
                    self.selected_pods.clear()
                    self.selected_pod = None

                    if self.selected_relationship:
                        self.selected_relationship.selected = False
                        self.selected_relationship = None

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
        elif self.dragging and self.selected_pods:
            # Calculate drag delta (account for zoom)
            dx = (event.x - self.drag_start_x) / self.zoom_scale
            dy = (event.y - self.drag_start_y) / self.zoom_scale

            # Move all selected pods
            for pod in self.selected_pods:
                new_x = pod.x + dx
                new_y = pod.y + dy

                # Apply snap to grid if enabled
                if self.snap_to_grid:
                    new_x = self.snap_to_grid_coord(new_x)
                    new_y = self.snap_to_grid_coord(new_y)

                pod.move_to(new_x, new_y)

            # Update drag start position
            self.drag_start_x = event.x
            self.drag_start_y = event.y

            self.render()

    def on_canvas_release(self, event):
        """Handle mouse button release."""
        # Save state if we made changes (dragging or resizing)
        if (self.dragging or self.resizing) and self.selected_pod:
            self.save_state()

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

            menu.add_separator()
            menu.add_command(label="Delete Pod", command=lambda: self.delete_pod(pod))

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
                menu.add_separator()
                menu.add_command(label="Delete Relationship", command=lambda: self.delete_relationship(relationship))

                # Display menu at cursor position
                try:
                    menu.tk_popup(event.x_root, event.y_root)
                finally:
                    menu.grab_release()
            else:
                # Right-clicked on empty space
                menu = tk.Menu(self.root, tearoff=0)
                menu.add_command(label="Add Oval Pod", command=lambda: self.add_pod_at_position(event.x, event.y, "oval"))
                menu.add_command(label="Add Rectangle Pod", command=lambda: self.add_pod_at_position(event.x, event.y, "rectangle"))
                menu.add_separator()
                menu.add_command(label="Reset View (Pan & Zoom)", command=self.reset_view)

                # Add delete options if something is selected
                if self.selected_pod:
                    menu.add_separator()
                    menu.add_command(label=f"Delete '{self.selected_pod.name}'", command=lambda: self.delete_pod(self.selected_pod))
                elif self.selected_relationship:
                    menu.add_separator()
                    menu.add_command(label="Delete Selected Relationship", command=lambda: self.delete_relationship(self.selected_relationship))

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
            # Save state for undo
            self.save_state()
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
            # Save state for undo
            self.save_state()
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
        # Save state for undo
        self.save_state()
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
            # Save state for undo
            self.save_state()
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
            # Save state for undo
            self.save_state()
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

                # Save state for undo
                self.save_state()

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
        self.selected_pods.clear()

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
            self.selected_pods.clear()

            # Reset pan offset and zoom when going back
            self.pan_offset_x = 0
            self.pan_offset_y = 0
            self.zoom_scale = 1.0

            if not self.navigation_history:
                self.back_button.config(state=tk.DISABLED)

            self.render()

    def add_new_pod(self):
        """Add a new pod to the current container."""
        # Save state for undo
        self.save_state()

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

    def add_pod_at_position(self, canvas_x: float, canvas_y: float, shape: str = "oval"):
        """Add a new pod at a specific canvas position."""
        # Save state for undo
        self.save_state()

        # Convert canvas coordinates to world coordinates
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.pan_offset_x
        offset_y = canvas_height / 2 + self.pan_offset_y

        world_x = (canvas_x - offset_x) / self.zoom_scale
        world_y = (canvas_y - offset_y) / self.zoom_scale

        # Apply snap to grid if enabled
        if self.snap_to_grid:
            world_x = self.snap_to_grid_coord(world_x)
            world_y = self.snap_to_grid_coord(world_y)

        # Create new pod at the clicked position
        new_pod = Pod(
            f"New Pod {len(self.current_container.children) + 1}",
            x=world_x, y=world_y,
            width=120, height=70,
            shape=shape
        )

        self.current_container.add_child(new_pod)
        self.render()

    def reset_view(self):
        """Reset pan offset and zoom to default values."""
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.zoom_scale = 1.0
        self.render()

    def delete_pod(self, pod: Pod):
        """Delete a pod and all its relationships."""
        # Confirm deletion
        response = messagebox.askyesno(
            "Delete Pod",
            f"Are you sure you want to delete '{pod.name}'?\nThis will also delete all relationships connected to it."
        )
        if not response:
            return

        # Save state for undo
        self.save_state()

        # Remove all relationships connected to this pod
        self.relationships = [
            rel for rel in self.relationships
            if rel.source != pod and rel.target != pod
        ]

        # Remove pod from parent
        if pod.parent:
            pod.parent.remove_child(pod)

        # Deselect if this was the selected pod
        if self.selected_pod == pod:
            self.selected_pod = None

        self.render()

    def delete_relationship(self, relationship: Relationship):
        """Delete a relationship."""
        # Confirm deletion
        label_text = relationship.label if relationship.label else "this relationship"
        response = messagebox.askyesno(
            "Delete Relationship",
            f"Are you sure you want to delete {label_text}?"
        )
        if not response:
            return

        # Save state for undo
        self.save_state()

        # Remove relationship
        if relationship in self.relationships:
            self.relationships.remove(relationship)

        # Deselect if this was the selected relationship
        if self.selected_relationship == relationship:
            self.selected_relationship = None

        self.render()

    def delete_selected(self):
        """Delete the currently selected pod(s) or relationship using Delete key."""
        if self.selected_pods:
            # Delete all selected pods
            if len(self.selected_pods) == 1:
                self.delete_pod(self.selected_pods[0])
            else:
                # Confirm deletion of multiple pods
                response = messagebox.askyesno(
                    "Delete Pods",
                    f"Are you sure you want to delete {len(self.selected_pods)} pods?\nThis will also delete all relationships connected to them."
                )
                if not response:
                    return

                # Save state for undo
                self.save_state()

                # Delete all selected pods
                for pod in list(self.selected_pods):  # Use list() to avoid modifying during iteration
                    # Remove all relationships connected to this pod
                    self.relationships = [
                        rel for rel in self.relationships
                        if rel.source != pod and rel.target != pod
                    ]

                    # Remove pod from parent
                    if pod.parent:
                        pod.parent.remove_child(pod)

                    pod.selected = False

                # Clear selections
                self.selected_pods.clear()
                self.selected_pod = None
                self.render()
        elif self.selected_relationship:
            self.delete_relationship(self.selected_relationship)

    def save_state(self):
        """Save the current state for undo/redo functionality."""
        # Create a snapshot of the current state
        state = {
            "main_pod": self.main_pod.to_dict(),
            "relationships": [rel.to_dict() for rel in self.relationships],
            "current_container_id": self.current_container.id,
            "navigation_history_ids": [pod.id for pod in self.navigation_history]
        }

        # Add to undo stack
        self.undo_stack.append(state)

        # Limit stack size
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)

        # Clear redo stack when a new action is performed
        self.redo_stack.clear()

    def restore_state(self, state: dict):
        """Restore a saved state."""
        # Deserialize main pod
        self.main_pod = Pod.from_dict(state["main_pod"])

        # Build pod lookup dictionary
        pod_lookup: Dict[str, Pod] = {}
        self.build_pod_lookup(self.main_pod, pod_lookup)

        # Deserialize relationships
        self.relationships = [
            Relationship.from_dict(rel_data, pod_lookup)
            for rel_data in state.get("relationships", [])
        ]

        # Restore current container
        container_id = state.get("current_container_id")
        self.current_container = pod_lookup.get(container_id, self.main_pod)

        # Restore navigation history
        self.navigation_history = [
            pod_lookup[pod_id]
            for pod_id in state.get("navigation_history_ids", [])
            if pod_id in pod_lookup
        ]

        # Update UI
        self.nav_label.config(text=f"Current: {self.current_container.name}")
        self.back_button.config(state=tk.NORMAL if self.navigation_history else tk.DISABLED)
        self.selected_pod = None
        self.selected_pods.clear()
        self.selected_relationship = None

        self.render()

    def undo(self):
        """Undo the last action."""
        if not self.undo_stack:
            return

        # Save current state to redo stack before undoing
        current_state = {
            "main_pod": self.main_pod.to_dict(),
            "relationships": [rel.to_dict() for rel in self.relationships],
            "current_container_id": self.current_container.id,
            "navigation_history_ids": [pod.id for pod in self.navigation_history]
        }
        self.redo_stack.append(current_state)

        # Restore previous state
        previous_state = self.undo_stack.pop()
        self.restore_state(previous_state)

    def redo(self):
        """Redo the last undone action."""
        if not self.redo_stack:
            return

        # Save current state to undo stack before redoing
        current_state = {
            "main_pod": self.main_pod.to_dict(),
            "relationships": [rel.to_dict() for rel in self.relationships],
            "current_container_id": self.current_container.id,
            "navigation_history_ids": [pod.id for pod in self.navigation_history]
        }
        self.undo_stack.append(current_state)

        # Restore next state
        next_state = self.redo_stack.pop()
        self.restore_state(next_state)

    def copy_pod(self):
        """Copy the selected pod(s) to clipboard."""
        if not self.selected_pods:
            return

        # Save pod data to clipboard (support multiple pods)
        if len(self.selected_pods) == 1:
            self.clipboard = {"single": self.selected_pods[0].to_dict()}
        else:
            self.clipboard = {"multiple": [pod.to_dict() for pod in self.selected_pods]}

    def paste_pod(self):
        """Paste pod(s) from clipboard."""
        if not self.clipboard:
            return

        # Save state for undo
        self.save_state()

        # Handle both old (single pod dict) and new (single/multiple) clipboard formats
        if "single" in self.clipboard:
            pod_data = self.clipboard["single"]
            new_pod = Pod.from_dict(pod_data)
            new_pod.id = str(uuid.uuid4())
            new_pod.x += 30
            new_pod.y += 30
            new_pod.name = f"{new_pod.name} (Copy)"
            self._update_pod_ids(new_pod)
            self.current_container.add_child(new_pod)
        elif "multiple" in self.clipboard:
            # Paste multiple pods
            for pod_data in self.clipboard["multiple"]:
                new_pod = Pod.from_dict(pod_data)
                new_pod.id = str(uuid.uuid4())
                new_pod.x += 30
                new_pod.y += 30
                new_pod.name = f"{new_pod.name} (Copy)"
                self._update_pod_ids(new_pod)
                self.current_container.add_child(new_pod)
        else:
            # Old format - single pod dict
            new_pod = Pod.from_dict(self.clipboard)
            new_pod.id = str(uuid.uuid4())
            new_pod.x += 30
            new_pod.y += 30
            new_pod.name = f"{new_pod.name} (Copy)"
            self._update_pod_ids(new_pod)
            self.current_container.add_child(new_pod)

        self.render()

    def _update_pod_ids(self, pod: Pod):
        """Recursively update pod and children IDs when copying."""
        for child in pod.children:
            child.id = str(uuid.uuid4())
            self._update_pod_ids(child)

    def align_pods(self, direction: str):
        """Align selected pods in the specified direction."""
        if len(self.selected_pods) < 2:
            return  # Need at least 2 pods to align

        # Save state for undo
        self.save_state()

        if direction == "left":
            # Align to leftmost edge
            min_x = min(pod.x - pod.width / 2 for pod in self.selected_pods)
            for pod in self.selected_pods:
                pod.x = min_x + pod.width / 2
        elif direction == "right":
            # Align to rightmost edge
            max_x = max(pod.x + pod.width / 2 for pod in self.selected_pods)
            for pod in self.selected_pods:
                pod.x = max_x - pod.width / 2
        elif direction == "center":
            # Align to horizontal center
            avg_x = sum(pod.x for pod in self.selected_pods) / len(self.selected_pods)
            for pod in self.selected_pods:
                pod.x = avg_x
        elif direction == "top":
            # Align to top edge
            min_y = min(pod.y - pod.height / 2 for pod in self.selected_pods)
            for pod in self.selected_pods:
                pod.y = min_y + pod.height / 2
        elif direction == "bottom":
            # Align to bottom edge
            max_y = max(pod.y + pod.height / 2 for pod in self.selected_pods)
            for pod in self.selected_pods:
                pod.y = max_y - pod.height / 2
        elif direction == "middle":
            # Align to vertical middle
            avg_y = sum(pod.y for pod in self.selected_pods) / len(self.selected_pods)
            for pod in self.selected_pods:
                pod.y = avg_y

        self.render()

    def render_grid(self, canvas_width: float, canvas_height: float, offset_x: float, offset_y: float):
        """Render a grid overlay on the canvas."""
        grid_size_zoomed = self.grid_size * self.zoom_scale

        # Calculate starting positions to align grid with world coordinates
        start_x = (offset_x % grid_size_zoomed)
        start_y = (offset_y % grid_size_zoomed)

        # Draw vertical lines
        x = start_x
        while x < canvas_width:
            self.canvas.create_line(x, 0, x, canvas_height, fill="#E0E0E0", tags=("grid",))
            x += grid_size_zoomed

        # Draw horizontal lines
        y = start_y
        while y < canvas_height:
            self.canvas.create_line(0, y, canvas_width, y, fill="#E0E0E0", tags=("grid",))
            y += grid_size_zoomed

    def toggle_grid(self):
        """Toggle grid visibility."""
        self.show_grid = self.grid_var.get()
        self.render()

    def toggle_snap(self):
        """Toggle snap to grid."""
        self.snap_to_grid = self.snap_var.get()

    def snap_to_grid_coord(self, coord: float) -> float:
        """Snap a coordinate to the nearest grid point."""
        if not self.snap_to_grid:
            return coord
        return round(coord / self.grid_size) * self.grid_size

    def open_search_dialog(self):
        """Open the search dialog to find pods."""
        # If dialog already exists, just focus it
        if self.search_dialog and self.search_dialog.winfo_exists():
            self.search_dialog.focus()
            return

        # Create search dialog
        self.search_dialog = tk.Toplevel(self.root)
        self.search_dialog.title("Search Pods")
        self.search_dialog.geometry("450x400")
        self.search_dialog.transient(self.root)

        # Position near top-right of main window
        self.search_dialog.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - 470
        y = self.root.winfo_y() + 50
        self.search_dialog.geometry(f"+{x}+{y}")

        # Search entry frame
        search_frame = tk.Frame(self.search_dialog)
        search_frame.pack(padx=10, pady=10, fill=tk.X)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = tk.Entry(search_frame, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        search_entry.focus()

        # Search in current container or all toggle
        search_scope_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(search_frame, text="All", variable=search_scope_var,
                       command=lambda: self.perform_search(search_entry.get(), search_scope_var.get(), results_listbox, count_label)).pack(side=tk.LEFT)

        # Results count label
        count_label = tk.Label(self.search_dialog, text="0 results", fg="#666")
        count_label.pack(padx=10, pady=(0, 5))

        # Results listbox with scrollbar
        results_frame = tk.Frame(self.search_dialog)
        results_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        results_listbox = tk.Listbox(results_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=results_listbox.yview)

        # Bind search entry to perform search as user types
        def on_search_change(*args):
            self.perform_search(search_entry.get(), search_scope_var.get(), results_listbox, count_label)

        search_entry.bind("<KeyRelease>", on_search_change)

        # Bind double-click and Enter to navigate to result
        def on_result_select(event=None):
            selection = results_listbox.curselection()
            if selection and self.search_results:
                idx = selection[0]
                self.navigate_to_search_result(idx)

        results_listbox.bind("<Double-Button-1>", on_result_select)
        results_listbox.bind("<Return>", on_result_select)

        # Navigation buttons
        button_frame = tk.Frame(self.search_dialog)
        button_frame.pack(padx=10, pady=10, fill=tk.X)

        def go_previous():
            if self.search_results:
                self.search_result_index = (self.search_result_index - 1) % len(self.search_results)
                results_listbox.selection_clear(0, tk.END)
                results_listbox.selection_set(self.search_result_index)
                results_listbox.see(self.search_result_index)
                self.navigate_to_search_result(self.search_result_index)

        def go_next():
            if self.search_results:
                self.search_result_index = (self.search_result_index + 1) % len(self.search_results)
                results_listbox.selection_clear(0, tk.END)
                results_listbox.selection_set(self.search_result_index)
                results_listbox.see(self.search_result_index)
                self.navigate_to_search_result(self.search_result_index)

        ttk.Button(button_frame, text="Previous", command=go_previous).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Next", command=go_next).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.search_dialog.destroy).pack(side=tk.RIGHT, padx=5)

        # Bind Escape to close
        self.search_dialog.bind("<Escape>", lambda e: self.search_dialog.destroy())

        # Perform initial search if there's any text
        if search_entry.get():
            self.perform_search(search_entry.get(), search_scope_var.get(), results_listbox, count_label)

    def perform_search(self, query: str, search_all: bool, results_listbox: tk.Listbox, count_label: tk.Label):
        """Perform search and update results listbox."""
        results_listbox.delete(0, tk.END)
        self.search_results.clear()
        self.search_result_index = 0

        if not query:
            count_label.config(text="0 results")
            return

        # Convert query to lowercase for case-insensitive search
        query_lower = query.lower()

        # Determine search root
        search_root = self.main_pod if search_all else self.current_container

        # Recursively search for matching pods
        def search_pods(pod: Pod, path: str = ""):
            current_path = f"{path}/{pod.name}" if path else pod.name

            # Check if this pod matches
            if query_lower in pod.name.lower():
                # Don't include the search root itself in results
                if pod != search_root:
                    self.search_results.append((pod, current_path))

            # Search children
            for child in pod.children:
                search_pods(child, current_path)

        # Perform search
        search_pods(search_root)

        # Populate results listbox
        for pod, path in self.search_results:
            results_listbox.insert(tk.END, path)

        # Update count label
        count = len(self.search_results)
        count_label.config(text=f"{count} result{'s' if count != 1 else ''}")

        # Auto-select first result
        if self.search_results:
            results_listbox.selection_set(0)

    def navigate_to_search_result(self, index: int):
        """Navigate to a search result and select the pod."""
        if not self.search_results or index >= len(self.search_results):
            return

        target_pod, path = self.search_results[index]

        # Build navigation path to the pod
        nav_path = []
        current = target_pod.parent
        while current and current != self.main_pod:
            nav_path.insert(0, current)
            current = current.parent

        # Navigate to the pod's container
        if target_pod.parent:
            # Clear current navigation history
            self.navigation_history.clear()

            # Build new navigation history
            current = self.main_pod
            for container in nav_path:
                self.navigation_history.append(current)
                current = container

            if nav_path:
                self.current_container = nav_path[-1]
            else:
                # Pod is directly in main
                self.current_container = self.main_pod

            # Update UI
            self.nav_label.config(text=f"Current: {self.current_container.name}")
            self.back_button.config(state=tk.NORMAL if self.navigation_history else tk.DISABLED)

            # Clear all selections
            for p in self.selected_pods:
                p.selected = False
            self.selected_pods.clear()

            # Select the target pod
            target_pod.selected = True
            self.selected_pod = target_pod
            self.selected_pods = [target_pod]

            # Reset view
            self.pan_offset_x = 0
            self.pan_offset_y = 0

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
        self.selected_pods.clear()
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
            self.selected_pods.clear()
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
