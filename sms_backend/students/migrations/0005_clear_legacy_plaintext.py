"""
Remove plaintext message bodies left over from before messaging was encrypted.

Messages used to be stored in a readable `body` column. Now that the API only
exposes ciphertext, those rows are unreachable but the text would still sit in
the database, so it is cleared here. The message itself is kept so the
conversation history stays intact; those messages simply become unreadable,
which is what encryption implies for anything sent in the clear.
"""

from django.db import migrations


def clear_legacy_plaintext(apps, schema_editor):
    Message = apps.get_model('students', 'Message')

    legacy = Message.objects.filter(body__gt='')
    count = legacy.count()
    if not count:
        return

    Message.objects.filter(body__gt='').update(body='')
    print(f'  cleared plaintext body from {count} pre-encryption message(s)')


def noop(apps, schema_editor):
    """The plaintext is gone and cannot be restored from this schema."""


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0004_message_algorithm_message_ciphertext_message_iv_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_legacy_plaintext, noop),
    ]
