from decimal import ROUND_HALF_UP, Decimal
import json
import os
from django.db.models import Count, Q, Avg
from django.http import JsonResponse
from django.utils import timezone
from google import genai
import numpy as np
from dotenv import load_dotenv
from django.shortcuts import get_object_or_404

from apps.academico.models import AsignacionAcademica, Aula, CatalogoMaterial, CierreRegistroBimestral, EntregaSimulacro, Estudiante, Evaluacion, Matricula, Nota, PeriodoLectivo, SolicitudImpresion
from apps.asistencia.models import AsistenciaEstudiante
from django.conf import settings
from django.contrib.auth.decorators import login_required

from apps.personal.models import Personal

# Carga las variables del archivo .env
load_dotenv()

# =====================================================================
# CONFIGURACIÓN GLOBAL DE LA IA
# =====================================================================
# Extraemos la llave una sola vez al iniciar el servidor
api_key_segura = os.getenv("GEMINI_API_KEY")

# Inicializamos el cliente globalmente
client = genai.Client(api_key=api_key_segura)

# Constante del modelo especificado para la tesis
MODELO_IA = 'gemini-3.5-flash-lite'

# =====================================================================
# 1. MOTOR PREDICTIVO NEURO-SIMBÓLICO (HÍBRIDO)
# =====================================================================

