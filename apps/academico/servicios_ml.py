from decimal import ROUND_HALF_UP, Decimal

import numpy as np # 💥 NUEVO: Importación necesaria para calcular la varianza
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from django.db.models import Avg
from apps.academico.models import Aula, Matricula, Nota, PeriodoLectivo, AsignacionAcademica
from apps.academico.services import obtener_consolidado_aula_maestro, calcular_matriz_vigesimal

def agrupar_estudiantes_kmeans(aula_id, periodo_id, curso_id=None):
    """
    Agrupa a los estudiantes usando K-Means dinámico, 
    alimentado EXCLUSIVAMENTE por los promedios oficiales del bimestre actual.
    """
    try:
        aula = Aula.objects.get(id=aula_id)
        periodo = PeriodoLectivo.objects.get(id=periodo_id)
        bimestre_actual = periodo.bimestre_actual or 'I'
    except (Aula.DoesNotExist, PeriodoLectivo.DoesNotExist):
        return {"error": "Aula o periodo no encontrados."}

    # Extraemos el consolidado general (esto siempre se necesita para la conducta)
    data_alumnos, _ = obtener_consolidado_aula_maestro(aula, periodo)
    
    # 💥 LÓGICA DE CURSO: Definimos de dónde sacar el Promedio Académico
    notas_oficiales_acad = {}
    if curso_id:
        asignacion_sel = AsignacionAcademica.objects.filter(curso_id=curso_id, aula=aula, periodo=periodo).first()
        if asignacion_sel:
            matriz_data = calcular_matriz_vigesimal(asignacion_sel, aula, bimestre_actual)
            for fila in matriz_data.get('datos_matriz', []):
                notas_oficiales_acad[fila.get('matricula_id')] = fila.get('prom_general', 0)
    else:
        for m_id, data in data_alumnos.items():
            notas_oficiales_acad[m_id] = data.get('promedios_bimestre', {}).get(bimestre_actual, 0)
            
    datos = []
    
    # 2. FEATURE EXTRACTION
    for m_id, data in data_alumnos.items():
        mat = data['matricula']
        
        # Leemos de nuestro diccionario dinámico (Curso específico o General)
        prom_academico_raw = notas_oficiales_acad.get(m_id, 0)
        prom_actitudinal_raw = data.get('comportamiento', {}).get(bimestre_actual, 15.0)
        
        if prom_academico_raw > 0:
            prom_academico = int(Decimal(str(prom_academico_raw)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            prom_actitudinal = int(Decimal(str(prom_actitudinal_raw)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

            datos.append({
                'matricula_id': mat.id,
                'nombre': f"{mat.estudiante.apellidos}, {mat.estudiante.nombres}",
                'promedio_academico': prom_academico,
                'promedio_actitudinal': prom_actitudinal
            })

    if len(datos) < 3:
        return {"error": "Se necesitan al menos 3 estudiantes con notas en este filtro para generar agrupamientos."}

    df = pd.DataFrame(datos)
    
    # 3. INTELIGENCIA DINÁMICA: Cálculo de la Varianza
    X_raw = df[['promedio_academico', 'promedio_actitudinal']].values
    varianza_media = np.var(X_raw, axis=0).mean()
    
    if varianza_media < 2.0:
        k_optimo = 1
    elif varianza_media < 5.0:
        k_optimo = 2
    else:
        k_optimo = 3
    
    # 4. Normalización de datos
    scaler = StandardScaler()
    caracteristicas = scaler.fit_transform(X_raw)
    
    # 5. Aplicar K-Means Clustering 
    kmeans = KMeans(n_clusters=k_optimo, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(caracteristicas)
    
    # 6. Interpretación Automática de los Centroides
    centroides = df.groupby('cluster')[['promedio_academico', 'promedio_actitudinal']].mean()
    
    perfiles_nombres = {}
    for cluster_id, fila in centroides.iterrows():
        acad = fila['promedio_academico']
        acti = fila['promedio_actitudinal']
        
        # 1. Nivel Superior (Los top de la clase: Notas altas y buena conducta)
        if acad >= 16.5 and acti >= 15.0:
            perfiles_nombres[cluster_id] = "🏆 Alto Rendimiento (Sobresaliente en notas y conducta)"
            
        # 2. Nivel Bueno (El grupo promedio-alto)
        elif acad >= 13.5 and acti >= 14.0:
            perfiles_nombres[cluster_id] = "🌟 Perfil Óptimo (Buen rendimiento y conducta)"
            
        # 3. Riesgo Crítico (Bajas notas y mala conducta)
        elif acad < 12.5 and acti < 13.0:
            perfiles_nombres[cluster_id] = "🚨 Riesgo Integral (Requiere apoyo académico y conductual)"
            
        # 4. Esfuerzo sin resultados (Conducta decente, pero no aprueba)
        elif acad < 12.5 and acti >= 13.0:
            perfiles_nombres[cluster_id] = "📚 Esfuerzo sin resultados (Buena actitud, bajo rendimiento)"
            
        # 5. Talento Indisciplinado (Aprueba, pero su conducta es un problema)
        elif acad >= 13.0 and acti < 12.5:
            perfiles_nombres[cluster_id] = "⚠️ Talento indisciplinado (Rendimiento aceptable, mala conducta)"
            
        # 6. El punto medio 
        else:
            if acad > acti:
                perfiles_nombres[cluster_id] = "📊 Perfil Estable (Mejor en notas que en conducta)"
            else:
                perfiles_nombres[cluster_id] = "📊 Perfil Estable (Mejor actitud que notas)"

    # 7. Preparar la respuesta JSON
    resultados = []
    # Usamos unique() para asegurarnos de solo iterar sobre los clusters que realmente se crearon
    for cluster_id in df['cluster'].unique():
        alumnos_en_cluster = df[df['cluster'] == cluster_id]
        
        resultados.append({
            "perfil": perfiles_nombres.get(cluster_id, "Grupo No Definido"),
            "cantidad": len(alumnos_en_cluster),
            "alumnos": alumnos_en_cluster[['nombre', 'promedio_academico', 'promedio_actitudinal']].to_dict(orient='records')
        })
        
    # Ordenar los resultados para que el grupo "Óptimo" o de mejor nota salga primero
    resultados.sort(key=lambda x: ("Riesgo" in x['perfil'], "Esfuerzo" in x['perfil'], "Talento" in x['perfil']))

    return {"status": "success", "clusters": resultados}