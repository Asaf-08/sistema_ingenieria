# apps/academico/services.py (o donde decidas crearlo)
from decimal import Decimal, ROUND_HALF_UP
from apps.academico.models import Matricula, Nota

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
        
        nota_mensual = notas_alumno.get(eval_mensual.id, 0) if eval_mensual else 0
        nota_bimestral = notas_alumno.get(eval_bimestral.id, 0) if eval_bimestral else 0

        componentes = [prom_mensual_lc, prom_bimestral_lc, prom_desafio, nota_mensual, nota_bimestral, prom_simulacro]
        sumatoria_validos = [p for p in componentes if p > 0]
        prom_general = int(Decimal(str(sum(sumatoria_validos) / len(sumatoria_validos))).quantize(Decimal('1'), rounding=ROUND_HALF_UP)) if sumatoria_validos else 0

        datos_matriz.append({
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