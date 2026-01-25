# views.py optimizado
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from functools import wraps
from django.utils import timezone
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from decimal import Decimal
from django.db.models import Max, Count, Sum

# Importación de modelos
from .models import (
    Publicacion, Noticia, Grupo, Inscripcion, Usuario,
    LogisticaKit, InventarioGlobal, Actividad, Notificacion,
    Iglesia, Union, Reaccion, Comentario, HistorialPuntos
)

# Importación de formularios
from .forms import (
    PublicacionForm, InscripcionForm, GrupoForm, ActividadForm,
    NoticiaForm, IglesiaForm, UnionForm, InventarioForm,
    UsuarioCrearForm, UsuarioEditarForm, HistorialPuntosForm,
    InscripcionUnificadoForm
)

# Importación de utilidades
from .utils import asignar_grupo_automatico

# ============ DECORADORES DE PERMISOS ============
def require_role(*roles):
    """Decorador para restricción de acceso por rol"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión para acceder a esta página.')
                return redirect('login')
            
            # Admin tiene acceso a todo
            if request.user.rol == 'admin':
                return view_func(request, *args, **kwargs)
            
            # Verificar si el usuario tiene uno de los roles requeridos
            if request.user.rol not in roles:
                messages.error(request, 'No tienes permiso para acceder a esta página.')
                return redirect('muro')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# ============ VISTAS DE AUTENTICACIÓN ============
def home_view(request):
    """Vista de inicio con botón de login"""
    if request.user.is_authenticated:
        if request.user.rol == 'admin':
            return redirect('dashboard')
        else:
            return redirect('muro')
    
    return render(request, 'principal/home.html')

def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        if request.user.rol == 'admin':
            return redirect('dashboard')
        else:
            return redirect('muro')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.first_name or user.username}')
            
            if user.rol == 'admin':
                return redirect('dashboard')
            else:
                return redirect('muro')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'principal/login.html')

def logout_view(request):
    """Vista de logout"""
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')

# ============ VISTAS PRINCIPALES ============
@require_role('admin')
def dashboard(request):
    """Dashboard solo para administradores"""
    user = request.user
    
    contexto = {
        'user': user,
        'rol_display': dict(user.ROLES).get(user.rol, user.rol),
        'notificaciones_no_leidas': user.notificaciones.filter(leida=False).count(),
        'total_inscritos': Inscripcion.objects.count(),
        'total_grupos': Grupo.objects.count(),
        'total_actividades': Actividad.objects.count(),
        'total_noticias': Noticia.objects.count(),
        'grupos': Grupo.objects.all().order_by('-puntos_totales'),
        'actividades': Actividad.objects.all().order_by('hora_inicio'),
        'noticias': Noticia.objects.all().order_by('-fecha_publicacion'),
        'publicaciones': Publicacion.objects.all().order_by('-fecha_creacion')[:10],
    }
    
    return render(request, 'principal/dashboard.html', contexto)

@require_role('campamentista', 'inscripcion', 'director', 'admin', 'lider')
def muro_social(request):
    """Muro social con publicaciones y noticias"""
    if request.method == 'POST' and request.user.is_authenticated:
        form = PublicacionForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.usuario = request.user
            post.save()
            messages.success(request, 'Publicación creada correctamente.')
            return redirect('muro')
    
    # Obtener likes del usuario actual
    user_likes = []
    if request.user.is_authenticated:
        user_likes = Reaccion.objects.filter(
            usuario=request.user, 
            tipo='like'
        ).values_list('publicacion_id', flat=True)
    
    notificaciones_no_leidas = 0
    if request.user.is_authenticated:
        notificaciones_no_leidas = request.user.notificaciones.filter(leida=False).count()
    
    contexto = {
        'publicaciones': Publicacion.objects.all().order_by('-fecha_creacion'),
        'noticias': Noticia.objects.all().order_by('-fecha_publicacion'),
        'grupos': Grupo.objects.all().order_by('-puntos_totales'),
        'form': PublicacionForm(),
        'user_likes': user_likes,
        'notificaciones_no_leidas': notificaciones_no_leidas,
    }
    return render(request, 'principal/muro.html', contexto)

@require_role('campamentista', 'inscripcion', 'director', 'admin', 'lider')
def ranking_grupos(request):
    """Vista detallada del ranking de competencia"""
    grupos = Grupo.objects.all().order_by('-puntos_totales')
    notificaciones_no_leidas = 0
    if request.user.is_authenticated:
        notificaciones_no_leidas = request.user.notificaciones.filter(leida=False).count()
    
    return render(request, 'principal/ranking.html', {
        'grupos': grupos,
        'notificaciones_no_leidas': notificaciones_no_leidas,
    })

def detalle_grupo(request, grupo_id):
    """Vista de integrantes e historial de un grupo específico"""
    grupo = get_object_or_404(Grupo, id=grupo_id)
    miembros = grupo.miembros.all().order_by('nombre_persona')
    historial = HistorialPuntos.objects.filter(grupo=grupo).order_by('-fecha')
    return render(request, 'principal/detalle_grupo.html', {
        'grupo': grupo, 
        'miembros': miembros,
        'historial': historial
    })

def pantalla_ruleta(request):
    """Vista para la pantalla de ruleta con grupos reales"""
    grupos = Grupo.objects.all()
    contexto = {
        'grupos_json': list(grupos.values('nombre', 'color_hex', 'color_nombre', 'puntos_totales'))
    }
    return render(request, 'principal/pantalla_ruleta.html', contexto)

# ============ VISTAS DE INSCRIPCIONES (MODIFICADAS) ============
@require_role('campamentista', 'inscripcion', 'director', 'admin', 'lider')
def lista_inscritos(request):
    """Vista principal para listar y crear inscripciones usando formulario unificado"""
    
    if request.method == 'POST':
        form = InscripcionUnificadoForm(request.POST)
        
        if form.is_valid():
            tipo_inscripcion = form.cleaned_data['inscripcion_tipo']
            
            if tipo_inscripcion == 'simple':
                return procesar_inscripcion_unificada(request, form, es_doble=False)
            else:
                return procesar_inscripcion_unificada(request, form, es_doble=True)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    
    else:
        form = InscripcionUnificadoForm()
    
    # Obtener datos para el template
    inscritos = Inscripcion.objects.all().select_related(
        'user', 'grupo', 'iglesia', 'union'
    ).prefetch_related('logisticakit')
    
    # Estadísticas
    poleras_stock = InventarioGlobal.objects.filter(articulo='polera')
    total_poleras = sum(p.stock_actual for p in poleras_stock) if poleras_stock else 0
    tallas_disponibles = poleras_stock.filter(
        stock_actual__gt=0
    ).values_list('talla', flat=True).distinct()
    
    # Última inscripción si viene por GET
    last_id = request.GET.get('last')
    last = None
    es_inscripcion_doble = False
    otra_persona = None
    poleras_asignadas_color = []
    proximo_numero_polera = 0
    
    if last_id:
        last = Inscripcion.objects.filter(id=last_id).select_related(
            'grupo', 'user', 'iglesia', 'union'
        ).first()
        
        if last:
            # Calcular poleras asignadas para este color
            color_grupo = last.grupo.color_nombre if last.grupo else None
            color_hex = last.grupo.color_hex if last.grupo else None
            
            if color_grupo:
                poleras_asignadas_color = LogisticaKit.objects.filter(
                    pañoleta_color__iexact=color_hex if color_hex else '',
                    polera_numero_id__isnull=False
                ).select_related('inscripcion').order_by('polera_numero_id')
                
                # Calcular próximo número para este color
                conteo_poleras_color = LogisticaKit.objects.filter(
                    pañoleta_color__iexact=color_hex if color_hex else ''
                ).exclude(polera_numero_id__isnull=True).count()
                
                # Ajustar para Naranja (comienza desde 8)
                if color_grupo.upper() == "NARANJA":
                    proximo_numero_polera = 8 + conteo_poleras_color
                else:
                    proximo_numero_polera = conteo_poleras_color
                
                # Verificar si el número ya existe
                while LogisticaKit.objects.filter(
                    polera_numero_id=proximo_numero_polera,
                    pañoleta_color__iexact=color_hex if color_hex else ''
                ).exists():
                    proximo_numero_polera += 1
    
    # Si no hay last, calcular el próximo número general
    if not last or not last.grupo:
        ultimo_numero = LogisticaKit.objects.aggregate(Max('polera_numero_id'))['polera_numero_id__max']
        proximo_numero_polera = (ultimo_numero or 0) + 1
    
    # Prepara datos de poleras asignadas por color para la plantilla
    poleras_asignadas_para_template = []
    for kit in poleras_asignadas_color:
        poleras_asignadas_para_template.append({
            'numero': kit.polera_numero_id,
            'talla': kit.polera_talla,
            'nombre': kit.inscripcion.nombre_persona if kit.inscripcion else ''
        })
    
    contexto = {
        'form': form,
        'lista_inscritos': inscritos,
        'last': last,
        'es_inscripcion_doble': es_inscripcion_doble,
        'otra_persona': otra_persona,
        'total_poleras': total_poleras,
        'tallas_disponibles': tallas_disponibles,
        'proximo_numero_polera': proximo_numero_polera,
        'poleras_stock': poleras_stock,
        'poleras_asignadas_color': poleras_asignadas_para_template,
        'grupos': Grupo.objects.all().order_by('nombre'),
    }
    
    # Calcular precio_final y saldo para last si existe
    if last:
        try:
            precio_base = last.costo_total or Decimal('0')
            descuento = last.descuento or Decimal('0')
            precio_final = (precio_base * (Decimal('1') - (descuento / Decimal('100')))).quantize(Decimal('0.01'))
            paga = last.paga or Decimal('0')
            saldo = max(Decimal('0'), precio_final - paga)
            contexto.update({
                'precio_final': precio_final,
                'saldo': saldo,
            })
        except:
            contexto.update({
                'precio_final': Decimal('0'),
                'saldo': Decimal('0'),
            })
        
        # Obtener el kit si existe
        kit = getattr(last, 'logisticakit', None)
        contexto['kit'] = kit
    
    return render(request, 'principal/lista_inscritos.html', contexto)

# ============ FUNCIONES AUXILIARES PARA INSCRIPCIONES ============
def crear_usuario_automatico(nombre_completo):
    """Crea un usuario Django automáticamente"""
    base = slugify(nombre_completo.split()[0] if ' ' in nombre_completo else nombre_completo)[:15]
    username = base
    suffix = 1
    
    while Usuario.objects.filter(username=username).exists():
        username = f"{base}{suffix}"
        suffix += 1
    
    password = get_random_string(8)
    user = Usuario.objects.create_user(username=username, password=password)
    
    if ' ' in nombre_completo:
        user.first_name = nombre_completo.split()[0]
    user.save()
    
    return user

def procesar_inscripcion_unificada(request, form, es_doble=False):
    """Procesa inscripción unificada (simple o doble)"""
    try:
        datos = form.cleaned_data
        
        if es_doble:
            return procesar_inscripcion_doble_completa(request, datos)
        else:
            return procesar_inscripcion_simple(request, datos)
            
    except Exception as e:
        messages.error(request, f'❌ Error al procesar inscripción: {str(e)}')
        import traceback
        print(traceback.format_exc())
        return redirect('lista_inscritos')

def procesar_inscripcion_simple(request, datos):
    """Procesa una inscripción simple"""
    # Crear usuario
    user = crear_usuario_automatico(datos['nombre_persona'])
    
    # Asignar grupo
    grupo = asignar_grupo_automatico(
        int(datos['edad']),
        datos['sexo'],
        datos.get('union')
    )
    
    # Asignar polera
    polera_info = asignar_polera_automatica(
        grupo.color_hex if grupo else None,
        datos.get('talla_polera')
    )
    
    # Calcular precios
    precio_base = datos['costo_total'] or Decimal('0')
    descuento = datos['descuento'] or Decimal('0')
    paga = datos['paga'] or Decimal('0')
    precio_final = (precio_base * (Decimal('1') - (descuento / Decimal('100')))).quantize(Decimal('0.01'))
    cambio = (paga - precio_final).quantize(Decimal('0.01'))
    
    # Crear inscripción
    inscripcion = Inscripcion.objects.create(
        user=user,
        nombre_persona=datos['nombre_persona'],
        iglesia=datos['iglesia'],
        union=datos['union'],
        sexo=datos['sexo'],
        edad=datos['edad'],
        grupo=grupo,
        costo_total=precio_base,
        descuento=descuento,
        paga=paga,
        cambio=cambio,
        monto_pagado=precio_final
    )
    
    # Crear kit
    LogisticaKit.objects.create(
        inscripcion=inscripcion,
        polera_numero_id=polera_info['numero'],
        polera_talla=polera_info['talla'],
        polera_entregada=False,
        pañoleta_color=polera_info['color_hex'],
        manilla_color=polera_info['color_hex'],
        pañoleta_entregada=False,
        credencial_entregada=False,
        manilla_entregada=False
    )
    
    # Mensaje de éxito
    mensaje = f'✅ <strong>{datos["nombre_persona"]}</strong> registrado(a) exitosamente.<br>'
    mensaje += f'👕 <strong>Polera asignada:</strong> #{polera_info["numero"]} (Talla: {polera_info["talla"]})<br>'
    
    if grupo:
        mensaje += f'🎯 <strong>Equipo:</strong> {grupo.nombre} ({grupo.color_nombre})<br>'
        mensaje += f'🎨 <strong>Color:</strong> {grupo.color_hex}'
    
    if polera_info.get('sin_stock'):
        mensaje += '<br>⚠️ <strong>Atención:</strong> Número asignado sin stock físico disponible'
    
    messages.success(request, mensaje)
    return redirect(f"/inscripcion/lista/?last={inscripcion.id}")

def procesar_inscripcion_doble_completa(request, datos):
    """Procesa una inscripción doble"""
    # Extraer datos de persona 1
    nombre_p1 = datos['nombre_persona']
    datos_p1 = {
        'nombre_persona': nombre_p1,
        'iglesia': datos['iglesia'],
        'union': datos['union'],
        'edad': datos['edad'],
        'sexo': datos['sexo'],
        'costo_total': datos['costo_total'],
        'descuento': datos['descuento'],
        'paga': datos['paga'],
        'talla_polera': datos.get('talla_polera')
    }
    
    # Extraer datos de persona 2
    nombre_p2 = datos['nombre_persona_2']
    datos_p2 = {
        'nombre_persona': nombre_p2,
        'iglesia': datos['iglesia_2'],
        'union': datos['union_2'],
        'edad': datos['edad_2'],
        'sexo': datos['sexo_2'],
        'costo_total': datos['costo_total_2'],
        'descuento': datos['descuento_2'],
        'paga': datos['paga_2'],
        'talla_polera': datos.get('talla_polera_2')
    }
    
    # Validar datos obligatorios
    if not nombre_p1 or not nombre_p2:
        messages.error(request, '❌ Ambas personas deben tener nombre completo')
        return redirect('lista_inscritos')
    
    # Asignar grupo (mismo para ambos)
    grupo = asignar_grupo_automatico(
        int(datos['edad']),
        datos['sexo'],
        datos.get('union')
    )
    
    # Asignar poleras correlativas
    polera_info_p1 = asignar_polera_automatica_con_numero(
        grupo.color_hex if grupo else None,
        datos.get('talla_polera')
    )
    
    polera_info_p2 = asignar_polera_automatica_con_numero(
        grupo.color_hex if grupo else None,
        datos.get('talla_polera_2'),
        polera_info_p1['numero'] + 1  # Número siguiente
    )
    
    # Procesar persona 1
    user_p1 = crear_usuario_automatico(nombre_p1)
    inscripcion_p1 = crear_inscripcion_completa(user_p1, datos_p1, grupo, polera_info_p1)
    
    # Procesar persona 2
    user_p2 = crear_usuario_automatico(nombre_p2)
    inscripcion_p2 = crear_inscripcion_completa(user_p2, datos_p2, grupo, polera_info_p2)
    
    # Mensaje de éxito
    mensaje = f'✅ <strong>Inscripción Doble Exitosa</strong><br><br>'
    mensaje += f'👤 <strong>Persona 1:</strong> {nombre_p1}<br>'
    mensaje += f'&nbsp;&nbsp;&nbsp;👕 Polera #{polera_info_p1["numero"]} (Talla: {polera_info_p1["talla"]})<br><br>'
    mensaje += f'👤 <strong>Persona 2:</strong> {nombre_p2}<br>'
    mensaje += f'&nbsp;&nbsp;&nbsp;👕 Polera #{polera_info_p2["numero"]} (Talla: {polera_info_p2["talla"]})<br><br>'
    
    if grupo:
        mensaje += f'🎯 <strong>Equipo (ambos):</strong> {grupo.nombre}<br>'
        mensaje += f'🎨 <strong>Color:</strong> {grupo.color_nombre or grupo.color_hex}'
    
    messages.success(request, mensaje)
    return redirect(f"/inscripcion/lista/?last={inscripcion_p2.id}")

def crear_inscripcion_completa(user, datos, grupo, polera_info):
    """Crea una inscripción completa"""
    # Calcular precios
    precio_base = datos['costo_total'] or Decimal('0')
    descuento = datos['descuento'] or Decimal('0')
    paga = datos['paga'] or Decimal('0')
    precio_final = (precio_base * (Decimal('1') - (descuento / Decimal('100')))).quantize(Decimal('0.01'))
    cambio = (paga - precio_final).quantize(Decimal('0.01'))
    
    # Crear inscripción
    inscripcion = Inscripcion.objects.create(
        user=user,
        nombre_persona=datos['nombre_persona'],
        iglesia=datos['iglesia'],
        union=datos['union'],
        sexo=datos['sexo'],
        edad=datos['edad'],
        grupo=grupo,
        costo_total=precio_base,
        descuento=descuento,
        paga=paga,
        cambio=cambio,
        monto_pagado=precio_final
    )
    
    # Crear kit
    LogisticaKit.objects.create(
        inscripcion=inscripcion,
        polera_numero_id=polera_info['numero'],
        polera_talla=polera_info['talla'],
        polera_entregada=False,
        pañoleta_color=polera_info['color_hex'],
        manilla_color=polera_info['color_hex'],
        pañoleta_entregada=False,
        credencial_entregada=False,
        manilla_entregada=False
    )
    
    return inscripcion

def asignar_polera_automatica(grupo_color_hex=None, talla_preferida=None):
    """Asigna automáticamente una polera considerando el color del grupo"""
    try:
        if not grupo_color_hex:
            inventario_disponible = InventarioGlobal.objects.filter(
                articulo='polera',
                stock_actual__gt=0
            ).first()
            
            if not inventario_disponible:
                return {
                    'numero': 0,
                    'talla': talla_preferida or 'M',
                    'color_hex': '#000000',
                    'sin_stock': True,
                    'mensaje': 'No hay stock de poleras disponible'
                }
            
            grupo_color_hex = inventario_disponible.color_hex
        
        query = InventarioGlobal.objects.filter(
            articulo='polera',
            color_hex__iexact=grupo_color_hex,
            stock_actual__gt=0
        )
        
        if talla_preferida:
            query = query.filter(talla=talla_preferida)
        
        if not query.exists() and talla_preferida:
            query = InventarioGlobal.objects.filter(
                articulo='polera',
                color_hex__iexact=grupo_color_hex,
                stock_actual__gt=0
            )
        
        inventario_disponible = query.first()
        
        if not inventario_disponible:
            inventario_disponible = InventarioGlobal.objects.filter(
                articulo='polera',
                stock_actual__gt=0
            ).first()
            
            if not inventario_disponible:
                return {
                    'numero': 0,
                    'talla': talla_preferida or 'M',
                    'color_hex': grupo_color_hex or '#000000',
                    'sin_stock': True,
                    'mensaje': 'No hay stock de poleras disponible'
                }
        
        ultimo_numero_color = LogisticaKit.objects.filter(
            pañoleta_color__iexact=inventario_disponible.color_hex
        ).aggregate(Max('polera_numero_id'))['polera_numero_id__max']
        
        proximo_numero = (ultimo_numero_color or 0) + 1
        
        while LogisticaKit.objects.filter(
            polera_numero_id=proximo_numero,
            pañoleta_color__iexact=inventario_disponible.color_hex
        ).exists():
            proximo_numero += 1
        
        inventario_disponible.stock_actual -= 1
        inventario_disponible.save()
        
        return {
            'numero': proximo_numero,
            'talla': inventario_disponible.talla,
            'color_hex': inventario_disponible.color_hex,
            'color_nombre': inventario_disponible.color_nombre,
            'sin_stock': False,
            'mensaje': f'Polera asignada: #{proximo_numero} ({inventario_disponible.color_nombre})'
        }
        
    except Exception as e:
        return {
            'numero': 0,
            'talla': talla_preferida or 'M',
            'color_hex': grupo_color_hex or '#000000',
            'sin_stock': True,
            'mensaje': f'Error al asignar polera: {str(e)}'
        }

def asignar_polera_automatica_con_numero(grupo_color_hex=None, talla_preferida=None, numero_forzado=None):
    """Versión modificada que acepta número forzado para inscripciones correlativas"""
    try:
        # Si se especifica número forzado (inscripción doble)
        if numero_forzado:
            numero = numero_forzado
        else:
            ultimo_numero_color = LogisticaKit.objects.filter(
                pañoleta_color__iexact=grupo_color_hex
            ).aggregate(Max('polera_numero_id'))['polera_numero_id__max']
            
            numero = (ultimo_numero_color or 0) + 1
            
            while LogisticaKit.objects.filter(
                polera_numero_id=numero,
                pañoleta_color__iexact=grupo_color_hex
            ).exists():
                numero += 1
        
        # Buscar polera en inventario
        if not grupo_color_hex:
            inventario_disponible = InventarioGlobal.objects.filter(
                articulo='polera',
                stock_actual__gt=0
            ).first()
            
            if not inventario_disponible:
                return {
                    'numero': numero,
                    'talla': talla_preferida or 'M',
                    'color_hex': '#000000',
                    'sin_stock': True
                }
            
            grupo_color_hex = inventario_disponible.color_hex
        
        query = InventarioGlobal.objects.filter(
            articulo='polera',
            color_hex__iexact=grupo_color_hex,
            stock_actual__gt=0
        )
        
        if talla_preferida:
            query = query.filter(talla=talla_preferida)
        
        if not query.exists() and talla_preferida:
            query = InventarioGlobal.objects.filter(
                articulo='polera',
                color_hex__iexact=grupo_color_hex,
                stock_actual__gt=0
            )
        
        inventario_disponible = query.first()
        
        if not inventario_disponible:
            inventario_disponible = InventarioGlobal.objects.filter(
                articulo='polera',
                stock_actual__gt=0
            ).first()
            
            if not inventario_disponible:
                return {
                    'numero': numero,
                    'talla': talla_preferida or 'M',
                    'color_hex': grupo_color_hex or '#000000',
                    'sin_stock': True
                }
        
        # Reducir stock
        inventario_disponible.stock_actual -= 1
        inventario_disponible.save()
        
        return {
            'numero': numero,
            'talla': inventario_disponible.talla,
            'color_hex': inventario_disponible.color_hex,
            'color_nombre': inventario_disponible.color_nombre,
            'sin_stock': False
        }
        
    except Exception as e:
        return {
            'numero': numero if 'numero' in locals() else 0,
            'talla': talla_preferida or 'M',
            'color_hex': grupo_color_hex or '#000000',
            'sin_stock': True
        }

# ============ FUNCIONES API/AJAX ============
def ultima_inscripcion_ajax(request):
    """API para obtener la última inscripción en tiempo real"""
    try:
        last = Inscripcion.objects.select_related('grupo', 'iglesia').latest('id')
        data = {
            'id': last.id,
            'nombre': last.nombre_persona,
            'equipo': last.grupo.nombre if last.grupo else 'Sin equipo',
            'color': last.grupo.color_hex if last.grupo else '#10B981',
            'iglesia': last.iglesia.nombre if last.iglesia else 'General',
        }
        return JsonResponse(data)
    except Inscripcion.DoesNotExist:
        return JsonResponse({'error': 'No hay inscripciones'}, status=404)

@require_GET
def api_colores_existentes(request):
    """API para obtener colores existentes por artículo y talla"""
    articulo = request.GET.get('articulo')
    talla = request.GET.get('talla')
    
    if not articulo or not talla:
        return JsonResponse({
            'success': False,
            'error': 'Faltan parámetros: articulo y talla son requeridos'
        }, status=400)
    
    try:
        articulos_validos = [choice[0] for choice in InventarioGlobal.ARTICULOS]
        if articulo not in articulos_validos:
            return JsonResponse({
                'success': False,
                'error': f'Artículo inválido. Opciones válidas: {", ".join(articulos_validos)}'
            }, status=400)
        
        colores = InventarioGlobal.objects.filter(
            articulo=articulo,
            talla=talla
        ).exclude(
            color_hex__isnull=True
        ).exclude(
            color_hex=''
        ).order_by('color_nombre', 'color_hex')
        
        colores_unicos = []
        colores_vistos = set()
        
        for item in colores:
            key = (item.color_hex, item.color_nombre or '')
            if key not in colores_vistos:
                colores_vistos.add(key)
                colores_unicos.append({
                    'id': item.id,
                    'hex': item.color_hex,
                    'nombre': item.color_nombre or item.color_hex,
                    'stock_actual': item.stock_actual,
                    'texto': f"{item.color_nombre or item.color_hex} ({item.color_hex}) - Stock: {item.stock_actual}"
                })
        
        return JsonResponse({
            'success': True,
            'colores': colores_unicos,
            'count': len(colores_unicos),
            'articulo': articulo,
            'talla': talla,
            'articulo_display': dict(InventarioGlobal.ARTICULOS).get(articulo, articulo)
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

def tallas_disponibles_api(request):
    """API para obtener tallas disponibles de poleras"""
    try:
        tallas = InventarioGlobal.objects.filter(
            articulo='polera',
            stock_actual__gt=0
        ).values('talla').distinct()
        
        tallas_list = [item['talla'] for item in tallas if item['talla']]
        
        return JsonResponse({
            'success': True,
            'tallas': tallas_list,
            'count': len(tallas_list)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'tallas': []
        })

# ============ VISTAS DE KITS E INVENTARIO ============
def entregar_kit(request, insc_id):
    """Vista para entregar kit con control de inventario POR COLOR"""
    from django.utils import timezone
    
    insc = get_object_or_404(Inscripcion, id=insc_id)
    kit = getattr(insc, 'logisticakit', None)
    
    if not kit:
        messages.error(request, 'No se encontró kit para esta inscripción.')
        return redirect('lista_inscritos')
    
    color_grupo = insc.grupo.color_hex if insc.grupo else None
    color_nombre = insc.grupo.color_nombre if insc.grupo else None
    
    # ========== CALCULAR PRÓXIMO NÚMERO PARA ESTE COLOR ==========
    proximo_numero = 0
    poleras_asignadas_color = []
    
    if color_grupo:
        # Buscar poleras ya asignadas de este color
        poleras_asignadas_color = LogisticaKit.objects.filter(
            pañoleta_color__iexact=color_grupo,
            polera_numero_id__isnull=False
        ).exclude(id=kit.id).order_by('polera_numero_id')
        
        # Contar poleras asignadas
        conteo_poleras_color = poleras_asignadas_color.count()
        
        # Ajustar para Naranja
        if color_nombre and color_nombre.upper() == "NARANJA":
            proximo_numero = 8 + conteo_poleras_color
        else:
            proximo_numero = conteo_poleras_color
        
        # Verificar que el número no esté usado
        while LogisticaKit.objects.filter(
            polera_numero_id=proximo_numero,
            pañoleta_color__iexact=color_grupo
        ).exclude(id=kit.id).exists():
            proximo_numero += 1
    
    if request.method == 'POST':
        polera_talla = request.POST.get('polera_talla')
        polera_num = request.POST.get('polera_numero_id')
        pañoleta = request.POST.get('pañoleta_entregada') == 'on'
        credencial = request.POST.get('credencial_entregada') == 'on'
        manilla = request.POST.get('manilla_entregada') == 'on'

        # ========== VALIDAR QUE AL MENOS UN ELEMENTO SEA MARCADO ==========
        elementos_entregados = []
        elementos_nuevos = 0
        
        # Verificar si hay elementos nuevos por entregar
        if polera_talla and not kit.polera_entregada:
            elementos_nuevos += 1
        if pañoleta and not kit.pañoleta_entregada:
            elementos_nuevos += 1
        if credencial and not kit.credencial_entregada:
            elementos_nuevos += 1
        if manilla and not kit.manilla_entregada:
            elementos_nuevos += 1
        
        # Si no hay elementos nuevos para entregar, mostrar error
        if elementos_nuevos == 0:
            messages.error(request, '⚠️ Por favor, marca al menos un elemento del kit como entregado.')
            return redirect('entregar_kit', insc_id=insc_id)
        
        # ========== PROCESAR LA POLERA ==========
        if polera_talla:
            kit.polera_talla = polera_talla
        
        if polera_num:
            try:
                requested = int(polera_num)
                conflict = LogisticaKit.objects.filter(
                    polera_numero_id=requested,
                    pañoleta_color__iexact=color_grupo
                ).exclude(id=kit.id).first()
                
                if conflict:
                    # Encontrar próximo número disponible
                    candidate = proximo_numero
                    while LogisticaKit.objects.filter(
                        polera_numero_id=candidate,
                        pañoleta_color__iexact=color_grupo
                    ).exclude(id=kit.id).exists():
                        candidate += 1
                    
                    kit.polera_numero_id = candidate
                    messages.warning(request, f'Número {requested} ya asignado en color {color_nombre or color_grupo}; se usó {candidate}.')
                else:
                    kit.polera_numero_id = requested
            except ValueError:
                # Si no se especifica número, usar el calculado
                kit.polera_numero_id = proximo_numero
        else:
            # Asignar número calculado automáticamente
            kit.polera_numero_id = proximo_numero
        
        delivered = []
        errors = []
        
        # ========== ENTREGAR POLERA ==========
        if polera_talla and not kit.polera_entregada:
            polera_inv = InventarioGlobal.objects.filter(
                articulo='polera',
                talla=polera_talla,
                color_hex__iexact=color_grupo,
                stock_actual__gt=0
            ).first()
            
            if polera_inv:
                kit.polera_entregada = True
                delivered.append('polera')
                polera_inv.stock_actual -= 1
                polera_inv.save()
                messages.info(request, f'✅ Polera {color_nombre or color_grupo} talla {polera_talla} entregada.')
            else:
                errors.append(f'❌ No hay stock de polera {color_nombre or color_grupo} talla {polera_talla}.')
        
        # ========== ENTREGAR PAÑOLETA ==========
        if pañoleta and not kit.pañoleta_entregada:
            pañoleta_inv = InventarioGlobal.objects.filter(
                articulo='pañoleta',
                talla='unica',
                color_hex__iexact=color_grupo,
                stock_actual__gt=0
            ).first()
            
            if pañoleta_inv:
                kit.pañoleta_entregada = True
                kit.pañoleta_color = color_grupo
                delivered.append('pañoleta')
                pañoleta_inv.stock_actual -= 1
                pañoleta_inv.save()
                messages.info(request, f'✅ Pañoleta {color_nombre or color_grupo} entregada.')
            else:
                errors.append(f'❌ No hay stock de pañoleta {color_nombre or color_grupo}.')
        
        # ========== ENTREGAR CREDENCIAL ==========
        if credencial and not kit.credencial_entregada:
            credencial_inv = InventarioGlobal.objects.filter(
                articulo='credencial',
                stock_actual__gt=0
            ).first()
            
            if credencial_inv:
                kit.credencial_entregada = True
                delivered.append('credencial')
                credencial_inv.stock_actual -= 1
                credencial_inv.save()
                messages.info(request, '✅ Credencial entregada.')
            else:
                errors.append('❌ No hay stock de credenciales.')
        
        # ========== ENTREGAR MANILLA ==========
        if manilla and not kit.manilla_entregada:
            manilla_inv = InventarioGlobal.objects.filter(
                articulo='manilla',
                talla='unica',
                color_hex__iexact=color_grupo,
                stock_actual__gt=0
            ).first()
            
            if manilla_inv:
                kit.manilla_entregada = True
                kit.manilla_color = color_grupo
                delivered.append('manilla')
                manilla_inv.stock_actual -= 1
                manilla_inv.save()
                messages.info(request, f'✅ Manilla {color_nombre or color_grupo} entregada.')
            else:
                errors.append(f'❌ No hay stock de manilla {color_nombre or color_grupo}.')
        
        # ========== GUARDAR CAMBIOS ==========
        if delivered or errors:
            kit.entregado_por = request.user if request.user.is_authenticated else None
            kit.fecha_entrega = timezone.now()
            kit.save()

        if delivered:
            messages.success(request, f'🎉 Kit actualizado para {insc.nombre_persona}. Elementos entregados: {", ".join(delivered)}')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        
        return redirect('lista_inscritos')
    
    # Preparar datos para el template (GET request)
    poleras_disponibles = InventarioGlobal.objects.filter(
        articulo='polera',
        color_hex__iexact=color_grupo,
        stock_actual__gt=0
    ).order_by('talla') if color_grupo else []
    
    pañoletas_disponibles = InventarioGlobal.objects.filter(
        articulo='pañoleta',
        color_hex__iexact=color_grupo,
        stock_actual__gt=0
    ).first() if color_grupo else None
    
    credenciales_disponibles = InventarioGlobal.objects.filter(
        articulo='credencial',
        stock_actual__gt=0
    ).first()
    
    manillas_disponibles = InventarioGlobal.objects.filter(
        articulo='manilla',
        color_hex__iexact=color_grupo,
        stock_actual__gt=0
    ).first() if color_grupo else None
    
    tallas_polera = []
    if color_grupo:
        tallas_polera = poleras_disponibles.values_list('talla', flat=True).distinct()
    
    # Preparar lista de poleras asignadas para mostrar
    poleras_asignadas_para_template = []
    for polera_kit in poleras_asignadas_color:
        poleras_asignadas_para_template.append({
            'numero': polera_kit.polera_numero_id,
            'talla': polera_kit.polera_talla,
            'nombre': polera_kit.inscripcion.nombre_persona if polera_kit.inscripcion else ''
        })
    
    return render(request, 'principal/entregar_kit.html', {
        'insc': insc,
        'kit': kit,
        'color_grupo': color_grupo,
        'color_nombre': color_nombre,
        'proximo_numero_polera': proximo_numero,
        'poleras_disponibles': poleras_disponibles,
        'pañoletas_disponibles': pañoletas_disponibles,
        'credenciales_disponibles': credenciales_disponibles,
        'manillas_disponibles': manillas_disponibles,
        'tallas_polera': list(tallas_polera),
        'poleras_asignadas_color': poleras_asignadas_para_template,
        'hay_stock_polera': poleras_disponibles.exists() if hasattr(poleras_disponibles, 'exists') else False,
        'hay_stock_pañoleta': pañoletas_disponibles is not None,
        'hay_stock_credencial': credenciales_disponibles is not None,
        'hay_stock_manilla': manillas_disponibles is not None,
    })

@require_role('admin', 'director')
def gestionar_poleras(request):
    """Vista para gestionar inventario de poleras"""
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.articulo = 'polera'
            item.autor = request.user
            item.stock_total = item.stock_actual
            item.save()
            messages.success(request, f'Polera {item.color_nombre} talla {item.talla} agregada al inventario')
            return redirect('gestionar_poleras')
    else:
        form = InventarioForm(initial={'articulo': 'polera'})
    
    # Estadísticas
    poleras = InventarioGlobal.objects.filter(articulo='polera').order_by('color_nombre', 'talla')
    total_stock = sum(p.stock_actual for p in poleras)
    total_asignadas = sum(len(p.numeros_asignados.split(',')) for p in poleras if p.numeros_asignados)
    
    return render(request, 'principal/gestionar_poleras.html', {
        'form': form,
        'poleras': poleras,
        'total_stock': total_stock,
        'total_asignadas': total_asignadas,
        'disponibles': total_stock - total_asignadas,
    })

# ============ VISTAS DE PUNTOS Y COMPETENCIA ============
@require_role('director', 'admin')
def agregar_puntos(request):
    """Vista para agregar puntos a grupos"""
    if request.method == 'POST':
        form = HistorialPuntosForm(request.POST)
        if form.is_valid():
            historial = form.save(commit=False)
            historial.autor = request.user if request.user.is_authenticated else None
            historial.save()
            
            grupo = historial.grupo
            grupo.puntos_totales += historial.cantidad
            grupo.save()
            
            messages.success(request, f'Se agregaron {historial.cantidad} puntos a {grupo.nombre}')
            return redirect('ranking')
    else:
        form = HistorialPuntosForm()
    
    return render(request, 'principal/agregar_puntos.html', {'form': form})

def historial_puntos(request, grupo_id=None):
    """Vista del historial de puntos por grupo"""
    if grupo_id:
        grupo = get_object_or_404(Grupo, id=grupo_id)
        historial = HistorialPuntos.objects.filter(grupo=grupo).order_by('-fecha')
        return render(request, 'principal/historial_puntos.html', {'grupo': grupo, 'historial': historial})
    else:
        grupos = Grupo.objects.all().order_by('-puntos_totales')
        return render(request, 'principal/historial_puntos.html', {'grupos': grupos})

# ============ VISTAS DE USUARIOS ============
def listar_usuarios(request):
    """Lista todos los usuarios"""
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'principal/usuarios_lista.html', {'usuarios': usuarios})

def crear_usuario(request):
    """Crea un nuevo usuario"""
    if request.method == 'POST':
        form = UsuarioCrearForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario {user.username} creado correctamente.')
            return redirect('listar_usuarios')
    else:
        form = UsuarioCrearForm()
    
    return render(request, 'principal/usuario_crear.html', {'form': form})

def editar_usuario(request, usuario_id):
    """Edita un usuario existente"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        form = UsuarioEditarForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario {usuario.username} actualizado correctamente.')
            return redirect('listar_usuarios')
    else:
        form = UsuarioEditarForm(instance=usuario)
    
    return render(request, 'principal/usuario_editar.html', {'form': form, 'usuario': usuario})

