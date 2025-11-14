"""Views for Pods application."""

from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Pod, Relationship
from .serializers import PodSerializer, PodSimpleSerializer, RelationshipSerializer


def index(request):
    """Main application view."""
    return render(request, 'pods_app/index.html')


class PodViewSet(viewsets.ModelViewSet):
    """API endpoints for Pod CRUD operations."""

    queryset = Pod.objects.all()
    serializer_class = PodSimpleSerializer

    def get_queryset(self):
        """Optionally filter pods by parent."""
        queryset = Pod.objects.all()
        parent_id = self.request.query_params.get('parent', None)

        if parent_id == 'null' or parent_id == 'None':
            # Get root pods (no parent)
            queryset = queryset.filter(parent__isnull=True)
        elif parent_id:
            # Get children of specific parent
            queryset = queryset.filter(parent__id=parent_id)

        return queryset

    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Get a pod with all its children recursively."""
        pod = self.get_object()
        serializer = PodSerializer(pod)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get all children of a pod."""
        pod = self.get_object()
        children = pod.children.all()
        serializer = PodSimpleSerializer(children, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def root(self, request):
        """Get or create the root 'Main' pod."""
        root_pod, created = Pod.objects.get_or_create(
            name='Main',
            parent__isnull=True,
            defaults={
                'x': 0,
                'y': 0,
                'width': 0,
                'height': 0,
                'shape': 'rectangle'
            }
        )
        serializer = PodSerializer(root_pod)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move a pod to a new position."""
        pod = self.get_object()
        pod.x = request.data.get('x', pod.x)
        pod.y = request.data.get('y', pod.y)
        pod.save()
        serializer = PodSimpleSerializer(pod)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_visual(self, request, pk=None):
        """Update visual properties of a pod."""
        pod = self.get_object()

        if 'color' in request.data:
            pod.color = request.data['color']
        if 'border_color' in request.data:
            pod.border_color = request.data['border_color']
        if 'text_color' in request.data:
            pod.text_color = request.data['text_color']
        if 'shape' in request.data:
            pod.shape = request.data['shape']

        pod.save()
        serializer = PodSimpleSerializer(pod)
        return Response(serializer.data)


class RelationshipViewSet(viewsets.ModelViewSet):
    """API endpoints for Relationship CRUD operations."""

    queryset = Relationship.objects.all()
    serializer_class = RelationshipSerializer

    def get_queryset(self):
        """Optionally filter relationships by container."""
        queryset = Relationship.objects.all()
        container_id = self.request.query_params.get('container', None)

        if container_id:
            # Get relationships where both source and target are in the container
            queryset = queryset.filter(
                source__parent__id=container_id,
                target__parent__id=container_id
            )

        return queryset

    @action(detail=False, methods=['get'])
    def for_pods(self, request):
        """Get all relationships involving specific pods."""
        pod_ids = request.query_params.getlist('pod_ids[]')
        if not pod_ids:
            return Response([])

        relationships = Relationship.objects.filter(
            source__id__in=pod_ids
        ) | Relationship.objects.filter(
            target__id__in=pod_ids
        )

        serializer = RelationshipSerializer(relationships, many=True)
        return Response(serializer.data)
