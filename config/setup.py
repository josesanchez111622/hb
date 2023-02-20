from django.contrib.auth.models import Group

pro_group, created = Group.objects.get_or_create(name='pro')