"""Unit tests for the Relationship class."""

import unittest
import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pod import Pod
from src.relationship import Relationship


class TestRelationship(unittest.TestCase):
    """Test cases for the Relationship class."""

    def setUp(self):
        """Set up test fixtures."""
        self.pod1 = Pod("Pod 1", x=0, y=0)
        self.pod2 = Pod("Pod 2", x=100, y=100)
        self.container = Pod("Container", x=0, y=0)

    def test_relationship_creation(self):
        """Test basic relationship creation."""
        rel = Relationship(self.pod1, self.pod2, label="connects to")

        self.assertEqual(rel.source, self.pod1)
        self.assertEqual(rel.target, self.pod2)
        self.assertEqual(rel.label, "connects to")
        self.assertEqual(rel.relationship_type, "default")

    def test_relationship_has_unique_id(self):
        """Test that each relationship gets a unique ID."""
        rel1 = Relationship(self.pod1, self.pod2)
        rel2 = Relationship(self.pod1, self.pod2)

        self.assertNotEqual(rel1.id, rel2.id)
        self.assertIsInstance(rel1.id, str)

    def test_relationship_with_custom_type(self):
        """Test creating relationship with custom type."""
        rel = Relationship(
            self.pod1,
            self.pod2,
            label="owns",
            relationship_type="ownership"
        )

        self.assertEqual(rel.label, "owns")
        self.assertEqual(rel.relationship_type, "ownership")

    def test_get_endpoints(self):
        """Test getting relationship endpoints."""
        rel = Relationship(self.pod1, self.pod2)
        x1, y1, x2, y2 = rel.get_endpoints()

        self.assertEqual(x1, 0)
        self.assertEqual(y1, 0)
        self.assertEqual(x2, 100)
        self.assertEqual(y2, 100)

    def test_is_external_both_in_container(self):
        """Test is_external when both pods are in the same container."""
        self.container.add_child(self.pod1)
        self.container.add_child(self.pod2)

        rel = Relationship(self.pod1, self.pod2)

        self.assertFalse(rel.is_external(self.container))

    def test_is_external_source_outside(self):
        """Test is_external when source is outside container."""
        other_container = Pod("Other Container")
        other_container.add_child(self.pod1)
        self.container.add_child(self.pod2)

        rel = Relationship(self.pod1, self.pod2)

        self.assertTrue(rel.is_external(self.container))

    def test_is_external_target_outside(self):
        """Test is_external when target is outside container."""
        other_container = Pod("Other Container")
        self.container.add_child(self.pod1)
        other_container.add_child(self.pod2)

        rel = Relationship(self.pod1, self.pod2)

        self.assertTrue(rel.is_external(self.container))

    def test_is_external_both_outside(self):
        """Test is_external when both pods are outside container."""
        other_container = Pod("Other Container")
        other_container.add_child(self.pod1)
        other_container.add_child(self.pod2)

        rel = Relationship(self.pod1, self.pod2)

        self.assertTrue(rel.is_external(self.container))

    def test_to_dict(self):
        """Test serialization to dictionary."""
        rel = Relationship(
            self.pod1,
            self.pod2,
            label="manages",
            relationship_type="management"
        )
        rel.description = "Test description"

        data = rel.to_dict()

        self.assertEqual(data["source_id"], self.pod1.id)
        self.assertEqual(data["target_id"], self.pod2.id)
        self.assertEqual(data["label"], "manages")
        self.assertEqual(data["relationship_type"], "management")
        self.assertEqual(data["description"], "Test description")
        self.assertEqual(data["color"], "#34495E")
        self.assertEqual(data["line_width"], 2)
        self.assertTrue(data["arrow"])

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        pod_lookup = {
            self.pod1.id: self.pod1,
            self.pod2.id: self.pod2
        }

        data = {
            "id": "test-rel-id",
            "source_id": self.pod1.id,
            "target_id": self.pod2.id,
            "label": "connects to",
            "relationship_type": "connection",
            "description": "Test description",
            "color": "#FF0000",
            "line_width": 3,
            "arrow": False
        }

        rel = Relationship.from_dict(data, pod_lookup)

        self.assertEqual(rel.id, "test-rel-id")
        self.assertEqual(rel.source, self.pod1)
        self.assertEqual(rel.target, self.pod2)
        self.assertEqual(rel.label, "connects to")
        self.assertEqual(rel.relationship_type, "connection")
        self.assertEqual(rel.description, "Test description")
        self.assertEqual(rel.color, "#FF0000")
        self.assertEqual(rel.line_width, 3)
        self.assertFalse(rel.arrow)

    def test_from_dict_with_defaults(self):
        """Test deserialization with missing optional fields."""
        pod_lookup = {
            self.pod1.id: self.pod1,
            self.pod2.id: self.pod2
        }

        data = {
            "id": "test-rel-id",
            "source_id": self.pod1.id,
            "target_id": self.pod2.id
        }

        rel = Relationship.from_dict(data, pod_lookup)

        self.assertEqual(rel.label, "")
        self.assertEqual(rel.relationship_type, "default")
        self.assertEqual(rel.description, "")
        self.assertEqual(rel.color, "#34495E")
        self.assertEqual(rel.line_width, 2)
        self.assertTrue(rel.arrow)

    def test_roundtrip_serialization(self):
        """Test that serializing and deserializing preserves data."""
        original = Relationship(
            self.pod1,
            self.pod2,
            label="owns",
            relationship_type="ownership"
        )
        original.description = "Test description"
        original.color = "#00FF00"
        original.line_width = 4
        original.arrow = False

        # Serialize
        data = original.to_dict()

        # Create pod lookup
        pod_lookup = {
            self.pod1.id: self.pod1,
            self.pod2.id: self.pod2
        }

        # Deserialize
        restored = Relationship.from_dict(data, pod_lookup)

        self.assertEqual(restored.source, original.source)
        self.assertEqual(restored.target, original.target)
        self.assertEqual(restored.label, original.label)
        self.assertEqual(restored.relationship_type, original.relationship_type)
        self.assertEqual(restored.description, original.description)
        self.assertEqual(restored.color, original.color)
        self.assertEqual(restored.line_width, original.line_width)
        self.assertEqual(restored.arrow, original.arrow)

    def test_visual_properties(self):
        """Test that relationships have visual properties initialized."""
        rel = Relationship(self.pod1, self.pod2)

        self.assertIsNotNone(rel.color)
        self.assertEqual(rel.line_width, 2)
        self.assertTrue(rel.arrow)
        self.assertFalse(rel.selected)
        self.assertFalse(rel.hovered)

    def test_description_property(self):
        """Test description property."""
        rel = Relationship(self.pod1, self.pod2)

        self.assertEqual(rel.description, "")

        rel.description = "New description"
        self.assertEqual(rel.description, "New description")

    def test_repr(self):
        """Test string representation."""
        rel = Relationship(self.pod1, self.pod2, label="connects")

        repr_str = repr(rel)

        self.assertIn("Pod 1", repr_str)
        self.assertIn("Pod 2", repr_str)
        self.assertIn("connects", repr_str)


if __name__ == '__main__':
    unittest.main()
