from django.utils import timezone
from .models import Comunicado, LecturaComunicado, Notificacion
from django.db.models import Q

def comunicado_pendiente_context(request):
    if request.user.is_authenticated:
        hoy = timezone.now()
        cargo = request.user.perfil_personal.cargo if hasattr(request.user, 'perfil_personal') else ''
        
        # 1. Traemos TODOS los comunicados activos y vigentes ordenados por el más reciente
        vigentes = Comunicado.objects.filter(
            activo=True
        ).filter(
            Q(fecha_expiracion__gte=hoy) | Q(fecha_expiracion__isnull=True)
        ).order_by('-fecha_creacion')

        comunicado_urgente_global = None
        comunicados_dropdown = []
        no_leidos_count = 0

        # 2. OPTIMIZACIÓN SENIOR: Traemos todos los IDs que ya leyó en una sola consulta
        # y los guardamos en un 'set' de Python para búsquedas ultra rápidas en RAM
        leidos_ids = set(LecturaComunicado.objects.filter(
            usuario=request.user, 
            leido=True
        ).values_list('comunicado_id', flat=True))

        # 3. Iteramos para resolver el contador de la campanita y tu Regla de Negocio
        for c in vigentes:
            ya_leido = c.id in leidos_ids

            if not ya_leido:
                no_leidos_count += 1
                
                # 💥 TU CANDADO MÁGICO: Solo bloqueamos si es URGENTE, NO lo ha leído y NO es COO/DIR
                if cargo not in ['COO', 'DIR'] and c.importancia == 'URGENTE' and not comunicado_urgente_global:
                    comunicado_urgente_global = c

            # 4. Llenamos la campanita con los últimos 10 comunicados (Urgentes y Normales)
            if len(comunicados_dropdown) < 10:
                c.ya_leido = ya_leido  # Inyectamos esto temporalmente para que el HTML sepa si pintarlo gris o blanco
                comunicados_dropdown.append(c)

        return {
            'comunicado_urgente_global': comunicado_urgente_global,
            'comunicado_informativo': vigentes.first() if vigentes.exists() else None, 
            'comunicados_dropdown': comunicados_dropdown, # <-- NUEVO: Para la lista desplegable con scroll
            'count_notificaciones': no_leidos_count       # <-- NUEVO: Para el número rojo de la bolita
        }
        
    return {}

def notificaciones_globales(request):
    """ Procesador para la campanita del sistema """
    context = {}
    if request.user.is_authenticated:
        cargo = request.user.perfil_personal.cargo if hasattr(request.user, 'perfil_personal') else ''
        
        # 1. Contamos las notificaciones normales (Ej: "Materiales listos")
        no_leidas_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
        
        # 2. Contamos los COMUNICADOS no leídos
        hoy = timezone.now()
        vigentes = Comunicado.objects.filter(activo=True).filter(
            Q(fecha_expiracion__gte=hoy) | Q(fecha_expiracion__isnull=True)
        )
        
        comunicados_no_leidos_count = 0
        
        # REGLA: Si NO es coordinadora/directora, calculamos cuántos comunicados le faltan leer
        if cargo not in ['COO', 'DIR']:
            leidos_ids = LecturaComunicado.objects.filter(usuario=request.user, leido=True).values_list('comunicado_id', flat=True)
            comunicados_no_leidos_count = vigentes.exclude(id__in=leidos_ids).count()
            
        # 💥 EL TRUCO: La burbuja roja es la SUMA total
        context['count_notificaciones'] = no_leidas_count + comunicados_no_leidos_count
        
        # Variable mágica para que el HTML sepa si debe pintar el anuncio de gris
        context['comunicado_no_leido'] = comunicados_no_leidos_count > 0
        
        # La lista histórica desplegable (las últimas 7 notificaciones normales)
        context['lista_notificaciones'] = Notificacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')[:7]
        
    return context