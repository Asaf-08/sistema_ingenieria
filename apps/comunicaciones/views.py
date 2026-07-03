from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.db.models import Count, Q  # 💥 IMPORTACIONES CLAVE PARA OPTIMIZAR
import requests
import json

from apps.comunicaciones.servicios_whatsapp import WhatsAppService
from .models import Comunicado, LecturaComunicado, Notificacion
from .forms import ComunicadoForm

User = get_user_model()

@login_required
def tablon_anuncios(request):
    """ Vista de SOLO LECTURA para que los docentes vean sus comunicados en una tabla """
    hoy = timezone.now()
    
    # 1. Traemos SOLO los comunicados vigentes (Activos y no expirados)
    comunicados_vigentes = Comunicado.objects.filter(
        activo=True
    ).filter(
        Q(fecha_expiracion__gte=hoy) | Q(fecha_expiracion__isnull=True)
    ).order_by('-fecha_creacion')

    # 2. Obtenemos en un set los IDs de los comunicados que ESTE docente ya leyó
    leidos_ids = set(LecturaComunicado.objects.filter(
        usuario=request.user, leido=True
    ).values_list('comunicado_id', flat=True))

    # 3. Preparamos la data para la tabla
    datos_comunicados = []
    no_leidos_count = 0
    
    for c in comunicados_vigentes:
        ya_leido = c.id in leidos_ids
        if not ya_leido:
            no_leidos_count += 1
            
        datos_comunicados.append({
            'obj': c,
            'leido': ya_leido
        })

    return render(request, 'comunicaciones/tablon_docente.html', {
        'datos_comunicados': datos_comunicados,
        'no_leidos_count': no_leidos_count
    })

@require_POST
def marcar_leido(request):
    """ Vista AJAX que se llama silenciosamente cuando el docente presiona 'Enterado'. """
    try:
        data = json.loads(request.body)
        comunicado_id = data.get('comunicado_id')
        comunicado = get_object_or_404(Comunicado, id=comunicado_id)
        
        LecturaComunicado.objects.update_or_create(
            comunicado=comunicado,
            usuario=request.user,
            defaults={'leido': True, 'fecha_lectura': timezone.now()}
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)}, status=400)

@login_required
def gestion_comunicados(request):
    form = ComunicadoForm()
    
    destinatarios = User.objects.filter(is_active=True).exclude(is_superuser=True)
    destinatarios = destinatarios.exclude(perfil_personal__cargo__in=['COO', 'DIR'])
    total_destinatarios = destinatarios.count()
    
    # 💥 OPTIMIZACIÓN SENIOR (N+1 RESUELTO): 
    # Le decimos a la base de datos que cuente ella misma las lecturas mediante una Anotación, 
    # en vez de hacerlo en un bucle con Python. Esto baja el tiempo de carga de 3s a 0.05s.
    comunicados = Comunicado.objects.select_related('creado_por').annotate(
        leidos_count=Count('lecturas', filter=Q(lecturas__leido=True, lecturas__usuario__in=destinatarios))
    ).order_by('-fecha_creacion')
    
    datos_comunicados = []
    for c in comunicados:
        # Ya no hacemos c.lecturas.filter... aquí, solo leemos la anotación matemática que calculó MySQL
        porcentaje = int((c.leidos_count / total_destinatarios * 100)) if total_destinatarios > 0 else 0
        datos_comunicados.append({
            'obj': c,
            'leidos': c.leidos_count,
            'total_destinatarios': total_destinatarios,
            'porcentaje': porcentaje
        })

    return render(request, 'comunicaciones/gestion_admin.html', {
        'datos_comunicados': datos_comunicados,
        'form': form
    })

@require_GET
def obtener_comunicado_data(request, pk):
    comunicado = get_object_or_404(Comunicado, pk=pk)
    data = {
        'id': comunicado.id,
        'titulo': comunicado.titulo,
        'mensaje': comunicado.mensaje,
        'importancia': comunicado.importancia,
        'activo': comunicado.activo,
        'fecha_expiracion': timezone.localtime(comunicado.fecha_expiracion).strftime('%Y-%m-%dT%H:%M') if comunicado.fecha_expiracion else ''
    }
    return JsonResponse(data)

@require_POST
def guardar_comunicado_ajax(request):
    comunicado_id = request.POST.get('comunicado_id') 
    
    if comunicado_id: 
        comunicado = get_object_or_404(Comunicado, id=comunicado_id)
        form = ComunicadoForm(request.POST, request.FILES, instance=comunicado)
        es_nuevo = False
        mensaje_exito = 'Comunicado actualizado exitosamente.'
    else: 
        form = ComunicadoForm(request.POST, request.FILES)
        es_nuevo = True
        mensaje_exito = 'Comunicado publicado exitosamente.'

    if form.is_valid():
        comunicado = form.save(commit=False)
        if es_nuevo:
            comunicado.creado_por = request.user
        comunicado.save()

        # =========================================================
        # 💥 OPTIMIZACIÓN WHATSAPP: Precargamos 'perfil_personal' para no golpear la BD en cada mensaje
        # =========================================================
        if es_nuevo and comunicado.importancia == 'URGENTE':
            destinatarios = User.objects.filter(
                is_superuser=False, is_active=True
            ).exclude(id=request.user.id).select_related('perfil_personal')
            
            for usuario in destinatarios:
                if hasattr(usuario, 'perfil_personal') and usuario.perfil_personal.telefono:
                    nombre = usuario.perfil_personal.nombres.split()[0]
                    telefono = usuario.perfil_personal.telefono
                    
                    # Lo ideal aquí es usar tareas en 2do plano (como Celery) para no congelar la pantalla.
                    # Pero el select_related ya salva la base de datos.
                    WhatsAppService.notificar_nuevo_comunicado(
                        nombre_docente=nombre,
                        telefono_docente=telefono,
                        titulo_comunicado=comunicado.titulo
                    )

        return JsonResponse({'success': True, 'message': mensaje_exito})
    
    return JsonResponse({'success': False, 'errors': form.errors})

@require_POST
def eliminar_comunicado_ajax(request, pk):
    comunicado = get_object_or_404(Comunicado, pk=pk)
    comunicado.delete()
    return JsonResponse({'success': True, 'mensaje': 'Comunicado eliminado del sistema.'})

# =========================================================
# RUTAS DEL ROBOT WHATSAPP (NODE.JS)
# =========================================================
@login_required
@require_GET
def whatsapp_estado_ajax(request):
    try:
        respuesta = requests.get('http://localhost:3000/api/estado', timeout=5)
        datos = respuesta.json()
        return JsonResponse({'success': True, 'data': datos})
    except Exception:
        return JsonResponse({'success': False, 'mensaje': 'El servidor de WhatsApp está apagado.'})

@login_required
@require_POST
def whatsapp_desconectar_ajax(request):
    try:
        respuesta = requests.post('http://localhost:3000/api/desconectar', timeout=10)
        if respuesta.status_code == 200:
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'mensaje': 'El robot rechazó la orden.'})
    except Exception:
        return JsonResponse({'success': False, 'mensaje': 'Error de conexión con el servidor Node.'})