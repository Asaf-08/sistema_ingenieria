import json
import qrcode
import datetime
import calendar

from django.utils.timezone import localtime, now
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from apps.academico.models import Aula, Estudiante, Matricula, PeriodoLectivo
from apps.personal.models import Personal
from apps.asistencia.models import AsistenciaPersonal, AsistenciaEstudiante
from apps.personal.views import obtener_personal_logueado

# ==============================================================================
# ⏰ CONFIGURACIÓN DE HORARIOS LÍMITE Y TOLERANCIA (MODIFICABLE A FUTURO)
# ==============================================================================
# Si en el futuro deseas cambiar las horas de tolerancia, solo modifica los
# números dentro de datetime.time(HORA, MINUTO) aquí abajo:
#
# 1. ESTUDIANTES:
#    Hasta las 08:00 AM es Puntual. A partir de las 08:01 AM se considera Tardanza.
HORA_LIMITE_ESTUDIANTE = datetime.time(8, 0)

# 2. DOCENTES POR HORAS / TALLERES (tipo_contrato == 'Por Horas'):
#    Hasta las 07:50 AM es Puntual. A partir de las 07:51 AM se considera Tardanza.
HORA_LIMITE_PERSONAL_POR_HORAS = datetime.time(7, 50)

# 3. PERSONAL FIJO - TIEMPO COMPLETO (tipo_contrato == 'Fijo'):
#    Hasta las 07:40 AM es Puntual. A partir de las 07:41 AM se considera Tardanza.
HORA_LIMITE_PERSONAL_FIJO = datetime.time(7, 40)

# ==============================================================================
# 🚦 VENTANAS HORARIAS PERMITIDAS PARA EL ESCÁNER QR (MODIFICABLE A FUTURO)
# ==============================================================================
# 4. ESTUDIANTES (Escáner QR):
#    Solo permite registrar asistencia entre 06:30 AM y 02:30 PM (14:30).
HORA_INICIO_QR_ESTUDIANTE = datetime.time(6, 30)
HORA_FIN_QR_ESTUDIANTE = datetime.time(14, 30)

# 5. PERSONAL / DOCENTES (Escáner QR):
#    Solo permite registrar asistencia entre 06:30 AM y 07:00 PM (19:00).
HORA_INICIO_QR_PERSONAL = datetime.time(6, 30)
HORA_FIN_QR_PERSONAL = datetime.time(19, 0)

# 6. ASESORÍAS EN LA TARDE (Docentes Por Horas):
#    Si un docente Por Horas marca su ingreso desde las 02:30 PM (14:30),
#    se registra automáticamente como Asesoría/Reunión (Puntual, sin tardanza).
HORA_INICIO_ASESORIA_TARDE = datetime.time(14, 30)


def obtener_hora_limite_personal(personal_obj):
    """
    Devuelve la hora límite de ingreso según el tipo de contrato del trabajador.
    - 'Por Horas' -> 07:50 AM (tardanza desde 07:51 AM)
    - 'Fijo' (u otros) -> 07:40 AM (tardanza desde 07:41 AM)
    """
    if personal_obj and personal_obj.tipo_contrato == 'Por Horas':
        return HORA_LIMITE_PERSONAL_POR_HORAS
    return HORA_LIMITE_PERSONAL_FIJO


def calcular_minutos_tardanza(hora_llegada, hora_limite):
    """
    Calcula cuántos minutos de retraso tiene un registro respecto a su hora límite.
    Compara a nivel de (hora, minuto):
    - Ej. Personal Fijo (límite 07:40): llega 07:40 -> 0 min | llega 07:41 -> 1 min
    - Ej. Por Horas (límite 07:50): llega 07:50 -> 0 min | llega 07:51 -> 1 min
    - Ej. Estudiante (límite 08:00): llega 08:00 -> 0 min | llega 08:01 -> 1 min
    """
    if not hora_llegada or not hora_limite:
        return 0
    minutos_llegada = (hora_llegada.hour * 60) + hora_llegada.minute
    minutos_limite = (hora_limite.hour * 60) + hora_limite.minute
    return max(0, minutos_llegada - minutos_limite)


def calcular_minutos_laborados(hora_entrada, hora_salida):
    """Calcula los minutos trabajados entre la hora de entrada y salida."""
    if not hora_entrada or not hora_salida:
        return 0
    min_ent = (hora_entrada.hour * 60) + hora_entrada.minute
    min_sal = (hora_salida.hour * 60) + hora_salida.minute
    return max(0, min_sal - min_ent)


