"""
Custom DRF permission classes for College Student Management System.
Enforces role-based permissions at the view and object levels.
"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Grants access only to users with the 'admin' role or Django superusers.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == 'admin' or request.user.is_superuser)
        )


class IsTeacher(permissions.BasePermission):
    """
    Grants access only to users with the 'teacher' role.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'teacher'
        )


class IsStudent(permissions.BasePermission):
    """
    Grants access only to users with the 'student' role.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'student'
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access for authenticated users, but restricts write
    operations (POST, PUT, PATCH, DELETE) to Admin users.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user.role == 'admin' or request.user.is_superuser)


class StudentPermission(permissions.BasePermission):
    """
    Permission rules for Student endpoints:
    - Admin: full CRUD.
    - Teacher: read-only access to all students.
    - Student: read-only access ONLY to their own student profile.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Only Admin can create new student records
        if request.method == 'POST':
            return bool(request.user.role == 'admin' or request.user.is_superuser)

        return True

    def has_object_permission(self, request, view, obj):
        # Admin has full access (read and write)
        if request.user.role == 'admin' or request.user.is_superuser:
            return True

        # Teacher has read-only access to any student
        if request.user.role == 'teacher' and request.method in permissions.SAFE_METHODS:
            return True

        # Student has read-only access ONLY to their own student record
        if request.user.role == 'student' and request.method in permissions.SAFE_METHODS:
            return obj.user == request.user

        # All other write attempts by non-admins are forbidden
        return False


class SubjectPermission(permissions.BasePermission):
    """
    Permission rules for Subject endpoints:
    - Any authenticated user can view subjects (SAFE_METHODS).
    - Only Admin can create, update, or delete subjects.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user.role == 'admin' or request.user.is_superuser)


class GradePermission(permissions.BasePermission):
    """
    Permission rules for Grade endpoints:
    - Read: Admin & Teacher can view all; Student can view only their own grades.
    - Create: Admin, or Teacher assigned to the subject of the grade.
    - Update/Delete: Admin, or Teacher assigned to the subject of the grade.
    - Student: No write access.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        # Read operations allowed for authenticated (queryset handles row-level isolation)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Students cannot create/modify grades
        if request.user.role == 'student':
            return False

        # Admin and Teacher can attempt write (Teacher subject assignment checked in serializer/object perm)
        return True

    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin' or request.user.is_superuser:
            return True

        # Teacher can read any grade, but can only modify grades for their assigned subject
        if request.user.role == 'teacher':
            if request.method in permissions.SAFE_METHODS:
                return True
            return obj.subject.instructor == request.user

        # Student can only read their own grade
        if request.user.role == 'student':
            if request.method in permissions.SAFE_METHODS:
                return obj.student.user == request.user
            return False

        return False
