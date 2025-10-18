"""State management for undo/redo functionality."""

from typing import Dict, TYPE_CHECKING
import tkinter as tk

if TYPE_CHECKING:
    from ..pod import Pod


class StateManager:
    """Handles undo/redo state management."""

    def __init__(self, app):
        """Initialize state manager with reference to main app."""
        self.app = app
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_levels = 50

    def save_state(self):
        """Save the current state for undo/redo functionality."""
        # Serialize ghost_positions for undo/redo (handle None case)
        ghost_positions_copy = {}
        if self.app.ghost_positions:
            ghost_positions_copy = {
                f"{container_id}_{ghost_id}": (x, y)
                for (container_id, ghost_id), (x, y) in self.app.ghost_positions.items()
            }

        # Create a snapshot of the current state
        state = {
            "main_pod": self.app.main_pod.to_dict(),
            "relationships": [rel.to_dict() for rel in self.app.relationships],
            "current_container_id": self.app.current_container.id,
            "navigation_history_ids": [pod.id for pod in self.app.navigation_history],
            "ghost_positions": ghost_positions_copy
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
        # Import here to avoid circular imports
        from ..pod import Pod
        from ..relationship import Relationship

        # Deserialize main pod
        self.app.main_pod = Pod.from_dict(state["main_pod"])

        # Build pod lookup dictionary
        pod_lookup: Dict[str, Pod] = {}
        self._build_pod_lookup(self.app.main_pod, pod_lookup)

        # Deserialize relationships
        self.app.relationships = [
            Relationship.from_dict(rel_data, pod_lookup)
            for rel_data in state.get("relationships", [])
        ]

        # Restore ghost positions
        self.app.ghost_positions = {}
        ghost_data = state.get("ghost_positions", {})
        for key_str, (x, y) in ghost_data.items():
            # Parse key string back to tuple
            parts = key_str.split('_', 1)  # Split on first underscore only
            if len(parts) == 2:
                container_id, ghost_id = parts
                self.app.ghost_positions[(container_id, ghost_id)] = (x, y)

        # Restore current container
        container_id = state.get("current_container_id")
        self.app.current_container = pod_lookup.get(container_id, self.app.main_pod)

        # Restore navigation history
        self.app.navigation_history = [
            pod_lookup[pod_id]
            for pod_id in state.get("navigation_history_ids", [])
            if pod_id in pod_lookup
        ]

        # Update UI
        self.app.nav_label.config(text=f"Current: {self.app.current_container.name}")
        self.app.back_button.config(state=tk.NORMAL if self.app.navigation_history else tk.DISABLED)
        self.app.selected_pod = None
        self.app.selected_pods.clear()
        self.app.selected_relationship = None
        self.app.selected_ghost = None

        self.app.render()

    def undo(self):
        """Undo the last action."""
        if not self.undo_stack:
            return

        # Save current state to redo stack before undoing
        current_state = {
            "main_pod": self.app.main_pod.to_dict(),
            "relationships": [rel.to_dict() for rel in self.app.relationships],
            "current_container_id": self.app.current_container.id,
            "navigation_history_ids": [pod.id for pod in self.app.navigation_history]
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
            "main_pod": self.app.main_pod.to_dict(),
            "relationships": [rel.to_dict() for rel in self.app.relationships],
            "current_container_id": self.app.current_container.id,
            "navigation_history_ids": [pod.id for pod in self.app.navigation_history]
        }
        self.undo_stack.append(current_state)

        # Restore next state
        next_state = self.redo_stack.pop()
        self.restore_state(next_state)

    def _build_pod_lookup(self, pod: 'Pod', lookup: Dict[str, 'Pod']):
        """Recursively build a lookup dictionary of pod ID -> pod object."""
        lookup[pod.id] = pod
        for child in pod.children:
            self._build_pod_lookup(child, lookup)
