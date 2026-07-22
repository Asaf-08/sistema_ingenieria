import os
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.drawing.image import Image as OpenpyxlImage

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings

from apps.academico.models import Aula, PeriodoLectivo, Matricula, AsignacionAcademica, Nota, Curso, EvaluacionActitudinal
from apps.asistencia.models import AsistenciaEstudiante
from django.db.models import Avg, Sum, Q
from openpyxl.drawing.spreadsheet_drawing import OneCellAnchor, AnchorMarker
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU

@login_required
def consolidado_notas_admin(request):
    """ Vista exclusiva para que Dirección/Coordinación descargue los Excels y vea Analíticas """
    
    # Traemos todas las aulas ordenadas
    aulas = Aula.objects.all().order_by('nivel', 'grado', 'seccion')
    
    aula_id = request.GET.get('aula_id')
    # 1. Primero obtenemos el periodo lectivo que está activo en el colegio
    periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
    
    # 💥 LA SOLUCIÓN: Si hay un periodo activo, extraemos su bimestre actual.
    # Si por alguna razón no hay ninguno activo, usamos 'I' como salvavidas.
    bimestre_predeterminado = periodo_actual.bimestre_actual if periodo_actual else 'I'
    
    # 2. Capturamos el parámetro de la URL. Si viene vacío, adoptará el del sistema (ej: 'II')
    bimestre_actual = request.GET.get('bimestre', bimestre_predeterminado)
    
    # 💥 NUEVO: Atrapamos de dónde viene el usuario
    origen = request.GET.get('origen', '')
    
    # 💥 NUEVO: Atrapamos el curso que quiere inspeccionar
    asignacion_id = request.GET.get('asignacion_id')
    
    asignaciones = []
    aula_seleccionada = None
    
    # Variables dinámicas para el Dashboard
    total_alumnos = 0
    promedio_aula = 0.0
    top_estudiantes = []
    
    # NUEVAS VARIABLES PARA LA TABLA INFERIOR
    asignacion_seleccionada = None
    evals_cuaderno, evals_desafio, evals_examenes = [], [], []
    datos_matriz = []
    
    if aula_id:
        aula_seleccionada = get_object_or_404(Aula, id=aula_id)
        
        # 1. Traemos los cursos asignados a esa aula
        asignaciones = AsignacionAcademica.objects.filter(
            aula=aula_seleccionada, 
            periodo__activo=True
        ).select_related('curso', 'personal')
        
        # 2. Obtenemos los alumnos matriculados
        matriculas = Matricula.objects.filter(
            aula=aula_seleccionada, 
            periodo__activo=True
        ).select_related('estudiante')
        
        total_alumnos = matriculas.count()
        
        # 3. Calculamos el Promedio General del Aula
        promedio_aula = Nota.objects.filter(
            matricula__in=matriculas,
            evaluacion__bimestre=bimestre_actual
        ).aggregate(prom=Avg('valor'))['prom'] or 0.0
        
        # 4. Cuadro de Honor (Top 3): Sumamos las notas usando tu related_name='notas' 💥
        top_estudiantes = matriculas.annotate(
            puntaje_total=Sum('notas__valor', filter=Q(notas__evaluacion__bimestre=bimestre_actual))
        ).exclude(puntaje_total__isnull=True).order_by('-puntaje_total')[:3]
        
        # 💥 NUEVO BLOQUE: Lógica para la Matriz Detallada de la parte inferior
        if asignaciones.exists():
            # Si eligió un curso en el select, lo buscamos. Si no, mostramos el primer curso del salón por defecto.
            if asignacion_id:
                asignacion_seleccionada = asignaciones.filter(id=asignacion_id).first()
            else:
                asignacion_seleccionada = asignaciones.first()

            if asignacion_seleccionada:
                # Reutilizamos el motor matemático que armamos para el profesor
                evaluaciones = asignacion_seleccionada.evaluaciones.filter(bimestre=bimestre_actual).order_by('fecha', 'id')

                evals_cuaderno = evaluaciones.filter(tipo__in=['CUADERNO', 'LIBRO'])
                evals_desafio = evaluaciones.filter(tipo='DESAFIO')
                evals_examenes = evaluaciones.filter(tipo__in=['MENSUAL', 'BIMESTRAL', 'SIMULACRO'])

                matriculas = Matricula.objects.filter(aula=aula_seleccionada, estudiante__estado='Activo').order_by('estudiante__apellidos')
                notas_db = Nota.objects.filter(evaluacion__in=evaluaciones).select_related('matricula', 'evaluacion')

                diccionario_notas = {}
                for n in notas_db:
                    if n.matricula_id not in diccionario_notas:
                        diccionario_notas[n.matricula_id] = {}
                    diccionario_notas[n.matricula_id][n.evaluacion_id] = n.valor

                for mat in matriculas:
                    notas_alumno = diccionario_notas.get(mat.id, {})

                    def calcular_promedio(grupo_evaluaciones):
                        valores = [notas_alumno[e.id] for e in grupo_evaluaciones if e.id in notas_alumno and notas_alumno[e.id] is not None]
                        return round(sum(valores) / len(valores), 2) if valores else 0.0

                    prom_cuaderno = calcular_promedio(evals_cuaderno)
                    prom_desafio = calcular_promedio(evals_desafio)
                    prom_examen = calcular_promedio(evals_examenes)

                    sumatoria_promedios = [p for p in [prom_cuaderno, prom_desafio, prom_examen] if p > 0]
                    prom_general = round(sum(sumatoria_promedios) / len(sumatoria_promedios), 2) if sumatoria_promedios else 0.0

                    datos_matriz.append({
                        'estudiante': f"{mat.estudiante.apellidos}, {mat.estudiante.nombres}",
                        'notas': notas_alumno,
                        'prom_cuaderno': prom_cuaderno,
                        'prom_desafio': prom_desafio,
                        'prom_examen': prom_examen,
                        'prom_general': prom_general
                    })
        
    return render(request, 'personal/consolidado_notas.html', {
        'aulas': aulas,
        'asignaciones': asignaciones,
        'aula_seleccionada': aula_seleccionada,
        'bimestre': bimestre_actual,
        'origen': origen,
        # Enviamos las métricas reales
        'total_alumnos': total_alumnos,
        'promedio_aula': promedio_aula,
        'top_estudiantes': top_estudiantes,
        
        # Nuestras variables nuevas
        'asignacion_seleccionada': asignacion_seleccionada,
        'evals_cuaderno': evals_cuaderno,
        'evals_desafio': evals_desafio,
        'evals_examenes': evals_examenes,
        'datos_matriz': datos_matriz,
    })

