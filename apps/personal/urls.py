from django.urls import path
from . import views

app_name = 'personal'

urlpatterns = [
    # ==========================================
    # 👤 GESTIÓN ADMINISTRATIVA DE PERSONAL (CRUD)
    # ==========================================
    path('', views.lista_personal, name='lista_personal'),
    path('guardar/', views.guardar_personal_ajax, name='guardar_personal_ajax'),
    path('datos/<int:pk>/', views.obtener_personal_data, name='obtener_personal_data'),
    path('eliminar/<int:pk>/', views.eliminar_personal_ajax, name='eliminar_personal_ajax'),
    path('cambiar-estado/<int:pk>/', views.cambiar_estado_personal_ajax, name='cambiar_estado_personal_ajax'),
    
    # ==========================================
    # 👨‍🏫 PORTAL DEL DOCENTE Y NAVEGACIÓN
    # ==========================================
    path('enrutador/', views.enrutador_principal, name='enrutador_principal'),
    path('mi-perfil/', views.mi_perfil, name='mi_perfil'),
    path('mis-cursos/', views.mis_cursos, name='mis_cursos'),
    path('aula/<int:aula_id>/agenda/', views.reporte_agenda_semanal, name='reporte_agenda_semanal'),
    
    # ==========================================
    # 📚 CENTRO DE MATERIALES (DOCENTES)
    # ==========================================
    path('materiales/subir/<int:asignacion_id>/', views.material_upload, name='material_upload'),
    path('centro-materiales/', views.centro_materiales, name='centro_materiales'),
    path('centro-materiales/eliminar/<int:solicitud_id>/', views.eliminar_solicitud, name='eliminar_solicitud'),

    # ==========================================
    # 📝 EVALUACIONES Y NOTAS
    # ==========================================
    path('evaluaciones/<int:asignacion_id>/', views.lista_evaluaciones, name='lista_evaluaciones'),
    path('evaluaciones/guardar/', views.guardar_evaluacion_ajax, name='guardar_evaluacion_ajax'),
    path('notas/<int:evaluacion_id>/', views.registro_notas, name='registro_notas'),
    path('notas/guardar/', views.guardar_nota_ajax, name='guardar_nota_ajax'),
    path('curso/<int:asignacion_id>/matriz/', views.matriz_notas, name='matriz_notas'),
    
    # ==========================================
    # 🧠 TUTORÍA Y EVALUACIÓN ACTITUDINAL
    # ==========================================
    path('tutor/aula/<int:aula_id>/actitudinal/<str:bimestre>/', views.registro_actitudinal, name='registro_actitudinal'),
    path('tutor/actitudinal/guardar-ajax/', views.guardar_actitudinal_ajax, name='guardar_actitudinal_ajax'),
    
    # ==========================================
    # 📊 SINCRONIZACIÓN
    # ==========================================
    path('aula/<int:aula_id>/sincronizar-drive/', views.sincronizar_google_sheets, name='sincronizar_google_sheets'),
]