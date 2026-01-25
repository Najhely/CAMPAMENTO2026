from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# 0. IGLESIAS Y UNIONES
class Iglesia(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class Union(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

# 1. USUARIOS Y ROLES
class Usuario(AbstractUser):
    ROLES = (
        ('admin', 'Administrador'),
        ('director', 'Director'),
        ('lider', 'Líder'),
        ('inscripcion', 'Inscripción'),
        ('campamentista', 'Campamentista'),
        ('pastor', 'Pastor'),
    )
    rol = models.CharField(max_length=15, choices=ROLES, default='campamentista')

# 2. GRUPOS
# En models.py - Modelo Grupo CORREGIDO
class Grupo(models.Model):
    nombre = models.CharField(max_length=100)
    color_nombre = models.CharField(max_length=50, default='Sin color', help_text="Nombre del color: Rojo, Azul, etc.")
    color_hex = models.CharField(max_length=7, default='#000000', help_text="Código hexadecimal: #FF0000")
    insignia = models.ImageField(upload_to='insignias/', null=True, blank=True)
    puntos_totales = models.IntegerField(default=0)
    
    # Opciones para asignación automática
    min_age = models.PositiveIntegerField(null=True, blank=True)
    max_age = models.PositiveIntegerField(null=True, blank=True)
    sexo = models.CharField(max_length=2, null=True, blank=True)
    union = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.color_nombre})"
    
    @property
    def color(self):
        """Propiedad para compatibilidad con código existente"""
        return self.color_hex

# 3. PERFIL E INSCRIPCIÓN (Finanzas y Datos Personales)
class Inscripcion(models.Model):
    user = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil')
    nombre_persona = models.CharField(max_length=200)
    iglesia = models.ForeignKey(Iglesia, on_delete=models.PROTECT)
    union = models.ForeignKey(Union, on_delete=models.PROTECT, null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=(('M', 'Masculino'), ('F', 'Femenino')))
    edad = models.PositiveIntegerField()
    grupo = models.ForeignKey(Grupo, on_delete=models.SET_NULL, null=True, blank=True, related_name='miembros')
    
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, default=89.00)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Porcentaje de descuento")
    paga = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Monto que da el campamentista")
    cambio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Cambio automático")
    comision_iglesia = models.DecimalField(max_digits=10, decimal_places=2, default=30.00)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    asistencia_confirmada = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre_persona

# 4. INVENTARIO GLOBAL
# En models.py, modifica la clase InventarioGlobal:

class InventarioGlobal(models.Model):
    ARTICULOS = (
        ('polera', 'Polera'),
        ('pañoleta', 'Pañoleta'),
        ('credencial', 'Credencial'),
        ('manilla', 'Manilla'),
    )
    
    TALLAS = (
        ('XS', 'XS - Extra Pequeño'),
        ('S', 'S - Pequeño'),
        ('M', 'M - Mediano'),
        ('L', 'L - Grande'),
        ('XL', 'XL - Extra Grande'),
        ('XXL', 'XXL - Doble Extra Grande'),
        ('unica', 'Talla Única'),
    )
    
    articulo = models.CharField(max_length=20, choices=ARTICULOS)
    talla = models.CharField(max_length=10, choices=TALLAS, default='unica')
    color_hex = models.CharField(max_length=7, default='#000000', help_text="Código hexadecimal del color")
    color_nombre = models.CharField(max_length=50, null=True, blank=True, help_text="Nombre del color")
    stock_actual = models.PositiveIntegerField(default=0)
    stock_total = models.PositiveIntegerField(default=0, help_text="Stock inicial")
    
    # Para numeración por color
    numeros_asignados = models.TextField(blank=True, help_text="Números asignados por color, formato: color:#1,#2,#3")
    siguiente_numero = models.PositiveIntegerField(default=1)
    
    autor = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        unique_together = ['articulo', 'talla', 'color_hex']
        verbose_name = "Inventario Global"
        verbose_name_plural = "Inventarios Globales"
        ordering = ['articulo', 'color_nombre', 'talla']
    
    def __str__(self):
        return f"{self.get_articulo_display()} - {self.color_nombre} ({self.color_hex}) - Talla: {self.talla}"
    
    @property
    def color(self):
        """Propiedad para compatibilidad"""
        return self.color_nombre or self.color_hex
    
    def obtener_proximo_numero_por_color(self, color_hex):
        """Obtiene el próximo número para un color específico"""
        if self.stock_actual <= 0:
            return None
        
        # Parsear los números asignados por color
        numeros_por_color = {}
        if self.numeros_asignados:
            for entrada in self.numeros_asignados.split(';'):
                if ':' in entrada:
                    color, numeros_str = entrada.split(':', 1)
                    numeros_por_color[color] = [int(n) for n in numeros_str.split(',') if n.isdigit()]
        
        # Obtener números para este color
        numeros_del_color = numeros_por_color.get(color_hex, [])
        
        # Calcular próximo número
        if numeros_del_color:
            siguiente = max(numeros_del_color) + 1
        else:
            siguiente = 1
        
        # Actualizar registro
        numeros_del_color.append(siguiente)
        numeros_por_color[color_hex] = numeros_del_color
        
        # Convertir de nuevo a string
        nuevo_numeros_str = ';'.join([f"{color}:{','.join(map(str, nums))}" 
                                     for color, nums in numeros_por_color.items()])
        
        self.numeros_asignados = nuevo_numeros_str
        self.siguiente_numero = siguiente + 1
        self.stock_actual -= 1
        self.save()
        
        return siguiente
    
    def clean(self):
        """Validar que el color ya exista para el mismo artículo y talla"""
        from django.db.models import Q
        from django.core.exceptions import ValidationError
        
        # Solo validar si es un nuevo registro o se cambió el color
        if self.pk:
            # Si estamos editando, obtener el registro original
            try:
                original = InventarioGlobal.objects.get(pk=self.pk)
                # Si no cambió color_hex, no validar
                if original.color_hex == self.color_hex and original.color_nombre == self.color_nombre:
                    return
            except InventarioGlobal.DoesNotExist:
                pass
        
        # Buscar si ya existe el mismo color (hex o nombre) para el mismo artículo y talla
        if self.color_hex:
            existing_by_hex = InventarioGlobal.objects.filter(
                Q(articulo=self.articulo) &
                Q(talla=self.talla) &
                Q(color_hex=self.color_hex)
            )
            
            if self.pk:
                existing_by_hex = existing_by_hex.exclude(pk=self.pk)
            
            if existing_by_hex.exists():
                raise ValidationError({
                    'color_hex': f'Ya existe un color con código {self.color_hex} para {self.get_articulo_display()} talla {self.talla}'
                })
        
        if self.color_nombre:
            existing_by_name = InventarioGlobal.objects.filter(
                Q(articulo=self.articulo) &
                Q(talla=self.talla) &
                Q(color_nombre=self.color_nombre)
            )
            
            if self.pk:
                existing_by_name = existing_by_name.exclude(pk=self.pk)
            
            if existing_by_name.exists():
                raise ValidationError({
                    'color_nombre': f'Ya existe un color llamado {self.color_nombre} para {self.get_articulo_display()} talla {self.talla}'
                })
    
    def save(self, *args, **kwargs):
        # No ejecutar full_clean() aquí para evitar errores
        if not self.pk:  # Solo para nuevo registro
            self.stock_total = self.stock_actual
        super().save(*args, **kwargs)
