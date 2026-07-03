from django.urls import path
from . import views

app_name = 'asistencia'

urlpatterns = [
    # ==========================================
    # 📱 MÓDULO DE ESCÁNER Y QR
    # ==========================================
    path('escaner/', views.escaner_asistencia, name='escaner'),
    path('generar-qr/<str:tipo>/<int:id_usuario>/', views.generar_qr, name='generar_qr'),
    
    # ==========================================
    # 📊 DASHBOARDS Y REPORTES ADMINISTRATIVOS
    # ==========================================
    path('reporte-personal/', views.reporte_asistencia_personal, name='reporte_asistencia_personal'),
    path('reporte-estudiantes/', views.reporte_asistencia_estudiantes, name='reporte_asistencia_estudiantes'),

    # ==========================================
    # ⚙️ APIs DE ASISTENCIA (PERSONAL)
    # ==========================================
    path('api/guardar-personal/', views.guardar_asistencia_personal_api, name='api_guardar_personal'),
    path('api/editar-personal/', views.editar_hora_personal_api, name='api_editar_personal'),
    path('api/eliminar-personal/<int:id_asistencia>/', views.eliminar_asistencia_personal_api, name='api_eliminar_personal'),
    
    # ==========================================
    # ⚙️ APIs DE ASISTENCIA (ESTUDIANTES)
    # ==========================================
    path('api/registrar/', views.registrar_asistencia_api, name='api_registrar'),
    path('api/guardar-estudiante/', views.guardar_asistencia_estudiante_api, name='api_guardar_estudiante'),
    path('api/eliminar-estudiante/<int:id_asistencia>/', views.eliminar_asistencia_estudiante_api, name='api_eliminar_estudiante'),
]