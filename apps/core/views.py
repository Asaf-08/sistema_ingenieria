from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import timedelta

# Importa tus modelos de las otras apps
from apps.personal.models import Personal
from apps.academico.models import Aula, Estudiante, AsignacionAcademica, Nota, CatalogoMaterial, PeriodoLectivo
from apps.asistencia.models import AsistenciaEstudiante

@login_required
def dashboard_principal(request):
    """ Vista inteligente multirrol para el inicio del sistema """
    hoy = timezone.now()
    user_personal = getattr(request.user, 'perfil_personal', None)
    
    # Inicializamos el contexto base
    context = {'segment': 'dashboard'}

    if not user_personal:
        # Si por alguna razón el usuario no tiene perfil de personal (ej: superuser puro)
        return render(request, 'core/dashboard_admin.html', context)

    # =========================================================================
    # FLUJO A: VISTA DE COORDINACIÓN / DIRECCIÓN (DIR o COO)
    # =========================================================================
    if user_personal.cargo in ['DIR', 'COO']:
        # 1. KPIs Globales
        total_estudiantes = Estudiante.objects.filter(estado='Activo').count()
        total_docentes = Personal.objects.filter(cargo='DOC', estado='Activo').count()
        
        asistencias_hoy = AsistenciaEstudiante.objects.filter(fecha=hoy)
        presentes_hoy = asistencias_hoy.filter(estado__in=['P', 'T', 'J']).count()
        porcentaje_asistencia = int((presentes_hoy / total_estudiantes * 100)) if total_estudiantes > 0 else 0

        alertas_inventario = CatalogoMaterial.objects.filter(
            Q(inventarios_aula__mal_estado__gt=0) | Q(inventarios_aula__se_requiere__gt=0),
            activo=True
        ).distinct().count()

        # 2. Listas de Acción por Excepción
        docentes_pendientes = Personal.objects.filter(
            cargo='DOC', estado='Activo', asignaciones__isnull=False
        ).exclude(asignaciones__evaluaciones__isnull=False).distinct()[:5]

        mejores_alumnos = Estudiante.objects.filter(estado='Activo').annotate(
            promedio_general=Avg('matricula__notas__valor')
        ).exclude(promedio_general__isnull=True).order_by('-promedio_general')[:5]

        # 3. Gráfico 1: Asistencia Semanal Real (Lunes a Viernes)
        dias_semana = []
        asistencias_semana = []
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        for i in range(5):
            dia_evaluar = inicio_semana + timedelta(days=i)
            dias_semana.append(dia_evaluar.strftime('%d/%m'))
            presentes = AsistenciaEstudiante.objects.filter(fecha=dia_evaluar, estado__in=['P', 'T', 'J']).count()
            asistencias_semana.append(presentes)

        # 4. Gráfico 2: Desempeño Escolar Dinámico por Bimestres reales
        # Obtenemos los bimestres que tengan al menos una nota registrada
        notas_por_bimestre = Nota.objects.values('evaluacion__bimestre').annotate(
            promedio=Avg('valor')
        ).order_by('evaluacion__bimestre')
        
        labels_bimestres = [f"Bimestre {n['evaluacion__bimestre']}" for n in notas_por_bimestre]
        valores_bimestres = [float(round(n['promedio'], 1)) for n in notas_por_bimestre]

        # 5. Gráfico 3: Distribución Real IA (Semáforo K-Means)
        estudiantes_con_promedio = Estudiante.objects.filter(estado='Activo').annotate(
            promedio_general=Avg('matricula__notas__valor')
        )
        total_optimos = estudiantes_con_promedio.filter(promedio_general__gte=14).count()
        total_esfuerzo = estudiantes_con_promedio.filter(promedio_general__gte=11, promedio_general__lt=14).count()
        total_riesgo = estudiantes_con_promedio.filter(promedio_general__lt=11).count()
        
        total_sin_notas = estudiantes_con_promedio.filter(promedio_general__isnull=True).count()
        total_esfuerzo += total_sin_notas # Nuevos ingresos entran a observación por defecto

        # 6. Cálculo del Delta de Riesgo Real para el footer de la tarjeta
        hace_un_mes = hoy - timedelta(days=30)
        riesgo_mes_pasado = Estudiante.objects.filter(estado='Activo', fecha_registro__lt=hace_un_mes).annotate(
            prom_ant=Avg('matricula__notas__valor')
        ).filter(prom_ant__lt=11).count()
        
        delta_riesgo = total_riesgo - riesgo_mes_pasado
        texto_delta = f"+{delta_riesgo}" if delta_riesgo >= 0 else f"{delta_riesgo}"

        # Inyectamos todo al contexto de Coordinación
        context.update({
            'rol': 'COORDINACION',
            'total_estudiantes': total_estudiantes,
            'total_docentes': total_docentes,
            'porcentaje_asistencia': porcentaje_asistencia,
            'alertas_inventario': alertas_inventario,
            'docentes_pendientes': docentes_pendientes,
            'mejores_alumnos': mejores_alumnos,
            'dias_semana': dias_semana,
            'asistencias_semana': asistencias_semana,
            'labels_bimestres': labels_bimestres,
            'valores_bimestres': valores_bimestres,
            'total_optimos': total_optimos,
            'total_esfuerzo': total_esfuerzo,
            'total_riesgo': total_riesgo,
            'texto_delta': texto_delta,
        })
        
        return render(request, 'core/dashboard_admin.html', context)

    # =========================================================================
    # FLUJO B: VISTA DEL DOCENTE (DOC)
    # =========================================================================
    elif user_personal.cargo == 'DOC':
        # 1. Cursos y Aula de Tutoría
        periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
        mis_cursos = AsignacionAcademica.objects.filter(
            personal=user_personal, 
            periodo=periodo_actual
        ).select_related('curso', 'aula')
        aula_tutoria = Aula.objects.filter(tutor=user_personal).first()

        # 2. 💥 NUEVO: Desglose de Alumnos por Nivel (Solo los niveles que dicta)
        niveles_dicta = mis_cursos.values_list('aula__nivel', flat=True).distinct()
        breakdown_alumnos = []
        mis_alumnos_count = 0
        
        for nivel in niveles_dicta:
            count = Estudiante.objects.filter(
                estado='Activo',
                matricula__aula__nivel=nivel,
                matricula__aula__asignaciones__personal=user_personal
            ).distinct().count()
            
            if count > 0:
                breakdown_alumnos.append({'nivel': nivel, 'total': count})
                mis_alumnos_count += count

        # 3. Lógica de "Materiales" (Mostrar Tema y Fecha real en lugar de adivinar días)
        from apps.academico.models import SolicitudImpresion
        ultimo_material = SolicitudImpresion.objects.filter(personal=user_personal).order_by('-fecha_subida').first()
        
        # Validamos si han pasado más de 7 días para lanzar la alerta visual
        alerta_material = False
        if ultimo_material:
            dias_sin_subir = (hoy - ultimo_material.fecha_subida.date()).days
            alerta_material = dias_sin_subir > 7
        else:
            alerta_material = True

        # 4. Notas Pendientes
        notas_pendientes = Nota.objects.filter(
            evaluacion__asignacion__in=mis_cursos, 
            valor__isnull=True
        ).count()

        # 5. Gráfico: Mejores Alumnos por Nivel
        mejores_por_nivel = {}
        for nivel in niveles_dicta:
            top_alumnos = Estudiante.objects.filter(
                estado='Activo', matricula__aula__nivel=nivel
            ).annotate(
                promedio=Avg('matricula__notas__valor')
            ).exclude(promedio__isnull=True).order_by('-promedio')[:5]
            
            if top_alumnos.exists():
                mejores_por_nivel[nivel] = top_alumnos

        context.update({
            'rol': 'DOCENTE',
            'mis_cursos_lista': mis_cursos, # 💥 Enviamos los cursos para la nueva tarjeta
            'aula_tutoria': aula_tutoria,
            'mis_alumnos_count': mis_alumnos_count,
            'breakdown_alumnos': breakdown_alumnos, # 💥 Enviamos el desglose
            'ultimo_material': ultimo_material,
            'alerta_material': alerta_material,
            'notas_pendientes': notas_pendientes,
            'mejores_por_nivel': mejores_por_nivel,
        })

        return render(request, 'core/dashboard_docente.html', context)