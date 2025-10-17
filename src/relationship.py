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
        self.description = ""

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

    def to_dict(self) -> dict:
        """Serialize relationship to dictionary."""
        return {
            "id": self.id,
            "source_id": self.source.id,
            "target_id": self.target.id,
            "label": self.label,
            "relationship_type": self.relationship_type,
            "description": self.description,
            "color": self.color,
            "line_width": self.line_width,
            "arrow": self.arrow
        }

    @staticmethod
    def from_dict(data: dict, pod_lookup: dict) -> 'Relationship':
        """Deserialize relationship from dictionary.

        Args:
            data: Dictionary containing relationship data
            pod_lookup: Dictionary mapping pod IDs to Pod objects
        """
        source_pod = pod_lookup[data["source_id"]]
        target_pod = pod_lookup[data["target_id"]]

        rel = Relationship(
            source_pod=source_pod,
            target_pod=target_pod,
            label=data.get("label", ""),
            relationship_type=data.get("relationship_type", "default")
        )
        rel.id = data["id"]
        rel.description = data.get("description", "")
        rel.color = data.get("color", "#34495E")
        rel.line_width = data.get("line_width", 2)
        rel.arrow = data.get("arrow", True)

        return rel

    def __repr__(self):
        return f"Relationship('{self.source.name}' -> '{self.target.name}', label='{self.label}')"