# 5. LOGÍSTICA DE KITS (Entregas)
# En models.py, REEMPLAZA la clase LogisticaKit con esta versión:

class LogisticaKit(models.Model):
    inscripcion = models.OneToOneField(Inscripcion, on_delete=models.CASCADE)
    polera_entregada = models.BooleanField(default=False)
    polera_talla = models.CharField(max_length=10, null=True, blank=True)
    # ✅ CAMBIO CRÍTICO: Quitar unique=True para permitir numeración por color
    polera_numero_id = models.IntegerField(null=True, blank=True)
    pañoleta_entregada = models.BooleanField(default=False)
    pañoleta_color = models.CharField(max_length=50, null=True, blank=True, help_text="Color de la pañoleta")
    credencial_entregada = models.BooleanField(default=False)
    manilla_entregada = models.BooleanField(default=False)
    manilla_color = models.CharField(max_length=50, null=True, blank=True, help_text="Color de la manilla")
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    entregado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='kits_entregados')

    class Meta:
        # ✅ NUEVO: Constraint para que el número sea único POR COLOR
        constraints = [
            models.UniqueConstraint(
                fields=['polera_numero_id', 'pañoleta_color'],
                name='unique_numero_por_color',
                condition=models.Q(polera_numero_id__isnull=False, pañoleta_color__isnull=False)
            )
        ]
    
    def __str__(self):
        return f"Kit de {self.inscripcion.nombre_persona} - Polera #{self.polera_numero_id or 'Sin asignar'}"
# 6. COMPETENCIA (Puntos)
class HistorialPuntos(models.Model):
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=255)
    autor = models.ForeignKey(Usuario, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)

# 7. RED SOCIAL
class Publicacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='publicaciones/')
    referencia = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class Reaccion(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='reacciones')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, default='like')

class Comentario(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

# 8. PASTOREO (Devocionales)
class Devocional(models.Model):
    pastor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    cita_biblica = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)

# 9. COMUNICACIÓN (Noticias y Actividades)
class Noticia(models.Model):
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

class Actividad(models.Model):
    titulo = models.CharField(max_length=150)
    hora_inicio = models.DateTimeField()
    ubicacion = models.CharField(max_length=150)
    es_obligatoria = models.BooleanField(default=True)
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE)

# 10. NOTIFICACIONES
class Notificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=(
        ('info', 'Información'),
        ('alerta', 'Alerta'),
        ('exito', 'Éxito'),
        ('actividad', 'Actividad'),
        ('noticia', 'Noticia'),
    ), default='info')
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"
