"""
Authentication views for College Student Management System.
Provides endpoints for login, refresh, logout, and current user profile inspection.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import CustomTokenObtainPairSerializer, LogoutSerializer, UserSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Authenticates user with username & password, returns JWT tokens and user metadata.
    """

    permission_classes = (AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """
    POST /api/auth/refresh/
    Takes a valid refresh token and returns a new access token.
    """

    permission_classes = (AllowAny,)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the provided refresh token so it cannot be used again.
    """

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Successfully logged out. Refresh token has been blacklisted."},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    GET /api/auth/me/
    Returns information about the currently authenticated user, including their
    role and associated student record if applicable.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user)
        data = serializer.data

        # Attach student record details if user has student role
        if hasattr(user, 'student_profile') and user.student_profile is not None:
            student = user.student_profile
            data['student'] = {
                'id': student.id,
                'name': student.name,
                'email': student.email,
                'program': student.program,
                'year_level': student.year_level,
                'gpa': student.gpa,
            }
        else:
            data['student'] = None

        return Response(data, status=status.HTTP_200_OK)