def formatear_minutos_a_texto(minutos_totales):
    """Convierte minutos (ej. 85) a un formato legible (ej. '1h 25m' o '45 min')."""
    minutos_totales = int(minutos_totales or 0)
    if minutos_totales <= 0:
        return "0 min"
    if minutos_totales < 60:
        return f"{minutos_totales} min"
    horas = minutos_totales // 60
    mins = minutos_totales % 60
    if mins == 0:
        return f"{horas}h"
    return f"{horas}h {mins}m"


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
            if inicio > fin:
                inicio, fin = fin, inicio
            return inicio, fin
        except ValueError:
            pass
            
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
    datos_qr = f"{tipo}-{id_usuario}"
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(datos_qr)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response

@login_required
def panel_fotochecks(request):
    """ Vista dedicada para imprimir fotochecks QR por Aula """
    periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
    aulas = Aula.objects.all().order_by('nivel', 'grado', 'seccion')
    
    aula_id = request.GET.get('aula_id')
    matriculas = []
    aula_seleccionada = None
    
    if aula_id and aula_id.isdigit():
        aula_seleccionada = get_object_or_404(Aula, id=aula_id)
        if periodo_actual:
            matriculas = Matricula.objects.filter(
                periodo=periodo_actual, 
                aula=aula_seleccionada
            ).select_related('estudiante').order_by('estudiante__apellidos')
            
    return render(request, 'academico/panel_fotochecks.html', {
        'aulas': aulas,
        'matriculas': matriculas,
        'aula_seleccionada': aula_seleccionada
    })

# ==========================================================
# 📊 REPORTES ADMINISTRATIVOS (WEB Y PDF)
# ==========================================================
@login_required
def reporte_asistencia_personal(request):
    fecha_inicio, fecha_fin = obtener_rango_fechas(request)
    
    asistencias_qs = AsistenciaPersonal.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin]
    ).select_related('personal').order_by('-fecha', 'personal__apellidos')

    asistencias_personal = []
    for a in asistencias_qs:
        if a.personal:
            limite = obtener_hora_limite_personal(a.personal)
            a.hora_limite_ref = limite
            a.minutos_tardanza = 0 if a.tipo_actividad == 'ASESORIA' else calcular_minutos_tardanza(a.hora_entrada, limite)
        else:
            a.hora_limite_ref = None
            a.minutos_tardanza = 0
        asistencias_personal.append(a)
    
    return render(request, 'asistencia/reporte_personal.html', {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'personal': asistencias_personal,
        'lista_personal': Personal.objects.filter(estado='Activo'),
        'hora_limite_fijo': HORA_LIMITE_PERSONAL_FIJO.strftime('%I:%M %p'),
        'hora_limite_horas': HORA_LIMITE_PERSONAL_POR_HORAS.strftime('%I:%M %p'),
    })


