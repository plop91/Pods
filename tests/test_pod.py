"""Unit tests for the Pod class."""

import unittest
import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pod import Pod


class TestPod(unittest.TestCase):
    """Test cases for the Pod class."""

    def test_pod_creation(self):
        """Test basic pod creation with default parameters."""
        pod = Pod("Test Pod")
        self.assertEqual(pod.name, "Test Pod")
        self.assertEqual(pod.x, 0)
        self.assertEqual(pod.y, 0)
        self.assertEqual(pod.width, 100)
        self.assertEqual(pod.height, 60)
        self.assertEqual(pod.shape, "oval")
        self.assertIsNone(pod.parent)
        self.assertEqual(len(pod.children), 0)

    def test_pod_creation_with_parameters(self):
        """Test pod creation with custom parameters."""
        pod = Pod("Custom Pod", x=100, y=200, width=150, height=80, shape="rectangle")
        self.assertEqual(pod.name, "Custom Pod")
        self.assertEqual(pod.x, 100)
        self.assertEqual(pod.y, 200)
        self.assertEqual(pod.width, 150)
        self.assertEqual(pod.height, 80)
        self.assertEqual(pod.shape, "rectangle")

    def test_pod_has_unique_id(self):
        """Test that each pod gets a unique ID."""
        pod1 = Pod("Pod 1")
        pod2 = Pod("Pod 2")
        self.assertNotEqual(pod1.id, pod2.id)
        self.assertIsInstance(pod1.id, str)

    def test_add_child(self):
        """Test adding a child pod."""
        parent = Pod("Parent")
        child = Pod("Child")

        parent.add_child(child)

        self.assertEqual(len(parent.children), 1)
        self.assertIn(child, parent.children)
        self.assertEqual(child.parent, parent)

    def test_add_multiple_children(self):
        """Test adding multiple child pods."""
        parent = Pod("Parent")
        child1 = Pod("Child 1")
        child2 = Pod("Child 2")
        child3 = Pod("Child 3")

        parent.add_child(child1)
        parent.add_child(child2)
        parent.add_child(child3)

        self.assertEqual(len(parent.children), 3)
        self.assertIn(child1, parent.children)
        self.assertIn(child2, parent.children)
        self.assertIn(child3, parent.children)

    def test_add_duplicate_child(self):
        """Test that adding the same child twice doesn't duplicate it."""
        parent = Pod("Parent")
        child = Pod("Child")

        parent.add_child(child)
        parent.add_child(child)  # Try to add again

        self.assertEqual(len(parent.children), 1)

    def test_remove_child(self):
        """Test removing a child pod."""
        parent = Pod("Parent")
        child = Pod("Child")

        parent.add_child(child)
        parent.remove_child(child)

        self.assertEqual(len(parent.children), 0)
        self.assertIsNone(child.parent)

    def test_remove_nonexistent_child(self):
        """Test removing a pod that is not a child."""
        parent = Pod("Parent")
        child = Pod("Child")

        # Should not raise an error
        parent.remove_child(child)
        self.assertEqual(len(parent.children), 0)

    def test_get_bounds(self):
        """Test getting pod bounds."""
        pod = Pod("Test", x=100, y=200, width=60, height=40)
        x1, y1, x2, y2 = pod.get_bounds()

        self.assertEqual(x1, 70)   # 100 - 60/2
        self.assertEqual(y1, 180)  # 200 - 40/2
        self.assertEqual(x2, 130)  # 100 + 60/2
        self.assertEqual(y2, 220)  # 200 + 40/2

    def test_contains_point_inside(self):
        """Test point containment for a point inside the pod."""
        pod = Pod("Test", x=100, y=100, width=60, height=40)

        # Point in the center
        self.assertTrue(pod.contains_point(100, 100))

        # Points inside but not centered
        self.assertTrue(pod.contains_point(80, 90))
        self.assertTrue(pod.contains_point(120, 110))

    def test_contains_point_on_edge(self):
        """Test point containment for points on the edge."""
        pod = Pod("Test", x=100, y=100, width=60, height=40)

        # Points on the edges (should be included)
        self.assertTrue(pod.contains_point(70, 100))   # Left edge
        self.assertTrue(pod.contains_point(130, 100))  # Right edge
        self.assertTrue(pod.contains_point(100, 80))   # Top edge
        self.assertTrue(pod.contains_point(100, 120))  # Bottom edge

    def test_contains_point_outside(self):
        """Test point containment for a point outside the pod."""
        pod = Pod("Test", x=100, y=100, width=60, height=40)

        # Points clearly outside
        self.assertFalse(pod.contains_point(0, 0))
        self.assertFalse(pod.contains_point(200, 200))
        self.assertFalse(pod.contains_point(50, 100))
        self.assertFalse(pod.contains_point(150, 100))

    def test_move_to(self):
        """Test moving a pod to a new position."""
        pod = Pod("Test", x=100, y=100)

        pod.move_to(200, 300)

        self.assertEqual(pod.x, 200)
        self.assertEqual(pod.y, 300)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        pod = Pod("Test Pod", x=100, y=200, width=120, height=70, shape="rectangle")
        pod.description = "Test description"
        pod.has_description = True

        data = pod.to_dict()

        self.assertEqual(data["name"], "Test Pod")
        self.assertEqual(data["x"], 100)
        self.assertEqual(data["y"], 200)
        self.assertEqual(data["width"], 120)
        self.assertEqual(data["height"], 70)
        self.assertEqual(data["shape"], "rectangle")
        self.assertEqual(data["description"], "Test description")
        self.assertTrue(data["has_description"])
        self.assertEqual(len(data["children"]), 0)

    def test_to_dict_with_children(self):
        """Test serialization with child pods."""
        parent = Pod("Parent")
        child1 = Pod("Child 1")
        child2 = Pod("Child 2")

        parent.add_child(child1)
        parent.add_child(child2)

        data = parent.to_dict()

        self.assertEqual(len(data["children"]), 2)
        self.assertEqual(data["children"][0]["name"], "Child 1")
        self.assertEqual(data["children"][1]["name"], "Child 2")

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": "test-id-123",
            "name": "Test Pod",
            "x": 150,
            "y": 250,
            "width": 100,
            "height": 60,
            "shape": "oval",
            "description": "Test description",
            "has_description": True,
            "color": "#E8F4F8",
            "border_color": "#2C3E50",
            "text_color": "#2C3E50",
            "children": []
        }

        pod = Pod.from_dict(data)

        self.assertEqual(pod.id, "test-id-123")
        self.assertEqual(pod.name, "Test Pod")
        self.assertEqual(pod.x, 150)
        self.assertEqual(pod.y, 250)
        self.assertEqual(pod.width, 100)
        self.assertEqual(pod.height, 60)
        self.assertEqual(pod.shape, "oval")
        self.assertEqual(pod.description, "Test description")
        self.assertTrue(pod.has_description)

    def test_from_dict_with_children(self):
        """Test deserialization with nested children."""
        data = {
            "id": "parent-id",
            "name": "Parent",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 60,
            "shape": "oval",
            "description": "",
            "has_description": False,
            "color": "#E8F4F8",
            "border_color": "#2C3E50",
            "text_color": "#2C3E50",
            "children": [
                {
                    "id": "child-id",
                    "name": "Child",
                    "x": 50,
                    "y": 50,
                    "width": 80,
                    "height": 50,
                    "shape": "rectangle",
                    "description": "",
                    "has_description": False,
                    "color": "#E8F4F8",
                    "border_color": "#2C3E50",
                    "text_color": "#2C3E50",
                    "children": []
                }
            ]
        }

        pod = Pod.from_dict(data)

        self.assertEqual(len(pod.children), 1)
        self.assertEqual(pod.children[0].name, "Child")
        self.assertEqual(pod.children[0].parent, pod)
        self.assertEqual(pod.children[0].x, 50)

    def test_roundtrip_serialization(self):
        """Test that serializing and deserializing preserves data."""
        original = Pod("Test Pod", x=100, y=200, width=150, height=80)
        original.description = "Test description"
        original.has_description = True
        child = Pod("Child Pod", x=50, y=50)
        original.add_child(child)

        # Serialize
        data = original.to_dict()

        # Deserialize
        restored = Pod.from_dict(data)

        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.x, original.x)
        self.assertEqual(restored.y, original.y)
        self.assertEqual(restored.width, original.width)
        self.assertEqual(restored.height, original.height)
        self.assertEqual(restored.description, original.description)
        self.assertEqual(restored.has_description, original.has_description)
        self.assertEqual(len(restored.children), len(original.children))
        self.assertEqual(restored.children[0].name, child.name)

    def test_visual_properties(self):
        """Test that pods have visual properties initialized."""
        pod = Pod("Test")

        self.assertIsNotNone(pod.color)
        self.assertIsNotNone(pod.border_color)
        self.assertIsNotNone(pod.text_color)
        self.assertFalse(pod.selected)
        self.assertFalse(pod.hovered)

    def test_description_properties(self):
        """Test description-related properties."""
        pod = Pod("Test")

        self.assertEqual(pod.description, "")
        self.assertFalse(pod.has_description)

        pod.description = "New description"
        pod.has_description = True

        self.assertEqual(pod.description, "New description")
        self.assertTrue(pod.has_description)


if __name__ == '__main__':
    unittest.main()
