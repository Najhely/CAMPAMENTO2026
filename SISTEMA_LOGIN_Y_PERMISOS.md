# 🔐 Sistema de Login y Permisos - Campamento 2026

## Overview
Se ha implementado un sistema completo de autenticación y autorización basado en roles (RBAC) para el sistema de gestión de campamento.

---

## 📋 Roles Implementados

### 1. **Campamentista** 
- **Permisos:**
  - ✅ Ver Red Social (Muro)
  - ✅ Ver Ranking de Puntos
  - ✅ Ver Actividades (solo lectura, cronograma)
  - ✅ Ver Noticias
  - ✅ Ver Notificaciones

- **Restricciones:**
  - ❌ No puede crear/editar Grupos
  - ❌ No puede crear/editar Actividades
  - ❌ No puede crear/editar Noticias
  - ❌ No puede gestionar Puntos
  - ❌ No puede ver Usuarios ni Inventario

### 2. **Director**
- **Permisos:**
  - ✅ Acceso a Red Social (Muro)
  - ✅ Ver y Gestionar Actividades (crear, editar, eliminar)
  - ✅ Ver y Gestionar Noticias (crear, editar, eliminar)
  - ✅ Ver y Gestionar Puntos
  - ✅ Ver y Gestionar Grupos (crear, editar, eliminar)
  - ✅ Ver Ranking
  - ✅ Ver Notificaciones

- **Restricciones:**
  - ❌ No puede gestionar Usuarios
  - ❌ No puede gestionar Inventario
  - ❌ No puede acceder al Admin de Django

### 3. **Admin**
- **Permisos:**
  - ✅ Acceso COMPLETO a todas las funcionalidades
  - ✅ Gestionar Usuarios (crear, editar, eliminar)
  - ✅ Gestionar Inventario
  - ✅ Acceso al Admin Panel de Django
  - ✅ Ver todas las estadísticas

---

## 🔑 Credenciales de Prueba

```
CAMPAMENTISTA:
  Usuario: campamentista1
  Contraseña: Campamento123

DIRECTOR:
  Usuario: director1
  Contraseña: Director123

ADMIN:
  Usuario: nayjhel
  Contraseña: nayjhelNCA
```

---

## 🛠️ Implementación Técnica

### 1. **Decorador @require_role**
Ubicación: `principal/views.py` (líneas 18-39)

```python
def require_role(*roles):
    """Decorador para restricción de acceso por rol"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Debes iniciar sesión...')
                return redirect('login')
            
            if request.user.rol == 'admin':
                return view_func(request, *args, **kwargs)
            
            if request.user.rol not in roles:
                messages.error(request, 'No tienes permiso...')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 2. **Vistas Protegidas**

Todas las vistas críticas están protegidas con el decorador:

```
✓ @require_role('campamentista', 'director', 'admin', 'lider')
  - muro_social()
  - ranking_grupos()
  - listar_actividades()

✓ @require_role('director', 'admin')
  - crear_actividad()
  - editar_actividad()
  - eliminar_actividad()
  - crear_grupo()
  - editar_grupo()
  - eliminar_grupo()
```

### 3. **Dashboard Personalizado**
Ubicación: `principal/views.py` (líneas 89-155)

```python
@login_required(login_url='login')
def dashboard(request):
    """Dashboard personalizado según rol"""
    if user.rol == 'campamentista':
        # Muestra: actividades, puntos, grupos, red social
    elif user.rol == 'director':
        # Muestra: todos los anteriores + opciones de edición
    elif user.rol == 'admin':
        # Panel de control completo con estadísticas
```

### 4. **Template Base Actualizado**
Ubicación: `principal/templates/principal/base.html`

Navegación condicional:
```html
<!-- Visible solo para Director y Admin -->
{% if user.rol in 'director,admin' %}
  <a href="{% url 'listar_grupos' %}">Grupos</a>
  <a href="{% url 'agregar_puntos' %}">Puntos</a>
{% endif %}