@login_required
def exportar_matriz_oficial_excel(request, asignacion_id):
    asignacion = get_object_or_404(AsignacionAcademica, id=asignacion_id)
    # 1. Primero obtenemos el periodo lectivo que está activo en el colegio
    periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
    
    # 💥 LA SOLUCIÓN: Si hay un periodo activo, extraemos su bimestre actual.
    # Si por alguna razón no hay ninguno activo, usamos 'I' como salvavidas.
    bimestre_predeterminado = periodo_actual.bimestre_actual if periodo_actual else 'I'
    
    # 2. Capturamos el parámetro de la URL. Si viene vacío, adoptará el del sistema (ej: 'II')
    bimestre_actual = request.GET.get('bimestre', bimestre_predeterminado)
    en_blanco = request.GET.get('blanco', '0') == '1'

    # 1. Traer datos
    matriculas = Matricula.objects.filter(aula=asignacion.aula, estudiante__estado='Activo').select_related('estudiante').order_by('estudiante__apellidos')
    evaluaciones = asignacion.evaluaciones.filter(bimestre=bimestre_actual)
    notas_db = Nota.objects.filter(evaluacion__in=evaluaciones)
    
    diccionario_notas = {}
    for n in notas_db:
        if n.matricula_id not in diccionario_notas:
            diccionario_notas[n.matricula_id] = {}
        diccionario_notas[n.matricula_id][n.evaluacion_id] = n.valor

    evals_cuaderno = list(evaluaciones.filter(tipo='CUADERNO'))
    evals_desafio = list(evaluaciones.filter(tipo='DESAFIO'))
    evals_examenes = list(evaluaciones.filter(tipo__in=['MENSUAL', 'BIMESTRAL', 'SIMULACRO']))

    # 2. Inicializar Excel y Estilos
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Notas {bimestre_actual} Bim"
    
    # Paleta de colores
    fill_naranja = PatternFill(start_color="FF6600", end_color="FF6600", fill_type="solid")
    fill_blanco = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    fill_promedios = PatternFill(start_color="FDE9D9", end_color="FDE9D9", fill_type="solid") 
    
    # Fuentes
    font_titulo = Font(name="Arial", size=14, bold=True)
    font_blanca = Font(name="Arial", size=9, bold=True, color="FFFFFF")
    font_negra_bold = Font(name="Arial", size=9, bold=True)
    font_normal = Font(name="Arial", size=9)
    
    # Alineaciones
    align_centro = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_izq = Alignment(horizontal="left", vertical="center")
    align_bottom_center = Alignment(horizontal="center", vertical="bottom")
    align_vertical_bottom = Alignment(horizontal="center", vertical="bottom", textRotation=90)
    
    borde_fino = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    borde_grueso_outer = Border(left=Side(style='thick'), right=Side(style='thick'), top=Side(style='thick'), bottom=Side(style='thick'))

    # ==========================================
    # 3. CONSTRUCCIÓN DE LA CABECERA PRINCIPAL
    # ==========================================
    # FILA 2: Título Principal con Borde Grueso y Altura 35
    ws.row_dimensions[2].height = 35
    ws.merge_cells("A2:W2")
    ws["A2"] = f"INVENTARIO DE GANANCIAS Y PÉRDIDAS DE APRENDIZAJES {asignacion.periodo.anio}"
    ws["A2"].font = font_titulo
    ws["A2"].alignment = align_centro
    
    for col in range(1, 24):
        ws.cell(row=2, column=col).border = borde_grueso_outer

    # FILA 3: Subtítulos del Curso
    ws.merge_cells("A3:B3")
    ws["A3"] = f"ACTIVIDAD: {asignacion.curso.nombre.upper()}"
    
    ws.merge_cells("C3:I3")
    ws["C3"] = f"AULA: {asignacion.aula.grado} '{asignacion.aula.seccion}'"
    
    ws.merge_cells("K3:S3")
    ws["K3"] = f"NIVEL: {asignacion.aula.get_nivel_display().upper()}"
    
    ws.merge_cells("T3:W3")
    ws["T3"] = f"BIMESTRE: {bimestre_actual}"

    for cell in ["A3", "C3", "K3", "T3"]:
        ws[cell].font = font_negra_bold

    # ==========================================
    # 4. ESTRUCTURA DE TABLA (FILAS 4, 5 y 6)
    # ==========================================
    ws.row_dimensions[6].height = 160  # 💥 Fila 6 con altura 160

    ws.merge_cells("A4:A6")
    ws["A4"] = "N°"
    ws["A4"].alignment, ws["A4"].font = align_centro, font_negra_bold

    ws.merge_cells("B4:B6")
    ws["B4"] = "APELLIDOS Y NOMBRES"
    ws["B4"].alignment, ws["B4"].font = align_centro, font_negra_bold

    # -- EVALUACIONES MENSUALES --
    ws.merge_cells("C4:E5")
    ws["C4"] = "EVALUACIONES MENSUALES"
    ws["C4"].fill, ws["C4"].font, ws["C4"].alignment = fill_naranja, font_blanca, align_centro

    ws["C6"], ws["D6"], ws["E6"] = "DESARROLLO DE LIBRO", "DESARROLLO DE TAREAS", "PROM - 1"
    
    ws["C6"].fill, ws["C6"].alignment, ws["C6"].font = fill_blanco, align_vertical_bottom, font_negra_bold
    ws["D6"].fill, ws["D6"].alignment, ws["D6"].font = fill_blanco, align_vertical_bottom, font_negra_bold
    ws["E6"].fill, ws["E6"].alignment, ws["E6"].font = fill_naranja, align_vertical_bottom, font_blanca

    # -- EVALUACIONES BIMESTRALES --
    ws.merge_cells("F4:H5")
    ws["F4"] = "EVALUACIONES BIMESTRALES"
    ws["F4"].fill, ws["F4"].font, ws["F4"].alignment = fill_naranja, font_blanca, align_centro

    ws["F6"], ws["G6"], ws["H6"] = "DESARROLLO DE LIBRO", "DESARROLLO DE TAREAS", "PROM - 2"
    
    ws["F6"].fill, ws["F6"].alignment, ws["F6"].font = fill_blanco, align_vertical_bottom, font_negra_bold
    ws["G6"].fill, ws["G6"].alignment, ws["G6"].font = fill_blanco, align_vertical_bottom, font_negra_bold
    ws["H6"].fill, ws["H6"].alignment, ws["H6"].font = fill_naranja, align_vertical_bottom, font_blanca

    # -- EVALUACIONES DIARIAS --
    ws.merge_cells("I4:Q4")
    ws["I4"] = "EVALUACIONES DIARIAS"
    ws["I4"].fill, ws["I4"].font, ws["I4"].alignment = fill_naranja, font_blanca, align_centro

    ws.merge_cells("I5:Q5")
    ws["I5"] = "DESAFIO EMPRENDEDOR"
    ws["I5"].fill, ws["I5"].font, ws["I5"].alignment = fill_blanco, font_negra_bold, align_centro

    for i in range(1, 9):
        col_letra = openpyxl.utils.get_column_letter(8 + i)
        ws[f"{col_letra}6"] = str(i)
        ws[f"{col_letra}6"].fill = fill_blanco
        ws[f"{col_letra}6"].alignment, ws[f"{col_letra}6"].font = align_bottom_center, font_negra_bold

    ws["Q6"] = "PROM - 3"
    ws["Q6"].fill, ws["Q6"].alignment, ws["Q6"].font = fill_naranja, align_vertical_bottom, font_blanca

    # -- EXÁMENES IMPORTANTES --
    ws.merge_cells("R4:R6")
    ws["R4"] = "CONTROL DE CALIDAD"
    ws["R4"].fill, ws["R4"].alignment, ws["R4"].font = fill_naranja, align_vertical_bottom, font_blanca

    ws.merge_cells("S4:S6")
    ws["S4"] = "ISO INGENIERÍA"
    ws["S4"].fill, ws["S4"].alignment, ws["S4"].font = fill_naranja, align_vertical_bottom, font_blanca

    # -- CONCURSO DE APTITUD --
    ws.merge_cells("T4:V5")  # 💥 Cubre fila 4 y 5
    ws["T4"] = "CONCURSO DE APTITUD"
    ws["T4"].fill, ws["T4"].font, ws["T4"].alignment = fill_naranja, font_blanca, align_centro

    ws["T6"] = "CONCURSO DE APTITUD MENSUAL"
    ws["T6"].fill, ws["T6"].alignment, ws["T6"].font = fill_blanco, align_vertical_bottom, font_negra_bold

    ws["U6"] = "CONCURSO DE APTITUD MENSUAL"
    ws["U6"].fill, ws["U6"].alignment, ws["U6"].font = fill_blanco, align_vertical_bottom, font_negra_bold

    ws["V6"] = "PROM - CONCURSO DE APTITUD"
    ws["V6"].fill, ws["V6"].alignment, ws["V6"].font = fill_naranja, align_vertical_bottom, font_blanca

    # -- CERTIFICACIÓN DE CALIDAD --
    ws.merge_cells("W4:W6")
    ws["W4"] = "CERTIFICACIÓN DE CALIDAD"
    ws["W4"].fill, ws["W4"].alignment, ws["W4"].font = fill_naranja, align_vertical_bottom, font_blanca

    # Aplicar bordes finos a las celdas de la cabecera
    for row in ws.iter_rows(min_row=4, max_row=6, min_col=1, max_col=23):
        for cell in row:
            cell.border = borde_fino

    # ==========================================
    # 5. ESCRIBIR DATOS (Desde Fila 7)
    # ==========================================
    fila_actual = 7
    for idx, mat in enumerate(matriculas, 1):
        ws[f"A{fila_actual}"] = idx
        ws[f"B{fila_actual}"] = f"{mat.estudiante.apellidos}, {mat.estudiante.nombres}"
        ws[f"A{fila_actual}"].alignment = align_centro
        ws[f"B{fila_actual}"].alignment = align_izq

        for col_idx in range(1, 24):
            celda = ws.cell(row=fila_actual, column=col_idx)
            celda.border = borde_fino
            celda.font = font_normal
            if col_idx > 2:
                celda.alignment = align_centro
            
            if col_idx in [5, 8, 17, 18, 19, 22, 23]:
                celda.fill = fill_promedios

        if not en_blanco:
            notas_alumno = diccionario_notas.get(mat.id, {})
            
            def calcular_y_redondear(grupo):
                valores = [float(notas_alumno[e.id]) for e in grupo if e.id in notas_alumno and notas_alumno[e.id] is not None]
                if valores:
                    promedio = sum(valores) / len(valores)
                    return int(promedio + 0.5) 
                return 0

            prom_cuaderno = calcular_y_redondear(evals_cuaderno)
            prom_desafio = calcular_y_redondear(evals_desafio)
            
            nota_control = calcular_y_redondear([e for e in evals_examenes if e.tipo == 'MENSUAL'])
            nota_iso = calcular_y_redondear([e for e in evals_examenes if e.tipo == 'BIMESTRAL'])
            
            simulacros_list = [e for e in evals_examenes if e.tipo == 'SIMULACRO']
            val_sim1 = int(float(notas_alumno[simulacros_list[0].id]) + 0.5) if len(simulacros_list) > 0 and simulacros_list[0].id in notas_alumno and notas_alumno[simulacros_list[0].id] is not None else ""
            val_sim2 = int(float(notas_alumno[simulacros_list[1].id]) + 0.5) if len(simulacros_list) > 1 and simulacros_list[1].id in notas_alumno and notas_alumno[simulacros_list[1].id] is not None else ""
            
            prom_simulacro = 0
            sims_validos = [v for v in [val_sim1, val_sim2] if v != ""]
            if sims_validos:
                prom_simulacro = int(sum(sims_validos) / len(sims_validos) + 0.5)

            sumatoria_general = []
            if prom_cuaderno > 0: sumatoria_general.append(prom_cuaderno) 
            if prom_cuaderno > 0: sumatoria_general.append(prom_cuaderno) 
            if prom_desafio > 0: sumatoria_general.append(prom_desafio)   
            if nota_control > 0: sumatoria_general.append(nota_control)   
            if nota_iso > 0: sumatoria_general.append(nota_iso)           
            if prom_simulacro > 0: sumatoria_general.append(prom_simulacro) 
            
            prom_final_certificacion = int(sum(sumatoria_general) / len(sumatoria_general) + 0.5) if sumatoria_general else ""

            ws[f"E{fila_actual}"] = prom_cuaderno if prom_cuaderno > 0 else ""
            ws[f"H{fila_actual}"] = prom_cuaderno if prom_cuaderno > 0 else ""
            ws[f"Q{fila_actual}"] = prom_desafio if prom_desafio > 0 else ""
            ws[f"R{fila_actual}"] = nota_control if nota_control > 0 else ""
            ws[f"S{fila_actual}"] = nota_iso if nota_iso > 0 else ""
            ws[f"T{fila_actual}"] = val_sim1
            ws[f"U{fila_actual}"] = val_sim2
            ws[f"V{fila_actual}"] = prom_simulacro if prom_simulacro > 0 else ""
            ws[f"W{fila_actual}"] = prom_final_certificacion

            for i, ev in enumerate(evals_desafio[:8]):
                nota = notas_alumno.get(ev.id)
                if nota is not None:
                    col_letra = openpyxl.utils.get_column_letter(9 + i)
                    ws[f"{col_letra}{fila_actual}"] = int(float(nota) + 0.5)

        fila_actual += 1

    # 6. Ajustar Anchos
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 35
    for col_idx in range(3, 24):
        col_letra = openpyxl.utils.get_column_letter(col_idx)
        ws.column_dimensions[col_letra].width = 5

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Matriz_{asignacion.curso.nombre}_{bimestre_actual}B.xlsx'
    wb.save(response)
    return response

