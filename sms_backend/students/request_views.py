"""
Views for subject-add requests and student-teacher messaging.
"""

from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import EnrollmentRequestPermission, MessageThreadPermission
from .models import EnrollmentRequest, Message, MessageThread, Student
from .serializers import (
    EnrollmentDecisionSerializer,
    EnrollmentRequestSerializer,
    MessageSerializer,
    MessageThreadSerializer,
    SendMessageSerializer,
    StartThreadSerializer,
)


class EnrollmentRequestViewSet(viewsets.ModelViewSet):
    """
    Subject-add requests.

    A student files a request to add a subject to their load; the instructor for
    that subject, or an admin, approves or rejects it. Approving enrolls the
    student and rebuilds their timetable.
    """

    serializer_class = EnrollmentRequestSerializer
    permission_classes = [EnrollmentRequestPermission, IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'subject', 'semester', 'school_year']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        base = EnrollmentRequest.objects.select_related(
            'student', 'student__user', 'subject', 'reviewed_by'
        )

        # Superuser first: create_superuser leaves role at its student default.
        if user.role == 'admin' or user.is_superuser:
            return base

        if user.role == 'student':
            return base.filter(student__user=user)

        if user.role == 'teacher':
            # Teachers see requests for the subjects they teach.
            return base.filter(subject__instructor=user)

        return base.none()

    def create(self, request, *args, **kwargs):
        # A student does not choose who they are; it comes from their account.
        payload = dict(request.data)
        if request.user.role == 'student':
            profile = getattr(request.user, 'student_profile', None)
            if profile is None:
                return Response(
                    {'detail': 'No student profile for this account.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            payload['student'] = profile.id

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='decision')
    def decision(self, request, pk=None):
        """
        POST /api/enrollment-requests/{id}/decision/
        Body: {"decision": "approved" | "rejected", "note": "..."}

        Approving adds the subject to the student's load and rebuilds their
        timetable for that term.
        """
        request_obj = self.get_object()

        if request_obj.status != EnrollmentRequest.STATUS_PENDING:
            return Response(
                {'detail': f'This request was already {request_obj.get_status_display().lower()}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        if not (user.role == 'admin' or user.is_superuser):
            if user.role != 'teacher' or request_obj.subject.instructor_id != user.id:
                return Response(
                    {'detail': 'You can only decide on requests for subjects you teach.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = EnrollmentDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data['decision']
        note = serializer.validated_data.get('note', '')

        if decision == EnrollmentRequest.STATUS_APPROVED:
            student = request_obj.student
            subject = request_obj.subject
            student.enrolled_subjects.add(subject)

            # Rebuild the student's timetable so the new class has a real slot.
            scheduled = 0
            from schedules.scheduler import regenerate_student_schedule

            try:
                results = regenerate_student_schedule(
                    student,
                    semester=request_obj.semester,
                    school_year=request_obj.school_year,
                )
                scheduled = sum(1 for r in results if r['time_slot'] is not None)
            except Exception:
                # The enrollment stands even if scheduling could not be rebuilt.
                scheduled = 0

            request_obj.status = EnrollmentRequest.STATUS_APPROVED
            message = f'Enrollment approved. {scheduled} class(es) scheduled.'
        else:
            request_obj.status = EnrollmentRequest.STATUS_REJECTED
            message = 'Enrollment request rejected.'

        request_obj.reviewed_by = user
        request_obj.reviewed_at = timezone.now()
        request_obj.review_note = note
        request_obj.save(update_fields=[
            'status', 'reviewed_by', 'reviewed_at', 'review_note', 'updated_at',
        ])

        return Response({
            **EnrollmentRequestSerializer(request_obj, context={'request': request}).data,
            'detail': message,
        })


class MessageThreadViewSet(viewsets.ModelViewSet):
    """
    Private conversations between a student and one of their teachers.
    """

    serializer_class = MessageThreadSerializer
    permission_classes = [MessageThreadPermission, IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        base = MessageThread.objects.select_related(
            'student', 'student__user', 'teacher', 'subject'
        ).prefetch_related('messages')

        # Superuser first: create_superuser leaves role at its student default.
        if user.role == 'admin' or user.is_superuser:
            return base

        if user.role == 'student':
            return base.filter(student__user=user)
        if user.role == 'teacher':
            return base.filter(teacher=user)
        return base.none()

    def create(self, request, *args, **kwargs):
        """
        POST /api/threads/
        Body: {"counterpart": <student id or teacher user id>, "subject": 3}

        Returns the existing thread when one already exists, so the UI can treat
        starting a conversation as idempotent.
        """
        serializer = StartThreadSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        thread, created = MessageThread.objects.get_or_create(
            student=data['student'],
            teacher=data['teacher'],
            defaults={'subject': data.get('subject')},
        )
        if not created and data.get('subject') and thread.subject_id is None:
            thread.subject = data['subject']
            thread.save(update_fields=['subject', 'updated_at'])

        out = self.get_serializer(thread)
        return Response(
            out.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        """
        GET  /api/threads/{id}/messages/ : list the conversation, marking it read.
        POST /api/threads/{id}/messages/ : send an encrypted message.

        Posting requires ciphertext and iv. The server never receives the
        plaintext body, so it cannot read the conversation.
        """
        thread = self.get_object()

        if request.method == 'POST':
            serializer = SendMessageSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            message = Message.objects.create(
                thread=thread,
                sender=request.user,
                ciphertext=serializer.validated_data['ciphertext'],
                iv=serializer.validated_data['iv'],
                algorithm=serializer.validated_data.get('algorithm', 'AES-GCM-256'),
            )
            thread.last_message_at = message.created_at
            thread.save(update_fields=['last_message_at', 'updated_at'])
            return Response(
                MessageSerializer(message).data,
                status=status.HTTP_201_CREATED,
            )

        # Reading the thread marks the other side's messages as read.
        thread.messages.exclude(sender=request.user).filter(
            read_at__isnull=True
        ).update(read_at=timezone.now())

        rows = thread.messages.select_related('sender')
        return Response({
            'thread': self.get_serializer(thread).data,
            'messages': MessageSerializer(rows, many=True).data,
        })
