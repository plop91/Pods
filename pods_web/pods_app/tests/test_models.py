"""Tests for Pod and Relationship models."""

from django.test import TestCase
from django.core.exceptions import ValidationError
from pods_app.models import Pod, Relationship
import uuid


class PodModelTest(TestCase):
    """Test Pod model functionality."""

    def setUp(self):
        """Set up test data."""
        self.pod = Pod.objects.create(
            name="Test Pod",
            x=100,
            y=200,
            width=150,
            height=100
        )

    def test_create_pod(self):
        """Test creating a basic pod."""
        pod = Pod.objects.create(
            name="New Pod",
            x=50,
            y=75
        )
        self.assertEqual(pod.name, "New Pod")
        self.assertEqual(pod.x, 50)
        self.assertEqual(pod.y, 75)
        self.assertEqual(pod.width, 100)  # Default
        self.assertEqual(pod.height, 60)  # Default
        self.assertIsInstance(pod.id, uuid.UUID)

    def test_pod_defaults(self):
        """Test pod default values."""
        pod = Pod.objects.create(name="Defaults")
        self.assertEqual(pod.shape, 'oval')
        self.assertEqual(pod.color, '#E8F4F8')
        self.assertEqual(pod.border_color, '#2C3E50')
        self.assertEqual(pod.has_description, False)

    def test_pod_str(self):
        """Test pod string representation."""
        self.assertIn("Test Pod", str(self.pod))
        self.assertIn(str(self.pod.id), str(self.pod))

    def test_pod_get_bounds(self):
        """Test get_bounds method."""
        bounds = self.pod.get_bounds()
        self.assertEqual(bounds[0], 25)  # x1 = 100 - 150/2
        self.assertEqual(bounds[1], 150)  # y1 = 200 - 100/2
        self.assertEqual(bounds[2], 175)  # x2 = 100 + 150/2
        self.assertEqual(bounds[3], 250)  # y2 = 200 + 100/2

    def test_pod_with_description(self):
        """Test has_description auto-update."""
        pod = Pod.objects.create(
            name="Described Pod",
            description="This is a test description"
        )
        self.assertTrue(pod.has_description)

        pod.description = ""
        pod.save()
        self.assertFalse(pod.has_description)

    def test_pod_parent_relationship(self):
        """Test hierarchical parent-child relationship."""
        parent = Pod.objects.create(name="Parent")
        child = Pod.objects.create(name="Child", parent=parent)

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

    def test_pod_cascade_delete(self):
        """Test that deleting parent deletes children."""
        parent = Pod.objects.create(name="Parent")
        child = Pod.objects.create(name="Child", parent=parent)
        child_id = child.id

        parent.delete()
        self.assertFalse(Pod.objects.filter(id=child_id).exists())

    def test_invalid_color_validation(self):
        """Test color validation."""
        pod = Pod(name="Invalid", color="invalid-color")
        with self.assertRaises(ValidationError):
            pod.full_clean()

    def test_valid_hex_colors(self):
        """Test valid hex color codes."""
        pod = Pod(name="Valid", color="#FF5733", border_color="#00FF00")
        pod.full_clean()  # Should not raise

    def test_invalid_dimensions(self):
        """Test validation for invalid dimensions."""
        pod = Pod(name="Invalid", width=-10)
        with self.assertRaises(ValidationError):
            pod.full_clean()

        pod = Pod(name="Invalid", height=0)
        with self.assertRaises(ValidationError):
            pod.full_clean()

    def test_valid_shape_choices(self):
        """Test shape choices validation."""
        oval_pod = Pod.objects.create(name="Oval", shape='oval')
        rect_pod = Pod.objects.create(name="Rect", shape='rectangle')

        self.assertEqual(oval_pod.shape, 'oval')
        self.assertEqual(rect_pod.shape, 'rectangle')

    def test_circular_parent_prevention(self):
        """Test prevention of circular parent references."""
        pod1 = Pod.objects.create(name="Pod1")
        pod2 = Pod.objects.create(name="Pod2", parent=pod1)
        pod3 = Pod.objects.create(name="Pod3", parent=pod2)

        # Try to make pod1 a child of pod3 (circular)
        pod1.parent = pod3
        with self.assertRaises(ValidationError):
            pod1.clean()


class RelationshipModelTest(TestCase):
    """Test Relationship model functionality."""

    def setUp(self):
        """Set up test data."""
        self.pod1 = Pod.objects.create(name="Pod 1", x=0, y=0)
        self.pod2 = Pod.objects.create(name="Pod 2", x=100, y=100)

    def test_create_relationship(self):
        """Test creating a relationship."""
        rel = Relationship.objects.create(
            source=self.pod1,
            target=self.pod2,
            label="connects to"
        )
        self.assertEqual(rel.source, self.pod1)
        self.assertEqual(rel.target, self.pod2)
        self.assertEqual(rel.label, "connects to")
        self.assertIsInstance(rel.id, uuid.UUID)

    def test_relationship_defaults(self):
        """Test relationship default values."""
        rel = Relationship.objects.create(
            source=self.pod1,
            target=self.pod2
        )
        self.assertEqual(rel.color, '#34495E')
        self.assertEqual(rel.line_width, 2)
        self.assertTrue(rel.arrow)
        self.assertEqual(rel.relationship_type, 'default')

    def test_relationship_str(self):
        """Test relationship string representation."""
        rel = Relationship.objects.create(
            source=self.pod1,
            target=self.pod2
        )
        self.assertIn("Pod 1", str(rel))
        self.assertIn("Pod 2", str(rel))

    def test_relationship_cascade_delete(self):
        """Test relationship deletion when pod is deleted."""
        rel = Relationship.objects.create(
            source=self.pod1,
            target=self.pod2
        )
        rel_id = rel.id

        self.pod1.delete()
        self.assertFalse(Relationship.objects.filter(id=rel_id).exists())

    def test_self_referential_prevention(self):
        """Test prevention of self-referential relationships."""
        rel = Relationship(source=self.pod1, target=self.pod1)
        with self.assertRaises(ValidationError):
            rel.clean()

    def test_invalid_line_width(self):
        """Test line width validation."""
        rel = Relationship(
            source=self.pod1,
            target=self.pod2,
            line_width=0
        )
        with self.assertRaises(ValidationError):
            rel.full_clean()

        rel.line_width = 100
        with self.assertRaises(ValidationError):
            rel.full_clean()

    def test_valid_relationship_properties(self):
        """Test valid relationship properties."""
        rel = Relationship.objects.create(
            source=self.pod1,
            target=self.pod2,
            label="Test",
            color="#FF0000",
            line_width=5,
            arrow=False
        )
        self.assertEqual(rel.color, "#FF0000")
        self.assertEqual(rel.line_width, 5)
        self.assertFalse(rel.arrow)
