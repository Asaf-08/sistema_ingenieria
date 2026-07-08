import json
import qrcode
import datetime

from django.utils.timezone import localtime, now
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from apps.academico.models import Estudiante
from apps.personal.models import Personal
from apps.asistencia.models import AsistenciaPersonal, AsistenciaEstudiante

# ==========================================================
# 🛠️ FUNCIONES AUXILIARES (PRINCIPIO DRY)
# ==========================================================
def obtener_rango_fechas(request):
    """ Extrae, valida y retorna el rango de fechas de la URL. Si falla, devuelve 'hoy'. """
    hoy = localtime(now()).date()
    fecha_inicio_query = request.GET.get('fecha_inicio')
    fecha_fin_query = request.GET.get('fecha_fin')
    
    if fecha_inicio_query and fecha_fin_query:
        try:
            inicio = datetime.datetime.strptime(fecha_inicio_query, '%Y-%m-%d').date()
            fin = datetime.datetime.strptime(fecha_fin_query, '%Y-%m-%d').date()
            return inicio, fin
        except ValueError:
            pass # Si escriben basura en la URL, pasamos de largo y devolvemos 'hoy'
            
    return hoy, hoy

# ==========================================================
# 📱 VISTAS DEL ESCÁNER Y QR
# ==========================================================
@login_required
def escaner_asistencia(request):
    """Renderiza la interfaz mobile-first del escáner QR."""
    return render(request, 'asistencia/escaner_qr.html')

def generar_qr(request, tipo, id_usuario):
    """ Genera una imagen QR al vuelo para el Personal (PER) o Estudiantes (EST). """
    # datos_qr será algo como "PER-5" o "EST-120"
    datos_qr = f"{tipo}-{id_usuario}"
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(datos_qr)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response

# ==========================================================
# 📊 REPORTES ADMINISTRATIVOS
# ==========================================================
@login_required
def reporte_asistencia_personal(request):
    # Usamos la función DRY
    fecha_inicio, fecha_fin = obtener_rango_fechas(request)
    
    asistencias_personal = AsistenciaPersonal.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin]
    ).select_related('personal').order_by('-fecha', 'personal__apellidos')
    
    return render(request, 'asistencia/reporte_personal.html', {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'personal': asistencias_personal,
        'lista_personal': Personal.objects.filter(estado='Activo')
    })

@login_required
def reporte_asistencia_estudiantes(request):
    # Usamos la función DRY
    fecha_inicio, fecha_fin = obtener_rango_fechas(request)
    
    asistencias_estudiantes = AsistenciaEstudiante.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin]
    ).select_related('estudiante').order_by('-fecha', 'estudiante__apellidos')
    
    return render(request, 'asistencia/reporte_estudiantes.html', {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estudiantes': asistencias_estudiantes,
        'lista_estudiantes': Estudiante.objects.filter(estado='Activo')
    })

# ==========================================================
# ⚙️ APIs DE ASISTENCIA Y ESCÁNER
# ==========================================================
@require_POST
def registrar_asistencia_api(request):
    try:
        data = json.loads(request.body)
        codigo_qr = data.get('codigo_qr') 
        
        if not codigo_qr or '-' not in codigo_qr:
            return JsonResponse({'status': 'error', 'mensaje': 'Código QR no válido.'}, status=400)

        tipo_usuario, id_usuario = codigo_qr.split('-')
        
        ahora = localtime(now()) 
        fecha_hoy = ahora.date()
        hora_actual = ahora.time()
        
        # Hora límite de ingreso
        HORA_LIMITE = datetime.time(8, 0)
        estado_calculado = 'P' if hora_actual <= HORA_LIMITE else 'T'

        # 💥 ACEPTAMOS TANTO 'DOC' (Docentes antiguos) COMO 'PER' (Personal nuevo)
        if tipo_usuario == 'DOC' or tipo_usuario == 'PER':
            personal = Personal.objects.filter(id=id_usuario).first()
            if not personal:
                return JsonResponse({'status': 'error', 'mensaje': 'Personal no encontrado.'}, status=404)

            asistencia, created = AsistenciaPersonal.objects.get_or_create(
                personal=personal, 
                fecha=fecha_hoy,
                defaults={'estado': estado_calculado, 'hora_entrada': hora_actual}
            )

            if created:
                mensaje = f"Entrada registrada: {personal.nombres}"
                tipo_registro = 'Entrada'
            elif not asistencia.hora_salida:
                asistencia.hora_salida = hora_actual
                asistencia.save()
                mensaje = f"Salida registrada: {personal.nombres}"
                tipo_registro = 'Salida'
            else:
                return JsonResponse({'status': 'error', 'mensaje': 'El personal ya registró entrada y salida hoy.'}, status=400)
            
        elif tipo_usuario == 'EST':
            estudiante = Estudiante.objects.filter(id=id_usuario).first()
            if not estudiante:
                return JsonResponse({'status': 'error', 'mensaje': 'Estudiante no encontrado.'}, status=404)

            asistencia, created = AsistenciaEstudiante.objects.get_or_create(
                estudiante=estudiante, 
                fecha=fecha_hoy,
                defaults={'estado': estado_calculado, 'hora_registro': hora_actual}
            )
            
            if created:
                mensaje = f"Asistencia registrada: {estudiante.nombres}"
                tipo_registro = 'Ingreso'
            else:
                return JsonResponse({'status': 'error', 'mensaje': 'El estudiante ya registró su asistencia hoy.'}, status=400)

        else:
            return JsonResponse({'status': 'error', 'mensaje': 'Formato de QR desconocido.'}, status=400)

        return JsonResponse({'status': 'success', 'mensaje': mensaje, 'tipo': tipo_registro, 'hora': hora_actual.strftime("%I:%M %p")})

    except Exception as e:
        print(f"Error en escáner: {str(e)}") 
        return JsonResponse({'status': 'error', 'mensaje': f"Error interno: {str(e)}"}, status=500)

