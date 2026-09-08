from decimal import ROUND_HALF_UP, Decimal
import json
import os
from google import genai
import numpy as np
from dotenv import load_dotenv

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