"""Views for Pods application."""

from django.shortcuts import render
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Pod, Relationship
from .serializers import PodSerializer, PodSimpleSerializer, RelationshipSerializer
import logging

logger = logging.getLogger(__name__)


def index(request):
    """Main application view."""
    return render(request, 'pods_app/index.html')


class PodViewSet(viewsets.ModelViewSet):
    """API endpoints for Pod CRUD operations."""

    queryset = Pod.objects.all()
    serializer_class = PodSimpleSerializer

    def get_queryset(self):
        """Optionally filter pods by parent. Optimized to prevent N+1 queries."""
        queryset = Pod.objects.select_related('parent').prefetch_related('children')
        parent_id = self.request.query_params.get('parent', None)

        if parent_id == 'null' or parent_id == 'None':
            # Get root pods (no parent)
            queryset = queryset.filter(parent__isnull=True)
        elif parent_id:
            try:
                # Get children of specific parent
                queryset = queryset.filter(parent__id=parent_id)
            except (ValueError, DjangoValidationError) as e:
                logger.warning(f'Invalid parent_id: {parent_id}')
                queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """Create pod with validation."""
        try:
            instance = serializer.save()
            instance.full_clean()  # Trigger model validation
        except DjangoValidationError as e:
            raise ValidationError(detail=e.message_dict)

    def perform_update(self, serializer):
        """Update pod with validation."""
        try:
            instance = serializer.save()
            instance.full_clean()  # Trigger model validation
        except DjangoValidationError as e:
            raise ValidationError(detail=e.message_dict)

    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Get a pod with all its children recursively. Optimized with prefetch."""
        try:
            # Prefetch all children to avoid N+1 queries
            pod = Pod.objects.prefetch_related('children').get(pk=pk)
            serializer = PodSerializer(pod)
            return Response(serializer.data)
        except Pod.DoesNotExist:
            return Response(
                {'error': 'Pod not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get all children of a pod."""
        try:
            pod = self.get_object()
            children = pod.children.all()
            serializer = PodSimpleSerializer(children, many=True)
            return Response(serializer.data)
        except Pod.DoesNotExist:
            return Response(
                {'error': 'Pod not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def root(self, request):
        """Get or create the root 'Main' pod. Optimized with caching."""
        try:
            root_pod, created = Pod.objects.prefetch_related('children').get_or_create(
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
        except Exception as e:
            logger.error(f'Error getting/creating root pod: {e}')
            return Response(
                {'error': 'Failed to get root pod'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move a pod to a new position with validation."""
        try:
            pod = self.get_object()

            # Validate and get coordinates
            try:
                x = float(request.data.get('x', pod.x))
                y = float(request.data.get('y', pod.y))
            except (TypeError, ValueError):
                return Response(
                    {'error': 'Invalid coordinates. Must be numbers.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            pod.x = x
            pod.y = y
            pod.save()
            serializer = PodSimpleSerializer(pod)
            return Response(serializer.data)

        except Pod.DoesNotExist:
            return Response(
                {'error': 'Pod not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f'Error moving pod {pk}: {e}')
            return Response(
                {'error': 'Failed to move pod'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def update_visual(self, request, pk=None):
        """Update visual properties of a pod with validation."""
        try:
            pod = self.get_object()

            if 'color' in request.data:
                pod.color = request.data['color']
            if 'border_color' in request.data:
                pod.border_color = request.data['border_color']
            if 'text_color' in request.data:
                pod.text_color = request.data['text_color']
            if 'shape' in request.data:
                if request.data['shape'] not in ['oval', 'rectangle']:
                    return Response(
                        {'error': 'Shape must be "oval" or "rectangle"'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                pod.shape = request.data['shape']

            try:
                pod.full_clean()  # Validate before saving
                pod.save()
            except DjangoValidationError as e:
                return Response(
                    {'error': e.message_dict},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = PodSimpleSerializer(pod)
            return Response(serializer.data)

        except Pod.DoesNotExist:
            return Response(
                {'error': 'Pod not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f'Error updating pod visual {pk}: {e}')
            return Response(
                {'error': 'Failed to update pod'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RelationshipViewSet(viewsets.ModelViewSet):
    """API endpoints for Relationship CRUD operations."""

    queryset = Relationship.objects.all()
    serializer_class = RelationshipSerializer

    def get_queryset(self):
        """Optionally filter relationships by container. Optimized to prevent N+1."""
        # Prefetch related pods to avoid N+1 queries
        queryset = Relationship.objects.select_related('source', 'target')
        container_id = self.request.query_params.get('container', None)

        if container_id:
            try:
                # Get relationships where both source and target are in the container
                queryset = queryset.filter(
                    source__parent__id=container_id,
                    target__parent__id=container_id
                )
            except (ValueError, DjangoValidationError) as e:
                logger.warning(f'Invalid container_id: {container_id}')
                queryset = queryset.none()

        return queryset

    def perform_create(self, serializer):
        """Create relationship with validation."""
        try:
            instance = serializer.save()
            instance.full_clean()  # Trigger model validation
        except DjangoValidationError as e:
            raise ValidationError(detail=e.message_dict)

    def perform_update(self, serializer):
        """Update relationship with validation."""
        try:
            instance = serializer.save()
            instance.full_clean()  # Trigger model validation
        except DjangoValidationError as e:
            raise ValidationError(detail=e.message_dict)

    @action(detail=False, methods=['get'])
    def for_pods(self, request):
        """Get all relationships involving specific pods."""
        pod_ids = request.query_params.getlist('pod_ids[]')
        if not pod_ids:
            return Response([])

        try:
            relationships = Relationship.objects.select_related('source', 'target').filter(
                source__id__in=pod_ids
            ) | Relationship.objects.select_related('source', 'target').filter(
                target__id__in=pod_ids
            )

            serializer = RelationshipSerializer(relationships, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f'Error getting relationships for pods: {e}')
            return Response(
                {'error': 'Failed to get relationships'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
