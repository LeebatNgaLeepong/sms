"""
Public-key exchange for end-to-end encrypted messaging.

The server only ever holds public keys and ciphertext. Private keys are generated
in the browser and never transmitted, so this endpoint cannot read any message.
"""

import base64
import binascii

from django.contrib.auth import get_user_model
from rest_framework import serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import EncryptionKey

User = get_user_model()

# A raw P-256 public key is 65 uncompressed bytes, base64 of that is ~88 chars.
MAX_PUBLIC_KEY_CHARS = 512


class EncryptionKeySerializer(serializers.ModelSerializer):
    """
    A user's public key.
    """

    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = EncryptionKey
        fields = ['id', 'username', 'public_key', 'algorithm', 'created_at', 'updated_at']
        read_only_fields = ['id', 'username', 'algorithm', 'created_at', 'updated_at']

    def validate_public_key(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('A public key is required.')
        if len(value) > MAX_PUBLIC_KEY_CHARS:
            raise serializers.ValidationError('That public key is too long to be valid.')
        try:
            raw = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError):
            raise serializers.ValidationError('The public key must be base64.')
        if len(raw) not in (33, 65):
            raise serializers.ValidationError(
                'That is not a valid P-256 public key.'
            )
        return value


class EncryptionKeyViewSet(viewsets.ViewSet):
    """
    GET /api/encryption-keys/me/ : this user's own public key.
    PUT /api/encryption-keys/me/ : publish or replace it.
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """GET /api/encryption-keys/ : the keys needed to start conversations."""
        # A user needs the public keys of anyone they may talk to.
        if request.user.role == 'student':
            peers = User.objects.filter(role='teacher', is_active=True)
        elif request.user.role == 'teacher':
            peers = User.objects.filter(role='student', is_active=True)
        else:
            peers = User.objects.none()

        keys = EncryptionKey.objects.filter(user__in=peers).select_related('user')
        return Response([
            {
                'user_id': key.user_id,
                'username': key.user.username,
                'public_key': key.public_key,
                'algorithm': key.algorithm,
            }
            for key in keys
        ])

    def retrieve(self, request, pk=None):
        """GET /api/encryption-keys/{user_id}/ : one peer's public key."""
        try:
            key = EncryptionKey.objects.get(user_id=pk)
        except EncryptionKey.DoesNotExist:
            return Response(
                {'detail': 'No public key has been published for that user.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            'user_id': key.user_id,
            'username': key.user.username,
            'public_key': key.public_key,
            'algorithm': key.algorithm,
        })

    def retrieve_me(self, request):
        """GET /api/encryption-keys/me/ : this user's own published key."""
        key = EncryptionKey.objects.filter(user=request.user).first()
        if key is None:
            return Response(
                {'detail': 'No public key published yet for this account.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            'user_id': key.user_id,
            'username': key.user.username,
            'public_key': key.public_key,
            'algorithm': key.algorithm,
        })

    def create(self, request):
        """PUT/POST /api/encryption-keys/me/ : publish this user's public key."""
        serializer = EncryptionKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key, _created = EncryptionKey.objects.update_or_create(
            user=request.user,
            defaults={'public_key': serializer.validated_data['public_key']},
        )
        return Response(
            EncryptionKeySerializer(key).data,
            status=status.HTTP_200_OK,
        )

    def partial_update(self, request, pk=None):
        """PUT /api/encryption-keys/me/ : replace this user's public key."""
        return self.create(request)