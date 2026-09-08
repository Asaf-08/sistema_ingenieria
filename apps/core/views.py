from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum
from datetime import timedelta
from django.core.cache import cache

# Importa tus modelos de las otras apps
from django.contrib.auth.views import LoginView
from apps.academico.services import obtener_consolidado_aula_maestro
from apps.academico.servicios_ia import analizar_rendimiento_estudiante
from apps.personal.models import Personal
from apps.academico.models import Aula, Estudiante, AsignacionAcademica, Matricula, Nota, CatalogoMaterial, PeriodoLectivo
from apps.asistencia.models import AsistenciaEstudiante

class LoginPersonalizadoView(LoginView):
    """
    Vista maestra de autenticación. 
    Intercepta el formulario para configurar la duración de la sesión y bloquear inactivos.
    """
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        # 💥 EL CANDADO DEFINITIVO: Interceptamos al usuario autenticado
        user = form.get_user()
        
        # Verificamos si tiene un perfil asociado y si su estado es 'Inactivo'
        if hasattr(user, 'perfil_personal') and user.perfil_personal.estado == 'Inactivo':
            # Le inyectamos el error estándar de Django al formulario 
            form.add_error(None, "Por favor, introduzca un nombre de usuario y clave correctos.")
            # Lo devolvemos a la pantalla de login como si hubiera fallado (form_invalid)
            return self.form_invalid(form)

        # 1. Hacemos que Django loguee al usuario normalmente
        response = super().form_valid(form)
        
        # 2. Leemos si el switch "Mantener sesión iniciada" llegó marcado
        remember_me = self.request.POST.get('remember_me', None)

        if remember_me == 'on':
            # Si marcó la casilla: La sesión durará 2 semanas (1209600 segundos)
            # Esto sobrevive aunque apague la PC o el celular
            self.request.session.set_expiry(1209600)
        else:
            # 💥 Si NO la marcó: La sesión se destruye automáticamente al cerrar la pestaña/navegador
            self.request.session.set_expiry(0)

        return response

