"""Serializers for Pods API."""

from rest_framework import serializers
from .models import Pod, Relationship


class PodSerializer(serializers.ModelSerializer):
    """Serializer for Pod model with recursive children."""

    children = serializers.SerializerMethodField()
    parent_id = serializers.UUIDField(source='parent.id', read_only=True, allow_null=True)

    class Meta:
        model = Pod
        fields = [
            'id', 'name', 'description', 'has_description',
            'x', 'y', 'width', 'height', 'shape',
            'color', 'border_color', 'text_color',
            'parent', 'parent_id', 'children',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_children(self, obj):
        """Recursively serialize children pods."""
        children = obj.children.all()
        return PodSerializer(children, many=True).data


class PodSimpleSerializer(serializers.ModelSerializer):
    """Simple Pod serializer without recursive children (for performance)."""

    parent_id = serializers.UUIDField(source='parent.id', read_only=True, allow_null=True)

    class Meta:
        model = Pod
        fields = [
            'id', 'name', 'description', 'has_description',
            'x', 'y', 'width', 'height', 'shape',
            'color', 'border_color', 'text_color',
            'parent', 'parent_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RelationshipSerializer(serializers.ModelSerializer):
    """Serializer for Relationship model."""

    source_name = serializers.CharField(source='source.name', read_only=True)
    target_name = serializers.CharField(source='target.name', read_only=True)

    class Meta:
        model = Relationship
        fields = [
            'id', 'source', 'source_name', 'target', 'target_name',
            'label', 'relationship_type', 'description',
            'color', 'line_width', 'arrow',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
