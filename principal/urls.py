from django.urls import path
from . import views

urlpatterns = [
    # Rutas de autenticación
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Rutas principales
    path('muro/', views.muro_social, name='muro'),
    path('ranking/', views.ranking_grupos, name='ranking'),
    path('grupo/<int:grupo_id>/', views.detalle_grupo, name='detalle_grupo'),
    
    # Rutas de inscripción
    path('inscripcion/nuevo/', views.registrar_inscrito, name='registrar_inscrito'),
    path('inscripcion/lista/', views.lista_inscritos, name='lista_inscritos'),
    path('inscripcion/<int:insc_id>/entregar/', views.entregar_kit, name='entregar_kit'),
    
    # ⭐ NUEVAS RUTAS PARA RULETA ⭐
    path('pantalla-ruleta/', views.pantalla_ruleta, name='pantalla_ruleta'),
    path('api/ultima-inscripcion/', views.ultima_inscripcion_ajax, name='ultima_inscripcion_ajax'),
    
    # Rutas de puntos
    path('puntos/agregar/', views.agregar_puntos, name='agregar_puntos'),
    path('puntos/historial/', views.historial_puntos, name='historial_puntos'),
    path('puntos/historial/<int:grupo_id>/', views.historial_puntos, name='historial_puntos_grupo'),
    
    # Rutas de gestión de usuarios
    path('usuarios/', views.listar_usuarios, name='listar_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    
    # Rutas de inventario
    path('inventario/', views.listar_inventario, name='listar_inventario'),
    path('inventario/crear/', views.crear_inventario, name='crear_inventario'),
    path('inventario/<int:item_id>/editar/', views.editar_inventario, name='editar_inventario'),
    path('inventario/<int:item_id>/eliminar/', views.eliminar_inventario, name='eliminar_inventario'),
    
    # ✅ NUEVA RUTA API PARA COLORES EXISTENTES
    path('api/colores-existentes/', views.api_colores_existentes, name='api_colores_existentes'),
    
    # Ruta de perfil del usuario
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    
    # Rutas de likes y comentarios
    path('publicacion/<int:publicacion_id>/like/', views.agregar_like, name='agregar_like'),
    path('publicacion/<int:publicacion_id>/comentario/', views.agregar_comentario, name='agregar_comentario'),
    path('comentario/<int:comentario_id>/eliminar/', views.eliminar_comentario, name='eliminar_comentario'),
    
    # Rutas de gestión de grupos
    path('grupos/', views.listar_grupos, name='listar_grupos'),
    path('grupos/crear/', views.crear_grupo, name='crear_grupo'),
    path('grupos/<int:grupo_id>/editar/', views.editar_grupo, name='editar_grupo'),
    path('grupos/<int:grupo_id>/eliminar/', views.eliminar_grupo, name='eliminar_grupo'),
    
    # Rutas de gestión de actividades (cronograma)
    path('actividades/', views.listar_actividades, name='listar_actividades'),
    path('actividades/crear/', views.crear_actividad, name='crear_actividad'),
    path('actividades/<int:actividad_id>/editar/', views.editar_actividad, name='editar_actividad'),
    path('actividades/<int:actividad_id>/eliminar/', views.eliminar_actividad, name='eliminar_actividad'),
    
    # Rutas de gestión de noticias
    path('noticias/', views.listar_noticias, name='listar_noticias'),
    path('noticias/crear/', views.crear_noticia, name='crear_noticia'),
    path('noticias/<int:noticia_id>/editar/', views.editar_noticia, name='editar_noticia'),
    path('noticias/<int:noticia_id>/eliminar/', views.eliminar_noticia, name='eliminar_noticia'),
    
    # Rutas de notificaciones
    path('notificaciones/', views.listar_notificaciones, name='listar_notificaciones'),
    path('notificaciones/<int:notificacion_id>/leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('notificaciones/marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('notificaciones/<int:notificacion_id>/eliminar/', views.eliminar_notificacion, name='eliminar_notificacion'),
    path('poleras/', views.gestionar_poleras, name='gestionar_poleras'),
    
    # API para obtener tallas disponibles
    path('api/tallas-disponibles/', views.tallas_disponibles_api, name='tallas_disponibles'),

  path('gestion_iglesias_uniones/', views.gestionar_iglesias_uniones, name='gestionar_iglesias_uniones'),
]