def eliminar_usuario(request, usuario_id):
    """Elimina un usuario"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario {username} eliminado correctamente.')
        return redirect('listar_usuarios')
    
    return render(request, 'principal/usuario_eliminar.html', {'usuario': usuario})

# ============ VISTAS DE INVENTARIO ============
def listar_inventario(request):
    """Lista todo el inventario"""
    items = InventarioGlobal.objects.all().order_by('articulo', 'color_nombre', 'talla')
    return render(request, 'principal/inventario_lista.html', {'items': items})

def crear_inventario(request):
    """Crea un nuevo item en el inventario"""
    if not request.user.is_authenticated:
        messages.error(request, 'Debes estar autenticado para crear inventario.')
        return redirect('login')
    
    grupos = Grupo.objects.all().order_by('nombre')
    
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.autor = request.user
            
            color_hex = request.POST.get('color_hex')
            color_nombre = request.POST.get('color_nombre')
            
            if not color_hex or not color_nombre:
                messages.error(request, '⚠️ Debes seleccionar un color de equipo')
                return render(request, 'principal/inventario_crear.html', {
                    'form': form,
                    'grupos': grupos,
                    'titulo': 'Crear Artículo en Inventario'
                })
            
            inv.color_hex = color_hex
            inv.color_nombre = color_nombre
            inv.stock_total = inv.stock_actual
            inv.save()
            
            messages.success(request, f'✅ Artículo {inv.get_articulo_display()} ({inv.color_nombre}) registrado correctamente.')
            return redirect('listar_inventario')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = InventarioForm()
    
    return render(request, 'principal/inventario_crear.html', {
        'form': form,
        'grupos': grupos,
        'titulo': 'Crear Artículo en Inventario'
    })

def editar_inventario(request, item_id):
    """Edita un item del inventario"""
    item = get_object_or_404(InventarioGlobal, id=item_id)
    
    grupos = Grupo.objects.all().order_by('nombre')
    
    if request.method == 'POST':
        form = InventarioForm(request.POST, instance=item)
        if form.is_valid():
            inv = form.save(commit=False)
            
            color_hex = request.POST.get('color_hex')
            color_nombre = request.POST.get('color_nombre')
            
            if not color_hex or not color_nombre:
                messages.error(request, '⚠️ Debes seleccionar un color de equipo')
                return render(request, 'principal/inventario_crear.html', {
                    'form': form,
                    'item': item,
                    'grupos': grupos,
                    'titulo': f'Editar {item.get_articulo_display()}'
                })
            
            inv.color_hex = color_hex
            inv.color_nombre = color_nombre
            inv.save()
            
            messages.success(request, '✅ Inventario actualizado correctamente.')
            return redirect('listar_inventario')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = InventarioForm(instance=item)
    
    return render(request, 'principal/inventario_crear.html', {
        'form': form,
        'item': item,
        'grupos': grupos,
        'titulo': f'Editar {item.get_articulo_display()}'
    })

def eliminar_inventario(request, item_id):
    """Elimina un item del inventario"""
    item = get_object_or_404(InventarioGlobal, id=item_id)
    
    if request.method == 'POST':
        articulo = item.get_articulo_display()
        color = item.color_nombre
        item.delete()
        messages.success(request, f'✅ Artículo {articulo} ({color}) eliminado correctamente.')
        return redirect('listar_inventario')
    
    return render(request, 'principal/inventario_eliminar.html', {'item': item})

# ============ VISTAS DE PERFIL ============
def mi_perfil(request):
    """Vista del perfil del usuario actual"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    usuario = request.user
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        nueva_contrasena = request.POST.get('nueva_contrasena')
        confirmar_contrasena = request.POST.get('confirmar_contrasena')
        contrasena_actual = request.POST.get('contrasena_actual')
        
        if nueva_contrasena:
            if not usuario.check_password(contrasena_actual):
                messages.error(request, 'Contraseña actual incorrecta.')
                return render(request, 'principal/mi_perfil.html', {'usuario': usuario})
            
            if nueva_contrasena != confirmar_contrasena:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'principal/mi_perfil.html', {'usuario': usuario})
            
            if len(nueva_contrasena) < 6:
                messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
                return render(request, 'principal/mi_perfil.html', {'usuario': usuario})
            
            usuario.set_password(nueva_contrasena)
        
        usuario.email = email
        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.save()
        
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('mi_perfil')
    
    return render(request, 'principal/mi_perfil.html', {'usuario': usuario})

