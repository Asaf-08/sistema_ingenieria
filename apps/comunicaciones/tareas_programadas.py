from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.utils import timezone
from datetime import timedelta

from apps.academico.models import Aula, Matricula, PeriodoLectivo, SolicitudImpresion
from apps.academico.servicios_ia import analizar_rendimiento_estudiante
from apps.comunicaciones.servicios_whatsapp import WhatsAppService
from apps.personal.models import Personal

import time
import random

def reporte_semanal_tutores():
    print(f"[{timezone.now()}] 🤖 RELOJ IA: Analizando rendimiento de alumnos para tutores...")
    
    # 1. Verificamos si estamos en modo "Pausar Notificaciones" (Feriados)
    periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
    if periodo_actual and periodo_actual.pausar_notificaciones:
        print("⏸️ SISTEMA PAUSADO: No se enviarán reportes de tutores esta semana.")
        return

    # 2. 💥 OPTIMIZACIÓN: select_related para traer los datos del tutor de un solo golpe
    aulas_con_tutor = Aula.objects.filter(tutor__isnull=False).select_related('tutor')
    
    for aula in aulas_con_tutor:
        tutor = aula.tutor
        if not tutor.telefono:
            continue 
            
        # 3. Buscamos a los alumnos activos de esta aula
        matriculas = Matricula.objects.filter(
            aula=aula, 
            estudiante__estado='Activo', 
            periodo=periodo_actual
        )
        
        alumnos_en_riesgo = 0
        
        # 4. AQUÍ ENTRA TU INTELIGENCIA ARTIFICIAL
        for mat in matriculas:
            analisis = analizar_rendimiento_estudiante(mat.id)
            if analisis['estado_ia'] in ["Riesgo Crítico", "Atención Requerida"]:
                alumnos_en_riesgo += 1
                
        # 5. Enviamos el mensaje correspondiente
        nombre_tutor = tutor.nombres.split()[0]
        
        if alumnos_en_riesgo > 0:
            WhatsAppService.alerta_tutor_riesgo(
                nombre_tutor, tutor.telefono, aula.grado, aula.seccion, alumnos_en_riesgo
            )
        else:
            WhatsAppService.alerta_tutor_exito(
                nombre_tutor, tutor.telefono, aula.grado, aula.seccion
            )
            
        print(f"✅ Análisis y reporte enviado al tutor: {nombre_tutor}")
        
        # 💥 MAGIA ANTI-BANEO
        pausa = random.randint(3, 7)
        time.sleep(pausa)

def revisar_materiales_faltantes():
    print(f"[{timezone.now()}] 🤖 RELOJ: Revisando qué profesores no han enviado materiales...")
    
    periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
    if periodo_actual and periodo_actual.pausar_notificaciones:
        print("⏸️ SISTEMA PAUSADO: El robot no enviará mensajes hoy.")
        return  
    
    hoy = timezone.now()
    lunes_semana = hoy - timedelta(days=hoy.weekday())
    lunes_semana = lunes_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    
    docentes_cumplidos_ids = SolicitudImpresion.objects.filter(
        fecha_subida__gte=lunes_semana
    ).values_list('personal_id', flat=True).distinct()
    
    docentes_faltantes = Personal.objects.filter(
        cargo='DOC', 
        estado='Activo',
        asignaciones__isnull=False 
    ).exclude(id__in=docentes_cumplidos_ids).distinct()
    
    for docente in docentes_faltantes:
        if docente.telefono:
            nombre = docente.nombres.split()[0]
            WhatsAppService.notificar_falta_material(
                nombre_docente=nombre,
                telefono_docente=docente.telefono
            )
            print(f"✅ Recordatorio de material enviado a: {nombre}")
            
            pausa = random.randint(4, 8)
            time.sleep(pausa)

def iniciar_reloj():
    scheduler = BackgroundScheduler()
    
    # ⏰ Recordatorio 1: Miércoles a las 6:00 PM (18:00)
    scheduler.add_job(
        revisar_materiales_faltantes,
        trigger=CronTrigger(day_of_week='wed', hour=18, minute=0),
        id='alerta_materiales_miercoles',
        replace_existing=True
    )
    
    # ⏰ Recordatorio 2: Jueves a las 8:00 AM (08:00)
    scheduler.add_job(
        revisar_materiales_faltantes,
        trigger=CronTrigger(day_of_week='thu', hour=8, minute=0),
        id='alerta_materiales_jueves',
        replace_existing=True
    )
    
    # 💥 CORRECCIÓN (EL BUG RESUELTO): Reporte de IA para Tutores: Viernes a las 3:00 PM (15:00)
    scheduler.add_job(
        reporte_semanal_tutores,
        trigger=CronTrigger(day_of_week='fri', hour=15, minute=0),
        id='alerta_ia_tutores_viernes',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Motor de Tareas Automáticas (APScheduler) INICIADO.")