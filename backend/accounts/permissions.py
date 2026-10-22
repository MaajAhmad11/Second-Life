from rest_framework import permissions


class IsAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (
                request.user.role == "ADMIN" or
                request.user.is_staff or
                request.user.is_superuser
            )
        )


class IsDonor(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (
                request.user.role in ["DONOR", "ADMIN"] or
                request.user.is_staff or
                request.user.is_superuser
            )
        )


class IsReceiver(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (
                request.user.role in ["RECEIVER", "ADMIN"] or
                request.user.is_staff or
                request.user.is_superuser
            )
        )


class IsOwnerOrAdmin(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        if not request.user or not request.user.is_authenticated:
            return False

        if (
            request.user.role == "ADMIN" or
            request.user.is_staff or
            request.user.is_superuser
        ):
            return True

        if hasattr(obj, "user"):
            return obj.user == request.user

        if hasattr(obj, "donor"):
            return obj.donor == request.user

        if hasattr(obj, "receiver"):
            return obj.receiver == request.user

        return False