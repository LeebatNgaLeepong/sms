"""
Serializers for accounts app, including custom JWT token serializer and user profiles.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the custom User model.
    """

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that adds user role and profile details to both
    the JWT token payload and the JSON response.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims embedded inside JWT
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Retrieve linked student ID if user is a student
        student_id = None
        if hasattr(self.user, 'student_profile') and self.user.student_profile is not None:
            student_id = self.user.student_profile.id

        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'student_id': student_id,
        }
        return data


class LogoutSerializer(serializers.Serializer):
    """
    Serializer to validate and blacklist refresh tokens on logout.
    """

    refresh = serializers.CharField(
        help_text="The refresh token to blacklist on logout."
    )

    def validate(self, attrs):
        self.token = attrs.get('refresh')
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError as exc:
            raise serializers.ValidationError({'refresh': 'Token is invalid or already expired.'}) from exc
