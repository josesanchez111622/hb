from django.dispatch import receiver
from django.db.backends.signals import connection_created
from django.contrib.auth.models import Group


@receiver(connection_created)
def on_connection_created(sender, connection, **kwargs):
    pro_group, created = Group.objects.get_or_create(name="pro")
    