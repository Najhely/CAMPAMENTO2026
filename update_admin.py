#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from principal.models import Usuario

try:
    u = Usuario.objects.get(username='nayjhel')
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print('✓ nayjhel es ahora SUPERUSER con todos los permisos')
    print(f'  - is_staff: {u.is_staff}')
    print(f'  - is_superuser: {u.is_superuser}')
except Usuario.DoesNotExist:
    print('Error: Usuario nayjhel no encontrado')
