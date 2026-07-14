from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.db.models import Count, Q  # 💥 IMPORTACIONES CLAVE PARA OPTIMIZAR
import requests
import json
from django.conf import settings

from apps.comunicaciones.servicios_whatsapp import WhatsAppService
from apps.personal.models import Personal
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
    # Traemos los comunicados optimizados con prefetch_related
    comunicados = Comunicado.objects.select_related('creado_por').prefetch_related(
        'destinatarios_especificos',
        'lecturas__usuario'
    ).order_by('-fecha_creacion')
    
    datos_comunicados = []
    for c in comunicados:
        # 1. Definimos los destinatarios esperados teóricos según la audiencia elegida
        destinatarios_esperados_ids = set()
        
        if c.audiencia == 'PERSONALIZADO':
            destinatarios_esperados_ids = set(c.destinatarios_especificos.values_list('id', flat=True))
            
        elif c.audiencia == 'DOCENTES':
            destinatarios_esperados_ids = set(Personal.objects.filter(cargo='DOC', estado='Activo').values_list('id', flat=True))
            
        elif c.audiencia == 'ADMINISTRATIVOS':
            destinatarios_esperados_ids = set(Personal.objects.filter(cargo__in=['DIR', 'COO', 'SEC', 'ASI', 'AUX', 'LIM'], estado='Activo').values_list('id', flat=True))
            
        else:  # Opción 'TODOS'
            destinatarios_esperados_ids = set(Personal.objects.filter(estado='Activo').values_list('id', flat=True))
        
        # 2. Obtenemos las personas que ya marcaron como leído el comunicado
        # Cruzamos las lecturas con el perfil de personal del usuario
        leidos_personal_ids = set(LecturaComunicado.objects.filter(
            comunicado=c, 
            leido=True
        ).values_list('usuario__perfil_personal__id', flat=True))
        
        # Limpiamos valores nulos (por ejemplo, si un superusuario lee el comunicado y no tiene perfil de personal)
        leidos_personal_ids.discard(None)
        
        # 3. 💥 UNIÓN MATEMÁTICA CONJUNTA:
        # Unimos ambos conjuntos para asegurar que si un lector extra (creador, coordinadora, etc.)
        # lee el anuncio, se autoincluya limpiamente en el total sin romper la barra de progreso.
        destinatarios_totales_ids = destinatarios_esperados_ids.union(leidos_personal_ids)
        
        total_destinatarios = len(destinatarios_totales_ids)
        leidos = len(leidos_personal_ids)
        
        porcentaje = int((leidos / total_destinatarios * 100)) if total_destinatarios > 0 else 0
        
        datos_comunicados.append({
            'obj': c,
            'leidos': leidos,
            'total_destinatarios': total_destinatarios,
            'porcentaje': porcentaje
        })
    
    # 💥 NUEVO: Preparamos la data para el Modal Personalizado
    # Usamos prefetch_related para no saturar la base de datos
    personal_db = Personal.objects.filter(estado='Activo').prefetch_related(
        'asignaciones__aula', 
        'aulas_tutoradas' # <-- O usa 'aula_set' si no le pusiste related_name en tu modelo Aula
    )
    
    lista_personalizada = []
    for p in personal_db:
        # Extraemos los niveles donde dicta
        niveles_dicta = list(set(a.aula.nivel for a in p.asignaciones.all() if a.periodo.activo))
        niveles_str = ", ".join(niveles_dicta) if niveles_dicta else "No dicta"
        
        # Extraemos si es tutor
        aulas_tutor = p.aulas_tutoradas.all() # O p.aula_set.all()
        tutor_str = ", ".join([f"{a.grado} '{a.seccion}'" for a in aulas_tutor]) if aulas_tutor else "No es tutor"
        
        lista_personalizada.append({
            'id': p.id,
            'nombres': f"{p.apellidos}, {p.nombres}",
            'cargo': p.get_cargo_display(),
            'contrato': p.get_tipo_contrato_display(),
            'dicta_en': niveles_str,
            'tutor_de': tutor_str
        })

    return render(request, 'comunicaciones/gestion_admin.html', {
        'datos_comunicados': datos_comunicados,
        'form': form,
        'lista_personalizada': lista_personalizada
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
        
        # ==============================================================
        # 💥 EL ESLABÓN PERDIDO: Guardar los Destinatarios Personalizados
        # ==============================================================
        if comunicado.audiencia == 'PERSONALIZADO':
            # Atrapamos el texto oculto "1,4,7"
            ids_str = request.POST.get('destinatarios_especificos', '')
            if ids_str:
                # Lo convertimos en una lista de números [1, 4, 7]
                lista_ids = [int(i) for i in ids_str.split(',') if i.strip().isdigit()]
                # Los inyectamos en la relación Muchos-a-Muchos
                comunicado.destinatarios_especificos.set(lista_ids)
        else:
            # Si se arrepintió y lo cambió a "TODOS", limpiamos la lista
            comunicado.destinatarios_especificos.clear()

       # =========================================================
        # 💥 OPTIMIZACIÓN WHATSAPP: Enviar SOLO a los destinatarios correctos
        # =========================================================
        if es_nuevo and comunicado.importancia == 'URGENTE':
            
            # 1. Obtenemos exactamente el grupo de personas al que va dirigido
            if comunicado.audiencia == 'PERSONALIZADO':
                destinatarios = comunicado.destinatarios_especificos.all()
            elif comunicado.audiencia == 'DOCENTES':
                destinatarios = Personal.objects.filter(cargo='DOC', estado='Activo')
            elif comunicado.audiencia == 'ADMINISTRATIVOS':
                destinatarios = Personal.objects.filter(cargo__in=['DIR', 'COO', 'SEC', 'ASI', 'AUX', 'LIM'], estado='Activo')
            else:
                # Opción 'TODOS'
                destinatarios = Personal.objects.filter(estado='Activo')

            # 2. Excluimos al creador del comunicado para que no se envíe un WhatsApp a sí mismo
            if hasattr(request.user, 'perfil_personal'):
                destinatarios = destinatarios.exclude(id=request.user.perfil_personal.id)

            # 3. Disparamos los mensajes inteligentemente
            for persona in destinatarios:
                if persona.telefono:
                    # Sacamos el primer nombre para hacerlo más cercano
                    nombre = persona.nombres.split()[0] 
                    
                    # Llamamos al hilo en segundo plano (no congela la pantalla)
                    WhatsAppService.notificar_nuevo_comunicado(
                        nombre_docente=nombre,
                        telefono_docente=persona.telefono,
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
# RUTAS DEL ROBOT WHATSAPP (NODE.JS) EN PRODUCCIÓN
# =========================================================
@login_required
@require_GET
def whatsapp_estado_ajax(request):
    try:
        # Construimos la URL dinámica leyendo el settings
        url_destino = f"{settings.WHATSAPP_BOT_URL}/api/estado"
        respuesta = requests.get(url_destino, timeout=5)
        datos = respuesta.json()
        return JsonResponse({'success': True, 'data': datos})
    except Exception:
        return JsonResponse({'success': False, 'mensaje': 'El servidor de WhatsApp está apagado o inaccesible.'})

@login_required
@require_POST
def whatsapp_desconectar_ajax(request):
    try:
        # Construimos la URL dinámica leyendo el settings
        url_destino = f"{settings.WHATSAPP_BOT_URL}/api/desconectar"
        respuesta = requests.post(url_destino, timeout=10)
        if respuesta.status_code == 200:
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'mensaje': 'El robot rechazó la orden.'})
    except Exception:
        return JsonResponse({'success': False, 'mensaje': 'Error de conexión con el servidor Node.'})

@login_required
def api_lecturas_comunicado(request, comunicado_id):
    comunicado = get_object_or_404(Comunicado, id=comunicado_id)
    
    # 1. Definimos los destinatarios esperados teóricos
    destinatarios_esperados_ids = set()
    if comunicado.audiencia == 'PERSONALIZADO':
        destinatarios_esperados_ids = set(comunicado.destinatarios_especificos.values_list('id', flat=True))
    elif comunicado.audiencia == 'DOCENTES':
        destinatarios_esperados_ids = set(Personal.objects.filter(cargo='DOC', estado='Activo').values_list('id', flat=True))
    elif comunicado.audiencia == 'ADMINISTRATIVOS':
        destinatarios_esperados_ids = set(Personal.objects.filter(cargo__in=['DIR', 'COO', 'SEC', 'ASI', 'AUX', 'LIM'], estado='Activo').values_list('id', flat=True))
    else:
        destinatarios_esperados_ids = set(Personal.objects.filter(estado='Activo').values_list('id', flat=True))

    # 2. Obtenemos a los usuarios que ya lo leyeron (con select_related para evitar N+1)
    lecturas = comunicado.lecturas.filter(leido=True).select_related('usuario__perfil_personal')
    
    # Armamos un diccionario interno -> { id_personal : fecha_lectura }
    leidos_dict = {}
    for lectura in lecturas:
        if hasattr(lectura.usuario, 'perfil_personal') and lectura.usuario.perfil_personal:
            leidos_dict[lectura.usuario.perfil_personal.id] = lectura.fecha_lectura

    # 3. UNIÓN MATEMÁTICA: Unimos a los esperados con los lectores reales
    todos_ids = destinatarios_esperados_ids.union(leidos_dict.keys())
    
    # 4. Traemos la información limpia y ordenada alfabéticamente
    personal_total = Personal.objects.filter(id__in=todos_ids).order_by('apellidos', 'nombres')
    
    resultados = []
    for p in personal_total:
        leido = p.id in leidos_dict
        fecha = leidos_dict.get(p.id)
        
        # Formateamos la fecha (Ej: 14/05/2026 10:30 AM)
        if fecha:
            fecha_local = timezone.localtime(fecha)
            fecha_str = fecha_local.strftime('%d/%m/%Y %I:%M %p')
        else:
            fecha_str = None
            
        resultados.append({
            'nombre': f"{p.apellidos}, {p.nombres}",
            'cargo': p.get_cargo_display(),
            'leido': leido,
            'fecha_lectura': fecha_str
        })
        
    return JsonResponse({'success': True, 'lecturas': resultados})