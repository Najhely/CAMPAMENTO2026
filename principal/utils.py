# principal/utils.py - VERSIÓN CORREGIDA COMPLETA
from decimal import Decimal
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.db.models import Count, Max, Q
import random

def asignar_polera_automatica(grupo_color_hex=None, talla_preferida=None):
    """
    Asigna polera del color del grupo con numeración por color.
    Cada color tiene su propia secuencia: Rojo 1-60, Azul 1-60, etc.
    """
    from .models import InventarioGlobal, LogisticaKit
    
    print(f"🔍 DEBUG: Asignando polera - Color: {grupo_color_hex}, Talla: {talla_preferida}")
    
    if not grupo_color_hex:
        print("⚠️ No hay color de grupo")
        return {
            'color_hex': None,
            'talla': talla_preferida or 'M',
            'numero': 0,
            'inventario_id': None,
            'sin_stock': True
        }
    
    # 1. Obtener el siguiente número para ESTE COLOR específico
    ultimo_numero = LogisticaKit.objects.filter(
        pañoleta_color__iexact=grupo_color_hex
    ).aggregate(Max('polera_numero_id'))['polera_numero_id__max']
    
    siguiente_numero = (ultimo_numero or 0) + 1
    
    print(f"📊 Último número del color {grupo_color_hex}: {ultimo_numero}")
    print(f"🔢 Siguiente número: {siguiente_numero}")
    
    # 2. Buscar inventario del color con stock
    inventario_disponible = InventarioGlobal.objects.filter(
        articulo='polera',
        color_hex__iexact=grupo_color_hex,
        stock_actual__gt=0
    )
    
    print(f"📦 Inventario disponible: {inventario_disponible.count()} items")
    
    # 3. Seleccionar inventario según talla
    inventario_item = None
    if talla_preferida:
        inventario_item = inventario_disponible.filter(talla=talla_preferida).first()
        print(f"👕 Buscando talla {talla_preferida}: {'Encontrada' if inventario_item else 'No encontrada'}")
    
    if not inventario_item:
        inventario_item = inventario_disponible.first()
        print(f"👕 Tomando primera disponible: {inventario_item.talla if inventario_item else 'Ninguna'}")
    
    # 4. Resultado
    if inventario_item and inventario_item.stock_actual > 0:
        # Hay stock físico disponible
        inventario_item.stock_actual -= 1
        inventario_item.save()
        
        print(f"✅ Stock decrementado. Quedan: {inventario_item.stock_actual}")
        
        return {
            'color_hex': grupo_color_hex,
            'talla': inventario_item.talla,
            'numero': siguiente_numero,
            'inventario_id': inventario_item.id,
            'sin_stock': False
        }
    else:
        # No hay stock físico, pero igual asignamos número
        print(f"⚠️ Sin stock físico, asignando número virtual")
        
        return {
            'color_hex': grupo_color_hex,
            'talla': talla_preferida or 'M',
            'numero': siguiente_numero,
            'inventario_id': None,
            'sin_stock': True
        }

def asignar_grupo_automatico(edad, sexo, union_obj):
    """Asignar grupo automáticamente basado en criterios"""
    from .models import Grupo
    
    print(f"🎯 Asignando grupo - Edad: {edad}, Sexo: {sexo}, Unión: {union_obj}")
    
    grupos = Grupo.objects.annotate(num_miembros=Count('miembros')).order_by('num_miembros')
    
    candidatos = []
    
    for grupo in grupos:
        ok = True
        
        # Verificar edad
        if edad is not None:
            if grupo.min_age is not None and edad < grupo.min_age:
                ok = False
            if grupo.max_age is not None and edad > grupo.max_age:
                ok = False
        
        # Verificar sexo
        if grupo.sexo and sexo and grupo.sexo != sexo:
            ok = False
        
        # Verificar unión
        if grupo.union and union_obj:
            if grupo.union.lower() != union_obj.nombre.lower():
                ok = False
        
        if ok:
            candidatos.append(grupo)
            print(f"✅ Grupo candidato: {grupo.nombre} ({grupo.num_miembros} miembros)")
    
    if candidatos:
        grupo_seleccionado = candidatos[0]
        print(f"🎉 Grupo asignado: {grupo_seleccionado.nombre}")
        return grupo_seleccionado
    
    grupo_default = grupos.first()
    print(f"⚠️ Sin candidatos, usando grupo por defecto: {grupo_default.nombre if grupo_default else 'Ninguno'}")
    return grupo_default

def verificar_numeracion_por_color():
    """
    Función de diagnóstico para verificar la numeración por color
    Ejecutar desde: python manage.py shell
    """
    from .models import LogisticaKit
    
    print("\n" + "="*60)
    print("DIAGNÓSTICO DE NUMERACIÓN POR COLOR")
    print("="*60 + "\n")
    
    # Agrupar por color
    colores = LogisticaKit.objects.exclude(
        pañoleta_color__isnull=True
    ).values('pañoleta_color').distinct()
    
    for color_dict in colores:
        color = color_dict['pañoleta_color']
        kits = LogisticaKit.objects.filter(
            pañoleta_color=color
        ).order_by('polera_numero_id')
        
        numeros = [k.polera_numero_id for k in kits if k.polera_numero_id]
        
        print(f"🎨 Color: {color}")
        print(f"   📊 Total kits: {kits.count()}")
        print(f"   🔢 Números: {numeros}")
        print(f"   ⬆️  Máximo: {max(numeros) if numeros else 0}")
        print()
    
    print("="*60 + "\n")