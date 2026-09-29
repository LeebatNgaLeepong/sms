"""
Teacher management views — list, create, update, delete teacher accounts.
Only accessible by Admin users.
"""

from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdmin

User = get_user_model()


class TeacherViewSet(viewsets.ViewSet):
    """
    CRUD for teacher accounts.
    List/retrieve accessible by authenticated users;
    Create/update/delete restricted to Admin.
    GET    /api/teachers/       — list all teachers
    POST   /api/teachers/       — create a teacher user
    PUT    /api/teachers/{id}/  — update a teacher
    DELETE /api/teachers/{id}/  — delete a teacher
    """

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdmin()]

    def list(self, request):
        teachers = User.objects.filter(role='teacher').order_by('username')
        data = [self._serialize(t) for t in teachers]
        return Response(data)

    def create(self, request):
        d = request.data
        username = d.get('username', '').strip()
        first_name = d.get('first_name', '').strip()
        last_name = d.get('last_name', '').strip()
        email = d.get('email', '').strip()
        password = d.get('password', '').strip()

        if not username or not password:
            return Response({'detail': 'username and password are required.'}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({'username': ['A user with that username already exists.']}, status=400)

        teacher = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            role='teacher',
        )
        return Response(self._serialize(teacher), status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        try:
            teacher = User.objects.get(pk=pk, role='teacher')
        except User.DoesNotExist:
            return Response({'detail': 'Teacher not found.'}, status=404)

        d = request.data
        teacher.first_name = d.get('first_name', teacher.first_name)
        teacher.last_name = d.get('last_name', teacher.last_name)
        teacher.email = d.get('email', teacher.email)
        if d.get('password'):
            teacher.set_password(d['password'])
        teacher.save()
        return Response(self._serialize(teacher))

    def destroy(self, request, pk=None):
        try:
            teacher = User.objects.get(pk=pk, role='teacher')
        except User.DoesNotExist:
            return Response({'detail': 'Teacher not found.'}, status=404)
        teacher.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _serialize(user):
        return {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'role': user.role,
            'date_joined': user.date_joined,
        }
