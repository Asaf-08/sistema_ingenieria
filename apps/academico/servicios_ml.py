import numpy as np # 💥 NUEVO: Importación necesaria para calcular la varianza
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from django.db.models import Avg
from apps.academico.models import Matricula, Nota
from apps.academico.models import EvaluacionActitudinal # Ajusta la importación según tu app

def agrupar_estudiantes_kmeans(aula_id, periodo_id):
    """
    Extrae las notas y la conducta de los alumnos de un aula, 
    y aplica K-Means con un 'K Dinámico' basado en la dispersión matemática.
    """
    # 1. Obtener los alumnos matriculados en esa aula
    matriculas = Matricula.objects.filter(aula_id=aula_id, periodo_id=periodo_id)
    
    if matriculas.count() < 3:
        return {"error": "Se necesitan al menos 3 estudiantes para generar agrupamientos matemáticos."}

    datos = []
    
    # 2. Extracción de características (Feature Extraction)
    for mat in matriculas:
        # Promedio Académico
        promedio_notas = Nota.objects.filter(matricula=mat).aggregate(Avg('valor'))['valor__avg']
        prom_academico = float(promedio_notas) if promedio_notas else 0.0
        
        # Promedio Actitudinal (Si no tiene, le ponemos 20 por defecto o un neutro)
        eval_act = EvaluacionActitudinal.objects.filter(matricula=mat).first()
        if eval_act:
            prom_actitudinal = float(eval_act.promedio_actitudinal)
        else:
            prom_actitudinal = 15.0 # Un valor neutro si el tutor aún no califica
            
        datos.append({
            'matricula_id': mat.id,
            'nombre': f"{mat.estudiante.apellidos}, {mat.estudiante.nombres}",
            'promedio_academico': prom_academico,
            'promedio_actitudinal': prom_actitudinal
        })
        
    df = pd.DataFrame(datos)
    
    # 💥 3. INTELIGENCIA DINÁMICA: Cálculo de la Varianza
    # Extraemos los datos puros para medir qué tan diferentes son los alumnos entre sí
    X_raw = df[['promedio_academico', 'promedio_actitudinal']].values
    varianza_media = np.var(X_raw, axis=0).mean()
    
    # Decidimos cuántos grupos (K) crear basados en las matemáticas, no en reglas rígidas
    if varianza_media < 2.0:
        # Todos tienen notas casi idénticas (ej. Todos son de 18 y 19). Hacemos 1 solo grupo.
        k_optimo = 1
    elif varianza_media < 5.0:
        # Hay cierta diferencia pero no extrema. Los dividimos en 2 perfiles.
        k_optimo = 2
    else:
        # Hay mucha desigualdad en el salón (Alumnos de 20 y alumnos de 08). Usamos 3 perfiles.
        k_optimo = 3
    
    # 4. Normalización de datos (Imprescindible para algoritmos de distancia)
    scaler = StandardScaler()
    caracteristicas = scaler.fit_transform(X_raw)
    
    # 💥 5. Aplicar K-Means Clustering con el 'k_optimo' en lugar del 3 fijo
    kmeans = KMeans(n_clusters=k_optimo, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(caracteristicas)
    
# 6. Interpretación Automática de los Clusters (Asignar nombres descriptivos)
    centroides = df.groupby('cluster')[['promedio_academico', 'promedio_actitudinal']].mean()
    
    perfiles_nombres = {}
    for cluster_id, fila in centroides.iterrows():
        acad = fila['promedio_academico']
        acti = fila['promedio_actitudinal']
        
        # 💥 REGLAS ESTRICTAS SIN "LIMBOS NUMÉRICOS"
        # Asumimos que la nota aprobatoria base es 13.
        
        if acad >= 14.5 and acti >= 14.5:
            perfiles_nombres[cluster_id] = "🌟 Perfil Óptimo (Buen rendimiento y conducta)"
            
        elif acad < 13 and acti < 13:
            perfiles_nombres[cluster_id] = "🚨 Riesgo Integral (Requiere apoyo académico y conductual)"
            
        elif acad < 13 and acti >= 13:
            perfiles_nombres[cluster_id] = "📚 Esfuerzo sin resultados (Buena conducta, bajo rendimiento)"
            
        elif acad >= 13 and acti < 13:
            perfiles_nombres[cluster_id] = "⚠️ Talento indisciplinado (Buenas notas, problemas de conducta)"
            
        else:
            # Aquí solo caerán los que tengan entre 13 y 14.4 en ambas cosas
            perfiles_nombres[cluster_id] = "📊 Perfil Promedio (Estable)"

    # 💥 7. Preparar la respuesta JSON iterando solo hasta el k_optimo
    resultados = []
    for cluster_id in range(k_optimo):
        alumnos_en_cluster = df[df['cluster'] == cluster_id]
        
        # Opcional pero recomendado: si el modelo crea un grupo y no tiene alumnos, lo ignoramos
        if len(alumnos_en_cluster) == 0:
            continue
            
        resultados.append({
            "perfil": perfiles_nombres.get(cluster_id, "Grupo No Definido"),
            "cantidad": len(alumnos_en_cluster),
            "alumnos": alumnos_en_cluster[['nombre', 'promedio_academico', 'promedio_actitudinal']].to_dict(orient='records')
        })
        
    return {"status": "success", "clusters": resultados}