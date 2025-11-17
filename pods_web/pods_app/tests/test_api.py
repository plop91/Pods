"""Tests for Pods API endpoints."""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from pods_app.models import Pod, Relationship


class PodAPITest(TestCase):
    """Test Pod API endpoints."""

    def setUp(self):
        """Set up test client and data."""
        self.client = APIClient()
        self.pod1 = Pod.objects.create(
            name="Test Pod 1",
            x=100,
            y=200,
            width=150,
            height=100
        )
        self.pod2 = Pod.objects.create(
            name="Test Pod 2",
            x=300,
            y=400
        )

    def test_list_pods(self):
        """Test listing all pods."""
        response = self.client.get('/api/pods/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)  # Paginated response

    def test_create_pod(self):
        """Test creating a new pod."""
        data = {
            'name': 'New Pod',
            'x': 50,
            'y': 75,
            'width': 100,
            'height': 60,
            'shape': 'oval'
        }
        response = self.client.post('/api/pods/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Pod')
        self.assertEqual(response.data['x'], 50)

    def test_create_pod_with_invalid_color(self):
        """Test validation of invalid color."""
        data = {
            'name': 'Bad Color',
            'color': 'not-a-hex-color'
        }
        response = self.client.post('/api/pods/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_pod_with_invalid_dimensions(self):
        """Test validation of invalid dimensions."""
        data = {
            'name': 'Bad Dimensions',
            'width': -10
        }
        response = self.client.post('/api/pods/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_pod(self):
        """Test retrieving a specific pod."""
        response = self.client.get(f'/api/pods/{self.pod1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Pod 1')

    def test_update_pod(self):
        """Test updating a pod."""
        data = {'name': 'Updated Name'}
        response = self.client.patch(
            f'/api/pods/{self.pod1.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Name')

    def test_delete_pod(self):
        """Test deleting a pod."""
        pod_id = self.pod1.id
        response = self.client.delete(f'/api/pods/{pod_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Pod.objects.filter(id=pod_id).exists())

    def test_get_root_pod(self):
        """Test getting or creating root pod."""
        response = self.client.get('/api/pods/root/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Main')

    def test_filter_pods_by_parent(self):
        """Test filtering pods by parent."""
        parent = Pod.objects.create(name="Parent")
        child1 = Pod.objects.create(name="Child 1", parent=parent)
        child2 = Pod.objects.create(name="Child 2", parent=parent)

        response = self.client.get(f'/api/pods/?parent={parent.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)

    def test_get_pod_children(self):
        """Test getting children of a pod."""
        parent = Pod.objects.create(name="Parent")
        child = Pod.objects.create(name="Child", parent=parent)

        response = self.client.get(f'/api/pods/{parent.id}/children/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Child')

    def test_move_pod(self):
        """Test moving a pod."""
        data = {'x': 500, 'y': 600}
        response = self.client.post(
            f'/api/pods/{self.pod1.id}/move/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['x'], 500)
        self.assertEqual(response.data['y'], 600)

    def test_move_pod_invalid_coordinates(self):
        """Test moving pod with invalid coordinates."""
        data = {'x': 'not-a-number'}
        response = self.client.post(
            f'/api/pods/{self.pod1.id}/move/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_visual_properties(self):
        """Test updating pod visual properties."""
        data = {
            'color': '#FF5733',
            'shape': 'rectangle'
        }
        response = self.client.post(
            f'/api/pods/{self.pod1.id}/update_visual/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['color'], '#FF5733')
        self.assertEqual(response.data['shape'], 'rectangle')

    def test_update_visual_invalid_shape(self):
        """Test validation of invalid shape."""
        data = {'shape': 'triangle'}  # Invalid
        response = self.client.post(
            f'/api/pods/{self.pod1.id}/update_visual/',
            data,
            format='json'
        )
        self.assertEqual(response.status.HTTP_400_BAD_REQUEST)


class RelationshipAPITest(TestCase):
    """Test Relationship API endpoints."""

    def setUp(self):
        """Set up test client and data."""
        self.client = APIClient()
        self.pod1 = Pod.objects.create(name="Pod 1", x=0, y=0)
        self.pod2 = Pod.objects.create(name="Pod 2", x=100, y=100)
        self.rel = Relationship.objects.create(
            source=self.pod1,
            target=self.pod2,
            label="test"
        )

    def test_list_relationships(self):
        """Test listing all relationships."""
        response = self.client.get('/api/relationships/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_create_relationship(self):
        """Test creating a new relationship."""
        pod3 = Pod.objects.create(name="Pod 3")
        data = {
            'source': str(self.pod1.id),
            'target': str(pod3.id),
            'label': 'connects'
        }
        response = self.client.post('/api/relationships/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['label'], 'connects')

    def test_create_self_referential_relationship(self):
        """Test prevention of self-referential relationships."""
        data = {
            'source': str(self.pod1.id),
            'target': str(self.pod1.id)
        }
        response = self.client.post('/api/relationships/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_relationship(self):
        """Test retrieving a specific relationship."""
        response = self.client.get(f'/api/relationships/{self.rel.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['label'], 'test')

    def test_update_relationship(self):
        """Test updating a relationship."""
        data = {'label': 'updated'}
        response = self.client.patch(
            f'/api/relationships/{self.rel.id}/',
            data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['label'], 'updated')

    def test_delete_relationship(self):
        """Test deleting a relationship."""
        rel_id = self.rel.id
        response = self.client.delete(f'/api/relationships/{rel_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Relationship.objects.filter(id=rel_id).exists())

    def test_filter_relationships_by_container(self):
        """Test filtering relationships by container."""
        container = Pod.objects.create(name="Container")
        pod_in = Pod.objects.create(name="In Container", parent=container)
        pod_in2 = Pod.objects.create(name="In Container 2", parent=container)
        rel_in = Relationship.objects.create(source=pod_in, target=pod_in2)

        response = self.client.get(f'/api/relationships/?container={container.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertTrue(any(r['id'] == str(rel_in.id) for r in results))


class RateLimitingTest(TestCase):
    """Test API rate limiting."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    def test_rate_limiting_enforced(self):
        """Test that rate limiting is enforced."""
        # Make many requests rapidly
        responses = []
        for i in range(150):  # More than 100/hour limit
            response = self.client.get('/api/pods/')
            responses.append(response.status_code)

        # Should eventually get rate limited
        self.assertIn(status.HTTP_429_TOO_MANY_REQUESTS, responses)
