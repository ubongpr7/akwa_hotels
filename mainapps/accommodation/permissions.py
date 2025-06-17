"""
Accommodation Microservice Permissions
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.created_by_id == str(request.user.id)


class IsProfileMember(permissions.BasePermission):
    """
    Custom permission to only allow profile members to access objects.
    """
    
    def has_permission(self, request, view):
        # Check if user has a profile ID in headers
        profile_id = request.headers.get('X-Profile-ID')
        return profile_id is not None
    
    def has_object_permission(self, request, view, obj):
        # Check if object belongs to the user's profile
        profile_id = request.headers.get('X-Profile-ID')
        return obj.profile_id == profile_id
