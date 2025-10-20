"""Event handling for user interactions."""

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..relationship import Relationship


class EventHandler:
    """Manages all user interaction events on the canvas."""

    def __init__(self, app):
        """Initialize event handler with reference to main app."""
        self.app = app

    def on_canvas_click(self, event):
        """Handle single click on canvas."""
        # Import here to avoid circular imports
        from ..relationship import Relationship

        # If in relationship creation mode, complete the relationship
        if self.app.creating_relationship:
            # Check if clicking on a ghost pod to create relationship to it
            ghost_pod = self.app.get_ghost_pod_at_position(event.x, event.y)
            if ghost_pod and ghost_pod != self.app.relationship_source_pod:
                # Save state for undo
                self.app.state_manager.save_state()

                # Create the relationship to the ghost pod
                new_rel = Relationship(
                    self.app.relationship_source_pod,
                    ghost_pod,
                    label="",
                    relationship_type="default"
                )
                self.app.relationships.append(new_rel)

                # Exit relationship creation mode
                self.app.creating_relationship = False
                self.app.relationship_source_pod = None
                self.app.relationship_source_direction = None
                self.app.canvas.config(cursor="arrow")
                self.app.render_manager.render()
                return

            # Check if clicking in external link zone
            canvas_width = self.app.canvas.winfo_width()
            zone_x = canvas_width - self.app.external_link_zone_width
            if event.x >= zone_x:
                # Show external pod selector
                self.app.show_external_pod_selector()
                return

            target_pod = self.app.get_pod_at_position(event.x, event.y)
            if target_pod and target_pod != self.app.relationship_source_pod:
                # Save state for undo
                self.app.state_manager.save_state()

                # Create the relationship
                new_rel = Relationship(
                    self.app.relationship_source_pod,
                    target_pod,
                    label="",
                    relationship_type="default"
                )
                self.app.relationships.append(new_rel)

            # Exit relationship creation mode
            self.app.creating_relationship = False
            self.app.relationship_source_pod = None
            self.app.relationship_source_direction = None
            self.app.canvas.config(cursor="arrow")
            self.app.render_manager.render()
            return

        # Check if clicking on a relationship button of the selected pod
        if self.app.selected_pod:
            rel_button = self.app.get_relationship_button_at_position(event.x, event.y, self.app.selected_pod)
            if rel_button:
                # Start relationship creation mode
                self.app.creating_relationship = True
                self.app.relationship_source_pod = self.app.selected_pod
                self.app.relationship_source_direction = rel_button
                self.app.canvas.config(cursor="crosshair")
                self.app.render_manager.render()  # Re-render to show external link zone and hint
                return

            # Check if clicking on a resize handle of the selected pod
            handle = self.app.get_resize_handle_at_position(event.x, event.y, self.app.selected_pod)
            if handle:
                # Start resizing
                self.app.resizing = True
                self.app.resize_handle = handle
                self.app.drag_start_x = event.x
                self.app.drag_start_y = event.y
                return

        # Check if clicking on a ghost pod
        ghost_pod = self.app.get_ghost_pod_at_position(event.x, event.y)
        if ghost_pod:
            # Clear regular pod selections
            for p in self.app.selected_pods:
                p.selected = False
            self.app.selected_pods.clear()
            self.app.selected_pod = None

            # Clear relationship selection
            if self.app.selected_relationship:
                self.app.selected_relationship.selected = False
                self.app.selected_relationship = None

            # Select the ghost pod
            self.app.selected_ghost = ghost_pod

            # Start dragging
            self.app.dragging = True
            self.app.drag_start_x = event.x
            self.app.drag_start_y = event.y
            self.app.render_manager.render()
            return

        # Check if clicking on a relationship
        rel = self.app.get_relationship_at_position(event.x, event.y)
        if rel:
            # Deselect all pods
            for p in self.app.selected_pods:
                p.selected = False
            self.app.selected_pods.clear()
            self.app.selected_pod = None

            # Deselect ghost
            self.app.selected_ghost = None

            # Deselect previous relationship
            if self.app.selected_relationship:
                self.app.selected_relationship.selected = False

            # Select new relationship
            self.app.selected_relationship = rel
            rel.selected = True
            self.app.render_manager.render()
            return

        # Check if clicking on a pod
        clicked_pod = self.app.get_pod_at_position(event.x, event.y)

        # Deselect ghost
        self.app.selected_ghost = None

        # Deselect relationship
        if self.app.selected_relationship:
            self.app.selected_relationship.selected = False
            self.app.selected_relationship = None

        if clicked_pod:
            # Start dragging
            self.app.dragging = True
            self.app.drag_start_x = event.x
            self.app.drag_start_y = event.y

            # If Ctrl is held, toggle selection
            if event.state & 0x4:  # Ctrl key
                if clicked_pod in self.app.selected_pods:
                    clicked_pod.selected = False
                    self.app.selected_pods.remove(clicked_pod)
                else:
                    clicked_pod.selected = True
                    self.app.selected_pods.append(clicked_pod)
                self.app.selected_pod = clicked_pod if clicked_pod.selected else (self.app.selected_pods[0] if self.app.selected_pods else None)
            else:
                # Clear previous selections
                for p in self.app.selected_pods:
                    p.selected = False
                self.app.selected_pods.clear()

                # Select clicked pod
                clicked_pod.selected = True
                self.app.selected_pod = clicked_pod
                self.app.selected_pods.append(clicked_pod)

            self.app.render_manager.render()
        else:
            # Clicked on empty space - deselect all
            for p in self.app.selected_pods:
                p.selected = False
            self.app.selected_pods.clear()
            self.app.selected_pod = None

            # Start panning
            self.app.panning = True
            self.app.drag_start_x = event.x
            self.app.drag_start_y = event.y

            self.app.render_manager.render()

    def on_canvas_double_click(self, event):
        """Handle double-click on canvas (navigate into a pod)."""
        clicked_pod = self.app.get_pod_at_position(event.x, event.y)
        if clicked_pod and clicked_pod.children:
            self.app.navigate_into(clicked_pod)

    def on_canvas_drag(self, event):
        """Handle dragging on canvas."""
        if self.app.resizing and self.app.selected_pod:
            # Resize the pod
            self.app.resize_pod(event.x, event.y)
            self.app.render_manager.render()
        elif self.app.panning:
            # Pan the view
            dx = event.x - self.app.drag_start_x
            dy = event.y - self.app.drag_start_y

            self.app.pan_offset_x += dx
            self.app.pan_offset_y += dy

            self.app.drag_start_x = event.x
            self.app.drag_start_y = event.y

            self.app.render_manager.render()
        elif self.app.dragging and self.app.selected_ghost:
            # Drag ghost pod
            dx = event.x - self.app.drag_start_x
            dy = event.y - self.app.drag_start_y

            # Convert canvas delta to world delta (accounting for zoom)
            world_dx = dx / self.app.zoom_scale
            world_dy = dy / self.app.zoom_scale

            # Update ghost position
            key = (self.app.current_container.id, self.app.selected_ghost.id)
            if key in self.app.ghost_positions:
                old_x, old_y = self.app.ghost_positions[key]
                self.app.ghost_positions[key] = (old_x + world_dx, old_y + world_dy)

            self.app.drag_start_x = event.x
            self.app.drag_start_y = event.y

            self.app.render_manager.render()
        elif self.app.dragging and self.app.selected_pods:
            # Drag selected pods
            dx = event.x - self.app.drag_start_x
            dy = event.y - self.app.drag_start_y

            # Convert canvas delta to world delta (accounting for zoom)
            world_dx = dx / self.app.zoom_scale
            world_dy = dy / self.app.zoom_scale

            for pod in self.app.selected_pods:
                pod.x += world_dx
                pod.y += world_dy

                # Snap to grid if enabled
                if self.app.snap_to_grid:
                    pod.x = self.app.snap_to_grid_coord(pod.x)
                    pod.y = self.app.snap_to_grid_coord(pod.y)

            self.app.drag_start_x = event.x
            self.app.drag_start_y = event.y

            self.app.render_manager.render()

    def on_canvas_release(self, event):
        """Handle mouse release."""
        if self.app.dragging or self.app.panning or self.app.resizing:
            # Save state after drag/pan/resize
            if self.app.dragging or self.app.resizing:
                self.app.state_manager.save_state()

            self.app.dragging = False
            self.app.panning = False
            self.app.resizing = False
            self.app.resize_handle = None

    def on_canvas_motion(self, event):
        """Handle mouse motion (for hover effects)."""
        # Reset all hover states
        for pod in self.app.current_container.children:
            pod.hovered = False

        # Check if hovering over a pod
        hovered_pod = self.app.get_pod_at_position(event.x, event.y)
        if hovered_pod:
            hovered_pod.hovered = True

            # Check if over resize handle
            if self.app.selected_pod:
                handle = self.app.get_resize_handle_at_position(event.x, event.y, self.app.selected_pod)
                if handle:
                    # Set cursor for resize direction
                    cursors = {
                        "nw": "size_nw_se", "n": "size_ns", "ne": "size_ne_sw",
                        "w": "size_we", "e": "size_we",
                        "sw": "size_ne_sw", "s": "size_ns", "se": "size_nw_se"
                    }
                    self.app.canvas.config(cursor=cursors.get(handle, "arrow"))
                    self.app.render_manager.render()
                    return

                # Check if over relationship button
                rel_button = self.app.get_relationship_button_at_position(event.x, event.y, self.app.selected_pod)
                if rel_button:
                    self.app.canvas.config(cursor="hand2")
                    self.app.render_manager.render()
                    return

            # Default cursor for pod hover
            self.app.canvas.config(cursor="hand2")
        else:
            # Check if hovering over a relationship
            rel = self.app.get_relationship_at_position(event.x, event.y)
            if rel:
                self.app.canvas.config(cursor="hand2")
            else:
                # Check if hovering over ghost pod
                ghost_pod = self.app.get_ghost_pod_at_position(event.x, event.y)
                if ghost_pod:
                    self.app.canvas.config(cursor="hand2")
                else:
                    self.app.canvas.config(cursor="arrow")

        self.app.render_manager.render()

    def on_escape_key(self, event):
        """Handle Escape key press."""
        if self.app.creating_relationship:
            self.app.creating_relationship = False
            self.app.relationship_source_pod = None
            self.app.relationship_source_direction = None
            self.app.canvas.config(cursor="arrow")
            self.app.render_manager.render()

    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming."""
        # Get mouse position relative to canvas
        mouse_x = event.x
        mouse_y = event.y

        # Calculate world position before zoom
        canvas_width = self.app.canvas.winfo_width()
        canvas_height = self.app.canvas.winfo_height()
        offset_x = canvas_width / 2 + self.app.pan_offset_x
        offset_y = canvas_height / 2 + self.app.pan_offset_y

        world_x_before = (mouse_x - offset_x) / self.app.zoom_scale
        world_y_before = (mouse_y - offset_y) / self.app.zoom_scale

        # Determine zoom direction
        if event.delta > 0 or event.num == 4:  # Zoom in
            self.app.zoom_scale *= 1.1
        elif event.delta < 0 or event.num == 5:  # Zoom out
            self.app.zoom_scale /= 1.1

        # Clamp zoom scale
        self.app.zoom_scale = max(0.1, min(self.app.zoom_scale, 5.0))

        # Calculate world position after zoom
        world_x_after = (mouse_x - offset_x) / self.app.zoom_scale
        world_y_after = (mouse_y - offset_y) / self.app.zoom_scale

        # Adjust pan offset to keep mouse position fixed
        self.app.pan_offset_x += (world_x_after - world_x_before) * self.app.zoom_scale
        self.app.pan_offset_y += (world_y_after - world_y_before) * self.app.zoom_scale

        self.app.render_manager.render()

    def on_canvas_right_click(self, event):
        """Handle right-click on canvas (show context menu)."""
        import tkinter as tk

        # Check what was right-clicked
        clicked_pod = self.app.get_pod_at_position(event.x, event.y)
        clicked_rel = self.app.get_relationship_at_position(event.x, event.y)

        # Create context menu
        context_menu = tk.Menu(self.app.root, tearoff=0)

        if clicked_pod:
            # Pod context menu
            context_menu.add_command(label="Edit Name", command=lambda: self.app.edit_pod_name(clicked_pod))
            context_menu.add_command(label="Edit Description", command=lambda: self.app.edit_pod_description(clicked_pod))
            context_menu.add_separator()
            context_menu.add_command(label="Change Color", command=lambda: self.app.color_picker_manager.change_pod_color(clicked_pod))
            context_menu.add_separator()

            # Toggle description submenu
            if clicked_pod.has_description:
                context_menu.add_command(label="Disable Description", command=lambda: self.app.toggle_pod_description(clicked_pod, False))
            else:
                context_menu.add_command(label="Enable Description", command=lambda: self.app.toggle_pod_description(clicked_pod, True))

            context_menu.add_separator()
            context_menu.add_command(label="Delete Pod", command=lambda: self.app.delete_pod(clicked_pod))

        elif clicked_rel:
            # Relationship context menu
            context_menu.add_command(label="Edit Label", command=lambda: self.app.edit_relationship_label(clicked_rel))
            context_menu.add_command(label="Edit Description", command=lambda: self.app.edit_relationship_description(clicked_rel))
            context_menu.add_separator()
            context_menu.add_command(label="Delete Relationship", command=lambda: self.app.delete_relationship(clicked_rel))

        else:
            # Empty space context menu
            context_menu.add_command(label="Add Oval Pod", command=lambda: self.app.add_pod_at_position(event.x, event.y, "oval"))
            context_menu.add_command(label="Add Rectangle Pod", command=lambda: self.app.add_pod_at_position(event.x, event.y, "rectangle"))
            context_menu.add_separator()
            context_menu.add_command(label="Reset View", command=self.app.reset_view)

        # Show context menu at cursor position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
