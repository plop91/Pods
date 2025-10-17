"""Pod data model - represents a container for ideas and other pods."""

from typing import List, Optional, Tuple
import uuid


class Pod:
    """
    A Pod is a container that represents an idea, person, group, or any concept.
    Pods can contain other pods and have visual properties for rendering.
    """

    def __init__(
        self,
        name: str,
        x: float = 0,
        y: float = 0,
        width: float = 100,
        height: float = 60,
        shape: str = "oval",  # "oval" or "rectangle"
        parent: Optional['Pod'] = None
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.shape = shape  # "oval" or "rectangle"
        self.parent = parent

        # Child pods contained within this pod
        self.children: List[Pod] = []

        # Visual properties
        self.color = "#E8F4F8"
        self.border_color = "#2C3E50"
        self.text_color = "#2C3E50"

        # Interaction state
        self.selected = False
        self.hovered = False

    def add_child(self, child: 'Pod'):
        """Add a child pod to this pod's container."""
        if child not in self.children:
            self.children.append(child)
            child.parent = self

    def remove_child(self, child: 'Pod'):
        """Remove a child pod from this pod's container."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Return the bounding box (x1, y1, x2, y2) of this pod."""
        x1 = self.x - self.width / 2
        y1 = self.y - self.height / 2
        x2 = self.x + self.width / 2
        y2 = self.y + self.height / 2
        return (x1, y1, x2, y2)

    def contains_point(self, px: float, py: float) -> bool:
        """Check if a point is inside this pod."""
        x1, y1, x2, y2 = self.get_bounds()
        return x1 <= px <= x2 and y1 <= py <= y2

    def move_to(self, x: float, y: float):
        """Move the pod to a new position."""
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Pod(name='{self.name}', x={self.x}, y={self.y}, children={len(self.children)})"
