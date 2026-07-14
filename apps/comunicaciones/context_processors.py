from django.utils import timezone
from .models import Comunicado, LecturaComunicado, Notificacion
from django.db.models import Q
from apps.academico.models import Aula  # Asegura esta importación

def notificaciones_globales(request):
    """ Procesador centralizado para la campanita de notificaciones del sistema """
    context = {}
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'perfil_personal', None)
        cargo = perfil.cargo if perfil else ''
        
        # 1. Contamos las notificaciones de sistema tradicionales
        no_leidas_count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
        
        # 2. Buscamos los comunicados activos y vigentes
        hoy = timezone.now()
        vigentes = Comunicado.objects.filter(activo=True).filter(
            Q(fecha_expiracion__gte=hoy) | Q(fecha_expiracion__isnull=True)
        )
        
        # 3. 💥 FILTRADO ESTRICTO DE AUDIENCIA (Aplica para TODOS sin excepción)
        if perfil:
            mis_audiencias = ['TODOS']
            
            if cargo == 'DOC':
                mis_audiencias.append('DOCENTES')
                if perfil.tipo_contrato == 'Por Horas':
                    mis_audiencias.append('HORAS')
                
                aulas_tutor = Aula.objects.filter(tutor=perfil)
                if aulas_tutor.exists():
                    mis_audiencias.append('TUTORES')
                    niveles_tutor = aulas_tutor.values_list('nivel', flat=True)
                    if 'Inicial' in niveles_tutor:
                        mis_audiencias.append('INICIAL')
                    if 'Primaria' in niveles_tutor:
                        mis_audiencias.append('PRIMARIA')
                    if 'Secundaria' in niveles_tutor:
                        mis_audiencias.append('SECUNDARIA')
                        
            elif cargo in ['DIR', 'COO', 'SEC', 'ASI', 'AUX', 'LIM']:
                mis_audiencias.append('ADMINISTRATIVOS')
            
            # Ahora sí, el filtro se aplica A TODOS, incluyendo a la coordinadora
            vigentes = vigentes.filter(
                Q(audiencia__in=mis_audiencias) | 
                Q(audiencia='PERSONALIZADO', destinatarios_especificos=perfil)
            ).distinct()
        
        # 4. Buscamos cuáles de esos comunicados permitidos ya leyó
        leidos_ids = LecturaComunicado.objects.filter(usuario=request.user, leido=True).values_list('comunicado_id', flat=True)
        comunicados_no_leidos_count = vigentes.exclude(id__in=leidos_ids).count()
        
        # 💥 EL CONTROLADOR MAESTRO: Sumamos ambas fuentes de manera segura
        context['count_notificaciones'] = no_leidas_count + comunicados_no_leidos_count
        context['comunicado_no_leido'] = comunicados_no_leidos_count > 0
        context['lista_notificaciones'] = Notificacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')[:7]
        
    return context


def comunicado_pendiente_context(request):
    """ Procesador para inyectar los datos visuales de los comunicados en el dropdown """
    if request.user.is_authenticated:
        hoy = timezone.now()
        perfil = getattr(request.user, 'perfil_personal', None)
        cargo = perfil.cargo if perfil else ''
        
        vigentes = Comunicado.objects.filter(activo=True).filter(
            Q(fecha_expiracion__gte=hoy) | Q(fecha_expiracion__isnull=True)
        )

        # 3. 💥 FILTRADO ESTRICTO DE AUDIENCIA (Aplica para TODOS sin excepción)
        if perfil:
            mis_audiencias = ['TODOS']
            
            if cargo == 'DOC':
                mis_audiencias.append('DOCENTES')
                if perfil.tipo_contrato == 'Por Horas':
                    mis_audiencias.append('HORAS')
                
                aulas_tutor = Aula.objects.filter(tutor=perfil)
                if aulas_tutor.exists():
                    mis_audiencias.append('TUTORES')
                    niveles_tutor = aulas_tutor.values_list('nivel', flat=True)
                    if 'Inicial' in niveles_tutor:
                        mis_audiencias.append('INICIAL')
                    if 'Primaria' in niveles_tutor:
                        mis_audiencias.append('PRIMARIA')
                    if 'Secundaria' in niveles_tutor:
                        mis_audiencias.append('SECUNDARIA')
                        
            elif cargo in ['DIR', 'COO', 'SEC', 'ASI', 'AUX', 'LIM']:
                mis_audiencias.append('ADMINISTRATIVOS')
            
            # Ahora sí, el filtro se aplica A TODOS, incluyendo a la coordinadora
            vigentes = vigentes.filter(
                Q(audiencia__in=mis_audiencias) | 
                Q(audiencia='PERSONALIZADO', destinatarios_especificos=perfil)
            ).distinct()

        vigentes = vigentes.order_by('-fecha_creacion')

        comunicado_urgente_global = None
        comunicados_dropdown = []

        leidos_ids = set(LecturaComunicado.objects.filter(
            usuario=request.user, 
            leido=True
        ).values_list('comunicado_id', flat=True))

        for c in vigentes:
            ya_leido = c.id in leidos_ids
            
            # El candado urgente solo bloquea a los destinatarios normales
            if not ya_leido:
                if cargo not in ['COO', 'DIR'] and c.importancia == 'URGENTE' and not comunicado_urgente_global:
                    comunicado_urgente_global = c

            if len(comunicados_dropdown) < 10:
                c.ya_leido = ya_leido
                comunicados_dropdown.append(c)

        return {
            'comunicado_urgente_global': comunicado_urgente_global,
            'comunicado_informativo': vigentes.first() if vigentes.exists() else None, 
            'comunicados_dropdown': comunicados_dropdown,
            # 💥 ELIMINADO 'count_notificaciones' de aquí para evitar la sobreescritura de variables
        }
        
    return {}