def analizar_rendimiento_estudiante(matricula_id, promedio_oficial, curso_id=None, bimestre_actual=None, usar_llm=True):
    from apps.academico.models import Nota # Evitar dependencias circulares

    if promedio_oficial is None or promedio_oficial == 0:
        return {
            'promedio': "-", 'proyeccion_bimestral': "-", 'proyeccion_anual': "-",
            'mostrar_proy_bimestral': False, 'tendencia_numerica': 0, 
            'estado_ia': 'Sin Datos', 'color': 'secondary', 'icono': 'horizontal_rule', 
            'alerta_critica': False, 'cantidad_notas': 0,
            'analisis_cualitativo': "Sin datos suficientes para análisis.",
            'recomendaciones': []
        }

    # 1. Extracción de datos
    notas_base = Nota.objects.filter(matricula_id=matricula_id, valor__isnull=False).select_related('evaluacion')
    if curso_id:
        notas_base = notas_base.filter(evaluacion__asignacion__curso__id=curso_id)
        
    notas_anuales = notas_base.order_by('evaluacion__fecha', 'evaluacion__id')
    notas_bimestre = notas_base.filter(evaluacion__bimestre=bimestre_actual).order_by('evaluacion__fecha', 'evaluacion__id')
    
    valores_anuales = [float(n.valor) for n in notas_anuales]
    valores_bimestre = [float(n.valor) for n in notas_bimestre]
    
    # 2. Lógica de cierre de bimestre (Apaga la proyección bimestral si ya casi termina)
    examen_final_rendido = any(n.evaluacion.tipo == 'BIMESTRAL' for n in notas_bimestre)
    volumen_casi_lleno = len(valores_bimestre) >= 11
    mostrar_proy_bimestral = not (examen_final_rendido or volumen_casi_lleno)

    # 3. Motor Matemático
    def proyectar(valores, prom_actual, factor_multiplicador):
        if len(valores) < 2: return prom_actual, 0
        x = np.arange(len(valores))
        y = np.array(valores)
        pendiente, _ = np.polyfit(x, y, 1)
        proyeccion = float(prom_actual) + (pendiente * factor_multiplicador)
        nota_limitada = max(0, min(20, proyeccion))
        nota_final = int(Decimal(str(nota_limitada)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        return nota_final, round(pendiente, 2)

    proy_bimestral, tendencia_bim = proyectar(valores_bimestre, promedio_oficial, factor_multiplicador=1.5)
    proy_anual, tendencia_anual = proyectar(valores_anuales, promedio_oficial, factor_multiplicador=3.0)

    # 4. Alerta crítica y Estados
    alerta_critica = False
    if len(valores_anuales) >= 2:
        ultima_nota = valores_anuales[-1]
        promedio_historico = sum(valores_anuales[:-1]) / len(valores_anuales[:-1])
        if ultima_nota <= (promedio_historico - 4):
            alerta_critica = True
            
    if proy_anual < 13:
        estado_ia, color, icono = "Riesgo Anual", "danger", "trending_down"
    elif alerta_critica:
        estado_ia, color, icono = "Alerta de Caída", "warning", "warning"
    elif proy_anual < 14.5:
        if tendencia_anual < -0.2:
            estado_ia, color, icono = "En Declive", "warning", "trending_down"
        elif tendencia_anual > 0.2:
            estado_ia, color, icono = "Recuperándose", "info", "trending_up"
        else:
            estado_ia, color, icono = "Estancado", "secondary", "trending_flat"
    else:
        estado_ia, color, icono = "Proyección Óptima", "success", "trending_up" if tendencia_anual > 0 else "trending_flat"

    # -------------------------------------------------------------
    # 💥 5. EL CEREBRO DE GEMINI (Se enciende SOLO si usar_llm=True)
    # -------------------------------------------------------------
    analisis_texto = "Análisis cualitativo no solicitado para esta vista rápida."
    recomendaciones_lista = []

    if usar_llm and len(valores_bimestre) >= 2:
        prompt = f"""
        Actúa como un psicopedagogo experto. Analiza el rendimiento de este estudiante en el BIMESTRE {bimestre_actual}:
        - Notas de este bimestre: {valores_bimestre}
        - Promedio actual: {promedio_oficial}
        - Proyección para fin de bimestre: {proy_bimestral}
        - Estado clasificado: {estado_ia}
        
        Genera un diagnóstico breve y sugiere acciones urgentes para que el docente intervenga en este bimestre.
        Tu respuesta debe ser estrictamente un JSON válido con esta estructura exacta:
        {{
            "analisis": "Texto breve explicando el diagnóstico pedagógico táctico",
            "recomendaciones": ["Acción 1", "Acción 2", "Acción 3"]
        }}
        No incluyas markdown, comillas triples, ni texto fuera del JSON.
        """
        
        try:
            # Asegúrate de tener 'client' o el objeto de Gemini configurado previamente en este archivo
            respuesta = client.models.generate_content(model=MODELO_IA, contents=prompt)
            texto_limpio = respuesta.text.strip().replace('```json', '').replace('```', '')
            data_ia = json.loads(texto_limpio)
            analisis_texto = data_ia.get('analisis', 'Análisis generado sin texto.')
            recomendaciones_lista = data_ia.get('recomendaciones', [])
        except Exception as e:
            analisis_texto = "El motor cognitivo experimentó un retraso. Se requiere intervención del docente basada en la tendencia numérica."
            recomendaciones_lista = ["Monitorear de cerca las próximas evaluaciones.", "Conversar directamente con el estudiante sobre su desempeño reciente."]

    return {
        'promedio': promedio_oficial,
        'proyeccion_bimestral': proy_bimestral,
        'proyeccion_anual': proy_anual,
        'mostrar_proy_bimestral': mostrar_proy_bimestral,
        'tendencia_numerica': tendencia_anual,
        'estado_ia': estado_ia,
        'color': color,
        'icono': icono,
        'alerta_critica': alerta_critica,
        'cantidad_notas': len(valores_bimestre),
        'analisis_cualitativo': analisis_texto,
        'recomendaciones': recomendaciones_lista
    }


# =====================================================================
# 2. GENERADOR DE DIAGNÓSTICOS PARA APODERADOS
# =====================================================================
def generar_diagnostico_cualitativo(nombre_alumno, promedio, tendencia, conducta, estado_ia, contexto_curso, bimestre):
    prompt = f"""
    Actúa como un psicopedagogo experto y empático de un colegio de prestigio. 
    Redacta un diagnóstico de máximo 3 párrafos cortos dirigido al apoderado del estudiante: {nombre_alumno}.
    
    El análisis corresponde al Bimestre {bimestre} y debe enfocarse {contexto_curso}.
    
    Métricas analíticas del estudiante:
    - Promedio académico actual: {promedio}/20
    - Calificación de conducta/actitud: {conducta}/20
    - Tendencia de notas: {tendencia} (Si es menor a -0.5, sus notas recientes han bajado en picada. Si es mayor a 0.5, está mejorando de forma sostenida).
    - Perfil predictivo asignado: {estado_ia}.
    
    Instrucciones de redacción:
    1. Relaciona su promedio académico con su actitud ({conducta}/20). Si la actitud es buena pero la nota baja, valora su esfuerzo; si la nota es buena pero la actitud baja, advierte sobre su disciplina.
    2. Evita usar los números exactos de la tendencia.
    3. Redacta de forma asertiva, indicando si hay que felicitar al alumno, ponerle atención o intervenir. 
    4. Finaliza con una recomendación metodológica de estudio en casa adaptada a este cuadro.
    """
    
    try:
        respuesta = client.models.generate_content(
            model=MODELO_IA,
            contents=prompt
        )
        return respuesta.text
    except Exception:
        return "Actualmente el sistema está experimentando alta demanda. Por favor, revise las notas cuantitativas del estudiante para determinar su progreso en este bimestre."


# =====================================================================
# 3. GENERADOR DE RECOMENDACIONES PARA EL INFORME DE PROGRESO
# =====================================================================
def generar_4_recomendaciones_ia(nombre_alumno, notas_dict):
    prompt = f"""
    Actúa como un psicopedagogo experto y tutor de un colegio de alto rendimiento.
    Genera exactamente 4 recomendaciones pedagógicas personalizadas para el informe de progreso del estudiante: {nombre_alumno}.

    Métricas de comportamiento y actitud del alumno (escala 0 a 20):
    - Puntualidad: {notas_dict.get('Puntualidad', 0)}/20
    - Presentación Personal: {notas_dict.get('Presentacion', 0)}/20
    - Participación en Clase: {notas_dict.get('Participacion', 0)}/20
    - Disciplina y Convivencia: {notas_dict.get('Disciplina', 0)}/20
    - Responsabilidad (Tareas): {notas_dict.get('Responsabilidad', 0)}/20

    REGLAS ESTRICTAS DE RESPUESTA:
    1. Debes devolver ÚNICAMENTE 4 líneas de texto. Ni una más, ni una menos.
    2. Cada línea debe ser una recomendación corta (máximo 15 a 20 palabras), directa y concisa.
    3. Enfócate en felicitar los puntos fuertes (notas altas) y dar pautas de mejora para los puntos bajos.
    4. NO incluyas números, guiones, asteriscos ni símbolos. Devuelve solo el texto limpio separado por un salto de línea.
    """
    
    try:
        respuesta = client.models.generate_content(
            model=MODELO_IA,
            contents=prompt
        )
        
        lineas = [linea.strip() for linea in respuesta.text.split('\n') if linea.strip()]
        return lineas[:4]
        
    except Exception:
        return [
            "Felicitaciones por mantener un esfuerzo constante en tus calificaciones de este periodo.",
            "Se sugiere continuar practicando la puntualidad diaria para optimizar el inicio de tus clases.",
            "Mantén el compromiso con las normas de convivencia del aula y el respeto a tus tutores.",
            "Sigue cumpliendo con la entrega oportuna de tus cuadernos y tareas asignadas."
        ]

@login_required
def consultar_aula_ia(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        consulta_docente = request.POST.get('consulta', '')
        user_personal = getattr(request.user, 'perfil_personal', None)
        
        if not consulta_docente or not user_personal:
            return JsonResponse({'status': 'error', 'message': 'Datos incompletos.'})
            
        try:
            # 1. RECOPILACIÓN MASIVA DE DATOS DEL AULA
            aula_tutoria = Aula.objects.filter(tutor=user_personal).first() 
            if not aula_tutoria:
                return JsonResponse({'status': 'error', 'message': 'No tienes un aula de tutoría asignada para analizar.'})

            periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
            bimestre_actual = periodo_actual.bimestre_actual if periodo_actual else 'I'

            matriculas = Matricula.objects.filter(
                aula=aula_tutoria, 
                estudiante__estado='Activo', 
                periodo=periodo_actual
            ).select_related('estudiante')
            
            # Le indicamos a Gemini cuál es el bimestre en curso
            contexto_datos = f"DATOS DEL AULA {aula_tutoria.grado} {aula_tutoria.seccion} {aula_tutoria.nivel} (BIMESTRE ACTUAL EN CURSO: {bimestre_actual}):\n"
            
            for mat in matriculas:
                nombre_completo = f"{mat.estudiante.nombres} {mat.estudiante.apellidos}"
                
                # 💥 CORRECCIÓN: Agrupamos las notas por Curso Y por Bimestre
                notas_cursos = mat.notas.values(
                    'evaluacion__asignacion__curso__nombre', 
                    'evaluacion__bimestre'
                ).annotate(
                    promedio=Avg('valor')
                ).order_by('evaluacion__bimestre')
                
                # Formateamos para que Gemini lea: "Álgebra (Bimestre I): 16.8, Álgebra (Bimestre II): 14.5"
                detalle_notas = ", ".join([
                    f"{n['evaluacion__asignacion__curso__nombre']} (Bim. {n['evaluacion__bimestre']}): {round(float(n['promedio']),1)}" 
                    for n in notas_cursos if n['promedio']
                ])
                
                if not detalle_notas:
                    detalle_notas = "Sin notas registradas aún"
                
                contexto_datos += f"- Alumno: {nombre_completo} | Notas: {detalle_notas}\n"

            # 2. EL PROMPT MAESTRO (Actualizado con consciencia temporal)
            prompt = f"""
            Eres el Asistente Académico de Inteligencia Artificial del sistema escolar.
            Tu objetivo es responder a la consulta del docente analizando ÚNICAMENTE la siguiente base de datos del salón.
            
            {contexto_datos}
            
            CONSULTA DEL DOCENTE:
            "{consulta_docente}"
            
            REGLAS:
            1. Sé directo, claro y profesional. Es un reporte para el consumo interno del profesor.
            2. 💥 IMPORTANTE: Presta mucha atención al bimestre que solicita el docente. Si te pregunta por "este bimestre" o "el bimestre actual", busca el BIMESTRE ACTUAL EN CURSO indicado arriba y revisa solo las notas de ese periodo.
            3. Si el alumno no tiene notas en el bimestre solicitado para ese curso, dilo claramente (Ej: "Aún no tiene notas registradas en este bimestre"). No asumas promedios de bimestres anteriores como si fueran del actual.
            4. No uses formato Markdown complejo (evita asteriscos, negritas o tablas), usa texto claro con saltos de línea normales.
            """
            
            # 2. EL PROMPT MAESTRO (LENGUAJE NATURAL Y CONVERSACIONAL)
            # prompt = f"""
            # Eres el Asistente Académico de Inteligencia Artificial del sistema escolar, actuando como un colega empático y analítico para el docente.
            # Tu objetivo es responder a la consulta del profesor analizando ÚNICAMENTE la siguiente base de datos del salón.
            
            # BASE DE DATOS DEL SALÓN:
            # {contexto_datos}
            
            # CONSULTA DEL DOCENTE:
            # "{consulta_docente}"
            
            # REGLAS ESTRICTAS DE RESPUESTA:
            # 1. Responde siempre en LENGUAJE NATURAL, fluido y conversacional. NUNCA devuelvas listas rígidas o estructuradas tipo "Alumno: X, Curso: Y, Nota: Z".
            # 2. Integra los datos en párrafos redactados. (Ejemplo ideal: "Emily Chupillon tiene un excelente desempeño en Herramientas Informáticas, manteniendo un promedio general de 17.0 hasta el momento.")
            # 3. Si preguntan algo que no está en los datos provistos, indica amablemente que no tienes esa información a la mano.
            # 4. Al final de tu respuesta, INCLUYE SIEMPRE UNA PREGUNTA DE SEGUIMIENTO para invitar al docente a profundizar. (Ejemplo: "¿Te gustaría saber cómo le va en otros cursos?", "¿Quieres que revisemos a los alumnos con promedios más bajos en esta materia?" o "¿Deseas conocer más detalles sobre alguna evaluación en específico?").
            # 5. No uses formato Markdown complejo (evita asteriscos, negritas o tablas), usa texto limpio con saltos de línea normales.
            # """
            
            try:
                respuesta = client.models.generate_content(
                    model=MODELO_IA,
                    contents=prompt
                )
                texto_ia = respuesta.text
            except Exception:
                texto_ia = "Actualmente el sistema está experimentando alta demanda. Por favor, revise las notas cuantitativas del estudiante para determinar su progreso en este bimestre."

            return JsonResponse({'status': 'success', 'respuesta': texto_ia})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error procesando los datos: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'})

@login_required
def consultar_coordinacion_ia(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        consulta_admin = request.POST.get('consulta', '')
        user_personal = getattr(request.user, 'perfil_personal', None)
        
        if not consulta_admin or not user_personal:
            return JsonResponse({'status': 'error', 'message': 'Datos incompletos.'})
            
        if user_personal.cargo not in ['DIR', 'COO']:
            return JsonResponse({'status': 'error', 'message': 'No tienes permisos de coordinación.'})

        try:
            hoy = timezone.now().date()
            
            # 1. PERIODO Y BIMESTRE ACTUAL
            periodo = PeriodoLectivo.objects.filter(activo=True).first()
            bimestre = periodo.bimestre_actual if periodo else 'I'

            # 2. EXTRACCIÓN DE DATOS DE AUDITORÍA (Rápido y en memoria)
            asignaciones = AsignacionAcademica.objects.filter(
                periodo=periodo
            ).select_related('personal', 'curso', 'aula')
            
            cierres = set(CierreRegistroBimestral.objects.filter(
                bimestre=bimestre, asignacion__periodo=periodo, cerrado=True
            ).values_list('asignacion_id', flat=True))
            
            asign_con_eval = set(Evaluacion.objects.filter(
                bimestre=bimestre, asignacion__periodo=periodo
            ).values_list('asignacion_id', flat=True))
            
            solicitudes = set(SolicitudImpresion.objects.filter(
                asignacion__periodo=periodo
            ).values_list('asignacion_id', flat=True))
            
            entregas_simulacro = set(EntregaSimulacro.objects.filter(
                finalizado=True
            ).values_list('curso_id', 'docente_id'))

            # 3. 💥 MAPEO GRANULAR DE NOTAS POR DOCENTE Y CURSO
            auditoria_docentes = {}
            docentes_falta_materiales = set()
            total_docentes = Personal.objects.filter(cargo='DOC', estado='Activo').count()

            for asig in asignaciones:
                nombre_docente = f"{asig.personal.nombres} {asig.personal.apellidos}"
                # Formateamos el curso para que la IA entienda de qué aula es
                detalle_curso = f"{asig.curso.nombre} ({asig.aula.grado} {asig.aula.seccion})"
                
                # Inicializamos la estructura del docente si no existe
                if nombre_docente not in auditoria_docentes:
                    auditoria_docentes[nombre_docente] = {
                        'completados': [], 
                        'en_progreso': [], 
                        'sin_iniciar': []
                    }
                
                # Clasificamos el estado exacto de ESE curso en particular
                if asig.id in cierres:
                    auditoria_docentes[nombre_docente]['completados'].append(detalle_curso)
                elif asig.id in asign_con_eval:
                    auditoria_docentes[nombre_docente]['en_progreso'].append(detalle_curso)
                else:
                    auditoria_docentes[nombre_docente]['sin_iniciar'].append(detalle_curso)

                # Auditoría de Cumplimiento (Materiales y Simulacros)
                tiene_solicitud = asig.id in solicitudes
                tiene_simulacro = (asig.curso_id, asig.personal_id) in entregas_simulacro
                if not (tiene_solicitud and tiene_simulacro):
                    docentes_falta_materiales.add(nombre_docente)

            # 4. CONVERSIÓN A TEXTO PARA GEMINI
            texto_auditoria = f"--- ESTADO DE REGISTRO DE NOTAS (BIMESTRE {bimestre} | Total Docentes: {total_docentes}) ---\n"
            for docente, estados in auditoria_docentes.items():
                texto_auditoria += f"👨‍🏫 {docente}:\n"
                if estados['completados']:
                    texto_auditoria += f"   ✅ Cerrados/Entregados: {', '.join(estados['completados'])}\n"
                if estados['en_progreso']:
                    texto_auditoria += f"   ⚠️ En Progreso (con evaluaciones creadas): {', '.join(estados['en_progreso'])}\n"
                if estados['sin_iniciar']:
                    texto_auditoria += f"   🚨 Sin Iniciar (vacío absoluto): {', '.join(estados['sin_iniciar'])}\n"

            texto_auditoria += f"\n--- MATERIALES Y SIMULACROS PENDIENTES ---\n"
            texto_auditoria += f"Docentes con deudas de materiales: {', '.join(docentes_falta_materiales) if docentes_falta_materiales else 'Ninguno'}\n"

            # 5. POBLACIÓN Y ASISTENCIA DIARIA
            total_est = Estudiante.objects.filter(estado='Activo').count()
            faltas_hoy = AsistenciaEstudiante.objects.filter(
                fecha=hoy, estado='F', estudiante__matricula__periodo__activo=True
            ).values(
                'estudiante__matricula__aula__grado', 
                'estudiante__matricula__aula__seccion',
                'estudiante__matricula__aula__nivel'
            ).annotate(total_faltas=Count('id')).order_by('-total_faltas')
            
            texto_asistencia = f"--- ASISTENCIA HOY ({hoy.strftime('%d/%m/%Y')}) ---\n"
            texto_asistencia += f"Total de estudiantes activos: {total_est}\n"
            if faltas_hoy:
                aulas_con_faltas = ", ".join([f"{f['estudiante__matricula__aula__grado']} {f['estudiante__matricula__aula__seccion']} {f['estudiante__matricula__aula__nivel']} ({f['total_faltas']} faltas)" for f in faltas_hoy])
                texto_asistencia += f"Inasistencias por aula: {aulas_con_faltas}\n"
            else:
                texto_asistencia += "Inasistencias por aula: 0 faltas registradas.\n"

            # 6. LOGÍSTICA
            alertas_inv = CatalogoMaterial.objects.filter(
                Q(inventarios_aula__mal_estado__gt=0) | Q(inventarios_aula__se_requiere__gt=0), activo=True
            ).distinct().count()
            texto_operaciones = f"--- LOGÍSTICA ---\nMateriales de aula con alertas de reposición: {alertas_inv}\n"

            # 7. PROMPT MAESTRO
            contexto_general = f"{texto_auditoria}\n\n{texto_asistencia}\n\n{texto_operaciones}"

            prompt = f"""
            Eres el Asistente Analítico de Dirección del colegio.
            Responde la consulta del coordinador basándote ÚNICAMENTE en este mapa de auditoría en tiempo real:

            {contexto_general}

            CONSULTA:
            "{consulta_admin}"

            REGLAS ESTRICTAS:
            1. Actúa como un consultor de datos ejecutivo.
            2. Si te preguntan quiénes han subido notas, revisa los campos 'Cerrados/Entregados' y 'En Progreso'. Si un profesor avanzó en algunos cursos pero en otros no, detalla exactamente en cuáles sí y en cuáles no.
            3. Si te preguntan por un profesor en específico, detalla el estado de cada uno de sus cursos.
            4. Si te preguntan cuántos faltan, cuenta a los que tienen cursos en la categoría 'Sin Iniciar' y nómbralos junto a sus cursos pendientes.
            5. Presenta la información en texto plano claro, sin asteriscos de Markdown ni negritas complejas. Usa saltos de línea y viñetas simples (-).
            """

            # 8. LLAMADA A LA IA
            try:
                respuesta = client.models.generate_content(
                    model=MODELO_IA,
                    contents=prompt
                )
                texto_ia = respuesta.text
            except Exception:
                texto_ia = "El motor de análisis directivo está experimentando alta demanda. Revise el panel de auditoría."

            return JsonResponse({'status': 'success', 'respuesta': texto_ia})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error en la auditoría de datos: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'})

@login_required
def procesar_ingreso_notas_ia(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        texto_docente = request.POST.get('texto_docente', '')
        evaluacion_id = request.POST.get('evaluacion_id')
        
        if not texto_docente or not evaluacion_id:
            return JsonResponse({'status': 'error', 'message': 'Faltan datos.'})
            
        try:
            evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id)
            notas_db = Nota.objects.filter(evaluacion=evaluacion).select_related('matricula__estudiante')
            
            # 1. ARMAMOS EL MAPA ESTRICTO PARA LA IA
            # Formato: [ID de Nota] - Nombre Completo del Alumno
            mapa_alumnos = ""
            for n in notas_db:
                nombre = f"{n.matricula.estudiante.nombres} {n.matricula.estudiante.apellidos}"
                mapa_alumnos += f"[ID: {n.id}] - {nombre}\n"
                
            # 2. EL PROMPT MAESTRO (Data Structure LLM)
            prompt = f"""
            Eres un procesador lógico estricto. Tu única tarea es extraer asignaciones de notas numéricas (o acciones de borrado) de un texto libre y cruzarlas con una lista oficial de alumnos.

            LISTA OFICIAL DEL SALÓN (Solo puedes asignar o borrar notas a estos IDs):
            {mapa_alumnos}

            TEXTO DEL PROFESOR:
            "{texto_docente}"

            REGLAS DE PROCESAMIENTO:
            1. Identifica a los alumnos mencionados y asígnales la nota numérica indicada.
            2. 💥 REGLA DE BORRADO: Si el profesor indica "borrar", "eliminar", "quitar" o "limpiar" las notas de un alumno (o de todos los alumnos), debes asignar obligatoriamente el valor "" (un string vacío) a esos IDs.
            3. Si el profesor dice "a todos los demás ponles X" o "borra a todos", aplica la instrucción a todos los IDs de la lista que no fueron exceptuados.
            4. CONTROL DE AMBIGÜEDAD: Si el profesor menciona solo un nombre (ej. "Juan") y hay más de una persona con ese nombre, NO le asignes nota a ninguno. En su lugar, agrega una advertencia en el campo "ambiguedades".
            5. DEVUELVE ÚNICAMENTE UN JSON VÁLIDO CON ESTA ESTRUCTURA EXACTA (sin comillas triples de Markdown ni la palabra 'json'):
            {{
                "notas": [
                    {{"nota_id": 12, "valor": 15}},
                    {{"nota_id": 15, "valor": ""}}
                ],
                "ambiguedades": []
            }}
            """

            # 3. LLAMADA AL MODELO (Flash-Lite es perfecto y rápido para JSON)
            respuesta = client.models.generate_content(
                model=MODELO_IA,
                contents=prompt
            )
            
            # Limpieza por si Gemini añade formato markdown ```json
            texto_ia = respuesta.text.strip()
            if texto_ia.startswith("```json"):
                texto_ia = texto_ia[7:]
            if texto_ia.endswith("```"):
                texto_ia = texto_ia[:-3]
            
            return JsonResponse({'status': 'success', 'ia_json': texto_ia.strip()})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error procesando notas: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'})