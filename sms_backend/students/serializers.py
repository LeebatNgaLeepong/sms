"""
Serializers for students app.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from schedules.terms import InvalidTerm, resolve_term
from .models import EnrollmentRequest, Message, MessageThread, Student

User = get_user_model()


class StudentSerializer(serializers.ModelSerializer):
    """
    Serializer for Student model with computed GPA and user linkage.
    """

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='student'),
        allow_null=True,
        required=False,
        help_text="User ID of the student's login account, if one exists.",
    )
    user_username = serializers.CharField(
        source='user.username',
        read_only=True,
        allow_null=True,
    )
    gpa = serializers.FloatField(
        read_only=True,
        help_text="Simple average of grade points across graded subjects.",
    )
    gwa = serializers.FloatField(
        read_only=True,
        help_text="General Weighted Average: grade points weighted by subject units.",
    )
    units_earned = serializers.IntegerField(read_only=True)
    grades_count = serializers.IntegerField(read_only=True)
    incomplete_count = serializers.IntegerField(source='inc_count', read_only=True)
    sections = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Student
        fields = [
            'id',
            'user',
            'user_username',
            'name',
            'email',
            'program',
            'year_level',
            'gpa',
            'gwa',
            'units_earned',
            'grades_count',
            'incomplete_count',
            'sections',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'gpa', 'gwa', 'units_earned', 'grades_count',
                            'incomplete_count', 'sections', 'created_at', 'updated_at']

    def get_sections(self, obj):
        return [
            {
                'id': s.id,
                'code': s.code,
                'subject_code': s.subject.code,
                'subject_name': s.subject.name,
            }
            for s in obj.sections.select_related('subject')
        ]

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        query = Student.objects.filter(email__iexact=email)
        if self.instance:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise serializers.ValidationError("A student with this email already exists.")
        return email


class StudentGradesSummarySerializer(serializers.Serializer):
    """
    Serializer to represent all grades and computed GPA for a specific student.
    """

    student_id = serializers.CharField()
    student_name = serializers.CharField()
    email = serializers.EmailField()
    program = serializers.CharField()
    year_level = serializers.CharField()
    gpa = serializers.FloatField()
    gwa = serializers.FloatField()
    units_earned = serializers.IntegerField()
    total_grades = serializers.IntegerField()
    grades = serializers.ListField(child=serializers.DictField())


class EnrollmentRequestSerializer(serializers.ModelSerializer):
    """
    A student's request to add a subject to their load.
    """

    student_name = serializers.CharField(source='student.name', read_only=True)
    student_id = serializers.CharField(source='student.id', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_units = serializers.IntegerField(source='subject.units', read_only=True)
    reviewed_by_username = serializers.CharField(
        source='reviewed_by.username', read_only=True, default=None
    )
    term = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EnrollmentRequest
        fields = [
            'id',
            'student',
            'student_id',
            'student_name',
            'subject',
            'subject_code',
            'subject_name',
            'subject_units',
            'semester',
            'school_year',
            'term',
            'reason',
            'status',
            'reviewed_by',
            'reviewed_by_username',
            'reviewed_at',
            'review_note',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'reviewed_by',
            'reviewed_by_username',
            'reviewed_at',
            'review_note',
            'created_at',
            'updated_at',
        ]
        # The model's unique_together would surface as a raw database message
        # before validate() runs, so the readable checks below own that case.
        validators = []

    def get_term(self, obj) -> str:
        return f"{obj.semester} {obj.school_year}".strip()

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        # Only a student may file their own request.
        if user is not None and user.role != 'student':
            raise serializers.ValidationError(
                'Only students can request a subject.'
            )

        student = attrs.get('student') or getattr(self.instance, 'student', None)
        if user is not None and user.role == 'student':
            if student is None or student.user != user:
                raise serializers.ValidationError(
                    'You can only request subjects for yourself.'
                )

        subject = attrs.get('subject') or getattr(self.instance, 'subject', None)

        try:
            semester, school_year = resolve_term(attrs)
        except InvalidTerm as exc:
            raise serializers.ValidationError({exc.field: [exc.message]})
        attrs['semester'] = semester
        attrs['school_year'] = school_year

        if student and subject:
            if student.enrolled_subjects.filter(id=subject.id).exists():
                raise serializers.ValidationError({
                    'subject': 'You are already enrolled in this subject.'
                })
            duplicate = EnrollmentRequest.objects.filter(
                student=student,
                subject=subject,
                semester=semester,
                school_year=school_year,
                status=EnrollmentRequest.STATUS_PENDING,
            )
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError({
                    'subject': 'You already have a pending request for this subject.'
                })

        return attrs


class MessageSerializer(serializers.ModelSerializer):
    """
    A single message in a thread.
    """

    sender_name = serializers.SerializerMethodField(read_only=True)
    sender_role = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'thread',
            'sender',
            'sender_name',
            'sender_role',
            'body',
            'read_at',
            'created_at',
        ]
        read_only_fields = ['id', 'thread', 'sender', 'read_at', 'created_at']

    def get_sender_name(self, obj) -> str:
        full = obj.sender.get_full_name()
        return full or obj.sender.username

    def get_sender_role(self, obj) -> str:
        return obj.sender.role

    def validate_body(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Message cannot be empty.')
        return value


class MessageThreadSerializer(serializers.ModelSerializer):
    """
    A conversation between one student and one teacher.
    """

    student_id = serializers.CharField(source='student.id', read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)
    student_program = serializers.CharField(source='student.program', read_only=True)
    teacher_username = serializers.CharField(source='teacher.username', read_only=True)
    teacher_name = serializers.SerializerMethodField(read_only=True)
    subject_code = serializers.CharField(
        source='subject.code', read_only=True, default=None
    )
    counterpart_name = serializers.SerializerMethodField(read_only=True)
    counterpart_role = serializers.SerializerMethodField(read_only=True)
    unread_count = serializers.SerializerMethodField(read_only=True)
    message_count = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MessageThread
        fields = [
            'id',
            'student',
            'student_id',
            'student_name',
            'student_program',
            'teacher',
            'teacher_username',
            'teacher_name',
            'subject',
            'subject_code',
            'counterpart_name',
            'counterpart_role',
            'unread_count',
            'message_count',
            'last_message',
            'last_message_at',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'student',
            'teacher',
            'subject',
            'last_message_at',
            'created_at',
        ]

    def _user(self):
        request = self.context.get('request')
        return getattr(request, 'user', None)

    def get_teacher_name(self, obj) -> str:
        full = obj.teacher.get_full_name()
        return full or obj.teacher.username

    def get_counterpart_name(self, obj) -> str:
        user = self._user()
        if user is not None and user == obj.student.user:
            full = obj.teacher.get_full_name()
            return full or obj.teacher.username
        return obj.student.name

    def get_counterpart_role(self, obj) -> str:
        user = self._user()
        if user is not None and user == obj.student.user:
            return 'teacher'
        return 'student'

    def get_unread_count(self, obj) -> int:
        user = self._user()
        return obj.unread_for(user) if user else 0

    def get_message_count(self, obj) -> int:
        return obj.messages.count()

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if not last:
            return None
        return {
            'body': last.body,
            'sender': last.sender.username,
            'created_at': last.created_at,
        }


class EnrollmentDecisionSerializer(serializers.Serializer):
    """A staff decision on a pending request."""

    decision = serializers.ChoiceField(choices=['approved', 'rejected'])
    note = serializers.CharField(required=False, allow_blank=True)


class StartThreadSerializer(serializers.Serializer):
    """Start, or reuse, a thread with someone."""

    counterpart = serializers.CharField(
        max_length=64,
        help_text=(
            'Student id (e.g. STU-10001) when a teacher starts the thread, '
            'or the teacher user id when a student starts it.'
        ),
    )
    subject = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        from subjects.models import Subject

        user = self.context['request'].user
        counterpart_id = attrs['counterpart']
        subject_id = attrs.get('subject')

        subject = None
        if subject_id is not None:
            subject = Subject.objects.filter(id=subject_id).first()
            if subject is None:
                raise serializers.ValidationError({'subject': 'Subject not found.'})
            # Keep the instance so the caller can assign it to the thread.
            attrs['subject'] = subject

        # An admin does not take part in conversations. Checked before the role
        # branches because create_superuser leaves role at its student default.
        if user.role == 'admin' or user.is_superuser:
            raise serializers.ValidationError(
                'Only students and teachers can message each other.'
            )

        if user.role == 'student':
            # getattr: a user with no student profile raises rather than returns None.
            student = getattr(user, 'student_profile', None)
            if student is None:
                raise serializers.ValidationError('No student profile for this account.')
            try:
                teacher_id = int(counterpart_id)
            except (TypeError, ValueError):
                raise serializers.ValidationError({
                    'counterpart': 'Choose a teacher from the list.'
                })
            teacher = User.objects.filter(
                id=teacher_id, role='teacher', is_active=True
            ).first()
            if teacher is None:
                raise serializers.ValidationError({
                    'counterpart': 'That user is not an active teacher.'
                })
            attrs['student'] = student
            attrs['teacher'] = teacher
        elif user.role == 'teacher':
            student = Student.objects.filter(id=counterpart_id).select_related('user').first()
            if student is None or student.user is None:
                raise serializers.ValidationError({
                    'counterpart': 'That student has no login account.'
                })
            attrs['student'] = student
            attrs['teacher'] = user
        else:
            raise serializers.ValidationError(
                'Only students and teachers can message each other.'
            )

        return attrs


class SendMessageSerializer(serializers.Serializer):
    """Post a message into an existing thread."""

    body = serializers.CharField(trim_whitespace=True)

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Message cannot be empty.')
        if len(value) > 5000:
            raise serializers.ValidationError('Message is too long.')
        return value