@login_required
def reporte_asistencia_personal_pdf(request):
    """
    Genera el Informe Ejecutivo de Asistencia y Puntualidad del Personal en formato A4 listo para PDF.
    Calcula minutos exactos de tardanza según tipo de contrato:
    - Personal Fijo: límite 07:40 AM (tardanza desde 07:41 AM)
    - Por Horas / Talleres: límite 07:50 AM (tardanza desde 07:51 AM)
    """
    fecha_inicio, fecha_fin = obtener_rango_fechas(request)
    filtro_contrato = request.GET.get('tipo_contrato', 'TODOS')
    incluir_detalle = request.GET.get('incluir_detalle', '1') == '1'

    personal_qs = Personal.objects.filter(estado='Activo').order_by('apellidos', 'nombres')
    if filtro_contrato == 'Fijo':
        personal_qs = personal_qs.filter(tipo_contrato='Fijo')
        etiqueta_filtro = 'Personal Fijo'
    elif filtro_contrato == 'Por Horas':
        personal_qs = personal_qs.filter(tipo_contrato='Por Horas')
        etiqueta_filtro = 'Por Horas / Talleres'
    else:
        etiqueta_filtro = 'Todo el Personal'

    asistencias_qs = AsistenciaPersonal.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin],
        personal__in=personal_qs
    ).select_related('personal').order_by('fecha', 'personal__apellidos')

    # Mapeo por trabajador
    mapa_trabajadores = {}
    for p in personal_qs:
        limite = obtener_hora_limite_personal(p)
        mapa_trabajadores[p.id] = {
            'personal': p,
            'hora_limite': limite,
            'puntuales': 0,
            'tardanzas': 0,
            'faltas': 0,
            'justificadas': 0,
            'total_registros': 0,
            'minutos_tardanza_acumulados': 0,
            'minutos_laborados_acumulados': 0,
            'suma_minutos_entrada': 0,
            'conteo_entradas': 0,
        }

    incidencias_detalle = []
    todos_los_registros = []
    total_puntuales_global = 0
    total_tardanzas_global = 0
    total_faltas_global = 0
    total_justificadas_global = 0
    total_minutos_tardanza_global = 0

    for reg in asistencias_qs:
        info = mapa_trabajadores.get(reg.personal_id)
        if not info:
            continue

        limite = info['hora_limite']
        min_tarde = 0 if reg.tipo_actividad == 'ASESORIA' else calcular_minutos_tardanza(reg.hora_entrada, limite)
        min_trabajados = calcular_minutos_laborados(reg.hora_entrada, reg.hora_salida)

        # Si llegó después de su hora límite o tiene estado 'T', contabilizamos los minutos de retraso
        es_tardanza_por_hora = min_tarde > 0 and reg.estado in ['P', 'T']
        estado_efectivo = 'T' if es_tardanza_por_hora else reg.estado

        info['total_registros'] += 1
        info['minutos_tardanza_acumulados'] += min_tarde
        info['minutos_laborados_acumulados'] += min_trabajados
        total_minutos_tardanza_global += min_tarde

        if reg.hora_entrada:
            info['suma_minutos_entrada'] += (reg.hora_entrada.hour * 60) + reg.hora_entrada.minute
            info['conteo_entradas'] += 1

        if estado_efectivo == 'P':
            info['puntuales'] += 1
            total_puntuales_global += 1
        elif estado_efectivo == 'T':
            info['tardanzas'] += 1
            total_tardanzas_global += 1
        elif estado_efectivo == 'F':
            info['faltas'] += 1
            total_faltas_global += 1
        elif estado_efectivo == 'J':
            info['justificadas'] += 1
            total_justificadas_global += 1

        item_detalle = {
            'fecha': reg.fecha,
            'personal': reg.personal,
            'hora_limite': limite,
            'hora_entrada': reg.hora_entrada,
            'hora_salida': reg.hora_salida,
            'estado': estado_efectivo,
            'estado_display': dict(AsistenciaPersonal.ESTADOS).get(estado_efectivo, reg.get_estado_display()),
            'minutos_tardanza': min_tarde,
            'tiempo_tardanza_str': formatear_minutos_a_texto(min_tarde),
            'horas_laboradas_str': formatear_minutos_a_texto(min_trabajados) if min_trabajados > 0 else '--',
            'justificacion': reg.justificacion or reg.observaciones or '',
            'tipo_actividad': reg.get_tipo_actividad_display(),
        }
        todos_los_registros.append(item_detalle)
        if estado_efectivo in ['T', 'F', 'J'] or min_tarde > 0:
            incidencias_detalle.append(item_detalle)

    # Construimos la lista consolidada final
    resumen_personal = []
    for p_id, data in mapa_trabajadores.items():
        # Si es un rango corto y queremos mostrar todos los activos (o los que tienen registros)
        total_reg = data['total_registros']
        asistencias_efectivas = data['puntuales'] + data['tardanzas'] + data['justificadas']
        porcentaje_asistencia = round((asistencias_efectivas / total_reg) * 100) if total_reg > 0 else 0
        porcentaje_puntualidad = round((data['puntuales'] / total_reg) * 100) if total_reg > 0 else 0

        if data['conteo_entradas'] > 0:
            prom_min = int(round(data['suma_minutos_entrada'] / data['conteo_entradas']))
            hora_prom = datetime.time(prom_min // 60, prom_min % 60).strftime('%I:%M %p')
        else:
            hora_prom = '--'

        min_acum = data['minutos_tardanza_acumulados']
        if total_reg == 0:
            nivel_cumplimiento = 'Sin registros'
            color_cumplimiento = 'secondary'
        elif data['faltas'] >= 1 or data['tardanzas'] >= 3 or min_acum > 15:
            nivel_cumplimiento = 'Crítico'
            color_cumplimiento = 'danger'
        elif data['tardanzas'] >= 1 or min_acum > 0:
            nivel_cumplimiento = 'Observado'
            color_cumplimiento = 'warning'
        else:
            nivel_cumplimiento = 'Óptimo'
            color_cumplimiento = 'success'

        data['hora_promedio_entrada'] = hora_prom
        data['tiempo_tardanza_texto'] = formatear_minutos_a_texto(min_acum)
        data['tiempo_laborado_texto'] = formatear_minutos_a_texto(data['minutos_laborados_acumulados'])
        data['porcentaje_asistencia'] = porcentaje_asistencia
        data['porcentaje_puntualidad'] = porcentaje_puntualidad
        data['nivel_cumplimiento'] = nivel_cumplimiento
        data['color_cumplimiento'] = color_cumplimiento
        resumen_personal.append(data)

    # Ordenamos: primero quienes tienen más minutos de tardanza o faltas para que Dirección los vea rápido
    resumen_personal.sort(
        key=lambda x: (x['minutos_tardanza_acumulados'], x['faltas'], x['tardanzas'], x['total_registros']),
        reverse=True
    )

    total_marcaciones = total_puntuales_global + total_tardanzas_global + total_faltas_global + total_justificadas_global
    indice_puntualidad_global = round((total_puntuales_global / total_marcaciones) * 100, 1) if total_marcaciones > 0 else 0.0

    visitas_externas = []
    if filtro_contrato == 'TODOS':
        visitas_externas = list(
            AsistenciaPersonal.objects.filter(
                fecha__range=[fecha_inicio, fecha_fin],
                personal__isnull=True
            ).order_by('fecha', 'hora_entrada')
        )

    return render(request, 'asistencia/reporte_personal_pdf.html', {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'es_mismo_dia': fecha_inicio == fecha_fin,
        'etiqueta_filtro': etiqueta_filtro,
        'filtro_contrato': filtro_contrato,
        'incluir_detalle': incluir_detalle,
        'resumen_personal': resumen_personal,
        'incidencias_detalle': incidencias_detalle,
        'visitas_externas': visitas_externas,
        'todos_los_registros': todos_los_registros,
        'total_trabajadores': len(resumen_personal),
        'total_marcaciones': total_marcaciones,
        'total_puntuales_global': total_puntuales_global,
        'total_tardanzas_global': total_tardanzas_global,
        'total_faltas_global': total_faltas_global,
        'total_justificadas_global': total_justificadas_global,
        'total_minutos_tardanza_global': total_minutos_tardanza_global,
        'tiempo_tardanza_global_str': formatear_minutos_a_texto(total_minutos_tardanza_global),
        'indice_puntualidad_global': indice_puntualidad_global,
        'fecha_emision': localtime(now()),
        'hora_limite_fijo_str': HORA_LIMITE_PERSONAL_FIJO.strftime('%I:%M %p'),
        'hora_limite_horas_str': HORA_LIMITE_PERSONAL_POR_HORAS.strftime('%I:%M %p'),
    })


@login_required
def reporte_asistencia_estudiantes(request):
    personal_actual = obtener_personal_logueado(request)
    
    # 💥 MAGIA RBAC: Definimos quién tiene acceso a los filtros globales
    es_admin = personal_actual.cargo in ['DIR', 'COO', 'SEC', 'ASI']
    periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
    bimestre_activo = periodo_actual.bimestre_actual if periodo_actual else 'I'

    # 1. Filtramos por una fecha específica (por defecto HOY)
    fecha_query = request.GET.get('fecha')
    if fecha_query:
        try:
            fecha_final = datetime.datetime.strptime(fecha_query, '%Y-%m-%d').date()
        except ValueError:
            fecha_final = localtime(now()).date()
    else:
        fecha_final = localtime(now()).date()

    # 2. Capturamos el filtro de Aula desde la URL
    aula_id = request.GET.get('aula_id', '')
    origen = request.GET.get('origen', '')
    
    # Traemos todas las aulas para armar el Select (solo útil para Admins)
    aulas = Aula.objects.all().order_by('nivel', 'grado', 'seccion')

    # 3. Traemos a los estudiantes activos
    estudiantes = Estudiante.objects.filter(estado='Activo').order_by('apellidos', 'nombres')
    
    # 💥 EL ESCUDO DE SEGURIDAD
    if not es_admin:
        mis_aulas = Aula.objects.filter(tutor=personal_actual)
        if aula_id and mis_aulas.filter(id=aula_id).exists():
            aula_id = int(aula_id)
        else:
            aula_id = mis_aulas.first().id if mis_aulas.exists() else None

    aula_obj = None
    # 4. Recortamos la lista a través de la tabla Matrícula
    if aula_id:
        aula_obj = Aula.objects.filter(id=aula_id).first()
        estudiantes = estudiantes.filter(
            matricula__aula_id=aula_id, 
            matricula__periodo__activo=True
        ).distinct()
    else:
        if not es_admin:
            estudiantes = Estudiante.objects.none()

    # 5. Traemos las asistencias de ESE DÍA solo de los alumnos filtrados
    asistencias_db = AsistenciaEstudiante.objects.filter(
        fecha=fecha_final,
        estudiante__in=estudiantes
    ).select_related('estudiante')
    
    dict_asistencias = {a.estudiante_id: a for a in asistencias_db}

    # 💥 HISTORIAL ESTRICTO: Adaptado a los campos reales de tu modelo
    historial_db = AsistenciaEstudiante.objects.filter(
        estudiante__in=estudiantes,
        bimestre=bimestre_activo
    ).values('estudiante_id', 'estado')
    
    stats_globales = {e.id: {'P': 0, 'T': 0, 'F': 0, 'J': 0} for e in estudiantes}
    
    for registro in historial_db:
        estado = registro['estado']
        if estado in stats_globales[registro['estudiante_id']]:
            stats_globales[registro['estudiante_id']][estado] += 1

    # 6. Armamos la Matriz Maestra
    lista_completa = []
    for e in estudiantes:
        asis = dict_asistencias.get(e.id)
        if asis and asis.hora_registro:
            asis.minutos_tardanza = calcular_minutos_tardanza(asis.hora_registro, HORA_LIMITE_ESTUDIANTE)
        lista_completa.append({
            'estudiante': e,
            'asistencia': asis,
            'stats': stats_globales[e.id],
        })

    return render(request, 'asistencia/reporte_estudiantes.html', {
        'fecha_seleccionada': fecha_final,
        'lista_completa': lista_completa,
        'aulas': aulas,
        'aula_seleccionada': int(aula_id) if aula_id else '',
        'es_admin': es_admin,
        'aula_obj': aula_obj,
        'origen': origen,
        'bimestre_actual': bimestre_activo,
    })


@login_required
def reporte_asistencia_estudiantes_pdf(request):
    """
    Genera el Reporte Oficial de Asistencia Estudiantil en formato A4 listo para PDF.
    Exige seleccionar un Aula específica para garantizar eficiencia y enfoque.
    Modalidades:
    - DIARIO: Parte del día seleccionado (hora de llegada, minutos de tardanza tras 08:00 AM, justificación)
    - SEMANAL: Consolidado de Lunes a Viernes de la semana seleccionada
    - MENSUAL: Consolidado de todo el mes seleccionado
    - BIMESTRAL: Consolidado acumulado del bimestre activo
    """
    personal_actual = obtener_personal_logueado(request)
    es_admin = personal_actual and personal_actual.cargo in ['DIR', 'COO', 'SEC', 'ASI']
    periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
    bimestre_activo = periodo_actual.bimestre_actual if periodo_actual else 'I'

    aula_id = request.GET.get('aula_id', '')
    tipo_reporte = request.GET.get('tipo_reporte', 'DIARIO').upper()
    fecha_query = request.GET.get('fecha', '')

    try:
        fecha_ref = datetime.datetime.strptime(fecha_query, '%Y-%m-%d').date() if fecha_query else localtime(now()).date()
    except ValueError:
        fecha_ref = localtime(now()).date()

    # Validación de seguridad de aula
    if not es_admin and personal_actual:
        mis_aulas = Aula.objects.filter(tutor=personal_actual)
        if aula_id and mis_aulas.filter(id=aula_id).exists():
            aula_obj = mis_aulas.filter(id=aula_id).first()
        else:
            aula_obj = mis_aulas.first()
    else:
        aula_obj = Aula.objects.filter(id=aula_id).first() if str(aula_id).isdigit() else Aula.objects.first()

    if not aula_obj:
        return redirect('asistencia:reporte_asistencia_estudiantes')

    estudiantes = list(
        Estudiante.objects.filter(
            estado='Activo',
            matricula__aula=aula_obj,
            matricula__periodo=periodo_actual
        ).distinct().order_by('apellidos', 'nombres')
    )

    # Determinamos el rango de fechas o filtro según tipo_reporte
    MESES_ES = [
        '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    if tipo_reporte == 'SEMANAL':
        fecha_inicio = fecha_ref - datetime.timedelta(days=fecha_ref.weekday())
        fecha_fin = fecha_inicio + datetime.timedelta(days=4)
        modalidad_texto = 'Semanal'
        fecha_consulta_texto = f"Del {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}"
        asistencias_qs = AsistenciaEstudiante.objects.filter(
            estudiante__in=estudiantes,
            fecha__range=[fecha_inicio, fecha_fin]
        )
    elif tipo_reporte == 'MENSUAL':
        ultimo_dia = calendar.monthrange(fecha_ref.year, fecha_ref.month)[1]
        fecha_inicio = datetime.date(fecha_ref.year, fecha_ref.month, 1)
        fecha_fin = datetime.date(fecha_ref.year, fecha_ref.month, ultimo_dia)
        nombre_mes = MESES_ES[fecha_ref.month]
        modalidad_texto = 'Mensual'
        fecha_consulta_texto = f"{nombre_mes} {fecha_ref.year}"
        asistencias_qs = AsistenciaEstudiante.objects.filter(
            estudiante__in=estudiantes,
            fecha__range=[fecha_inicio, fecha_fin]
        )
    elif tipo_reporte == 'BIMESTRAL':
        fecha_inicio = fecha_ref
        fecha_fin = fecha_ref
        modalidad_texto = 'Bimestral'
        fecha_consulta_texto = f"Bimestre {bimestre_activo}"
        asistencias_qs = AsistenciaEstudiante.objects.filter(
            estudiante__in=estudiantes,
            bimestre=bimestre_activo
        )
    else:
        tipo_reporte = 'DIARIO'
        fecha_inicio = fecha_ref
        fecha_fin = fecha_ref
        modalidad_texto = 'Diario'
        fecha_consulta_texto = fecha_ref.strftime('%d/%m/%Y')
        asistencias_qs = AsistenciaEstudiante.objects.filter(
            estudiante__in=estudiantes,
            fecha=fecha_ref
        )

    # Historial bimestral para enriquecer incluso el reporte diario
    historial_bim_qs = AsistenciaEstudiante.objects.filter(
        estudiante__in=estudiantes,
        bimestre=bimestre_activo
    ).values('estudiante_id', 'estado')

    stats_bimestrales = {e.id: {'P': 0, 'T': 0, 'F': 0, 'J': 0} for e in estudiantes}
    for h in historial_bim_qs:
        est_id = h['estudiante_id']
        st = h['estado']
        if est_id in stats_bimestrales and st in stats_bimestrales[est_id]:
            stats_bimestrales[est_id][st] += 1

    # Procesamos las asistencias del periodo elegido
    mapa_registros_por_alumno = {e.id: [] for e in estudiantes}
    for a in asistencias_qs:
        mapa_registros_por_alumno[a.estudiante_id].append(a)

    filas_estudiantes = []
    alumnos_alerta = []

    total_p_periodo = 0
    total_t_periodo = 0
    total_f_periodo = 0
    total_j_periodo = 0
    total_minutos_tardanza_aula = 0
    sin_registro_hoy = 0

    for idx, est in enumerate(estudiantes, start=1):
        regs = mapa_registros_por_alumno.get(est.id, [])
        p_cnt, t_cnt, f_cnt, j_cnt = 0, 0, 0, 0
        min_tarde_alumno = 0
        registro_dia = regs[0] if (tipo_reporte == 'DIARIO' and regs) else None

        for r in regs:
            min_t = calcular_minutos_tardanza(r.hora_registro, HORA_LIMITE_ESTUDIANTE)
            min_tarde_alumno += min_t
            es_tarde_hora = min_t > 0 and r.estado in ['P', 'T']
            estado_real = 'T' if es_tarde_hora else r.estado

            if estado_real == 'P':
                p_cnt += 1
            elif estado_real == 'T':
                t_cnt += 1
            elif estado_real == 'F':
                f_cnt += 1
            elif estado_real == 'J':
                j_cnt += 1

        total_p_periodo += p_cnt
        total_t_periodo += t_cnt
        total_f_periodo += f_cnt
        total_j_periodo += j_cnt
        total_minutos_tardanza_aula += min_tarde_alumno

        total_eval = p_cnt + t_cnt + f_cnt + j_cnt
        asist_efectiva = p_cnt + t_cnt + j_cnt
        porcentaje_asis = round((asist_efectiva / total_eval) * 100) if total_eval > 0 else 0

        if tipo_reporte == 'DIARIO':
            if not registro_dia:
                sin_registro_hoy += 1
                condicion = 'Sin marcaje'
                color_condicion = 'secondary'
            elif f_cnt > 0:
                condicion = 'Falta'
                color_condicion = 'danger'
            elif t_cnt > 0:
                condicion = 'Tardanza'
                color_condicion = 'warning'
            elif j_cnt > 0:
                condicion = 'Justificada'
                color_condicion = 'info'
            else:
                condicion = 'Puntual'
                color_condicion = 'success'
        else:
            if total_eval == 0:
                condicion = 'Sin registros'
                color_condicion = 'secondary'
            elif f_cnt >= 3 or (total_eval >= 3 and porcentaje_asis < 80):
                condicion = 'Riesgo'
                color_condicion = 'danger'
            elif t_cnt >= 3 or min_tarde_alumno >= 20 or f_cnt >= 1:
                condicion = 'Observado'
                color_condicion = 'warning'
            else:
                condicion = 'Regular'
                color_condicion = 'success'

        fila = {
            'numero': idx,
            'estudiante': est,
            'registro_dia': registro_dia,
            'p_cnt': p_cnt,
            't_cnt': t_cnt,
            'f_cnt': f_cnt,
            'j_cnt': j_cnt,
            'total_eval': total_eval,
            'minutos_tardanza': min_tarde_alumno,
            'tiempo_tardanza_str': formatear_minutos_a_texto(min_tarde_alumno),
            'porcentaje_asistencia': porcentaje_asis,
            'condicion': condicion,
            'color_condicion': color_condicion,
            'stats_bim': stats_bimestrales.get(est.id, {'P': 0, 'T': 0, 'F': 0, 'J': 0}),
        }
        filas_estudiantes.append(fila)

        # Seleccionamos para el cuadro de alerta temprana de tutoría
        if tipo_reporte == 'DIARIO':
            if f_cnt > 0 or t_cnt > 0 or j_cnt > 0:
                alumnos_alerta.append(fila)
        else:
            if f_cnt >= 1 or t_cnt >= 2 or min_tarde_alumno >= 15:
                alumnos_alerta.append(fila)

    total_marcajes_periodo = total_p_periodo + total_t_periodo + total_f_periodo + total_j_periodo
    asistencia_efectiva_global = round(
        ((total_p_periodo + total_t_periodo + total_j_periodo) / total_marcajes_periodo) * 100, 1
    ) if total_marcajes_periodo > 0 else 0.0

    return render(request, 'asistencia/reporte_estudiantes_pdf.html', {
        'aula': aula_obj,
        'periodo': periodo_actual,
        'bimestre_actual': bimestre_activo,
        'tipo_reporte': tipo_reporte,
        'modalidad_texto': modalidad_texto,
        'fecha_consulta_texto': fecha_consulta_texto,
        'es_diario': tipo_reporte == 'DIARIO',
        'fecha_ref': fecha_ref,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'filas_estudiantes': filas_estudiantes,
        'total_alumnos': len(estudiantes),
        'total_p_periodo': total_p_periodo,
        'total_t_periodo': total_t_periodo,
        'total_f_periodo': total_f_periodo,
        'total_j_periodo': total_j_periodo,
        'sin_registro_hoy': sin_registro_hoy,
        'asistencia_efectiva_global': asistencia_efectiva_global,
        'fecha_emision': localtime(now()),
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

        # Capturamos el bimestre actual para la base de datos
        periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
        bimestre = periodo_actual.bimestre_actual if periodo_actual else 'I'

        if tipo_usuario in ['DOC', 'PER']:
            # Validación de ventana horaria permitida para Personal (06:30 AM - 07:00 PM)
            if hora_actual < HORA_INICIO_QR_PERSONAL or hora_actual > HORA_FIN_QR_PERSONAL:
                return JsonResponse({
                    'status': 'warning',
                    'mensaje': f'Fuera de horario permitido para personal ({HORA_INICIO_QR_PERSONAL.strftime("%I:%M %p")} - {HORA_FIN_QR_PERSONAL.strftime("%I:%M %p")}).'
                })

            personal = Personal.objects.filter(id=id_usuario).first()
            if not personal:
                return JsonResponse({'status': 'error', 'mensaje': 'Personal no encontrado.'}, status=404)

            # Si es Docente Por Horas ingresando desde las 02:30 PM -> se marca como Asesoría (Puntual)
            if personal.tipo_contrato == 'Por Horas' and hora_actual >= HORA_INICIO_ASESORIA_TARDE:
                min_retraso = 0
                estado_calculado = 'P'
                tipo_actividad_calc = 'ASESORIA'
            else:
                hora_limite_per = obtener_hora_limite_personal(personal)
                min_retraso = calcular_minutos_tardanza(hora_actual, hora_limite_per)
                estado_calculado = 'P' if min_retraso == 0 else 'T'
                tipo_actividad_calc = 'REGULAR'

            asistencia, created = AsistenciaPersonal.objects.get_or_create(
                personal=personal, 
                fecha=fecha_hoy,
                defaults={
                    'estado': estado_calculado,
                    'hora_entrada': hora_actual,
                    'tipo_actividad': tipo_actividad_calc
                }
            )

            if created:
                if tipo_actividad_calc == 'ASESORIA':
                    mensaje = f"Entrada por Asesoría: {personal.nombres}"
                else:
                    mensaje = f"Entrada registrada: {personal.nombres}"
                    if min_retraso > 0:
                        mensaje += f" (Tardanza: +{min_retraso} min)"
                tipo_registro = 'Entrada'
            elif not asistencia.hora_salida:
                asistencia.hora_salida = hora_actual
                asistencia.save()
                mensaje = f"Salida registrada: {personal.nombres}"
                tipo_registro = 'Salida'
            else:
                return JsonResponse({'status': 'warning', 'mensaje': 'El personal ya registró entrada y salida hoy.'})
            
        elif tipo_usuario == 'EST':
            # Validación de ventana horaria permitida para Estudiantes (06:30 AM - 02:30 PM)
            if hora_actual < HORA_INICIO_QR_ESTUDIANTE or hora_actual > HORA_FIN_QR_ESTUDIANTE:
                return JsonResponse({
                    'status': 'warning',
                    'mensaje': f'Fuera de horario escolar permitido ({HORA_INICIO_QR_ESTUDIANTE.strftime("%I:%M %p")} - {HORA_FIN_QR_ESTUDIANTE.strftime("%I:%M %p")}).'
                })

            estudiante = Estudiante.objects.filter(id=id_usuario).first()
            if not estudiante:
                return JsonResponse({'status': 'error', 'mensaje': 'Estudiante no encontrado.'}, status=404)

            # Calculamos puntualidad de estudiante: límite 08:00 AM (tardanza desde 08:01 AM)
            min_retraso = calcular_minutos_tardanza(hora_actual, HORA_LIMITE_ESTUDIANTE)
            estado_calculado = 'P' if min_retraso == 0 else 'T'

            asistencia, created = AsistenciaEstudiante.objects.get_or_create(
                estudiante=estudiante, 
                fecha=fecha_hoy,
                defaults={'estado': estado_calculado, 'hora_registro': hora_actual, 'bimestre': bimestre}
            )
            
            if created:
                mensaje = f"Asistencia registrada: {estudiante.nombres}"
                if min_retraso > 0:
                    mensaje += f" (Tardanza: +{min_retraso} min)"
                tipo_registro = 'Ingreso'
            else:
                return JsonResponse({'status': 'warning', 'mensaje': 'El estudiante ya registró su asistencia hoy.'})

        else:
            return JsonResponse({'status': 'error', 'mensaje': 'Formato de QR desconocido.'}, status=400)

        return JsonResponse({'status': 'success', 'mensaje': mensaje, 'tipo': tipo_registro, 'hora': hora_actual.strftime("%I:%M %p")})

    except Exception as e:
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
            if asistencia.es_externo:
                nombre_ext = (data.get('nombre_externo') or '').strip()
                if nombre_ext:
                    asistencia.nombre_externo = nombre_ext
                asistencia.cargo_externo = (data.get('cargo_externo') or '').strip()
            mensaje = "Asistencia actualizada correctamente."
        else: 
            es_externo = bool(data.get('es_externo', False))
            if es_externo:
                nombre_ext = (data.get('nombre_externo') or '').strip()
                cargo_ext = (data.get('cargo_externo') or '').strip()
                if not nombre_ext:
                    return JsonResponse({'success': False, 'mensaje': 'Debe ingresar el nombre del personal externo o visitante.'})
                asistencia = AsistenciaPersonal(
                    personal=None,
                    nombre_externo=nombre_ext,
                    cargo_externo=cargo_ext or 'Visita / Externo',
                    fecha=hoy
                )
                mensaje = "Asistencia de personal externo registrada."
            else:
                personal_id = data.get('personal_id')
                if not personal_id:
                    return JsonResponse({'success': False, 'mensaje': 'Debe seleccionar un personal registrado.'})
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
def editar_hora_estudiante_api(request):
    try:
        data = json.loads(request.body)
        asistencia = get_object_or_404(AsistenciaEstudiante, id=data.get('id'))
        
        nueva_hora = data.get('hora_registro')
        if nueva_hora: 
            asistencia.hora_registro = nueva_hora
            asistencia.save()
            return JsonResponse({'success': True, 'mensaje': 'Hora de registro actualizada.'})
            
        return JsonResponse({'success': False, 'mensaje': 'Hora no válida.'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)})

@require_POST
def eliminar_asistencia_personal_api(request, id_asistencia):
    get_object_or_404(AsistenciaPersonal, id=id_asistencia).delete()
    return JsonResponse({'success': True, 'mensaje': 'Registro eliminado correctamente.'})


# 💥 NUEVA API: GUARDA LA ASISTENCIA MASIVA EN 1 SEGUNDO
@require_POST
def guardar_asistencia_masiva_api(request):
    try:
        data = json.loads(request.body)
        fecha_str = data.get('fecha')
        registros = data.get('registros', [])
        
        fecha_obj = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()

        # Capturamos el bimestre activo
        periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
        bimestre = periodo_actual.bimestre_actual if periodo_actual else 'I'

        for reg in registros:
            est_id = reg.get('estudiante_id')
            estado = reg.get('estado')
            justificacion = reg.get('justificacion', '')

            if estado: 
                asistencia, created = AsistenciaEstudiante.objects.get_or_create(
                    estudiante_id=est_id,
                    fecha=fecha_obj,
                    defaults={'estado': estado, 'justificacion': justificacion, 'bimestre': bimestre}
                )
                if not created:
                    asistencia.estado = estado
                    if justificacion:
                        asistencia.justificacion = justificacion
                    asistencia.save()
            else:
                AsistenciaEstudiante.objects.filter(estudiante_id=est_id, fecha=fecha_obj).delete()

        return JsonResponse({'success': True, 'mensaje': 'Matriz de asistencia guardada con éxito.'})
    except Exception as e:
        return JsonResponse({'success': False, 'mensaje': str(e)})

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
