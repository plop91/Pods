"""File management for saving and loading projects."""

import json
import os
from typing import Dict, Optional, TYPE_CHECKING
from tkinter import filedialog, messagebox

if TYPE_CHECKING:
    from ..pod import Pod
    from ..relationship import Relationship


class FileManager:
    """Handles saving and loading project files."""

    def __init__(self, app):
        """Initialize file manager with reference to main app."""
        self.app = app

    def save_project_as(self):
        """Save the project to a new file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Pods Project", "*.json"), ("All Files", "*.*")],
            title="Save Project As"
        )

        if file_path:
            self.app.current_file_path = file_path
            self._save_to_file(file_path)

    def save_project(self):
        """Save the project to the current file, or prompt for location if new."""
        if self.app.current_file_path:
            self._save_to_file(self.app.current_file_path)
        else:
            self.save_project_as()

    def _save_to_file(self, file_path: str):
        """Internal method to save project to a specific file."""
        try:
            # Convert ghost_positions dict to JSON-serializable format
            # Keys are tuples (container_id, ghost_id), convert to strings
            ghost_positions_serializable = {
                f"{container_id}_{ghost_id}": {"x": x, "y": y}
                for (container_id, ghost_id), (x, y) in self.app.ghost_positions.items()
            }

            # Build the project data structure
            project_data = {
                "version": "1.0",
                "main_pod": self.app.main_pod.to_dict(),
                "relationships": [rel.to_dict() for rel in self.app.relationships],
                "ghost_positions": ghost_positions_serializable
            }

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2)

            # Update window title
            filename = os.path.basename(file_path)
            self.app.root.title(f"Pods - {filename}")

            # Add to recent files
            self.app.add_recent_file(file_path)

            messagebox.showinfo("Save Successful", f"Project saved to {file_path}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save project:\n{str(e)}")

    def load_project(self):
        """Load a project from a file."""
        # Confirm if there are unsaved changes
        if self.app.main_pod.children or self.app.relationships:
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
            self.load_project_file(file_path)

    def load_project_file(self, file_path: str):
        """Load a specific project file."""
        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found:\n{file_path}")
            # Remove from recent files
            if file_path in self.app.recent_files:
                self.app.recent_files.remove(file_path)
                self.app.save_recent_files()
                self.app.update_recent_files_menu()
            return

        try:
            self._load_from_file(file_path)
            # Add to recent files
            self.app.add_recent_file(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load project:\n{str(e)}")

    def _load_from_file(self, file_path: str):
        """Internal method to load project from a specific file."""
        # Import here to avoid circular imports
        from ..pod import Pod
        from ..relationship import Relationship

        # Read from file
        with open(file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)

        # Deserialize main pod
        self.app.main_pod = Pod.from_dict(project_data["main_pod"])

        # Build pod lookup dictionary
        pod_lookup: Dict[str, Pod] = {}
        self.build_pod_lookup(self.app.main_pod, pod_lookup)

        # Deserialize relationships
        self.app.relationships = [
            Relationship.from_dict(rel_data, pod_lookup)
            for rel_data in project_data.get("relationships", [])
        ]

        # Deserialize ghost positions
        self.app.ghost_positions = {}
        ghost_data = project_data.get("ghost_positions", {})
        for key_str, pos_data in ghost_data.items():
            # Parse key string back to tuple
            parts = key_str.split('_', 1)  # Split on first underscore only
            if len(parts) == 2:
                container_id, ghost_id = parts
                self.app.ghost_positions[(container_id, ghost_id)] = (pos_data["x"], pos_data["y"])

        # Reset state
        self.app.current_container = self.app.main_pod
        self.app.navigation_history = []
        self.app.selected_pod = None
        self.app.selected_pods.clear()
        self.app.selected_relationship = None
        self.app.selected_ghost = None
        self.app.current_file_path = file_path
        self.app.pan_offset_x = 0
        self.app.pan_offset_y = 0
        self.app.zoom_scale = 1.0

        # Update UI
        self.app.nav_label.config(text="Current: Main")
        self.app.back_button.config(state="disabled")

        # Update window title
        filename = os.path.basename(file_path)
        self.app.root.title(f"Pods - {filename}")

        self.app.render()

        messagebox.showinfo("Load Successful", f"Project loaded from {file_path}")

    def build_pod_lookup(self, pod: 'Pod', lookup: Dict[str, 'Pod']):
        """Recursively build a lookup dictionary of pod ID -> pod object."""
        lookup[pod.id] = pod
        for child in pod.children:
            self.build_pod_lookup(child, lookup)

    def new_project(self):
        """Create a new empty project."""
        # Import here to avoid circular imports
        from ..pod import Pod

        # Confirm if there are unsaved changes
        if self.app.main_pod.children or self.app.relationships:
            response = messagebox.askyesno(
                "New Project",
                "Are you sure you want to create a new project? Any unsaved changes will be lost."
            )
            if not response:
                return

        # Reset to empty project
        self.app.main_pod = Pod("Main", x=0, y=0, width=0, height=0)
        self.app.current_container = self.app.main_pod
        self.app.relationships = []
        self.app.ghost_positions = {}
        self.app.navigation_history = []
        self.app.selected_pod = None
        self.app.selected_pods.clear()
        self.app.selected_relationship = None
        self.app.selected_ghost = None
        self.app.current_file_path = None
        self.app.pan_offset_x = 0
        self.app.pan_offset_y = 0
        self.app.zoom_scale = 1.0

        # Clear undo/redo stacks
        self.app.state_manager.undo_stack.clear()
        self.app.state_manager.redo_stack.clear()

        # Update UI
        self.app.nav_label.config(text="Current: Main")
        self.app.back_button.config(state="disabled")
        self.app.root.title("Pods - Visual Idea Organization")

        self.app.render()
