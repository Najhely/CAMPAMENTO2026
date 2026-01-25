from django.core.management.base import BaseCommand
from principal.models import Usuario

class Command(BaseCommand):
    help = 'Crear usuarios de prueba con diferentes roles'

    def handle(self, *args, **options):
        # Usuario Campamentista
        if not Usuario.objects.filter(username='campamentista1').exists():
            usuario_camp = Usuario.objects.create_user(
                username='campamentista1',
                password='Campamento123',
                email='campamentista@test.com',
                first_name='Juan',
                last_name='Campamentista',
                rol='campamentista'
            )
            self.stdout.write(self.style.SUCCESS(
                f'✓ Usuario campamentista creado: campamentista1 / Campamento123'
            ))
        
        # Usuario Inscripción
        if not Usuario.objects.filter(username='inscripcion1').exists():
            usuario_insc = Usuario.objects.create_user(
                username='inscripcion1',
                password='Inscripcion123',
                email='inscripcion@test.com',
                first_name='Carlos',
                last_name='Inscriptor',
                rol='inscripcion'
            )
            self.stdout.write(self.style.SUCCESS(
                f'✓ Usuario inscripción creado: inscripcion1 / Inscripcion123'
            ))
        
        # Usuario Director
        if not Usuario.objects.filter(username='director1').exists():
            usuario_dir = Usuario.objects.create_user(
                username='director1',
                password='Director123',
                email='director@test.com',
                first_name='María',
                last_name='Directora',
                rol='director',
                is_staff=True
            )
            self.stdout.write(self.style.SUCCESS(
                f'✓ Usuario director creado: director1 / Director123'
            ))
        
        # Admin ya existe
        if Usuario.objects.filter(username='nayjhel').exists():
            self.stdout.write(self.style.SUCCESS(
                '✓ Usuario admin (nayjhel) ya existe'
            ))
        
        self.stdout.write(self.style.SUCCESS('\n=== USUARIOS DE PRUEBA LISTOS ==='))
        self.stdout.write('\nPara acceder al sistema:')
        self.stdout.write('  Campamentista: campamentista1 / Campamento123')
        self.stdout.write('  Inscripción: inscripcion1 / Inscripcion123')
        self.stdout.write('  Director: director1 / Director123')
        self.stdout.write('  Admin: nayjhel / nayjhelNCA')

