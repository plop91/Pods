"""Main application window with canvas and interaction handling."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict
import math
import json
import uuid

from .pod import Pod
from .relationship import Relationship
from .persistence.file_manager import FileManager
from .persistence.state_manager import StateManager
from .features.search import SearchManager
from .features.minimap import MinimapManager
from .features.color_picker import ColorPickerManager
from .features.pod_operations import PodOperations
from .rendering.renderer import RenderManager
from .handlers.event_handler import EventHandler
from .handlers.hit_detection import HitDetection


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

        # Clipboard for copy/paste
        self.clipboard: Optional[dict] = None

        # Grid and snap settings
        self.show_grid = False
        self.snap_to_grid = False
        self.grid_size = 20  # Grid spacing in pixels

        # Autosave settings
        self.autosave_enabled = True
        self.autosave_interval = 300000  # 5 minutes in milliseconds
        self.autosave_timer_id = None
        self.last_autosave_time = 0

        # Recent files
        self.recent_files: List[str] = []
        self.max_recent_files = 10
        self.load_recent_files()

        # Dark mode
        self.dark_mode = False
        self.load_preferences()

        # Ghost pods (external pods shown in current view)
        self.ghost_pods: List[Pod] = []
        self.ghost_positions: dict = {}  # Maps (container_id, ghost_pod_id) to (x, y) world coordinates
        self.selected_ghost: Optional[Pod] = None  # Currently selected ghost pod

        # Initialize managers
        self.file_manager = FileManager(self)
        self.state_manager = StateManager(self)
        self.search_manager = SearchManager(self)
        self.minimap_manager = MinimapManager(self)
        self.color_picker_manager = ColorPickerManager(self)
        self.pod_operations = PodOperations(self)
        self.render_manager = RenderManager(self)
        self.hit_detection = HitDetection(self)
        self.event_handler = EventHandler(self)

        # Setup UI
        self.setup_ui()

        # Create some example pods
        self.create_example_data()

        # Delay initial render until window is fully displayed and canvas has correct dimensions
        self.root.after(100, self.initial_render)

        # Start autosave timer
        if self.autosave_enabled:
            self.schedule_autosave()

    def setup_ui(self):
        """Setup the user interface."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.file_manager.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.file_manager.load_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.file_manager.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.file_manager.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export to PNG...", command=self.export_to_png)
        file_menu.add_separator()

        # Recent files submenu
        self.recent_files_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_files_menu)
        self.update_recent_files_menu()

        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.state_manager.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.state_manager.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy Pod", command=self.pod_operations.copy_pod, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste Pod", command=self.pod_operations.paste_pod, accelerator="Ctrl+V")

        # Bind keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.file_manager.new_project())
        self.root.bind("<Control-o>", lambda e: self.file_manager.load_project())
        self.root.bind("<Control-s>", lambda e: self.file_manager.save_project())
        self.root.bind("<Control-Shift-S>", lambda e: self.file_manager.save_project_as())
        self.root.bind("<Control-z>", lambda e: self.state_manager.undo())
        self.root.bind("<Control-y>", lambda e: self.state_manager.redo())
        self.root.bind("<Control-c>", lambda e: self.pod_operations.copy_pod())
        self.root.bind("<Control-v>", lambda e: self.pod_operations.paste_pod())
        self.root.bind("<Delete>", lambda e: self.pod_operations.delete_selected())
        self.root.bind("<BackSpace>", lambda e: self.pod_operations.delete_selected())
        self.root.bind("<Control-f>", lambda e: self.search_manager.open_search_dialog())
        self.root.bind("<Control-a>", lambda e: self.pod_operations.select_all())
        self.root.bind("<Control-d>", lambda e: self.pod_operations.duplicate_selected())

        # Arrow key movement
        self.root.bind("<Left>", lambda e: self.pod_operations.move_selected(-5, 0))
        self.root.bind("<Right>", lambda e: self.pod_operations.move_selected(5, 0))
        self.root.bind("<Up>", lambda e: self.pod_operations.move_selected(0, -5))
        self.root.bind("<Down>", lambda e: self.pod_operations.move_selected(0, 5))

        # Shift+Arrow for larger movements
        self.root.bind("<Shift-Left>", lambda e: self.pod_operations.move_selected(-20, 0))
        self.root.bind("<Shift-Right>", lambda e: self.pod_operations.move_selected(20, 0))
        self.root.bind("<Shift-Up>", lambda e: self.pod_operations.move_selected(0, -20))
        self.root.bind("<Shift-Down>", lambda e: self.pod_operations.move_selected(0, 20))

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
        add_button = ttk.Button(toolbar, text="+ Add Pod", command=self.pod_operations.add_new_pod)
        add_button.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Alignment tools
        ttk.Label(toolbar, text="Align:").pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(toolbar, text="Left", width=5, command=lambda: self.pod_operations.align_pods("left")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Center", width=6, command=lambda: self.pod_operations.align_pods("center")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Right", width=5, command=lambda: self.pod_operations.align_pods("right")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Top", width=4, command=lambda: self.pod_operations.align_pods("top")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Middle", width=6, command=lambda: self.pod_operations.align_pods("middle")).pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="Bottom", width=6, command=lambda: self.pod_operations.align_pods("bottom")).pack(side=tk.LEFT, padx=1)

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Grid and snap checkboxes
        self.grid_var = tk.BooleanVar(value=False)
        self.snap_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="Show Grid", variable=self.grid_var, command=self.toggle_grid).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(toolbar, text="Snap to Grid", variable=self.snap_var, command=self.toggle_snap).pack(side=tk.LEFT, padx=2)

        # Minimap toggle
        ttk.Button(toolbar, text="Minimap", command=self.minimap_manager.toggle_minimap).pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Dark mode toggle
        self.dark_mode_var = tk.BooleanVar(value=self.dark_mode)
        ttk.Checkbutton(toolbar, text="Dark Mode", variable=self.dark_mode_var, command=self.toggle_dark_mode).pack(side=tk.LEFT, padx=2)

        # Status label (autosave indicator)
        self.status_label = ttk.Label(toolbar, text="", foreground="#666")
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Canvas
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Event bindings
        self.canvas.bind("<Button-1>", self.event_handler.on_canvas_click)
        self.canvas.bind("<Button-3>", self.event_handler.on_canvas_right_click)  # Right-click
        self.canvas.bind("<Double-Button-1>", self.event_handler.on_canvas_double_click)
        self.canvas.bind("<B1-Motion>", self.event_handler.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.event_handler.on_canvas_release)
        self.canvas.bind("<Motion>", self.event_handler.on_canvas_motion)
        self.canvas.bind("<MouseWheel>", self.event_handler.on_mouse_wheel)  # Windows/macOS
        self.canvas.bind("<Button-4>", self.event_handler.on_mouse_wheel)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.event_handler.on_mouse_wheel)  # Linux scroll down
        self.root.bind("<Escape>", self.event_handler.on_escape_key)

    def create_example_data(self):
        """Create some example pods and relationships for demonstration."""
        # Create some example pods in the main container
        # Position them around origin (0,0) so they appear centered
        pod1 = Pod("Project Ideas", x=-125, y=-100, width=120, height=70, shape="oval")
        pod2 = Pod("Team Members", x=125, y=-100, width=120, height=70, shape="oval")
        pod3 = Pod("Resources", x=-125, y=100, width=120, height=70, shape="oval")
        pod4 = Pod("Timeline", x=125, y=100, width=120, height=70, shape="oval")

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
        # Position relative to (0,0) within the Project Ideas pod
        sub_pod1 = Pod("Feature A", x=-100, y=0, width=100, height=60, shape="oval")
        sub_pod2 = Pod("Feature B", x=100, y=0, width=100, height=60, shape="oval")
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
        self.render_manager.render()

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
                self.state_manager.save_state()

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
                self.render_manager.render()

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

        self.render_manager.render()

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

            self.render_manager.render()

    def reset_view(self):
        """Reset pan offset and zoom to default values."""
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.zoom_scale = 1.0
        self.render_manager.render()

    def toggle_grid(self):
        """Toggle grid visibility."""
        self.show_grid = self.grid_var.get()
        self.render_manager.render()

    def toggle_snap(self):
        """Toggle snap to grid."""
        self.snap_to_grid = self.snap_var.get()

    def toggle_dark_mode(self):
        """Toggle dark mode."""
        self.dark_mode = self.dark_mode_var.get()
        self.save_preferences()
        self.render_manager.render()

        # Update minimap if visible
        if self.minimap_manager.show_minimap and self.minimap_manager.minimap_window and self.minimap_manager.minimap_window.winfo_exists():
            self.minimap_manager.render_minimap()

    def snap_to_grid_coord(self, coord: float) -> float:
        """Snap a coordinate to the nearest grid point."""
        if not self.snap_to_grid:
            return coord
        return round(coord / self.grid_size) * self.grid_size


    def schedule_autosave(self):
        """Schedule the next autosave."""
        if self.autosave_timer_id:
            self.root.after_cancel(self.autosave_timer_id)
        self.autosave_timer_id = self.root.after(self.autosave_interval, self.perform_autosave)

    def perform_autosave(self):
        """Perform autosave if a file is currently open."""
        if self.current_file_path and self.autosave_enabled:
            try:
                # Use file manager to save (without showing success message)
                # We'll manually save the data
                ghost_positions_serializable = {
                    f"{container_id}_{ghost_id}": {"x": x, "y": y}
                    for (container_id, ghost_id), (x, y) in self.ghost_positions.items()
                }

                project_data = {
                    "version": "1.0",
                    "main_pod": self.main_pod.to_dict(),
                    "relationships": [rel.to_dict() for rel in self.relationships],
                    "ghost_positions": ghost_positions_serializable
                }

                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=2)

                # Update status label
                import time
                self.last_autosave_time = time.time()
                self.status_label.config(text="Autosaved")
                # Clear status after 3 seconds
                self.root.after(3000, lambda: self.status_label.config(text=""))

            except Exception as e:
                print(f"Autosave failed: {e}")

        # Schedule next autosave
        self.schedule_autosave()


    def export_to_png(self):
        """Export the current view to a PNG file."""
        # Ask user for file path
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Export to PNG"
        )

        if not file_path:
            return

        try:
            # Try to use PIL/Pillow if available
            try:
                from PIL import Image, ImageDraw

                # Get canvas dimensions
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                # Create a white image
                img = Image.new('RGB', (canvas_width, canvas_height), 'white')

                # Generate PostScript and convert to image
                ps = self.canvas.postscript(colormode='color')

                # Save PostScript to temp file and convert
                import tempfile
                import os

                with tempfile.NamedTemporaryFile(delete=False, suffix='.ps') as tmp:
                    tmp.write(ps.encode('utf-8'))
                    tmp_path = tmp.name

                try:
                    # Try to convert using PIL
                    from PIL import Image
                    img = Image.open(tmp_path)
                    img.save(file_path, 'PNG')
                    messagebox.showinfo("Success", f"Exported to {file_path}")
                except:
                    # If PIL can't handle PS, use alternative method
                    raise ImportError("PostScript conversion not supported")
                finally:
                    os.unlink(tmp_path)

            except ImportError:
                # Fallback: Use tkinter's built-in screenshot capability
                # This requires the canvas to be visible
                x = self.root.winfo_rootx() + self.canvas.winfo_x()
                y = self.root.winfo_rooty() + self.canvas.winfo_y()
                x1 = x + self.canvas.winfo_width()
                y1 = y + self.canvas.winfo_height()

                # Try using PIL for screenshot
                from PIL import ImageGrab
                img = ImageGrab.grab(bbox=(x, y, x1, y1))
                img.save(file_path, 'PNG')
                messagebox.showinfo("Success", f"Exported to {file_path}")

        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export to PNG:\n{str(e)}\n\nNote: PNG export requires Pillow (pip install pillow)")

    def load_preferences(self):
        """Load user preferences from config file."""
        try:
            import os
            config_path = os.path.expanduser("~/.pods_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.dark_mode = data.get("dark_mode", False)
        except Exception as e:
            print(f"Could not load preferences: {e}")

    def save_preferences(self):
        """Save user preferences to config file."""
        try:
            import os
            config_path = os.path.expanduser("~/.pods_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({"dark_mode": self.dark_mode}, f, indent=2)
        except Exception as e:
            print(f"Could not save preferences: {e}")

    def load_recent_files(self):
        """Load recent files list from config file."""
        try:
            import os
            config_path = os.path.expanduser("~/.pods_recent.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recent_files = data.get("recent_files", [])
        except Exception as e:
            print(f"Could not load recent files: {e}")
            self.recent_files = []

    def save_recent_files(self):
        """Save recent files list to config file."""
        try:
            import os
            config_path = os.path.expanduser("~/.pods_recent.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({"recent_files": self.recent_files}, f, indent=2)
        except Exception as e:
            print(f"Could not save recent files: {e}")

    def add_recent_file(self, file_path: str):
        """Add a file to the recent files list."""
        import os
        # Get absolute path
        abs_path = os.path.abspath(file_path)

        # Remove if already in list
        if abs_path in self.recent_files:
            self.recent_files.remove(abs_path)

        # Add to front of list
        self.recent_files.insert(0, abs_path)

        # Limit list size
        self.recent_files = self.recent_files[:self.max_recent_files]

        # Save to disk
        self.save_recent_files()

        # Update menu
        self.update_recent_files_menu()

    def update_recent_files_menu(self):
        """Update the recent files menu."""
        # Clear existing items
        self.recent_files_menu.delete(0, tk.END)

        if not self.recent_files:
            self.recent_files_menu.add_command(label="(No recent files)", state=tk.DISABLED)
            return

        # Add recent files
        import os
        for file_path in self.recent_files:
            # Show just the filename for cleaner menu
            filename = os.path.basename(file_path)
            self.recent_files_menu.add_command(
                label=filename,
                command=lambda fp=file_path: self.file_manager.load_project_file(fp)
            )

        # Add separator and clear option
        self.recent_files_menu.add_separator()
        self.recent_files_menu.add_command(label="Clear Recent Files", command=self.clear_recent_files)

    def clear_recent_files(self):
        """Clear the recent files list."""
        self.recent_files.clear()
        self.save_recent_files()
        self.update_recent_files_menu()

