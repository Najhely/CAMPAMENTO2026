from .models import Grupo, Inscripcion, LogisticaKit
from django.db.models import Count
from django.db import transaction

class CampamentoService:
    @staticmethod
    @transaction.atomic
    def inscribir_y_asignar_grupo(datos, user_obj):
        # Asignación automática al grupo con menos miembros
        grupo = Grupo.objects.annotate(n=Count('miembros')).order_by('n').first()
        ins = Inscripcion.objects.create(user=user_obj, grupo=grupo, **datos)
        LogisticaKit.objects.create(inscripcion=ins)
        return ins