# ============ VISTAS DE LIKES Y COMENTARIOS ============
def agregar_like(request, publicacion_id):
    """Agrega o quita un like a una publicación"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    
    reaccion_existente = Reaccion.objects.filter(
        publicacion=publicacion, 
        usuario=request.user, 
        tipo='like'
    ).first()
    
    if reaccion_existente:
        reaccion_existente.delete()
        liked = False
    else:
        Reaccion.objects.create(
            publicacion=publicacion,
            usuario=request.user,
            tipo='like'
        )
        liked = True
    
    total_likes = Reaccion.objects.filter(
        publicacion=publicacion,
        tipo='like'
    ).count()
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'total_likes': total_likes
    })

def agregar_comentario(request, publicacion_id):
    """Agrega un comentario a una publicación"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    publicacion = get_object_or_404(Publicacion, id=publicacion_id)
    
    if request.method == 'POST':
        texto = request.POST.get('texto', '').strip()
        if texto:
            Comentario.objects.create(
                publicacion=publicacion,
                usuario=request.user,
                texto=texto
            )
            messages.success(request, 'Comentario agregado correctamente.')
        else:
            messages.error(request, 'El comentario no puede estar vacío.')
    
    return redirect('muro')

def eliminar_comentario(request, comentario_id):
    """Elimina un comentario"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    comentario = get_object_or_404(Comentario, id=comentario_id)
    
    if comentario.usuario != request.user and not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para eliminar este comentario.')
        return redirect('muro')
    
    comentario.delete()
    messages.success(request, 'Comentario eliminado.')
    return redirect('muro')

# ============ CRUD DE GRUPOS ============
@require_role('director', 'admin')
def listar_grupos(request):
    """Lista todos los grupos"""
    grupos = Grupo.objects.all().order_by('nombre')
    return render(request, 'principal/grupo_lista.html', {'grupos': grupos})

@require_role('director', 'admin')
def crear_grupo(request):
    """Crea un nuevo grupo"""
    if request.method == 'POST':
        form = GrupoForm(request.POST, request.FILES)
        if form.is_valid():
            grupo = form.save()
            messages.success(request, f'Grupo "{grupo.nombre}" creado correctamente.')
            return redirect('listar_grupos')
    else:
        form = GrupoForm()
    return render(request, 'principal/grupo_crear.html', {'form': form})

@require_role('director', 'admin')
def editar_grupo(request, grupo_id):
    """Edita un grupo existente"""
    grupo = get_object_or_404(Grupo, id=grupo_id)
    
    if request.method == 'POST':
        form = GrupoForm(request.POST, request.FILES, instance=grupo)
        if form.is_valid():
            grupo = form.save()
            messages.success(request, f'Grupo "{grupo.nombre}" actualizado correctamente.')
            return redirect('listar_grupos')
    else:
        form = GrupoForm(instance=grupo)
    
    return render(request, 'principal/grupo_editar.html', {'form': form, 'grupo': grupo})

@require_role('director', 'admin')
def eliminar_grupo(request, grupo_id):
    """Elimina un grupo"""
    grupo = get_object_or_404(Grupo, id=grupo_id)
    
    if request.method == 'POST':
        nombre = grupo.nombre
        grupo.delete()
        messages.success(request, f'Grupo "{nombre}" eliminado correctamente.')
        return redirect('listar_grupos')
    
    return render(request, 'principal/grupo_eliminar.html', {'grupo': grupo})

# ============ CRUD DE ACTIVIDADES ============
@require_role('campamentista', 'inscripcion', 'director', 'admin', 'lider')
def listar_actividades(request):
    """Listar todas las actividades en cronograma"""
    actividades = Actividad.objects.all().order_by('hora_inicio')
    
    es_obligatoria = request.GET.get('obligatoria')
    if es_obligatoria == 'true':
        actividades = actividades.filter(es_obligatoria=True)
    elif es_obligatoria == 'false':
        actividades = actividades.filter(es_obligatoria=False)
    
    return render(request, 'principal/actividad_lista.html', {
        'actividades': actividades,
        'hoy': timezone.now().date(),
    })

@require_role('director', 'admin')
def crear_actividad(request):
    """Crear una nueva actividad"""
    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.autor = request.user
            actividad.save()
            messages.success(request, f'Actividad "{actividad.titulo}" creada correctamente.')
            return redirect('listar_actividades')
    else:
        form = ActividadForm()
    return render(request, 'principal/actividad_crear.html', {'form': form})

@require_role('director', 'admin')
def editar_actividad(request, actividad_id):
    """Editar una actividad existente"""
    actividad = get_object_or_404(Actividad, id=actividad_id)
    
    if request.method == 'POST':
        form = ActividadForm(request.POST, instance=actividad)
        if form.is_valid():
            actividad = form.save()
            messages.success(request, f'Actividad "{actividad.titulo}" actualizada correctamente.')
            return redirect('listar_actividades')
    else:
        form = ActividadForm(instance=actividad)
    
    return render(request, 'principal/actividad_editar.html', {'form': form, 'actividad': actividad})

@require_role('director', 'admin')
def eliminar_actividad(request, actividad_id):
    """Eliminar una actividad"""
    actividad = get_object_or_404(Actividad, id=actividad_id)
    
    if request.method == 'POST':
        titulo = actividad.titulo
        actividad.delete()
        messages.success(request, f'Actividad "{titulo}" eliminada correctamente.')
        return redirect('listar_actividades')
    
    return render(request, 'principal/actividad_eliminar.html', {'actividad': actividad})

# ============ CRUD DE NOTICIAS ============
def listar_noticias(request):
    """Listar todas las noticias"""
    noticias = Noticia.objects.all().order_by('-fecha_publicacion')
    return render(request, 'principal/noticia_lista.html', {'noticias': noticias})

def crear_noticia(request):
    """Crear una nueva noticia"""
    if request.method == 'POST':
        form = NoticiaForm(request.POST)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor = request.user
            noticia.save()
            usuarios = Usuario.objects.all()
            for usuario in usuarios:
                Notificacion.objects.create(
                    usuario=usuario,
                    titulo=f'Nueva noticia: {noticia.titulo}',
                    mensaje=noticia.contenido[:100] + '...',
                    tipo='noticia'
                )
            messages.success(request, f'Noticia "{noticia.titulo}" creada correctamente.')
            return redirect('listar_noticias')
    else:
        form = NoticiaForm()
    return render(request, 'principal/noticia_crear.html', {'form': form})

def editar_noticia(request, noticia_id):
    """Editar una noticia existente"""
    noticia = get_object_or_404(Noticia, id=noticia_id)
    
    if request.method == 'POST':
        form = NoticiaForm(request.POST, instance=noticia)
        if form.is_valid():
            noticia = form.save()
            messages.success(request, f'Noticia "{noticia.titulo}" actualizada correctamente.')
            return redirect('listar_noticias')
    else:
        form = NoticiaForm(instance=noticia)
    
    return render(request, 'principal/noticia_editar.html', {'form': form, 'noticia': noticia})

def eliminar_noticia(request, noticia_id):
    """Eliminar una noticia"""
    noticia = get_object_or_404(Noticia, id=noticia_id)
    
    if request.method == 'POST':
        titulo = noticia.titulo
        noticia.delete()
        messages.success(request, f'Noticia "{titulo}" eliminada correctamente.')
        return redirect('listar_noticias')
    
    return render(request, 'principal/noticia_eliminar.html', {'noticia': noticia})

# ============ VISTAS DE NOTIFICACIONES ============
def listar_notificaciones(request):
    """Listar las notificaciones del usuario"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    notificaciones = request.user.notificaciones.all()
    no_leidas = notificaciones.filter(leida=False).count()
    
    return render(request, 'principal/notificacion_lista.html', {
        'notificaciones': notificaciones,
        'no_leidas': no_leidas,
    })