<!-- Visible solo para Admin -->
{% if user.rol == 'admin' %}
  <a href="{% url 'listar_usuarios' %}">Usuarios</a>
  <a href="{% url 'listar_inventario' %}">Inventario</a>
{% endif %}
```

### 5. **Rutas Configuradas**
Ubicación: `principal/urls.py`

```python
path('login/', views.login_view, name='login'),
path('logout/', views.logout_view, name='logout'),
path('dashboard/', views.dashboard, name='dashboard'),
```

### 6. **Settings de Django**
Ubicación: `config/settings.py` (líneas 131-134)

```python
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
```

---

## 🌐 Flujo de Navegación

### Campamentista
```
Login → Dashboard (Campamentista) → Opciones:
├─ Muro Social (comentar, dar like)
├─ Ranking (ver puntos)
├─ Actividades (solo lectura)
├─ Noticias (solo lectura)
└─ Notificaciones
```

### Director
```
Login → Dashboard (Director) → Opciones:
├─ Muro Social (completo)
├─ Actividades (CRUD completo)
├─ Noticias (CRUD completo)
├─ Grupos (CRUD completo)
├─ Puntos (gestionar)
└─ Notificaciones
```

### Admin
```
Login → Dashboard (Admin) → Opciones:
├─ Todos los anteriores
├─ Gestión de Usuarios
├─ Gestión de Inventario
├─ Panel de Control Django
└─ Estadísticas completas
```

---

## 📊 Estadísticas del Dashboard

### Campamentista
- Total de Actividades
- Puntos Totales del Campamento
- Grupos Activos
- Publicaciones Recientes

### Director
- Total de Inscritos
- Número de Grupos
- Actividades Programadas
- Noticias Publicadas
- Top 5 Grupos por Puntos

### Admin
- Total de Inscritos
- Total de Grupos
- Total de Actividades
- Total de Noticias
- Acceso a Panel de Control

---

## 🔒 Seguridad Implementada

1. **Autenticación requerida:**
   - Todas las vistas principales requieren login
   - Redirecto automático a login si no está autenticado

2. **Autorización por rol:**
   - Cada vista verifica el rol del usuario
   - Acceso denegado si no tiene permisos

3. **Mensajes personalizados:**
   - Advertencias al intentar acceder sin autenticar
   - Errores claros al intentar acceder sin permiso

4. **Logout seguro:**
   - Cierra la sesión correctamente
   - Redirige a login

---

## 📱 Interfaz de Usuario

### Login
- Interfaz moderna con Tailwind CSS
- Gradiente azul-púrpura
- Credenciales de prueba visibles
- Redirección automática al dashboard

### Navbar Dinámico
- Muestra opciones según el rol
- Dropdown del perfil del usuario
- Contador de notificaciones no leídas
- Botón de logout

### Dashboard Personalizado
- Tarjetas con estadísticas
- Acceso rápido a módulos permitidos
- Información específica por rol
- Diseño responsive

---

## 🚀 Cómo Usar

### Para Iniciar Sesión:

1. Ir a `http://localhost:8000/login/`
2. Ingresar credenciales según rol deseado
3. Sistema redirige automáticamente al dashboard

### Crear Nuevos Usuarios:

```bash
# En Django shell
python manage.py shell

from principal.models import Usuario

usuario = Usuario.objects.create_user(
    username='nuevo_usuario',
    password='contraseña123',
    email='email@example.com',
    rol='campamentista'  # o 'director', 'admin'
)
```

O usar el comando personalizado:

```bash
python manage.py crear_usuarios_prueba
```

---

## 🔄 Flujo de Permisos en Vistas

```
Usuario intenta acceder a /grupos/crear/
         ↓
¿Autenticado? NO → Redirige a /login/
         ↓ YES
¿Rol = director or admin? NO → Redirige a /dashboard/ + Mensaje error
         ↓ YES
Muestra formulario de crear grupo
```

---

## 📝 Cambios Realizados

### Archivos Modificados:
1. ✅ `principal/views.py` - Agregadas vistas de login, logout, dashboard y decoradores
2. ✅ `principal/urls.py` - Agregadas rutas de autenticación
3. ✅ `principal/templates/principal/base.html` - Navbar con navegación condicional
4. ✅ `config/settings.py` - Configuración de login/logout redirect
5. ✅ `principal/templates/principal/login.html` - Nuevo template de login (CREADO)
6. ✅ `principal/templates/principal/dashboard.html` - Nuevo dashboard personalizado (CREADO)

### Archivos Creados:
1. ✅ `principal/management/commands/crear_usuarios_prueba.py` - Command para crear usuarios

---

## ✅ Funcionalidades Completadas

- ✅ Sistema de login/logout funcional
- ✅ Dashboard personalizado por rol
- ✅ Restricción de acceso a vistas según rol
- ✅ Navbar dinámico con opciones por rol
- ✅ Usuarios de prueba creados
- ✅ Mensajes de error/éxito personalizados
- ✅ Navegación condicionada al dashboard
- ✅ Interfaz moderna con Tailwind CSS

---

## 🎯 Próximos Pasos (Opcional)

- [ ] Implementar reset de contraseña
- [ ] Agregar autenticación por correo
- [ ] Implementar 2FA (autenticación de dos factores)
- [ ] Agregar auditoría de cambios
- [ ] Implementar roles más granulares

---

**Sistema completamente funcional y listo para usar! 🚀**
