from decimal import Decimal, ROUND_HALF_UP
from apps.academico.models import AsignacionAcademica, Curso, Evaluacion, EvaluacionActitudinal, Matricula, Nota
from apps.asistencia.models import AsistenciaEstudiante

def calcular_matriz_vigesimal(asignacion, aula, bimestre):
    """
    Motor central que calcula promedios y agrupa notas.
    Retorna un diccionario con todas las variables necesarias para el HTML o Excel.
    """
    if not asignacion:
        return {'datos_matriz': [], 'evals_mensual_lc': [], 'evals_bimestral_lc': [], 'evals_desafio': [], 'eval_mensual': None, 'eval_bimestral': None, 'evals_simulacro': []}

    evaluaciones = asignacion.evaluaciones.filter(bimestre=bimestre).order_by('fecha', 'id')
    
    evals_mensual_lc = evaluaciones.filter(tipo__in=['CUADERNO', 'LIBRO'], nombre__icontains='Mensual')
    evals_bimestral_lc = evaluaciones.filter(tipo__in=['CUADERNO', 'LIBRO'], nombre__icontains='Bimestral')
    evals_desafio = evaluaciones.filter(tipo='DESAFIO')
    eval_mensual = evaluaciones.filter(tipo='MENSUAL').first()
    eval_bimestral = evaluaciones.filter(tipo='BIMESTRAL').first()
    evals_simulacro = evaluaciones.filter(tipo='SIMULACRO')

    matriculas = Matricula.objects.filter(aula=aula, estudiante__estado='Activo').order_by('estudiante__apellidos')
    notas_db = Nota.objects.filter(evaluacion__in=evaluaciones).select_related('matricula', 'evaluacion')

    diccionario_notas = {}
    for n in notas_db:
        if n.matricula_id not in diccionario_notas:
            diccionario_notas[n.matricula_id] = {}
        diccionario_notas[n.matricula_id][n.evaluacion_id] = int(Decimal(str(n.valor)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)) if n.valor is not None else None

    datos_matriz = []
    for mat in matriculas:
        notas_alumno = diccionario_notas.get(mat.id, {})

        def calcular_promedio(grupo_evaluaciones):
            valores = [notas_alumno[e.id] for e in grupo_evaluaciones if e.id in notas_alumno and notas_alumno[e.id] is not None]
            if not valores: return 0
            promedio_raw = sum(valores) / len(valores)
            return int(Decimal(str(promedio_raw)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

        prom_mensual_lc = calcular_promedio(evals_mensual_lc)
        prom_bimestral_lc = calcular_promedio(evals_bimestral_lc)
        prom_desafio = calcular_promedio(evals_desafio)
        prom_simulacro = calcular_promedio(evals_simulacro)
        
        # Obtenemos la nota de forma segura, respetando si es None (vacío)
        nota_mensual = notas_alumno.get(eval_mensual.id) if eval_mensual else None
        nota_bimestral = notas_alumno.get(eval_bimestral.id) if eval_bimestral else None

        componentes = [prom_mensual_lc, prom_bimestral_lc, prom_desafio, nota_mensual, nota_bimestral, prom_simulacro]
        
        # 💥 LA SOLUCIÓN: Exigimos que "p" no sea None antes de verificar si es mayor a 0
        sumatoria_validos = [p for p in componentes if p is not None and p > 0]
        prom_general = int(Decimal(str(sum(sumatoria_validos) / len(sumatoria_validos))).quantize(Decimal('1'), rounding=ROUND_HALF_UP)) if sumatoria_validos else 0

        datos_matriz.append({
            'matricula_id': mat.id,
            'estudiante': f"{mat.estudiante.apellidos}, {mat.estudiante.nombres}",
            'notas': notas_alumno,
            'prom_mensual_lc': prom_mensual_lc,
            'prom_bimestral_lc': prom_bimestral_lc,
            'prom_desafio': prom_desafio,
            'nota_mensual': nota_mensual,
            'nota_bimestral': nota_bimestral,
            'prom_simulacro': prom_simulacro,
            'prom_general': prom_general
        })

    # Devolvemos todo empaquetado
    return {
        'evals_mensual_lc': evals_mensual_lc,
        'evals_bimestral_lc': evals_bimestral_lc,
        'evals_desafio': evals_desafio,
        'eval_mensual': eval_mensual,
        'eval_bimestral': eval_bimestral,
        'evals_simulacro': evals_simulacro,
        'datos_matriz': datos_matriz,
    }
    
def get_configuracion_libreta(aula):
    """ Retorna el diccionario de configuración exacto según el Nivel y Grado del aula """
    nivel = aula.nivel
    grado = aula.grado

    if nivel == 'Inicial':
        return {
            'ruta_plantilla': 'plantilla_libreta_inicial.xlsx',
            'suman_al_puntaje': [
                'MATEMÁTICA', 'COMUNICACIÓN', 'CIENCIA Y TECNOLOGÍA', 'PERSONAL SOCIAL', 'PSICOMOTRIZ (ED. FÍSICA)', 'ARTE', 'RELIGIÓN', 'INGLÉS', 'DESARROLLO EMOCIONAL', 'HERRAMIENTAS INFORMÁTICAS', 'DANZA'
            ],
            'filas': {
                'ÁREA_CIENCIA Y TECNOLOGÍA': 11, 'ÁREA_COMUNICACIÓN': 12, 'ÁREA_MATEMÁTICA': 13, 
                'ÁREA_PERSONAL SOCIAL': 14, 'ÁREA_PSICOMOTRIZ (ED. FÍSICA)': 15,
                'ARTE': 18, 'RELIGIÓN': 19, 'INGLÉS': 20, 'HERRAMIENTAS INFORMÁTICAS': 21,
                'LÓGICO MATEMÁTICO': 31, 'RAZONAMIENTO MATEMÁTICO': 32, 'GRAFOESCRITURA': 35, 
                'COMPRENSIÓN LECTORA': 36, 'COMUNICACIÓN INTEGRAL': 37, 'RAZONAMIENTO VERBAL': 38,
                'ACTITUDINAL': 50, 
                'ASISTENCIA_TOTAL': 52, 'ASISTENCIA_J': 53, 'ASISTENCIA_F': 54, 'ASISTENCIA_T': 55,
                'PUNTAJE': 24, 'PROMEDIO': 25, 'ORDEN_MERITO': 26,
                'OBS_I': 59, 'OBS_II': 61, 'OBS_III': 63, 'OBS_IV': 65  # 💥 Filas de Recomendaciones
            }
        }
    elif nivel == 'Secundaria':
        return {
            'ruta_plantilla': 'plantilla_libreta_secundaria.xlsx',
            'suman_al_puntaje': [
                'ARTE, CULTURA Y DANZA', 'CIENCIA Y TECNOLOGÍA', 'CIENCIAS SOCIALES', 'COMUNICACIÓN',
                'DESARROLLO PERSONAL, CIUDADANÍA Y CÍVICA - ORATORIA', 'EDUCACIÓN FÍSICA', 
                'EDUCACIÓN PARA EL TRABAJO - COMPUTACIÓN', 'EDUCACIÓN RELIGIOSA - PSICOLOGÍA', 'INGLÉS', 'MATEMÁTICA'
            ],
            'filas': {
                'ÁREA_ARTE, CULTURA Y DANZA': 11, 'ÁREA_CIENCIA Y TECNOLOGÍA': 12, 'ÁREA_CIENCIAS SOCIALES': 13, 
                'ÁREA_COMUNICACIÓN': 14, 'ÁREA_DESARROLLO PERSONAL, CIUDADANÍA Y CÍVICA - ORATORIA': 15, 
                'ÁREA_EDUCACIÓN FÍSICA': 16, 'ÁREA_EDUCACIÓN PARA EL TRABAJO - COMPUTACIÓN': 17, 
                'ÁREA_EDUCACIÓN RELIGIOSA - PSICOLOGÍA': 18, 'ÁREA_INGLÉS': 19, 'ÁREA_MATEMÁTICA': 20,
                'ARITMÉTICA': 29, 'ÁLGEBRA': 30, 'GEOMETRÍA': 31, 'TRIGONOMETRÍA': 32, 'RAZONAMIENTO MATEMÁTICO': 33,
                'RAZONAMIENTO VERBAL': 36, 'LENGUAJE': 37,
                'HISTORIA': 40, 'ECONOMÍA Y FINANZAS': 41, 'GESTIÓN EMPRESARIAL Y CONTABILIDAD': 42,
                'GEOGRAFÍA': 45, 'BIOLOGÍA': 46, 'QUÍMICA': 47, 'FÍSICA ELEMENTAL': 48,
                'ACTITUDINAL': 60, 
                'ASISTENCIA_TOTAL': 63, 'ASISTENCIA_J': 64, 'ASISTENCIA_F': 65, 'ASISTENCIA_T': 66,
                'PUNTAJE': 22, 'PROMEDIO': 23, 'ORDEN_MERITO': 24,
                'OBS_I': 70, 'OBS_II': 72, 'OBS_III': 74, 'OBS_IV': 76
            }
        }
    else:
        # Primaria
        if grado == '1er Grado':
            return {
                'ruta_plantilla': 'plantilla_libreta_primaria_1ro.xlsx', 
                'suman_al_puntaje': ['MATEMÁTICA', 'COMUNICACIÓN', 'CIENCIA Y TECNOLOGÍA', 'PERSONAL SOCIAL', 'EDUCACIÓN FÍSICA', 'ARTE', 'RELIGIÓN', 'INGLÉS', 'DESARROLLO EMOCIONAL', 'VIDEOCULTURA', 'HERRAMIENTAS INFORMÁTICAS', 'DANZA'],
                'filas': {
                    'ÁREA_CIENCIA Y TECNOLOGÍA': 11, 'ÁREA_COMUNICACIÓN': 12, 'ÁREA_MATEMÁTICA': 13, 'ÁREA_PERSONAL SOCIAL': 14, 'EDUCACIÓN FÍSICA': 15, 'ARTE': 16, 'RELIGIÓN': 17, 'INGLÉS': 18, 'HERRAMIENTAS INFORMÁTICAS': 21, 'DESARROLLO EMOCIONAL': 22, 'DANZA': 24, 
                    'ARITMÉTICA': 33, 'ÁLGEBRA': 34, 'GEOMETRÍA': 35, 'RAZONAMIENTO MATEMÁTICO': 36, 'GRAMÁTICA': 39, 'COMPRENSIÓN LECTORA': 40, 'PERCENTIL ORTOGRÁFICO': 41, 'RAZONAMIENTO VERBAL': 42, 'PERSONAL SOCIAL': 45, 'CIENCIA Y TECNOLOGÍA': 50,  
                    'ACTITUDINAL': 54, 'ASISTENCIA_TOTAL': 56, 'ASISTENCIA_J': 57, 'ASISTENCIA_F': 58, 'ASISTENCIA_T': 59,
                    'PUNTAJE': 26, 'PROMEDIO': 27, 'ORDEN_MERITO': 28, 'OBS_I': 63, 'OBS_II': 65, 'OBS_III': 67, 'OBS_IV': 69
                }
            }
        elif grado == '2do Grado':
            return {
                'ruta_plantilla': 'plantilla_libreta_primaria_2do.xlsx', 
                'suman_al_puntaje': ['MATEMÁTICA', 'COMUNICACIÓN', 'CIENCIA Y TECNOLOGÍA', 'PERSONAL SOCIAL', 'EDUCACIÓN FÍSICA', 'ARTE', 'RELIGIÓN', 'INGLÉS', 'DESARROLLO EMOCIONAL', 'VIDEOCULTURA', 'HERRAMIENTAS INFORMÁTICAS', 'DANZA'],
                'filas': {
                    'ÁREA_CIENCIA Y TECNOLOGÍA': 11, 'ÁREA_COMUNICACIÓN': 12, 'ÁREA_MATEMÁTICA': 13, 'ÁREA_PERSONAL SOCIAL': 14, 'EDUCACIÓN FÍSICA': 15, 'ARTE': 16, 'RELIGIÓN': 17, 'INGLÉS': 18, 'HERRAMIENTAS INFORMÁTICAS': 21, 'DESARROLLO EMOCIONAL': 22, 'VIDEOCULTURA': 23, 'DANZA': 24, 
                    'ARITMÉTICA': 33, 'ÁLGEBRA': 34, 'GEOMETRÍA': 35, 'RAZONAMIENTO MATEMÁTICO': 36, 'GRAMÁTICA': 39, 'COMPRENSIÓN LECTORA': 40, 'PERCENTIL ORTOGRÁFICO': 41, 'RAZONAMIENTO VERBAL': 42, 'PERSONAL SOCIAL': 45, 'CIENCIA Y TECNOLOGÍA': 50,  
                    'ACTITUDINAL': 54, 'ASISTENCIA_TOTAL': 56, 'ASISTENCIA_J': 57, 'ASISTENCIA_F': 58, 'ASISTENCIA_T': 59,
                    'PUNTAJE': 26, 'PROMEDIO': 27, 'ORDEN_MERITO': 28, 'OBS_I': 63, 'OBS_II': 65, 'OBS_III': 67, 'OBS_IV': 69
                }
            }
        elif grado == '6to Grado':
            return {
                'ruta_plantilla': 'plantilla_libreta_primaria_6to.xlsx',
                'suman_al_puntaje': ['MATEMÁTICA', 'COMUNICACIÓN', 'CIENCIA Y TECNOLOGÍA', 'PERSONAL SOCIAL', 'EDUCACIÓN FÍSICA', 'ARTE', 'RELIGIÓN', 'INGLÉS', 'DESARROLLO EMOCIONAL', 'ORATORIA', 'HERRAMIENTAS INFORMÁTICAS', 'DANZA'],
                'filas': {
                    'ÁREA_CIENCIA Y TECNOLOGÍA': 11, 'ÁREA_COMUNICACIÓN': 12, 'ÁREA_MATEMÁTICA': 13, 'ÁREA_PERSONAL SOCIAL': 14, 'EDUCACIÓN FÍSICA': 15, 'ARTE': 16, 'RELIGIÓN': 17, 'INGLÉS': 18, 'HERRAMIENTAS INFORMÁTICAS': 21, 'DESARROLLO EMOCIONAL': 22, 'ORATORIA': 23, 'DANZA': 24, 
                    'ARITMÉTICA': 33, 'ÁLGEBRA': 34, 'GEOMETRÍA': 35, 'RAZONAMIENTO MATEMÁTICO': 36, 'GRAMÁTICA': 39, 'COMPRENSIÓN LECTORA': 40, 'PERCENTIL ORTOGRÁFICO': 41, 'RAZONAMIENTO VERBAL': 42, 'HISTORIA': 45, 'GEOGRAFÍA': 46, 'GESTIÓN EMPRESARIAL': 47, 'BIOLOGÍA': 50, 'FÍSICA ELEMENTAL': 51,
                    'ACTITUDINAL': 54, 'ASISTENCIA_TOTAL': 56, 'ASISTENCIA_J': 57, 'ASISTENCIA_F': 58, 'ASISTENCIA_T': 59,
                    'PUNTAJE': 26, 'PROMEDIO': 27, 'ORDEN_MERITO': 28, 'OBS_I': 63, 'OBS_II': 65, 'OBS_III': 67, 'OBS_IV': 69
                }
            }
        else:
            return {
                'ruta_plantilla': 'plantilla_libreta_primaria_poli.xlsx',
                'suman_al_puntaje': ['MATEMÁTICA', 'COMUNICACIÓN', 'CIENCIA Y TECNOLOGÍA', 'PERSONAL SOCIAL', 'EDUCACIÓN FÍSICA', 'ARTE', 'RELIGIÓN', 'INGLÉS', 'DESARROLLO EMOCIONAL', 'ORATORIA', 'HERRAMIENTAS INFORMÁTICAS', 'DANZA'],
                'filas': {
                    'ÁREA_CIENCIA Y TECNOLOGÍA': 11, 'ÁREA_COMUNICACIÓN': 12, 'ÁREA_MATEMÁTICA': 13, 'ÁREA_PERSONAL SOCIAL': 14, 'EDUCACIÓN FÍSICA': 15, 'ARTE': 16, 'RELIGIÓN': 17, 'INGLÉS': 18, 'HERRAMIENTAS INFORMÁTICAS': 21, 'DESARROLLO EMOCIONAL': 22, 'ORATORIA': 23, 'DANZA': 24, 
                    'ARITMÉTICA': 33, 'ÁLGEBRA': 34, 'GEOMETRÍA': 35, 'RAZONAMIENTO MATEMÁTICO': 36, 'GRAMÁTICA': 39, 'COMPRENSIÓN LECTORA': 40, 'PERCENTIL ORTOGRÁFICO': 41, 'RAZONAMIENTO VERBAL': 42, 'HISTORIA': 45, 'GEOGRAFÍA': 46, 'GESTIÓN EMPRESARIAL': 47, 'BIOLOGÍA': 50,
                    'ACTITUDINAL': 54, 'ASISTENCIA_TOTAL': 56, 'ASISTENCIA_J': 57, 'ASISTENCIA_F': 58, 'ASISTENCIA_T': 59,
                    'PUNTAJE': 26, 'PROMEDIO': 27, 'ORDEN_MERITO': 28, 'OBS_I': 63, 'OBS_II': 65, 'OBS_III': 67, 'OBS_IV': 69
                }
            }
            
            
def obtener_consolidado_aula_maestro(aula, periodo_actual):
    """
    Motor Centralizado en Memoria. Procesa un aula entera y retorna:
    - data_alumnos: Diccionario con todas las notas, puntajes, jerarquías y asistencias.
    - config: El diccionario de enrutamiento de Excel asociado.
    """
    config = get_configuracion_libreta(aula)
    lista_suman = [c.upper() for c in config['suman_al_puntaje']]
    bimestres_orden = ['I', 'II', 'III', 'IV']
    
    matriculas = list(Matricula.objects.filter(aula=aula, periodo=periodo_actual, estudiante__estado='Activo').select_related('estudiante').order_by('estudiante__apellidos'))
    asignaciones = list(AsignacionAcademica.objects.filter(aula=aula, periodo=periodo_actual).select_related('curso'))
    evaluaciones_totales = list(Evaluacion.objects.filter(asignacion__in=asignaciones))
    notas_db = Nota.objects.filter(evaluacion__in=evaluaciones_totales, matricula__in=matriculas)
    
    mapa_notas = {}
    for n in notas_db:
        if n.matricula_id not in mapa_notas: mapa_notas[n.matricula_id] = {}
        mapa_notas[n.matricula_id][n.evaluacion_id] = n.valor

    def redondear_vigesimal(valor):
        if valor is None: return None
        return int(Decimal(str(valor)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

    # 1. Base de datos del alumno
    data_alumnos = {}
    for m in matriculas:
        data_alumnos[m.id] = {
            'matricula': m,
            'areas': {},
            'talleres_cursos': {},
            'cursos_por_area': {},
            'puntajes_bimestre': {b: 0 for b in bimestres_orden},
            'promedios_bimestre': {b: 0 for b in bimestres_orden},
            'count_elements_bimestre': {b: 0 for b in bimestres_orden},
            'orden_merito': {b: "-" for b in bimestres_orden},
            'comportamiento': {b: None for b in bimestres_orden},
            'asistencias': {b: {'P': 0, 'J': 0, 'F': 0, 'T': 0} for b in bimestres_orden}
        }

    # 2. Asignación de Comportamiento y Asistencias
    actitudinales = EvaluacionActitudinal.objects.filter(matricula__in=matriculas)
    for act in actitudinales:
        if act.matricula_id in data_alumnos:
            data_alumnos[act.matricula_id]['comportamiento'][act.bimestre] = redondear_vigesimal(act.promedio_actitudinal)
            
    asistencias = AsistenciaEstudiante.objects.filter(estudiante_id__in=[m.estudiante_id for m in matriculas])
    mapa_mat_por_est = {m.estudiante_id: m.id for m in matriculas}
    for asis in asistencias:
        if asis.bimestre in bimestres_orden and asis.estado in ['P', 'J', 'F', 'T']:
            m_id = mapa_mat_por_est.get(asis.estudiante_id)
            if m_id:
                data_alumnos[m_id]['asistencias'][asis.bimestre][asis.estado] += 1

    # 3. Procesamiento Cuantitativo por Curso y Bimestre
    for asig in asignaciones:
        area_key = asig.curso.area
        area_nombre = dict(Curso.AREAS_ACADEMICAS).get(area_key, area_key).upper()
        curso_nombre = asig.curso.nombre.upper()

        for mat_id, data in data_alumnos.items():
            if area_key != 'TALLERES':
                if area_key not in data['areas']:
                    data['areas'][area_key] = {'nombre_display': area_nombre, 'finales': {}}
                    data['cursos_por_area'][area_key] = []
                # Inicializamos la memoria temporal para promediar el área luego
                if 'temp_notas' not in data['areas'][area_key]:
                    data['areas'][area_key]['temp_notas'] = {b: [] for b in bimestres_orden}
            else:
                if curso_nombre not in data['talleres_cursos']:
                    data['talleres_cursos'][curso_nombre] = {b: 0 for b in bimestres_orden}

        evals_asig = [e for e in evaluaciones_totales if e.asignacion_id == asig.id]
        
        for bim in bimestres_orden:
            evals_bim = [e for e in evals_asig if e.bimestre == bim]
            evals_mensual_lc = [e for e in evals_bim if e.tipo in ['CUADERNO', 'LIBRO'] and 'mensual' in e.nombre.lower()]
            evals_bimestral_lc = [e for e in evals_bim if e.tipo in ['CUADERNO', 'LIBRO'] and 'bimestral' in e.nombre.lower()]
            evals_desafio = [e for e in evals_bim if e.tipo == 'DESAFIO']
            evals_simulacro = [e for e in evals_bim if e.tipo == 'SIMULACRO']
            eval_mensual = next((e for e in evals_bim if e.tipo == 'MENSUAL'), None)
            eval_bimestral = next((e for e in evals_bim if e.tipo == 'BIMESTRAL'), None)

            for mat in matriculas:
                notas_alumno = mapa_notas.get(mat.id, {})
                
                def calc_prom(grupo):
                    valores = [redondear_vigesimal(notas_alumno[e.id]) for e in grupo if e.id in notas_alumno and notas_alumno[e.id] is not None]
                    return redondear_vigesimal(sum(valores) / len(valores)) if valores else None
                    
                componentes = [
                    calc_prom(evals_mensual_lc), calc_prom(evals_bimestral_lc), calc_prom(evals_desafio), calc_prom(evals_simulacro),
                    redondear_vigesimal(notas_alumno.get(eval_mensual.id) if eval_mensual else None),
                    redondear_vigesimal(notas_alumno.get(eval_bimestral.id) if eval_bimestral else None)
                ]
                sumatoria_validos = [p for p in componentes if p is not None and p > 0]
                prom_general = redondear_vigesimal(sum(sumatoria_validos) / len(sumatoria_validos)) if sumatoria_validos else 0
                
                # Inyección en la estructura
                if area_key != 'TALLERES':
                    # Agregamos a la lista de cursos del alumno
                    curso_info = next((c for c in data_alumnos[mat.id]['cursos_por_area'][area_key] if c['nombre'] == curso_nombre), None)
                    if not curso_info:
                        curso_info = {'nombre': curso_nombre, 'notas': {}}
                        data_alumnos[mat.id]['cursos_por_area'][area_key].append(curso_info)
                    curso_info['notas'][bim] = prom_general
                    
                    if prom_general > 0:
                        data_alumnos[mat.id]['areas'][area_key]['temp_notas'][bim].append(prom_general)
                else:
                    data_alumnos[mat.id]['talleres_cursos'][curso_nombre][bim] = prom_general

    # 4. Consolidación Exacta: Promedios de Área, Puntaje y Promedio Bimestral
    for mat_id, data in data_alumnos.items():
        for bim in bimestres_orden:
            puntaje_bimestre = 0
            cnt = 0
            
            # Promediamos las Áreas Académicas
            for area_key, data_area in data['areas'].items():
                lista_notas = data_area['temp_notas'][bim]
                es_area_puntuable = (data_area['nombre_display'] in lista_suman or area_key.upper() in lista_suman)
                
                if lista_notas:
                    prom_area = redondear_vigesimal(sum(lista_notas) / len(lista_notas))
                    data_area['finales'][bim] = prom_area
                    if prom_area > 0 and es_area_puntuable:
                        puntaje_bimestre += prom_area
                        cnt += 1
                else:
                    data_area['finales'][bim] = 0

            # Sumamos los Talleres Independientes
            for taller_nombre, notas_bims in data['talleres_cursos'].items():
                nota = notas_bims.get(bim, 0)
                if nota > 0 and taller_nombre in lista_suman:
                    puntaje_bimestre += nota
                    cnt += 1

            # Inyectamos el resultado exacto
            if cnt > 0:
                data['puntajes_bimestre'][bim] = puntaje_bimestre
                data['count_elements_bimestre'][bim] = cnt
                data['promedios_bimestre'][bim] = redondear_vigesimal(puntaje_bimestre / cnt)

    # 5. Lógica de Orden de Mérito por Bimestre (Jerarquía Excel)
    for bim in bimestres_orden:
        todos_los_puntajes = [data['puntajes_bimestre'][bim] for data in data_alumnos.values()]
        for mat_id, data in data_alumnos.items():
            val_pt = data['puntajes_bimestre'][bim]
            if val_pt > 0:
                data['orden_merito'][bim] = sum(1 for p in todos_los_puntajes if p > val_pt) + 1
                
    return data_alumnos, config