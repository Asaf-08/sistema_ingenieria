from django.urls import path
from . import views

app_name = 'comunicaciones'

urlpatterns = [
    # ==========================================
    # 📢 MÓDULO DEL TABLÓN DE DOCENTES
    # ==========================================
    path('tablon/', views.tablon_anuncios, name='tablon'),
    path('api/marcar-leido/', views.marcar_leido, name='marcar_leido'),
    
    # ==========================================
    # ⚙️ GESTIÓN ADMINISTRATIVA DE COMUNICADOS
    # ==========================================
    path('gestion/', views.gestion_comunicados, name='gestion_comunicados'),
    path('gestion/guardar/', views.guardar_comunicado_ajax, name='guardar_comunicado_ajax'),
    path('gestion/eliminar/<int:pk>/', views.eliminar_comunicado_ajax, name='eliminar_comunicado_ajax'),
    path('gestion/datos/<int:pk>/', views.obtener_comunicado_data, name='obtener_comunicado_data'),
    path('api/lecturas/<int:comunicado_id>/', views.api_lecturas_comunicado, name='api_lecturas_comunicado'),
    
    # ==========================================
    # 🤖 RUTAS DEL ROBOT DE WHATSAPP (NODE.JS)
    # ==========================================
    path('api/whatsapp/estado/', views.whatsapp_estado_ajax, name='whatsapp_estado_ajax'),
    path('api/whatsapp/desconectar/', views.whatsapp_desconectar_ajax, name='whatsapp_desconectar_ajax'),
]