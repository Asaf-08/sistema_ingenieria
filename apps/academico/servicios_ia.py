import numpy as np # Necesitarás instalar numpy: pip install numpy
from .models import EvaluacionActitudinal, Nota
from google.genai import Client

API_KEY_GEMINI = "AIzaSyBH9VkvD1kOBB09x9AQjvoDXTxoR4AK6_0"

def analizar_rendimiento_estudiante(matricula_id, curso_id=None):
    
    # 1. Base: Todas las notas académicas del alumno
    notas_qs = Nota.objects.filter(matricula_id=matricula_id, valor__isnull=False)
    
    if curso_id:
        notas_qs = notas_qs.filter(evaluacion__asignacion__curso__id=curso_id)
        
    notas_qs = notas_qs.order_by('evaluacion__id') 
    valores = [float(n.valor) for n in notas_qs]
    
    # 💥 NUEVO: Traemos su conducta para estar 100% alineados con servicios_ml.py
    eval_act = EvaluacionActitudinal.objects.filter(matricula_id=matricula_id).first()
    prom_actitudinal = float(eval_act.promedio_actitudinal) if eval_act else 15.0
    
    if not valores:
        return {'promedio': 0, 'tendencia_numerica': 0, 'estado_ia': 'Sin Datos', 'color': 'secondary', 'cantidad_notas': 0}
        
    promedio = sum(valores) / len(valores)
    
    if len(valores) < 3:
        tendencia = 0
    else:
        x = np.arange(len(valores))
        y = np.array(valores)
        pendiente, _ = np.polyfit(x, y, 1)
        tendencia = round(pendiente, 2)
        
    # ====================================================================
    # 💥 REGLAS DEL SEMÁFORO ALINEADAS MILIMÉTRICAMENTE CON K-MEANS
    # ====================================================================
    
    estado_ia = "Estable"
    color = "success" 
    
    # 1. Riesgo Crítico (DANGER) -> Promedio académico menor a 13 o bajada en picada
    if promedio < 13 or tendencia <= -1.5:
        color = "danger"
        if prom_actitudinal < 13:
            estado_ia = "Riesgo Integral" # Falla en notas y conducta
        else:
            estado_ia = "Riesgo Académico" # Falla solo en notas
            
    # 2. Atención Requerida (WARNING) -> Alumno regular, o talento con mala conducta
    elif (13 <= promedio < 14.5) or tendencia < -0.5:
        color = "warning"
        if prom_actitudinal < 13:
            estado_ia = "Alerta Conductual"
        else:
            estado_ia = "Observación"
            
    # 3. Óptimo (SUCCESS) -> Excelencia académica y buena conducta
    else:
        color = "success"
        if promedio >= 14.5 and prom_actitudinal >= 14.5:
            estado_ia = "Óptimo"
        else:
            estado_ia = "Estable"
            
    return {
        'promedio': round(promedio, 2),
        'tendencia_numerica': tendencia,
        'estado_ia': estado_ia,
        'color': color,
        'cantidad_notas': len(valores)
    }

def generar_diagnostico_cualitativo(nombre_alumno, promedio, tendencia, estado_ia, contexto_curso):
    """
    Llama al modelo Gemini 3.5 Flash de Google usando el nuevo SDK 'google-genai'.
    """
    # 1. Inicializamos el nuevo cliente
    client = Client(api_key=API_KEY_GEMINI)
    
    prompt = f"""
    Actúa como un psicopedagogo experto y empático de un colegio de prestigio. 
    Redacta un diagnóstico de máximo 3 párrafos cortos dirigido al apoderado del estudiante: {nombre_alumno}.
    
    El análisis debe enfocarse en el desempeño del alumno {contexto_curso}.
    
    Métricas analíticas del sistema:
    - Promedio actual en este alcance: {promedio}/20
    - Tendencia calculada: {tendencia} (Si es menor a -0.2, sus notas recientes han bajado. Si es mayor a 0.2, ha mejorado).
    - Estado de alerta según el Semáforo predictivo: {estado_ia}.
    
    Evita tecnicismos de programación o estadística. Redacta de forma asertiva, indicando si hay que felicitar al alumno, ponerle atención o intervenirlo. Finaliza con una recomendación metodológica de estudio en casa adecuada para esta situación.
    """
    
    # 2. 💥 Nueva forma de ejecutar el modelo
    respuesta = client.models.generate_content(
        model='gemini-3.1-flash-lite',
        contents=prompt
    )
    
    return respuesta.text


def generar_4_recomendaciones_ia(nombre_alumno, notas_dict):
    """
    Analiza las 5 notas actitudinales y genera exactamente 4 recomendaciones
    cortas y concisas para el Informe Progresivo.
    """
    client = Client(api_key=API_KEY_GEMINI)
    
    # Construimos un prompt ultra-estricto con el formato
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
    3. Enfócate en felicitar los puntos fuertes (notas altas) y dar pautas de mejora para los puntos bajos (notas menores a 14).
    4. NO incluyas números (1, 2, 3), guiones (-), asteriscos (*) ni el símbolo de check (✓). Devuelve solo el texto limpio de cada recomendación separado por un salto de línea.
    """
    
    try:
        respuesta = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=prompt
        )
        
        # Limpiamos la respuesta y la separamos por líneas
        lineas = [linea.strip() for linea in respuesta.text.split('\n') if linea.strip()]
        
        # Nos aseguramos de retornar exactamente 4 elementos por si la IA se desvía
        return lineas[:4]
        
    except Exception as e:
        # Fallback de seguridad por si falla el internet o la API Key para que no se caiga el PDF
        return [
            "Felicitaciones por mantener un esfuerzo constante en tus calificaciones de este periodo.",
            "Se sugiere continuar practicando la puntualidad diaria para optimizar el inicio de tus clases.",
            "Mantén el compromiso con las normas de convivencia del aula y el respeto a tus tutores.",
            "Sigue cumpliendo con la entrega oportuna de tus cuadernos y tareas asignadas."
        ]