@login_required
def dashboard_principal(request):
    """ Vista inteligente multirrol para el inicio del sistema """
    periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
    hoy = timezone.now().date()
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
        # 1. KPIs Globales en TIEMPO REAL (Esto se procesa rapidísimo y siempre está vivo)
        total_estudiantes = Estudiante.objects.filter(estado='Activo').count()
        total_docentes = Personal.objects.filter(cargo='DOC', estado='Activo').count()
        
        asistencias_hoy = AsistenciaEstudiante.objects.filter(fecha=hoy)
        presentes_hoy = asistencias_hoy.filter(estado__in=['P', 'T', 'J']).count()
        porcentaje_asistencia = int((presentes_hoy / total_estudiantes * 100)) if total_estudiantes > 0 else 0

        alertas_inventario = CatalogoMaterial.objects.filter(
            Q(inventarios_aula__mal_estado__gt=0) | Q(inventarios_aula__se_requiere__gt=0),
            activo=True
        ).distinct().count()

        docentes_pendientes = Personal.objects.filter(
            cargo='DOC', estado='Activo', asignaciones__isnull=False
        ).exclude(asignaciones__evaluaciones__isnull=False).distinct()[:5]

        # ---------------------------------------------------------------------
        # 💥 CAPA DE CACHÉ PARA MOTOR DE CÁLCULO E IA HÍBRIDA
        # ---------------------------------------------------------------------
        cache_key = f"dashboard_pesado_{periodo_actual.id}"
        datos_pesados = cache.get(cache_key)

        # Si no hay datos en caché (o ya pasaron 15 minutos), el servidor hace la matemática
        if not datos_pesados:
            todas_las_aulas = Aula.objects.filter(asignaciones__periodo=periodo_actual).distinct()
            
            lista_global_alumnos = []
            total_optimos = 0
            total_esfuerzo = 0
            total_riesgo = 0
            total_sin_notas = 0

            sumas_por_bimestre = {'I': 0, 'II': 0, 'III': 0, 'IV': 0}
            conteo_por_bimestre = {'I': 0, 'II': 0, 'III': 0, 'IV': 0}
            bimestre_activo = periodo_actual.bimestre_actual if periodo_actual else 'I'

            for aula in todas_las_aulas:
                data_alumnos, _ = obtener_consolidado_aula_maestro(aula, periodo_actual)
                
                for mat_id, data in data_alumnos.items():
                    mat = data['matricula']
                    
                    puntajes_validos = [p for p in data['puntajes_bimestre'].values() if p is not None and p > 0]
                    puntaje_anual = sum(puntajes_validos)
                    
                    if puntaje_anual > 0:
                        mat.puntaje_total_exacto = puntaje_anual 
                        lista_global_alumnos.append(mat)

                    promedio_oficial_bim = data['promedios_bimestre'].get(bimestre_activo, 0)

                    diagnostico_ia = analizar_rendimiento_estudiante(
                        matricula_id=mat.id,
                        promedio_oficial=promedio_oficial_bim,
                        bimestre_actual=bimestre_activo,
                        usar_llm=False
                    )

                    color_ia = diagnostico_ia.get('color')
                    if color_ia == 'danger': total_riesgo += 1
                    elif color_ia in ['warning', 'secondary']: total_esfuerzo += 1
                    elif color_ia in ['success', 'info']: total_optimos += 1

                    for bim in ['I', 'II', 'III', 'IV']:
                        prom_bim = data['promedios_bimestre'].get(bim)
                        if prom_bim is not None and prom_bim > 0:
                            sumas_por_bimestre[bim] += prom_bim
                            conteo_por_bimestre[bim] += 1

            lista_global_alumnos.sort(key=lambda x: x.puntaje_total_exacto, reverse=True)
            mejores_alumnos = lista_global_alumnos[:5]
            total_esfuerzo += total_sin_notas

            labels_bimestres = ["Bimestre I", "Bimestre II", "Bimestre III", "Bimestre IV"]
            valores_bimestres = []
            
            for bim in ['I', 'II', 'III', 'IV']:
                if conteo_por_bimestre[bim] > 0:
                    promedio_real_colegio = sumas_por_bimestre[bim] / conteo_por_bimestre[bim]
                    valores_bimestres.append(float(round(promedio_real_colegio, 1)))
                else:
                    valores_bimestres.append(0.0)

            # Empaquetamos todo el resultado y lo guardamos en la memoria RAM del servidor
            datos_pesados = {
                'mejores_alumnos': mejores_alumnos,
                'total_optimos': total_optimos,
                'total_esfuerzo': total_esfuerzo,
                'total_riesgo': total_riesgo,
                'labels_bimestres': labels_bimestres,
                'valores_bimestres': valores_bimestres
            }
            # 💥 Almacenamos en caché por 900 segundos (15 minutos)
            cache.set(cache_key, datos_pesados, 900)


        # ---------------------------------------------------------------------
        # Gráficos dinámicos y Deltas
        # ---------------------------------------------------------------------
        dias_semana = []
        asistencias_semana = []
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        for i in range(5):
            dia_evaluar = inicio_semana + timedelta(days=i)
            dias_semana.append(dia_evaluar.strftime('%d/%m'))
            presentes = AsistenciaEstudiante.objects.filter(fecha=dia_evaluar, estado__in=['P', 'T', 'J']).count()
            asistencias_semana.append(presentes)

        hace_un_mes = hoy - timedelta(days=30)
        riesgo_mes_pasado = Estudiante.objects.filter(estado='Activo', fecha_registro__lt=hace_un_mes).annotate(
            prom_ant=Avg('matricula__notas__valor')
        ).filter(prom_ant__lt=11).count()
        
        # Leemos el valor de la caché de forma segura
        riesgo_actual = datos_pesados.get('total_riesgo', 0)
        delta_riesgo = riesgo_actual - riesgo_mes_pasado
        texto_delta = f"+{delta_riesgo}" if delta_riesgo >= 0 else f"{delta_riesgo}"

        # Inyectamos todo al contexto
        context.update({
            'rol': 'COORDINACION',
            'total_estudiantes': total_estudiantes,
            'total_docentes': total_docentes,
            'porcentaje_asistencia': porcentaje_asistencia,
            'alertas_inventario': alertas_inventario,
            'docentes_pendientes': docentes_pendientes,
            'dias_semana': dias_semana,
            'asistencias_semana': asistencias_semana,
            'texto_delta': texto_delta,
            **datos_pesados  # 💥 Desempaquetamos los datos de la caché directamente al contexto
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
        ).select_related('curso', 'aula').order_by(
            'curso__nombre',   # 1. Agrupa por curso (ej. todas las Matemáticas juntas)
            'aula__nivel',     # 2. Ordena por nivel (Primaria, luego Secundaria)
            'aula__grado',     # 3. Ordena por grado (1, 2, 3...)
            'aula__seccion'    # 4. Ordena alfabéticamente por sección (A, B, C...)
        )
        aulas_tutoria = Aula.objects.filter(tutor=user_personal)

        # 2. 💥 NUEVO: Desglose de Alumnos por Nivel (Solo los niveles que dicta)
        niveles_dicta = mis_cursos.order_by().values_list('aula__nivel', flat=True).distinct()
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
                
        # =========================================================
        # 💥 NUEVO: INTELIGENCIA DE DATOS PARA TUTORAS DE SECUNDARIA
        # =========================================================
        es_tutor_secundaria = user_personal.es_tutor_secundaria
        graficos_tutor = {}
        
        if es_tutor_secundaria and aulas_tutoria.exists():
            from django.db.models import Avg
            import json # Aseguramos la importación
            
            def calcular_metricas_aula(aulas_queryset):
                promedios = Matricula.objects.filter(
                    estudiante__estado='Activo', 
                    aula__in=aulas_queryset,
                    periodo=periodo_actual
                ).annotate(
                    promedio_general=Avg('notas__valor') 
                ).values_list('promedio_general', flat=True)

                r_critico, observacion, estable, sobresaliente = 0, 0, 0, 0
                for prom in promedios:
                    if prom is not None:
                        p = float(prom)
                        if p < 11: r_critico += 1
                        elif p < 14: observacion += 1
                        elif p < 17: estable += 1
                        else: sobresaliente += 1
                        
                cursos_stats = AsignacionAcademica.objects.filter(
                    aula__in=aulas_queryset, 
                    periodo=periodo_actual,
                    evaluaciones__notas__valor__isnull=False
                ).annotate(
                    promedio_curso=Avg('evaluaciones__notas__valor')
                ).distinct().order_by('promedio_curso')[:5]

                l_cursos, v_cursos = [], []
                for asig in cursos_stats:
                    if asig.promedio_curso:
                        l_cursos.append(asig.curso.nombre)
                        v_cursos.append(round(float(asig.promedio_curso), 1))
                    
                return {
                    'mapa': [r_critico, observacion, estable, sobresaliente],
                    'cursos': {'labels': l_cursos, 'data': v_cursos}
                }

            # 💥 Generamos solo los datos de cada aula individual
            for aula in aulas_tutoria:
                graficos_tutor[str(aula.id)] = calcular_metricas_aula(Aula.objects.filter(id=aula.id))
        
        context.update({
            'rol': 'DOCENTE',
            'es_tutor_secundaria': es_tutor_secundaria,
            'graficos_tutor_json': json.dumps(graficos_tutor) if graficos_tutor else "{}",
            'mis_cursos_lista': mis_cursos, # 💥 Enviamos los cursos para la nueva tarjeta
            'aulas_tutoria': aulas_tutoria,
            'mis_alumnos_count': mis_alumnos_count,
            'breakdown_alumnos': breakdown_alumnos, # 💥 Enviamos el desglose
            'ultimo_material': ultimo_material,
            'alerta_material': alerta_material,
            'notas_pendientes': notas_pendientes,
            'mejores_por_nivel': mejores_por_nivel,
        })

        return render(request, 'core/dashboard_docente.html', context)
    # =========================================================================
    # FLUJO C: VISTA OPERATIVA (SECRETARIA, ASISTENTE, AUXILIAR)
    # =========================================================================
    elif user_personal.cargo in ['SEC', 'ASI', 'AUX']:
        total_estudiantes = Estudiante.objects.filter(estado='Activo').count()
        
        asistencias_hoy = AsistenciaEstudiante.objects.filter(fecha=hoy)
        presentes_hoy = asistencias_hoy.filter(estado__in=['P', 'T', 'J']).count()
        porcentaje_asistencia = int((presentes_hoy / total_estudiantes * 100)) if total_estudiantes > 0 else 0

        # Trabajos de Imprenta (Vital para la Asistente)
        from apps.academico.models import SolicitudImpresion
        impresiones_pendientes = SolicitudImpresion.objects.filter(estado__in=['PENDIENTE', 'EN_PROCESO']).count()
        
        # Inventario de Aulas
        alertas_inventario = CatalogoMaterial.objects.filter(
            Q(inventarios_aula__mal_estado__gt=0) | Q(inventarios_aula__se_requiere__gt=0),
            activo=True
        ).distinct().count()

        context.update({
            'rol': 'OPERATIVO',
            'cargo_nombre': user_personal.get_cargo_display(),
            'total_estudiantes': total_estudiantes,
            'porcentaje_asistencia': porcentaje_asistencia,
            'impresiones_pendientes': impresiones_pendientes,
            'alertas_inventario': alertas_inventario,
        })
        return render(request, 'core/dashboard_admin.html', context)

    # =========================================================================
    # FLUJO D: VISTA MANTENIMIENTO (PERSONAL DE LIMPIEZA)
    # =========================================================================
    elif user_personal.cargo == 'LIM':
        alertas_inventario = CatalogoMaterial.objects.filter(
            Q(inventarios_aula__mal_estado__gt=0) | Q(inventarios_aula__se_requiere__gt=0),
            activo=True
        ).distinct().count()

        context.update({
            'rol': 'MANTENIMIENTO',
            'cargo_nombre': user_personal.get_cargo_display(),
            'alertas_inventario': alertas_inventario,
        })
        return render(request, 'core/dashboard_admin.html', context)

    # =========================================================================
    # RED DE SEGURIDAD (Obligatorio para evitar el Error 500)
    # =========================================================================
    else:
        return render(request, 'errores/sin_perfil.html', {
            'mensaje': f'El rol "{user_personal.get_cargo_display()}" no tiene un panel asignado.'
        })