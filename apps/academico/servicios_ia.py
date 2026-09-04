from decimal import ROUND_HALF_UP, Decimal
import os
import numpy as np # Necesitarás instalar numpy: pip install numpy
from .models import EvaluacionActitudinal, Nota
from dotenv import load_dotenv
from google.genai import Client

# Carga las variables del archivo .env
load_dotenv()

def analizar_rendimiento_estudiante(matricula_id, promedio_oficial, curso_id=None, bimestre_actual=None):
    """
    Motor Predictivo: Recibe el promedio oficial exacto y usa el historial 
    de notas cronológicas solo para calcular tendencias y proyecciones.
    """
    # Si no hay promedio oficial registrado, detenemos el análisis
    if promedio_oficial is None or promedio_oficial == 0:
        return {
            'promedio': "-", 'promedio_proyectado': "-", 'tendencia_numerica': 0, 
            'estado_ia': 'Sin Datos', 'color': 'secondary', 'icono': 'horizontal_rule', 'alerta_critica': False, 'cantidad_notas': 0
        }

    # Extraemos el historial para ver la curva de rendimiento
    notas_qs = Nota.objects.filter(matricula_id=matricula_id, valor__isnull=False)
    if curso_id:
        notas_qs = notas_qs.filter(evaluacion__asignacion__curso__id=curso_id)
    if bimestre_actual:
        notas_qs = notas_qs.filter(evaluacion__bimestre=bimestre_actual)
        
    notas_qs = notas_qs.order_by('evaluacion__fecha', 'evaluacion__id') 
    valores = [float(n.valor) for n in notas_qs]
    
    tendencia = 0
    promedio_proyectado = promedio_oficial
    alerta_critica = False
    
    if len(valores) >= 2:
        # 1. DETECCIÓN DE TROPIEZO (La última nota es 4 puntos menor que su histórico)
        ultima_nota = valores[-1]
        promedio_historico = sum(valores[:-1]) / len(valores[:-1])
        if ultima_nota <= (promedio_historico - 4):
            alerta_critica = True
            
        # 2. CÁLCULO DE PROYECCIÓN BADA EN EL PROMEDIO OFICIAL
        x = np.arange(len(valores))
        y = np.array(valores)
        pendiente, _ = np.polyfit(x, y, 1)
        tendencia = round(pendiente, 2)
        
        # Proyectamos sumando la tendencia al PROMEDIO OFICIAL
        proyeccion_cruda = float(promedio_oficial) + (tendencia * 1.5) 
        proyeccion_limitada = max(0, min(20, proyeccion_cruda))
        promedio_proyectado = int(Decimal(str(proyeccion_limitada)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        
    # ====================================================================
    # LÓGICA VISUAL DEL SEMÁFORO
    # ====================================================================
    
    if promedio_proyectado < 13:
        estado_ia = "Proyecta Desaprobar"
        color = "danger"
        icono = "trending_down"
    elif alerta_critica:
        estado_ia = "Alerta: Bajón Repentino"
        color = "warning"
        icono = "warning"
    elif promedio_proyectado < 14.5:
        if tendencia < -0.3:
            estado_ia = "En Declive"
            color = "warning"
            icono = "trending_down"
        elif tendencia > 0.3:
            estado_ia = "Recuperándose"
            color = "info"
            icono = "trending_up"
        else:
            estado_ia = "Estancado (Riesgo)"
            color = "secondary"
            icono = "trending_flat"
    else:
        estado_ia = "Proyección Óptima"
        color = "success"
        icono = "trending_up" if tendencia > 0 else "trending_flat"
            
    return {
        'promedio': promedio_oficial, # Devolvemos el oficial intacto
        'promedio_proyectado': promedio_proyectado,
        'tendencia_numerica': tendencia,
        'estado_ia': estado_ia,
        'color': color,
        'icono': icono,
        'alerta_critica': alerta_critica,
        'cantidad_notas': len(valores)
    }

def generar_diagnostico_cualitativo(nombre_alumno, promedio, tendencia, conducta, estado_ia, contexto_curso, bimestre):
    """
    Llama al modelo Gemini 3.5 Flash de Google usando el nuevo SDK 'google-genai'.
    """
    # 1. Inicializamos el nuevo cliente
    api_key_segura = os.getenv("GEMINI_API_KEY")
    client = Client(api_key=api_key_segura)
    
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
    2. Evita usar los números exactos de la tendencia (ej. no digas "tu tendencia es de -0.6"), tradúcelo a lenguaje natural ("notamos una ligera caída en sus últimas evaluaciones").
    3. Redacta de forma asertiva, indicando si hay que felicitar al alumno, ponerle atención o intervenir. 
    4. Finaliza con una recomendación metodológica de estudio en casa adaptada a este cuadro.
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
    api_key_segura = os.getenv("GEMINI_API_KEY")
    client = Client(api_key=api_key_segura)

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