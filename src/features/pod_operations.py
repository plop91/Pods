"""Pod operations for creating, editing, deleting, and manipulating pods."""

import tkinter as tk
from tkinter import simpledialog
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pod import Pod
    from ..relationship import Relationship


class PodOperations:
    """Manages all pod creation, editing, deletion, and manipulation operations."""

    def __init__(self, app):
        """Initialize pod operations with reference to main app."""
        self.app = app

    def resize_pod(self, mouse_x: float, mouse_y: float):
        """Resize the selected pod based on the resize handle being dragged."""
        if not self.app.selected_pod or not self.app.resize_handle:
            return

        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        # Convert mouse position to world coordinates (accounting for zoom)
        world_x = (mouse_x - offset_x) / self.app.zoom_scale
        world_y = (mouse_y - offset_y) / self.app.zoom_scale

        # Get current bounds in world coordinates
        x1, y1, x2, y2 = self.app.selected_pod.get_bounds()

        # Minimum size constraints
        min_width = 40
        min_height = 30

        # Adjust bounds based on which handle is being dragged
        handle = self.app.resize_handle

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
        self.app.selected_pod.x = new_x
        self.app.selected_pod.y = new_y
        self.app.selected_pod.width = new_width
        self.app.selected_pod.height = new_height

    def edit_pod_name(self, pod: 'Pod'):
        """Open dialog to edit pod name."""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Edit Pod Name")
        dialog.geometry("400x120")
        dialog.transient(self.app.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.app.root.winfo_x() + (self.app.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Pod Name:").pack(pady=10)
        entry = tk.Entry(dialog, width=40)
        entry.insert(0, pod.name)
        entry.pack(pady=5)
        entry.focus()

        def on_ok():
            # Save state for undo
            self.app.state_manager.save_state()

            pod.name = entry.get()
            dialog.destroy()
            self.app.render_manager.render()

        def on_cancel():
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        # Bind Enter key to OK
        entry.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

    def edit_pod_description(self, pod: 'Pod'):
        """Open dialog to edit pod description."""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Edit Pod Description")
        dialog.geometry("500x300")
        dialog.transient(self.app.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.app.root.winfo_x() + (self.app.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Pod Description:").pack(pady=10)
        text_widget = tk.Text(dialog, width=60, height=10, wrap=tk.WORD)
        if pod.description:
            text_widget.insert("1.0", pod.description)
        text_widget.pack(pady=5, padx=10)
        text_widget.focus()

        def on_ok():
            # Save state for undo
            self.app.state_manager.save_state()

            pod.description = text_widget.get("1.0", tk.END).strip()
            dialog.destroy()
            self.app.render_manager.render()

        def on_cancel():
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        dialog.bind("<Escape>", lambda e: on_cancel())

    def toggle_pod_description(self, pod: 'Pod', enabled: bool):
        """Toggle description display for a pod."""
        # Save state for undo
        self.app.state_manager.save_state()

        pod.has_description = enabled
        self.app.render_manager.render()

    def edit_relationship_label(self, relationship: 'Relationship'):
        """Open dialog to edit relationship label."""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Edit Relationship Label")
        dialog.geometry("400x120")
        dialog.transient(self.app.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.app.root.winfo_x() + (self.app.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Relationship Label:").pack(pady=10)
        entry = tk.Entry(dialog, width=40)
        entry.insert(0, relationship.label)
        entry.pack(pady=5)
        entry.focus()

        def on_ok():
            # Save state for undo
            self.app.state_manager.save_state()

            relationship.label = entry.get()
            dialog.destroy()
            self.app.render_manager.render()

        def on_cancel():
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        # Bind Enter key to OK
        entry.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

    def edit_relationship_description(self, relationship: 'Relationship'):
        """Open dialog to edit relationship description."""
        dialog = tk.Toplevel(self.app.root)
        dialog.title("Edit Relationship Description")
        dialog.geometry("500x300")
        dialog.transient(self.app.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = self.app.root.winfo_x() + (self.app.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Relationship Description:").pack(pady=10)
        text_widget = tk.Text(dialog, width=60, height=10, wrap=tk.WORD)
        if relationship.description:
            text_widget.insert("1.0", relationship.description)
        text_widget.pack(pady=5, padx=10)
        text_widget.focus()

        def on_ok():
            # Save state for undo
            self.app.state_manager.save_state()

            relationship.description = text_widget.get("1.0", tk.END).strip()
            dialog.destroy()
            self.app.render_manager.render()

        def on_cancel():
            dialog.destroy()

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10).pack(side=tk.LEFT, padx=5)

        dialog.bind("<Escape>", lambda e: on_cancel())

    def add_new_pod(self):
        """Add a new pod in the center of the current view."""
        # Import here to avoid circular imports
        from ..pod import Pod

        # Save state for undo
        self.app.state_manager.save_state()

        # Create a new pod at the origin (center of view)
        new_pod = Pod(
            "New Pod",
            x=0,
            y=0,
            width=120,
            height=70,
            shape="oval"
        )
        self.app.current_container.add_child(new_pod)

        self.app.render_manager.render()

    def add_pod_at_position(self, canvas_x: float, canvas_y: float, shape: str = "oval"):
        """Add a new pod at the specified canvas position."""
        # Import here to avoid circular imports
        from ..pod import Pod

        # Save state for undo
        self.app.state_manager.save_state()

        # Convert canvas coordinates to world coordinates
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        world_x = (canvas_x - offset_x) / self.app.zoom_scale
        world_y = (canvas_y - offset_y) / self.app.zoom_scale

        # Create a new pod at this position
        new_pod = Pod(
            "New Pod",
            x=world_x,
            y=world_y,
            width=120,
            height=70,
            shape=shape
        )
        self.app.current_container.add_child(new_pod)

        self.app.render_manager.render()

    def delete_pod(self, pod: 'Pod'):
        """Delete the specified pod."""
        # Save state for undo
        self.app.state_manager.save_state()

        # Remove all relationships connected to this pod
        relationships_to_remove = []
        for rel in self.app.relationships:
            if rel.source == pod or rel.target == pod:
                relationships_to_remove.append(rel)

        for rel in relationships_to_remove:
            self.app.relationships.remove(rel)

        # Remove the pod from its parent
        if pod.parent:
            pod.parent.remove_child(pod)

        # If this pod was selected, deselect it
        if pod in self.app.selected_pods:
            self.app.selected_pods.remove(pod)
        if self.app.selected_pod == pod:
            self.app.selected_pod = None

        self.app.render_manager.render()

    def delete_relationship(self, relationship: 'Relationship'):
        """Delete the specified relationship."""
        # Save state for undo
        self.app.state_manager.save_state()

        if relationship in self.app.relationships:
            self.app.relationships.remove(relationship)

        # Deselect if this was the selected relationship
        if self.app.selected_relationship == relationship:
            self.app.selected_relationship = None

        self.app.render_manager.render()

    def delete_selected(self):
        """Delete the selected pod(s) or relationship."""
        if self.app.selected_relationship:
            self.delete_relationship(self.app.selected_relationship)
        elif self.app.selected_pods:
            # Save state for undo (only once for multiple deletions)
            self.app.state_manager.save_state()

            # Delete all selected pods
            pods_to_delete = list(self.app.selected_pods)  # Copy list since we'll modify it
            for pod in pods_to_delete:
                # Remove all relationships connected to this pod
                relationships_to_remove = []
                for rel in self.app.relationships:
                    if rel.source == pod or rel.target == pod:
                        relationships_to_remove.append(rel)

                for rel in relationships_to_remove:
                    self.app.relationships.remove(rel)

                # Remove the pod from its parent
                if pod.parent:
                    pod.parent.remove_child(pod)

            # Clear selection
            self.app.selected_pods.clear()
            self.app.selected_pod = None

            self.app.render_manager.render()

    def move_selected(self, dx: float, dy: float):
        """Move selected pods by the specified delta."""
        if not self.app.selected_pods:
            return

        # Save state for undo
        self.app.state_manager.save_state()

        for pod in self.app.selected_pods:
            pod.x += dx
            pod.y += dy

        self.app.render_manager.render()

    def select_all(self):
        """Select all pods in the current container."""
        # Deselect all first
        for p in self.app.selected_pods:
            p.selected = False
        self.app.selected_pods.clear()

        # Select all pods in current container
        for pod in self.app.current_container.children:
            pod.selected = True
            self.app.selected_pods.append(pod)

        self.app.selected_pod = self.app.selected_pods[0] if self.app.selected_pods else None

        self.app.render_manager.render()

    def duplicate_selected(self):
        """Duplicate the selected pod(s)."""
        # Import here to avoid circular imports
        from ..pod import Pod

        if not self.app.selected_pods:
            return

        # Save state for undo
        self.app.state_manager.save_state()

        new_pods = []
        for pod in self.app.selected_pods:
            new_pod = Pod.from_dict(pod.to_dict())
            new_pod.id = str(uuid.uuid4())
            new_pod.x += 30
            new_pod.y += 30
            new_pod.name = f"{new_pod.name} (Copy)"
            self._update_pod_ids(new_pod)
            self.app.current_container.add_child(new_pod)
            new_pods.append(new_pod)

        # Select the new pods
        for p in self.app.selected_pods:
            p.selected = False
        self.app.selected_pods = new_pods
        for p in new_pods:
            p.selected = True
        self.app.selected_pod = new_pods[0] if new_pods else None

        self.app.render_manager.render()

    def copy_pod(self):
        """Copy the selected pod(s) to clipboard."""
        if not self.app.selected_pods:
            return

        # Save pod data to clipboard (support multiple pods)
        if len(self.app.selected_pods) == 1:
            self.app.clipboard = {"single": self.app.selected_pods[0].to_dict()}
        else:
            self.app.clipboard = {"multiple": [pod.to_dict() for pod in self.app.selected_pods]}

    def paste_pod(self):
        """Paste pod(s) from clipboard."""
        # Import here to avoid circular imports
        from ..pod import Pod

        if not self.app.clipboard:
            return

        # Save state for undo
        self.app.state_manager.save_state()

        # Handle both old (single pod dict) and new (single/multiple) clipboard formats
        if "single" in self.app.clipboard:
            pod_data = self.app.clipboard["single"]
            new_pod = Pod.from_dict(pod_data)
            new_pod.id = str(uuid.uuid4())
            new_pod.x += 30
            new_pod.y += 30
            new_pod.name = f"{new_pod.name} (Copy)"
            self._update_pod_ids(new_pod)
            self.app.current_container.add_child(new_pod)
        elif "multiple" in self.app.clipboard:
            # Paste multiple pods
            for pod_data in self.app.clipboard["multiple"]:
                new_pod = Pod.from_dict(pod_data)
                new_pod.id = str(uuid.uuid4())
                new_pod.x += 30
                new_pod.y += 30
                new_pod.name = f"{new_pod.name} (Copy)"
                self._update_pod_ids(new_pod)
                self.app.current_container.add_child(new_pod)
        else:
            # Old format - single pod dict
            new_pod = Pod.from_dict(self.app.clipboard)
            new_pod.id = str(uuid.uuid4())
            new_pod.x += 30
            new_pod.y += 30
            new_pod.name = f"{new_pod.name} (Copy)"
            self._update_pod_ids(new_pod)
            self.app.current_container.add_child(new_pod)

        self.app.render_manager.render()

    def _update_pod_ids(self, pod: 'Pod'):
        """Recursively update pod and children IDs when copying."""
        for child in pod.children:
            child.id = str(uuid.uuid4())
            self._update_pod_ids(child)

    def align_pods(self, direction: str):
        """Align selected pods in the specified direction."""
        if len(self.app.selected_pods) < 2:
            return

        # Save state for undo
        self.app.state_manager.save_state()

        if direction == "left":
            # Align to leftmost pod
            min_x = min(pod.x - pod.width / 2 for pod in self.app.selected_pods)
            for pod in self.app.selected_pods:
                pod.x = min_x + pod.width / 2
        elif direction == "right":
            # Align to rightmost pod
            max_x = max(pod.x + pod.width / 2 for pod in self.app.selected_pods)
            for pod in self.app.selected_pods:
                pod.x = max_x - pod.width / 2
        elif direction == "top":
            # Align to topmost pod
            min_y = min(pod.y - pod.height / 2 for pod in self.app.selected_pods)
            for pod in self.app.selected_pods:
                pod.y = min_y + pod.height / 2
        elif direction == "bottom":
            # Align to bottommost pod
            max_y = max(pod.y + pod.height / 2 for pod in self.app.selected_pods)
            for pod in self.app.selected_pods:
                pod.y = max_y - pod.height / 2
        elif direction == "horizontal":
            # Align to horizontal center
            avg_x = sum(pod.x for pod in self.app.selected_pods) / len(self.app.selected_pods)
            for pod in self.app.selected_pods:
                pod.x = avg_x
        elif direction == "vertical":
            # Align to vertical center
            avg_y = sum(pod.y for pod in self.app.selected_pods) / len(self.app.selected_pods)
            for pod in self.app.selected_pods:
                pod.y = avg_y

        self.app.render_manager.render()
