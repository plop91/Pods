"""Admin configuration for Pods application."""

from django.contrib import admin
from .models import Pod, Relationship


@admin.register(Pod)
class PodAdmin(admin.ModelAdmin):
    list_display = ('name', 'shape', 'x', 'y', 'parent', 'created_at')
    list_filter = ('shape', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    list_display = ('source', 'target', 'label', 'relationship_type', 'created_at')
    list_filter = ('relationship_type', 'created_at')
    search_fields = ('label', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
