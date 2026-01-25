from django.core.management.base import BaseCommand
from principal.models import Iglesia, Union

class Command(BaseCommand):
    help = 'Carga datos ficticios de iglesias y uniones'

    def handle(self, *args, **options):
        iglesias_data = [
            {'nombre': 'Iglesia Central', 'ubicacion': 'Centro ciudad'},
            {'nombre': 'Iglesia Vida Nueva', 'ubicacion': 'Zona norte'},
            {'nombre': 'Iglesia Esperanza', 'ubicacion': 'Zona sur'},
            {'nombre': 'Iglesia del Camino', 'ubicacion': 'Zona este'},
            {'nombre': 'Iglesia Gracia y Paz', 'ubicacion': 'Zona oeste'},
        ]

        unions_data = [
            {'nombre': 'Unión Metropolitana', 'descripcion': 'Jóvenes de la ciudad'},
            {'nombre': 'Unión Regional', 'descripcion': 'Jóvenes de provincias'},
            {'nombre': 'Unión Distrital', 'descripcion': 'Jóvenes del distrito'},
            {'nombre': 'Unión Juvenil Nacional', 'descripcion': 'Jóvenes del país'},
        ]

        for iglesia_data in iglesias_data:
            iglesia, created = Iglesia.objects.get_or_create(
                nombre=iglesia_data['nombre'],
                defaults={'ubicacion': iglesia_data['ubicacion']}
            )
            status = 'creada' if created else 'ya existe'
            self.stdout.write(self.style.SUCCESS(f'Iglesia "{iglesia.nombre}" {status}'))

        for union_data in unions_data:
            union, created = Union.objects.get_or_create(
                nombre=union_data['nombre'],
                defaults={'descripcion': union_data['descripcion']}
            )
            status = 'creada' if created else 'ya existe'
            self.stdout.write(self.style.SUCCESS(f'Unión "{union.nombre}" {status}'))

        self.stdout.write(self.style.SUCCESS('✓ Datos ficticios cargados correctamente'))