# ==========================================
# FUNCIONES AUXILIARES PARA LIBRETAS
# ==========================================
def redondear(valor):
    return int(float(valor) + 0.5) if valor else 0

def obtener_recomendacion(promedio):
    if promedio == "" or promedio == 0 or promedio is None or promedio == "-": return "-"
    promedio = float(promedio)
    if promedio > 17: return "¡ Excelente, Buen trabajo, puedes llegar aún más lejos !"
    elif promedio > 13: return "¡ Buen trabajo, sigue avanzando !"
    elif promedio > 10: return " ¡ A esmerarse más, tú puedes !"
    else: return " ¡ No te desanimes, vamos, confiamos en ti !"

def clasificar_bimestre_asistencia(fecha, bimestre_actual_sistema):
    """ Filtra y agrupa la asistencia según el calendario escolar de forma histórica """
    mes = fecha.month
    if bimestre_actual_sistema == 'I': return 'I'
    if bimestre_actual_sistema == 'II':
        return 'I' if mes in [3, 4, 5, 6] else 'II'
    elif bimestre_actual_sistema == 'III':
        if mes in [3, 4, 5, 6]: return 'I'
        elif mes in [7, 8]: return 'II'
        else: return 'III'
    else:
        if mes in [3, 4, 5, 6]: return 'I'
        elif mes in [7, 8]: return 'II'
        elif mes in [9, 10]: return 'III'
        else: return 'IV'

