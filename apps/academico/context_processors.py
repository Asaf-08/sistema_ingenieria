from .models import Institucion

def institucion_global(request):
    # Enviamos la configuración a todas las pantallas
    institucion = Institucion.objects.first()
    return {'institucion_global': institucion}