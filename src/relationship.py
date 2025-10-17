"""Relationship model - represents connections between pods."""

from typing import Optional
import uuid


class Relationship:
    """
    A Relationship represents a connection between two pods.
    Can represent ownership, membership, dependencies, or any association.
    """

    def __init__(
        self,
        source_pod,  # Pod (avoid circular import with type hints)
        target_pod,  # Pod
        label: str = "",
        relationship_type: str = "default"
    ):
        self.id = str(uuid.uuid4())
        self.source = source_pod
        self.target = target_pod
        self.label = label
        self.relationship_type = relationship_type

        # Visual properties
        self.color = "#34495E"
        self.line_width = 2
        self.arrow = True  # Whether to show arrow at target

        # Interaction state
        self.selected = False
        self.hovered = False

    def is_external(self, current_container) -> bool:
        """
        Check if this relationship connects to a pod outside the current container.
        Used to determine if the line should go "off-screen".
        """
        source_parent = self.source.parent
        target_parent = self.target.parent

        # If either pod's parent is not the current container, it's external
        return (
            (source_parent != current_container and self.source != current_container) or
            (target_parent != current_container and self.target != current_container)
        )

    def get_endpoints(self):
        """Get the start and end coordinates for rendering."""
        return (
            self.source.x, self.source.y,
            self.target.x, self.target.y
        )

    def __repr__(self):
        return f"Relationship('{self.source.name}' -> '{self.target.name}', label='{self.label}')"