@login_required
def exportar_libretas_aula_excel(request, aula_id):
    """ Generador Maestro: Genera UN SOLO archivo Excel con pestañas por alumno y logos dinámicos """
    aula = get_object_or_404(Aula, id=aula_id)
    periodo_actual = PeriodoLectivo.objects.get(activo=True)
    bimestre_sistema = periodo_actual.bimestre_actual # 'I', 'II', 'III' o 'IV'
    
    # Lista e índices de control de flujo para bloquear bimestres futuros
    BIMESTRES_ORDEN = ['I', 'II', 'III', 'IV']
    idx_sistema = BIMESTRES_ORDEN.index(bimestre_sistema)
    
    matriculas = Matricula.objects.filter(aula=aula, estudiante__estado='Activo').select_related('estudiante').order_by('estudiante__apellidos')
    asignaciones = AsignacionAcademica.objects.filter(aula=aula, periodo=periodo_actual).select_related('curso')
    
    # Precarga masiva indexada de notas de alumnos
    todas_las_evaluaciones = []
    evaluaciones_por_asignacion = {}
    for asig in asignaciones:
        evals = list(asig.evaluaciones.all())
        todas_las_evaluaciones.extend(evals)
        evaluaciones_por_asignacion[asig.id] = evals
        
    notas_db = Nota.objects.filter(evaluacion__in=todas_las_evaluaciones).select_related('evaluacion')
    mapa_notas = {}
    for n in notas_db:
        if n.matricula_id not in mapa_notas: mapa_notas[n.matricula_id] = {}
        mapa_notas[n.matricula_id][n.evaluacion_id] = n.valor

    data_completa_alumnos = {}
    puntajes_orden_merito = []
    
    # 💥 PRECARGA MASIVA ANTI-N+1 (Actitudinales y Asistencias)
    todas_actitudinales = EvaluacionActitudinal.objects.filter(matricula__in=matriculas)
    mapa_actitudinales = {}
    for act in todas_actitudinales:
        if act.matricula_id not in mapa_actitudinales:
            mapa_actitudinales[act.matricula_id] = {}
        mapa_actitudinales[act.matricula_id][act.bimestre] = act.promedio_actitudinal

    estudiantes_ids = [m.estudiante_id for m in matriculas]
    todas_asistencias = AsistenciaEstudiante.objects.filter(estudiante_id__in=estudiantes_ids)
    mapa_asistencias = {}
    for asis in todas_asistencias:
        if asis.estudiante_id not in mapa_asistencias:
            mapa_asistencias[asis.estudiante_id] = []
        mapa_asistencias[asis.estudiante_id].append(asis)

    # 1. PROCESAMIENTO DE PROMEDIOS CUANTITATIVOS DESDE LA BASE DE DATOS
    for mat in matriculas:
        notas_alumno = mapa_notas.get(mat.id, {})
        alumno_data = {
            'areas': {}, 'talleres_cursos': {}, 'cursos_por_area': {},
            'puntajes_bimestre': {'I': 0, 'II': 0, 'III': 0, 'IV': 0},
            'promedios_bimestre': {'I': 0, 'II': 0, 'III': 0, 'IV': 0},
            'count_elements_bimestre': {'I': 0, 'II': 0, 'III': 0, 'IV': 0}
        }

        for asig in asignaciones:
            area_key = asig.curso.area
            curso_nombre = asig.curso.nombre
            
            if area_key != 'TALLERES':
                if area_key not in alumno_data['areas']: alumno_data['areas'][area_key] = {'I': [], 'II': [], 'III': [], 'IV': []}
                if area_key not in alumno_data['cursos_por_area']: alumno_data['cursos_por_area'][area_key] = []
                curso_info = {'nombre': curso_nombre, 'notas': {}}
            else:
                alumno_data['talleres_cursos'][curso_nombre] = {}
            
            evals_curso = evaluaciones_por_asignacion.get(asig.id, [])
            
            for idx_b, bim in enumerate(BIMESTRES_ORDEN):
                if idx_b <= idx_sistema: # Solo computamos si el bimestre ya pasó o está activo
                    evals_bim = [e for e in evals_curso if e.bimestre == bim]
                    cuadernos = [notas_alumno.get(e.id) for e in evals_bim if e.tipo == 'CUADERNO' and notas_alumno.get(e.id) is not None]
                    desafios = [notas_alumno.get(e.id) for e in evals_bim if e.tipo == 'DESAFIO' and notas_alumno.get(e.id) is not None]
                    examenes = [notas_alumno.get(e.id) for e in evals_bim if e.tipo in ['MENSUAL', 'BIMESTRAL', 'SIMULACRO'] and notas_alumno.get(e.id) is not None]
                    
                    validos = [p for p in [
                        sum(cuadernos)/len(cuadernos) if cuadernos else 0,
                        sum(desafios)/len(desafios) if desafios else 0,
                        sum(examenes)/len(examenes) if examenes else 0
                    ] if p > 0]
                    
                    prom_bim_curso = redondear(sum(validos) / len(validos)) if validos else 0
                    
                    if area_key != 'TALLERES':
                        curso_info['notas'][bim] = prom_bim_curso
                        if prom_bim_curso > 0: alumno_data['areas'][area_key][bim].append(prom_bim_curso)
                    else:
                        alumno_data['talleres_cursos'][curso_nombre][bim] = prom_bim_curso
                        if prom_bim_curso > 0:
                            alumno_data['puntajes_bimestre'][bim] += prom_bim_curso
                            alumno_data['count_elements_bimestre'][bim] += 1

            if area_key != 'TALLERES': alumno_data['cursos_por_area'][area_key].append(curso_info)

        # Promediar las Áreas Académicas
        for area, bims in alumno_data['areas'].items():
            alumno_data['areas'][area]['finales'] = {}
            for idx_b, bim in enumerate(BIMESTRES_ORDEN):
                if idx_b <= idx_sistema:
                    lista_notas = bims[bim]
                    prom_area_bim = redondear(sum(lista_notas) / len(lista_notas)) if lista_notas else 0
                    alumno_data['areas'][area]['finales'][bim] = prom_area_bim
                    if prom_area_bim > 0:
                        alumno_data['puntajes_bimestre'][bim] += prom_area_bim
                        alumno_data['count_elements_bimestre'][bim] += 1

        for idx_b, bim in enumerate(BIMESTRES_ORDEN):
            if idx_b <= idx_sistema:
                cnt = alumno_data['count_elements_bimestre'][bim]
                pts = alumno_data['puntajes_bimestre'][bim]
                alumno_data['promedios_bimestre'][bim] = redondear(pts / cnt) if cnt > 0 else 0

        data_completa_alumnos[mat.estudiante.dni] = alumno_data
        puntajes_orden_merito.append(alumno_data['puntajes_bimestre'][bimestre_sistema])

    # Orden de Mérito General del Salón
    puntajes_orden_merito = sorted(list(set(puntajes_orden_merito)), reverse=True)
    for dni in data_completa_alumnos:
        val_pt = data_completa_alumnos[dni]['puntajes_bimestre'][bimestre_sistema]
        data_completa_alumnos[dni]['orden_merito'] = puntajes_orden_merito.index(val_pt) + 1 if val_pt > 0 else "-"

    # ==========================================
    # 2. CONSTRUCCIÓN DEL LIBRO EXCEL ÚNICO
    # ==========================================
    ruta_plantilla = os.path.join(settings.BASE_DIR, 'templates_archivos', 'plantilla_libreta.xlsx')
    ruta_logo = os.path.join(settings.BASE_DIR, 'static', 'assets', 'img', 'logo_colegio_libreta.jpg')
    ruta_logo_titulo = os.path.join(settings.BASE_DIR, 'static', 'assets', 'img', 'titulo_libreta_2026.png')
    columnas_notas = {'I': 'F', 'II': 'H', 'III': 'J', 'IV': 'L'}
    
    # Cargamos el libro base de la plantilla
    wb = openpyxl.load_workbook(ruta_plantilla)
    hoja_molde = wb.active 

    # Escaneo dinámico de filas basado en la Columna D para evitar desalineaciones
    mapa_filas = {}
    for r in range(1, 150):
        val_d = hoja_molde.cell(row=r, column=4).value
        if val_d: mapa_filas[str(val_d).strip().lower()] = r

    # Iteramos y creamos las pestañas por cada alumno dentro del mismo archivo
    for idx, mat in enumerate(matriculas, 1):
        alumno = data_completa_alumnos[mat.estudiante.dni]
        
        # Clonamos la pestaña molde limpia
        ws = wb.copy_worksheet(hoja_molde)
        # El nombre de la pestaña debe ser único y menor a 31 caracteres
        ws.title = f"{idx:02d}.- {mat.estudiante.apellidos[:18]}"
        
        # Forzar que la hoja clonada mantenga la visualización limpia sin líneas grises secundarias
        ws.views.sheetView[0].showGridLines = False

        # Inyección de metadatos básicos del alumno
        ws["C4"] = f"{mat.estudiante.apellidos}, {mat.estudiante.nombres}"
        ws["D6"] = mat.estudiante.dni
        ws["J6"] = f"{aula.grado} '{aula.seccion}'"
        ws["M6"] = aula.get_nivel_display()
        
        # Título institucional dinámico en tus celdas combinadas D2:N3
        # ws["D2"] = f"REPORTE BIMESTRAL DE NOTAS - {periodo_actual.anio}"

        # INYECCIÓN TABLA 1: ÁREAS GENERALES
        for area_code, promedios in alumno['areas'].items():
            nombre_area = dict(Curso.AREAS_ACADEMICAS).get(area_code, area_code)
            fila_excel = mapa_filas.get(nombre_area.strip().lower())
            if fila_excel:
                for idx_b, (bim, col) in enumerate(columnas_notas.items()):
                    if idx_b <= idx_sistema:
                        nota_b = promedios['finales'].get(bim, 0)
                        if nota_b > 0: ws[f"{col}{fila_excel}"] = nota_b
                    else:
                        ws[f"{col}{fila_excel}"] = "-"

        # INYECCIÓN TABLA 2: TALLERES INDEPENDIENTES
        for taller_nombre, promedios in alumno['talleres_cursos'].items():
            fila_excel = mapa_filas.get(taller_nombre.strip().lower())
            if fila_excel:
                for idx_b, (bim, col) in enumerate(columnas_notas.items()):
                    if idx_b <= idx_sistema:
                        nota_b = promedios.get(bim, 0)
                        if nota_b > 0: ws[f"{col}{fila_excel}"] = nota_b
                    else:
                        ws[f"{col}{fila_excel}"] = "-"

        # INYECCIÓN RESUMEN (Puntaje, Promedio y Orden de Mérito) con Guiones a Futuro
        for concepto in ["puntaje", "promedio", "orden de mérito"]:
            fila_excel = mapa_filas.get(concepto)
            if fila_excel:
                for idx_b, (bim, col) in enumerate(columnas_notas.items()):
                    if idx_b > idx_sistema or alumno['count_elements_bimestre'][bim] == 0:
                        ws[f"{col}{fila_excel}"] = "-"
                    else:
                        if concepto == "puntaje": ws[f"{col}{fila_excel}"] = alumno['puntajes_bimestre'][bim]
                        elif concepto == "promedio": ws[f"{col}{fila_excel}"] = alumno['promedios_bimestre'][bim]
                        elif concepto == "orden de mérito": ws[f"{col}{fila_excel}"] = f"{alumno['orden_merito']}º"

        # INYECCIÓN TABLA 3: ASPECTOS ESPECÍFICOS (Sub-Cursos)
        for area_code, cursos_list in alumno['cursos_por_area'].items():
            for curso_data in cursos_list:
                fila_excel = mapa_filas.get(curso_data['nombre'].strip().lower())
                if fila_excel:
                    for idx_b, (bim, col) in enumerate(columnas_notas.items()):
                        if idx_b <= idx_sistema:
                            nota_c = curso_data['notas'].get(bim, 0)
                            if nota_c > 0: ws[f"{col}{fila_excel}"] = nota_c
                        else:
                            ws[f"{col}{fila_excel}"] = "-"

        # 💥 COMPORTAMIENTO REAL DESDE EL MAPA PRECARGADO (Fila 54)
        fila_comportamiento = 54
        act_dict = mapa_actitudinales.get(mat.id, {})
        for idx_b, (bim, col) in enumerate(columnas_notas.items()):
            if idx_b > idx_sistema:
                ws[f"{col}{fila_comportamiento}"] = "-"
            else:
                nota_act = act_dict.get(bim)
                ws[f"{col}{fila_comportamiento}"] = redondear(nota_act) if nota_act else "-"

        # 💥 ASISTENCIAS REALES DESDE EL MAPA PRECARGADO (Filas 56 a 59)
        filas_asis = {'P': 56, 'J': 57, 'F': 58, 'T': 59}
        asistencias_alumno = mapa_asistencias.get(mat.estudiante_id, [])
        conteo_asistencia = {b: {'P': 0, 'J': 0, 'F': 0, 'T': 0} for b in ['I', 'II', 'III', 'IV']}
        
        for asis in asistencias_alumno:
            b_key = clasificar_bimestre_asistencia(asis.fecha, bimestre_sistema)
            if asis.estado in ['P', 'J', 'F', 'T']:
                conteo_asistencia[b_key][asis.estado] += 1

        for idx_b, (bim, col) in enumerate(columnas_notas.items()):
            if idx_b > idx_sistema:
                for f in filas_asis.values(): ws[f"{col}{f}"] = "-"
            else:
                ws[f"{col}{filas_asis['P']}"] = conteo_asistencia[bim]['P']
                ws[f"{col}{filas_asis['J']}"] = conteo_asistencia[bim]['J']
                ws[f"{col}{filas_asis['F']}"] = conteo_asistencia[bim]['F']
                ws[f"{col}{filas_asis['T']}"] = conteo_asistencia[bim]['T']

        # 💥 RECOMENDACIONES FIJADAS EN CELDAS EXACTAS (D63 a D69)
        ws["D63"] = obtener_recomendacion(alumno['promedios_bimestre']['I']) if idx_sistema >= 0 and alumno['count_elements_bimestre']['I'] > 0 else "-"
        ws["D65"] = obtener_recomendacion(alumno['promedios_bimestre']['II']) if idx_sistema >= 1 and alumno['count_elements_bimestre']['II'] > 0 else "-"
        ws["D67"] = obtener_recomendacion(alumno['promedios_bimestre']['III']) if idx_sistema >= 2 and alumno['count_elements_bimestre']['III'] > 0 else "-"
        ws["D69"] = obtener_recomendacion(alumno['promedios_bimestre']['IV']) if idx_sistema >= 3 and alumno['count_elements_bimestre']['IV'] > 0 else "-"

        # 💥 INYECCIÓN DINÁMICA DEL LOGO SOBRE CADA HOJA CLONADA
        if os.path.exists(ruta_logo):
            img_logo = OpenpyxlImage(ruta_logo)
            img_logo.width = 194   # Ancho optimizado en píxeles para tu celda C2
            img_logo.height = 140  # Alto optimizado en píxeles para tu celda C2
            ws.add_image(img_logo, 'C2')
        
        if os.path.exists(ruta_logo_titulo):
            img_logo_titulo = OpenpyxlImage(ruta_logo_titulo)
            img_logo_titulo.width = 630   # Ancho optimizado en píxeles
            img_logo_titulo.height = 74   # Alto optimizado en píxeles

            # --- INICIO DE CONFIGURACIÓN MILIMÉTRICA ---
            
            # 1. ¿Cuántos píxeles quieres mover la imagen respecto a la esquina de la celda D2?
            desplazar_derecha = 190  # Aumenta para mover a la derecha, usa negativos para la izquierda
            desplazar_abajo = 30    # Aumenta para mover hacia abajo, usa negativos para arriba
            
            # 2. Excel usa índices base 0. La celda 'D2' es: 
            #    Columna D = 3 (A=0, B=1, C=2, D=3)
            #    Fila 2 = 1 (Fila 1=0, Fila 2=1)
            marcador = AnchorMarker(
                col=3, 
                colOff=pixels_to_EMU(desplazar_derecha), 
                row=1, 
                rowOff=pixels_to_EMU(desplazar_abajo)
            )
            
            # 3. Convertimos el ancho y alto de la imagen a EMUs
            tamano = XDRPositiveSize2D(
                pixels_to_EMU(img_logo_titulo.width), 
                pixels_to_EMU(img_logo_titulo.height)
            )
            
            # 4. Ensamblamos el ancla y se la inyectamos a la imagen
            img_logo_titulo.anchor = OneCellAnchor(_from=marcador, ext=tamano)
            
            # 5. La agregamos a la hoja de trabajo 
            # (¡OJO! Ya no le pasamos 'D2' aquí porque el ancla ya tiene las coordenadas exactas)
            ws.add_image(img_logo_titulo)

    # 3. ELIMINAMOS LA PESTAÑA MOLDE EN BLANCO ORIGINAL
    if len(wb.sheetnames) > 1:
        wb.remove(hoja_molde)

    # 4. ENTREGA DEL LIBRO ÚNICO MULTI-PESTAÑA LISTO PARA IMPRIMIR
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Libretas_Completas_{aula.grado}_{aula.seccion}.xlsx'
    wb.save(response)
    return response