def marcar_notificacion_leida(request, notificacion_id):
    """Marcar una notificación como leída"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
    notificacion.leida = True
    notificacion.save()
    
    return redirect('listar_notificaciones')

def marcar_todas_leidas(request):
    """Marcar todas las notificaciones como leídas"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    request.user.notificaciones.filter(leida=False).update(leida=True)
    messages.success(request, 'Todas las notificaciones marcadas como leídas.')
    
    return redirect('listar_notificaciones')

def eliminar_notificacion(request, notificacion_id):
    """Eliminar una notificación"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
    notificacion.delete()
    messages.success(request, 'Notificación eliminada.')
    
    return redirect('listar_notificaciones')

# ============ VISTAS PARA IGLESIAS Y UNIONES ============
@login_required
def gestionar_iglesias_uniones(request):
    """
    Vista unificada para gestionar iglesias y uniones en una sola página
    """
    if request.user.rol not in ['admin', 'director', 'inscripcion']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('dashboard')
    
    # Contexto inicial
    context = {
        'titulo': 'Gestión de Iglesias y Uniones',
        'active_tab': 'iglesias'  # Tab por defecto
    }
    
    # Obtener datos
    iglesias = Iglesia.objects.all().order_by('nombre')
    uniones = Union.objects.all().order_by('nombre')
    
    # Manejar creación/edición de iglesias
    if 'accion_iglesia' in request.GET:
        accion = request.GET.get('accion_iglesia')
        iglesia_id = request.GET.get('iglesia_id')
        
        if accion == 'crear':
            form_iglesia = IglesiaForm()
            context.update({
                'mostrar_form_iglesia': True,
                'form_iglesia': form_iglesia,
                'accion_iglesia': 'crear'
            })
        
        elif accion == 'editar' and iglesia_id:
            try:
                iglesia = Iglesia.objects.get(id=iglesia_id)
                form_iglesia = IglesiaForm(instance=iglesia)
                context.update({
                    'mostrar_form_iglesia': True,
                    'form_iglesia': form_iglesia,
                    'iglesia_actual': iglesia,
                    'accion_iglesia': 'editar'
                })
            except Iglesia.DoesNotExist:
                messages.error(request, 'Iglesia no encontrada.')
        
        elif accion == 'eliminar' and iglesia_id:
            try:
                iglesia = Iglesia.objects.get(id=iglesia_id)
                context.update({
                    'mostrar_eliminar_iglesia': True,
                    'iglesia_a_eliminar': iglesia
                })
            except Iglesia.DoesNotExist:
                messages.error(request, 'Iglesia no encontrada.')
    
    # Manejar creación/edición de uniones
    if 'accion_union' in request.GET:
        context['active_tab'] = 'uniones'
        accion = request.GET.get('accion_union')
        union_id = request.GET.get('union_id')
        
        if accion == 'crear':
            form_union = UnionForm()
            context.update({
                'mostrar_form_union': True,
                'form_union': form_union,
                'accion_union': 'crear'
            })
        
        elif accion == 'editar' and union_id:
            try:
                union = Union.objects.get(id=union_id)
                form_union = UnionForm(instance=union)
                context.update({
                    'mostrar_form_union': True,
                    'form_union': form_union,
                    'union_actual': union,
                    'accion_union': 'editar'
                })
            except Union.DoesNotExist:
                messages.error(request, 'Unión no encontrada.')
        
        elif accion == 'eliminar' and union_id:
            try:
                union = Union.objects.get(id=union_id)
                context.update({
                    'mostrar_eliminar_union': True,
                    'union_a_eliminar': union
                })
            except Union.DoesNotExist:
                messages.error(request, 'Unión no encontrada.')
    
    # Manejar POST para iglesias
    if request.method == 'POST':
        if 'form_iglesia_submit' in request.POST:
            iglesia_id = request.POST.get('iglesia_id')
            
            if iglesia_id:  # Editar
                try:
                    iglesia = Iglesia.objects.get(id=iglesia_id)
                    form_iglesia = IglesiaForm(request.POST, instance=iglesia)
                except Iglesia.DoesNotExist:
                    messages.error(request, 'Iglesia no encontrada.')
                    return redirect('gestionar_iglesias_uniones')
            else:  # Crear
                form_iglesia = IglesiaForm(request.POST)
            
            if form_iglesia.is_valid():
                form_iglesia.save()
                messages.success(request, f'Iglesia {"actualizada" if iglesia_id else "creada"} exitosamente.')
                return redirect('gestionar_iglesias_uniones')
            else:
                context.update({
                    'mostrar_form_iglesia': True,
                    'form_iglesia': form_iglesia,
                    'accion_iglesia': 'editar' if iglesia_id else 'crear',
                    'active_tab': 'iglesias'
                })
        
        elif 'form_union_submit' in request.POST:
            union_id = request.POST.get('union_id')
            
            if union_id:  # Editar
                try:
                    union = Union.objects.get(id=union_id)
                    form_union = UnionForm(request.POST, instance=union)
                except Union.DoesNotExist:
                    messages.error(request, 'Unión no encontrada.')
                    return redirect('gestionar_iglesias_uniones')
            else:  # Crear
                form_union = UnionForm(request.POST)
            
            if form_union.is_valid():
                form_union.save()
                messages.success(request, f'Unión {"actualizada" if union_id else "creada"} exitosamente.')
                return redirect('gestionar_iglesias_uniones')
            else:
                context.update({
                    'mostrar_form_union': True,
                    'form_union': form_union,
                    'accion_union': 'editar' if union_id else 'crear',
                    'active_tab': 'uniones'
                })
        
        elif 'eliminar_iglesia_confirm' in request.POST:
            iglesia_id = request.POST.get('iglesia_id')
            if iglesia_id and request.user.rol == 'admin':
                try:
                    iglesia = Iglesia.objects.get(id=iglesia_id)
                    # Verificar si tiene inscripciones
                    if hasattr(iglesia, 'inscripcion_set'):
                        if iglesia.inscripcion_set.exists():
                            messages.error(request, 'No se puede eliminar esta iglesia porque tiene inscripciones asociadas.')
                            return redirect('gestionar_iglesias_uniones')
                    
                    iglesia.delete()
                    messages.success(request, 'Iglesia eliminada exitosamente.')
                except Iglesia.DoesNotExist:
                    messages.error(request, 'Iglesia no encontrada.')
            
            return redirect('gestionar_iglesias_uniones')
        
        elif 'eliminar_union_confirm' in request.POST:
            union_id = request.POST.get('union_id')
            if union_id and request.user.rol == 'admin':
                try:
                    union = Union.objects.get(id=union_id)
                    # Verificar si tiene inscripciones
                    if Inscripcion.objects.filter(union=union).exists():
                        messages.error(request, 'No se puede eliminar esta unión porque tiene inscripciones asociadas.')
                        return redirect('gestionar_iglesias_uniones')
                    
                    union.delete()
                    messages.success(request, 'Unión eliminada exitosamente.')
                except Union.DoesNotExist:
                    messages.error(request, 'Unión no encontrada.')
            
            return redirect('gestionar_iglesias_uniones')
    
    # Añadir datos al contexto
    context.update({
        'iglesias': iglesias,
        'uniones': uniones,
        'es_admin': request.user.rol == 'admin'
    })
    
    return render(request, 'principal/gestion_iglesias_uniones.html', context)

def registrar_inscrito(request):
    """Redirige a la lista de inscritos con el formulario visible"""
    return redirect(f"{request.scheme}://{request.get_host()}{'/inscripcion/lista/'}?show=form")