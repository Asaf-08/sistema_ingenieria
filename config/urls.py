from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.personal import views as personal_views
from apps.core import views as core_views  # Evitamos colisión de nombres de 'views'
from django.shortcuts import redirect, render
from django.conf.urls import handler404
from apps.personal.views import LoginPersonalizadoView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 💥 URL Raíz del Servidor: Intercepta http://127.0.0.1:8000/
    path('', personal_views.raiz_redireccion, name='index'), 

    # ==========================================
    # 🔐 AUTENTICACIÓN OFICIAL PERSONALIZADA
    # ==========================================
    # 💥 Aquí es donde ocurre la magia: Reemplazamos la vista genérica por la tuya
    path('login/', LoginPersonalizadoView.as_view(), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Inclusión de Aplicaciones Modulares
    path('core/', include('apps.core.urls')), 
    path('academico/', include('apps.academico.urls')),
    path('personal/', include('apps.personal.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path('comunicaciones/', include('apps.comunicaciones.urls')),
    path('asistencia/', include('apps.asistencia.urls')),

    # Páginas de Cuenta auxiliares
    path('perfil/', core_views.dashboard_principal, name='profile'),
    path('registro/', core_views.dashboard_principal, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # 💥 Rutas del Debug Toolbar
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# 💥 CONTROLADOR MAESTRO DE ERRORES 404
def mi_error_404(request, exception):
    # Si el usuario NO ha iniciado sesión, lo mandamos directo al Login
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Si ya inició sesión pero se perdió, le mostramos la pantalla 404 elegante
    return render(request, 'errores/404.html', status=404)

# Le decimos a Django que use nuestra función cuando no encuentre una página
handler404 = mi_error_404