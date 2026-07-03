from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # Dashboards Administrativos
    path('consolidado-notas/', views.consolidado_notas_admin, name='consolidado_notas'),
    
    # Descargas de Archivos Pesados (Excel)
    path('descargar/matriz/<int:asignacion_id>/', views.exportar_matriz_oficial_excel, name='exportar_matriz_excel'),
    path('descargar/libretas/<int:aula_id>/', views.exportar_libretas_aula_excel, name='exportar_libretas_aula'),
]