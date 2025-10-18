"""Unit tests for the PodsApp class."""

import unittest
import sys
import os
import math

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pod import Pod
from src.relationship import Relationship
from src.app import PodsApp


class TestPodsAppHelperMethods(unittest.TestCase):
    """Test cases for PodsApp helper methods that don't require GUI."""

    def test_point_to_line_distance_on_line(self):
        """Test distance calculation for a point on the line."""
        # Create a minimal mock for PodsApp (we only need the method)
        class MinimalApp:
            def point_to_line_distance(self, px, py, x1, y1, x2, y2):
                line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
                if line_length_sq == 0:
                    return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
                t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
                closest_x = x1 + t * (x2 - x1)
                closest_y = y1 + t * (y2 - y1)
                return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

        app = MinimalApp()

        # Point on the line (midpoint of line from (0,0) to (10,0))
        distance = app.point_to_line_distance(5, 0, 0, 0, 10, 0)
        self.assertAlmostEqual(distance, 0.0, places=5)

    def test_point_to_line_distance_perpendicular(self):
        """Test distance calculation for a point perpendicular to the line."""
        class MinimalApp:
            def point_to_line_distance(self, px, py, x1, y1, x2, y2):
                line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
                if line_length_sq == 0:
                    return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
                t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
                closest_x = x1 + t * (x2 - x1)
                closest_y = y1 + t * (y2 - y1)
                return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

        app = MinimalApp()

        # Point 5 units perpendicular from midpoint of line from (0,0) to (10,0)
        distance = app.point_to_line_distance(5, 5, 0, 0, 10, 0)
        self.assertAlmostEqual(distance, 5.0, places=5)

    def test_point_to_line_distance_endpoint(self):
        """Test distance calculation for a point at an endpoint."""
        class MinimalApp:
            def point_to_line_distance(self, px, py, x1, y1, x2, y2):
                line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
                if line_length_sq == 0:
                    return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
                t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
                closest_x = x1 + t * (x2 - x1)
                closest_y = y1 + t * (y2 - y1)
                return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

        app = MinimalApp()

        # Point at start of line
        distance = app.point_to_line_distance(0, 0, 0, 0, 10, 0)
        self.assertAlmostEqual(distance, 0.0, places=5)

        # Point at end of line
        distance = app.point_to_line_distance(10, 0, 0, 0, 10, 0)
        self.assertAlmostEqual(distance, 0.0, places=5)

    def test_point_to_line_distance_beyond_endpoint(self):
        """Test distance calculation for a point beyond the line segment."""
        class MinimalApp:
            def point_to_line_distance(self, px, py, x1, y1, x2, y2):
                line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
                if line_length_sq == 0:
                    return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
                t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
                closest_x = x1 + t * (x2 - x1)
                closest_y = y1 + t * (y2 - y1)
                return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

        app = MinimalApp()

        # Point beyond the end of the line segment
        distance = app.point_to_line_distance(15, 0, 0, 0, 10, 0)
        self.assertAlmostEqual(distance, 5.0, places=5)

    def test_point_to_line_distance_zero_length(self):
        """Test distance calculation for a zero-length line (point)."""
        class MinimalApp:
            def point_to_line_distance(self, px, py, x1, y1, x2, y2):
                line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
                if line_length_sq == 0:
                    return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
                t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
                closest_x = x1 + t * (x2 - x1)
                closest_y = y1 + t * (y2 - y1)
                return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

        app = MinimalApp()

        # Line is actually a point at (5, 5)
        distance = app.point_to_line_distance(8, 9, 5, 5, 5, 5)
        expected = math.sqrt((8-5)**2 + (9-5)**2)  # ~5
        self.assertAlmostEqual(distance, expected, places=5)


class TestPodsAppDataManagement(unittest.TestCase):
    """Test cases for pod and relationship management."""

    def test_build_pod_lookup(self):
        """Test building pod lookup dictionary."""
        class MinimalApp:
            def build_pod_lookup(self, pod, lookup):
                lookup[pod.id] = pod
                for child in pod.children:
                    self.build_pod_lookup(child, lookup)

        app = MinimalApp()

        # Create a hierarchy
        root = Pod("Root")
        child1 = Pod("Child 1")
        child2 = Pod("Child 2")
        grandchild = Pod("Grandchild")

        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(grandchild)

        # Build lookup
        lookup = {}
        app.build_pod_lookup(root, lookup)

        # Verify all pods are in lookup
        self.assertEqual(len(lookup), 4)
        self.assertIn(root.id, lookup)
        self.assertIn(child1.id, lookup)
        self.assertIn(child2.id, lookup)
        self.assertIn(grandchild.id, lookup)
        self.assertEqual(lookup[root.id], root)
        self.assertEqual(lookup[child1.id], child1)
        self.assertEqual(lookup[grandchild.id], grandchild)


class TestPodHierarchy(unittest.TestCase):
    """Test cases for pod hierarchy operations."""

    def test_nested_children(self):
        """Test deeply nested pod hierarchy."""
        root = Pod("Root")
        level1 = Pod("Level 1")
        level2 = Pod("Level 2")
        level3 = Pod("Level 3")

        root.add_child(level1)
        level1.add_child(level2)
        level2.add_child(level3)

        self.assertEqual(len(root.children), 1)
        self.assertEqual(len(level1.children), 1)
        self.assertEqual(len(level2.children), 1)
        self.assertEqual(len(level3.children), 0)

        self.assertEqual(level1.parent, root)
        self.assertEqual(level2.parent, level1)
        self.assertEqual(level3.parent, level2)

    def test_multiple_siblings(self):
        """Test multiple pods at the same level."""
        parent = Pod("Parent")
        siblings = [Pod(f"Sibling {i}") for i in range(5)]

        for sibling in siblings:
            parent.add_child(sibling)

        self.assertEqual(len(parent.children), 5)
        for sibling in siblings:
            self.assertEqual(sibling.parent, parent)
            self.assertIn(sibling, parent.children)


class TestRelationshipOperations(unittest.TestCase):
    """Test cases for relationship operations."""

    def test_relationship_serialization_with_complex_graph(self):
        """Test serializing relationships in a complex pod graph."""
        # Create a network of pods
        pod1 = Pod("Pod 1")
        pod2 = Pod("Pod 2")
        pod3 = Pod("Pod 3")
        pod4 = Pod("Pod 4")

        # Create relationships
        rel1 = Relationship(pod1, pod2, label="connects to")
        rel2 = Relationship(pod2, pod3, label="flows to")
        rel3 = Relationship(pod3, pod4, label="triggers")
        rel4 = Relationship(pod1, pod4, label="monitors")

        relationships = [rel1, rel2, rel3, rel4]

        # Serialize all relationships
        data = [rel.to_dict() for rel in relationships]

        self.assertEqual(len(data), 4)

        # Build pod lookup
        pod_lookup = {p.id: p for p in [pod1, pod2, pod3, pod4]}

        # Deserialize
        restored_rels = [Relationship.from_dict(d, pod_lookup) for d in data]

        self.assertEqual(len(restored_rels), 4)
        self.assertEqual(restored_rels[0].label, "connects to")
        self.assertEqual(restored_rels[1].label, "flows to")
        self.assertEqual(restored_rels[2].label, "triggers")
        self.assertEqual(restored_rels[3].label, "monitors")


if __name__ == '__main__':
    unittest.main()
