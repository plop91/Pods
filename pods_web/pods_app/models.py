"""Django models for Pods application."""

from django.db import models
import uuid


class Pod(models.Model):
    """
    A Pod is a container that represents an idea, person, group, or any concept.
    Pods can contain other pods and have visual properties for rendering.
    """

    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic properties
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    has_description = models.BooleanField(default=False)

    # Position and size (center-based coordinates)
    x = models.FloatField(default=0)
    y = models.FloatField(default=0)
    width = models.FloatField(default=100)
    height = models.FloatField(default=60)

    # Shape: "oval" or "rectangle"
    shape = models.CharField(max_length=20, default='oval')

    # Visual properties
    color = models.CharField(max_length=7, default='#E8F4F8')
    border_color = models.CharField(max_length=7, default='#2C3E50')
    text_color = models.CharField(max_length=7, default='#2C3E50')

    # Hierarchy: parent-child relationships
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Pod: {self.name} ({self.id})"

    def get_bounds(self):
        """Return the bounding box (x1, y1, x2, y2) of this pod."""
        x1 = self.x - self.width / 2
        y1 = self.y - self.height / 2
        x2 = self.x + self.width / 2
        y2 = self.y + self.height / 2
        return (x1, y1, x2, y2)


class Relationship(models.Model):
    """
    A Relationship represents a connection between two pods.
    Can represent ownership, membership, dependencies, or any association.
    """

    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Source and target pods
    source = models.ForeignKey(
        Pod,
        on_delete=models.CASCADE,
        related_name='relationships_as_source'
    )
    target = models.ForeignKey(
        Pod,
        on_delete=models.CASCADE,
        related_name='relationships_as_target'
    )

    # Relationship properties
    label = models.CharField(max_length=255, blank=True, default='')
    relationship_type = models.CharField(max_length=50, default='default')
    description = models.TextField(blank=True, default='')

    # Visual properties
    color = models.CharField(max_length=7, default='#34495E')
    line_width = models.IntegerField(default=2)
    arrow = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Relationship: {self.source.name} -> {self.target.name}"