@require_POST
def guardar_asistencia_personal_api(request):
    try:
        data = json.loads(request.body)
        asistencia_id = data.get('id')
        hoy = localtime(now()).date()
        
        hora_entrada = data.get('hora_entrada')
        hora_salida = data.get('hora_salida')

        if hora_entrada and hora_salida and hora_entrada >= hora_salida:
            return JsonResponse({'success': False, 'mensaje': 'La hora de entrada no puede ser mayor o igual a la salida.'})

        if asistencia_id: 
            asistencia = get_object_or_404(AsistenciaPersonal, id=asistencia_id)
            mensaje = "Asistencia actualizada correctamente."
        else: 
            personal_id = data.get('personal_id')
            if AsistenciaPersonal.objects.filter(personal=personal_id, fecha=hoy).exists():
                return JsonResponse({'success': False, 'mensaje': 'El personal ya tiene una asistencia registrada hoy.'})

            personal = get_object_or_404(Personal, id=personal_id)
            asistencia = AsistenciaPersonal(personal=personal, fecha=hoy)
            mensaje = "Asistencia registrada manualmente."

        asistencia.hora_entrada = hora_entrada
        asistencia.hora_salida = hora_salida or None
        asistencia.estado = data.get('estado')
        asistencia.justificacion = data.get('justificacion', '')
        asistencia.tipo_actividad = data.get('tipo_actividad', 'REGULAR')
        asistencia.observaciones = data.get('observaciones', '')
        asistencia.save()

        return JsonResponse({'success': True, 'mensaje': mensaje})

    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': 'Ocurrió un error en el servidor.'})

@require_POST
def editar_hora_personal_api(request):
    data = json.loads(request.body)
    asistencia = get_object_or_404(AsistenciaPersonal, id=data.get('id'))
    
    if data.get('hora_entrada'): asistencia.hora_entrada = data.get('hora_entrada')
    if data.get('hora_salida'): asistencia.hora_salida = data.get('hora_salida')
    asistencia.save()
    
    return JsonResponse({'success': True, 'mensaje': 'Horas actualizadas correctamente.'})

@require_POST
def eliminar_asistencia_personal_api(request, id_asistencia):
    get_object_or_404(AsistenciaPersonal, id=id_asistencia).delete()
    return JsonResponse({'success': True, 'mensaje': 'Registro eliminado correctamente.'})

@require_POST
def guardar_asistencia_estudiante_api(request):
    try:
        data = json.loads(request.body)
        asistencia_id = data.get('id')
        hoy = localtime(now()).date()

        if asistencia_id: 
            asistencia = get_object_or_404(AsistenciaEstudiante, id=asistencia_id)
            mensaje = "Asistencia del estudiante actualizada."
        else: 
            estudiante_id = data.get('estudiante_id')
            if AsistenciaEstudiante.objects.filter(estudiante=estudiante_id, fecha=hoy).exists():
                return JsonResponse({'success': False, 'mensaje': 'El estudiante ya tiene asistencia hoy.'})

            estudiante = get_object_or_404(Estudiante, id=estudiante_id)
            asistencia = AsistenciaEstudiante(estudiante=estudiante, fecha=hoy)
            mensaje = "Asistencia registrada manualmente."

        asistencia.hora_registro = data.get('hora_registro')
        asistencia.estado = data.get('estado')
        asistencia.justificacion = data.get('justificacion', '')
        asistencia.observaciones = data.get('observaciones', '')
        asistencia.save()

        return JsonResponse({'success': True, 'mensaje': mensaje})

    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': 'Ocurrió un error en el servidor.'})

@require_POST
def eliminar_asistencia_estudiante_api(request, id_asistencia):
    get_object_or_404(AsistenciaEstudiante, id=id_asistencia).delete()
    return JsonResponse({'success': True, 'mensaje': 'Registro eliminado correctamente.'})