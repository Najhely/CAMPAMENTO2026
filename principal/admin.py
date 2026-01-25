from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Usuario, Grupo, Inscripcion, InventarioGlobal, 
    LogisticaKit, HistorialPuntos, Publicacion, 
    Reaccion, Comentario, Devocional, Noticia, Actividad,
    Iglesia, Union, Notificacion
)

# Definimos la clase primero
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'rol', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Información Extra', {'fields': ('rol',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Extra', {'fields': ('rol',)}),
    )

# REGISTRO MANUAL (Evita el error de retorno None)
admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(Iglesia)
admin.site.register(Union)
admin.site.register(Grupo)
admin.site.register(Inscripcion)
admin.site.register(InventarioGlobal)
admin.site.register(LogisticaKit)
admin.site.register(HistorialPuntos)
admin.site.register(Publicacion)
admin.site.register(Reaccion)
admin.site.register(Comentario)
admin.site.register(Devocional)
admin.site.register(Noticia)
admin.site.register(Actividad)
admin.site.register(Notificacion)