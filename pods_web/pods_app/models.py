"""Django models for Pods application."""

from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid


# Validators
hex_color_validator = RegexValidator(
    regex=r'^#[0-9A-Fa-f]{6}$',
    message='Color must be a valid hex code (e.g., #FF5733)'
)


class Pod(models.Model):
    """
    A Pod is a container that represents an idea, person, group, or any concept.
    Pods can contain other pods and have visual properties for rendering.
    """

    SHAPE_CHOICES = [
        ('oval', 'Oval'),
        ('rectangle', 'Rectangle'),
    ]

    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Basic properties
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    has_description = models.BooleanField(default=False, editable=False)

    # Position and size (center-based coordinates)
    x = models.FloatField(default=0)
    y = models.FloatField(default=0)
    width = models.FloatField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(10000)]
    )
    height = models.FloatField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(10000)]
    )

    # Shape: "oval" or "rectangle"
    shape = models.CharField(
        max_length=20,
        default='oval',
        choices=SHAPE_CHOICES
    )

    # Visual properties
    color = models.CharField(
        max_length=7,
        default='#E8F4F8',
        validators=[hex_color_validator]
    )
    border_color = models.CharField(
        max_length=7,
        default='#2C3E50',
        validators=[hex_color_validator]
    )
    text_color = models.CharField(
        max_length=7,
        default='#2C3E50',
        validators=[hex_color_validator]
    )

    # Hierarchy: parent-child relationships
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_index=True  # Add index for frequent filtering
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['parent', 'created_at']),
            models.Index(fields=['name']),
        ]
        verbose_name = 'Pod'
        verbose_name_plural = 'Pods'

    def __str__(self):
        return f"Pod: {self.name} ({self.id})"

    def save(self, *args, **kwargs):
        """Override save to auto-update has_description flag."""
        self.has_description = bool(self.description.strip())
        super().save(*args, **kwargs)

    def clean(self):
        """Validate model data."""
        super().clean()

        # Validate dimensions
        if self.width <= 0 or self.height <= 0:
            raise ValidationError('Width and height must be positive numbers')

        # Prevent circular parent references
        if self.parent:
            current = self.parent
            depth = 0
            max_depth = 100  # Prevent infinite loops
            while current and depth < max_depth:
                if current.id == self.id:
                    raise ValidationError('Cannot set a pod as its own ancestor')
                current = current.parent
                depth += 1

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
        related_name='relationships_as_source',
        db_index=True  # Add index for queries
    )
    target = models.ForeignKey(
        Pod,
        on_delete=models.CASCADE,
        related_name='relationships_as_target',
        db_index=True  # Add index for queries
    )

    # Relationship properties
    label = models.CharField(max_length=255, blank=True, default='')
    relationship_type = models.CharField(max_length=50, default='default')
    description = models.TextField(blank=True, default='')

    # Visual properties
    color = models.CharField(
        max_length=7,
        default='#34495E',
        validators=[hex_color_validator]
    )
    line_width = models.IntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(20)]
    )
    arrow = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['source', 'target']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Relationship'
        verbose_name_plural = 'Relationships'

    def __str__(self):
        return f"Relationship: {self.source.name} -> {self.target.name}"

    def clean(self):
        """Validate relationship data."""
        super().clean()

        # Prevent self-referential relationships
        if self.source_id and self.target_id and self.source_id == self.target_id:
            raise ValidationError('Cannot create a relationship from a pod to itself')
