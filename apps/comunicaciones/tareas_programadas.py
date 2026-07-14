from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.utils import timezone
from datetime import timedelta

from apps.academico.models import ArchivoMaterial, Aula, EntregaSimulacro, Matricula, PeriodoLectivo, SolicitudImpresion, EventoCronograma
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
    print(f"[{timezone.now()}] 🤖 RELOJ PREDICTIVO: Analizando fechas del Cronograma Institucional...")
    
    periodo_actual = PeriodoLectivo.objects.filter(activo=True).first()
    if periodo_actual and periodo_actual.pausar_notificaciones:
        print("⏸️ SISTEMA PAUSADO.")
        return  
    
    # Usamos localdate() para tener la fecha exacta según tu zona horaria
    hoy = timezone.localdate()
    
    # 💥 LA MAGIA PREDICTIVA: Buscamos hitos que empiecen exactamente en 3 días o mañana (1 día)
    dias_alerta = [1, 3] 
    fechas_objetivo = [hoy + timedelta(days=d) for d in dias_alerta]
    
    eventos_proximos = EventoCronograma.objects.exclude(tipo_academico='NINGUNO').filter(
        fecha_inicio__in=fechas_objetivo
    )
    
    if not eventos_proximos.exists():
        print("✅ No hay fechas límite críticas cercanas (1 o 3 días). El robot descansa hoy.")
        return

    # Si hay un evento que está por vencer, procesamos la auditoría
    for evento in eventos_proximos:
        dias_faltantes = (evento.fecha_inicio - hoy).days
        print(f"⚠️ ALERTA: '{evento.get_tipo_academico_display()}' empieza en {dias_faltantes} días.")
        
        # 1. Base: Todos los docentes que dictan clases este año
        docentes_activos = Personal.objects.filter(
            cargo='DOC', estado='Activo', asignaciones__periodo=periodo_actual
        ).distinct()
        
        docentes_cumplidos_ids = set()
        
        # 2. LÓGICA DE AUDITORÍA CRUZADA (Detecta Tema, Examen o Simulacro)
        if evento.tipo_academico.startswith('TEMA_'):
            # Cumplió si envió una Solicitud de Impresión con ese tema exacto
            docentes_cumplidos_ids = set(SolicitudImpresion.objects.filter(
                tema=evento.tipo_academico,
                asignacion__periodo=periodo_actual
            ).values_list('personal_id', flat=True))
            
        elif evento.tipo_academico in ['CALIDAD', 'ISO']:
            # Cumplió si subió un ArchivoMaterial de ese tipo
            docentes_cumplidos_ids = set(ArchivoMaterial.objects.filter(
                tipo=evento.tipo_academico,
                solicitud__asignacion__periodo=periodo_actual
            ).values_list('solicitud__personal_id', flat=True))
            
        elif evento.tipo_academico == 'SIMULACRO':
            # Cumplió si finalizó su Entrega de Simulacro
            docentes_cumplidos_ids = set(EntregaSimulacro.objects.filter(
                finalizado=True
            ).values_list('docente_id', flat=True))

        # 3. Resta de Conjuntos: Los activos menos los que ya cumplieron = FALTANTES
        docentes_faltantes = docentes_activos.exclude(id__in=docentes_cumplidos_ids)
        
        for docente in docentes_faltantes:
            if docente.telefono:
                nombre = docente.nombres.split()[0]
                
                # Disparamos la alerta predictiva a WhatsApp
                WhatsAppService.alerta_dinamica_cronograma(
                    nombre_docente=nombre,
                    telefono_docente=docente.telefono,
                    nombre_evento=evento.get_tipo_academico_display(),
                    dias_faltantes=dias_faltantes
                )
                print(f"   ✉️ Aviso de {evento.tipo_academico} enviado a: {nombre}")
                
                # Magia Anti-Baneo
                time.sleep(random.randint(4, 8))

def iniciar_reloj():
    scheduler = BackgroundScheduler()
    
    # 💥 NUEVO TRIGGER: En lugar de buscar los "miércoles", lo ponemos TODOS LOS DÍAS a las 8:00 AM.
    # Como la función adentro ya filtra para solo alertar si "faltan 3 días" o "falta 1 día", nunca hará Spam.
    scheduler.add_job(
        revisar_materiales_faltantes,
        trigger=CronTrigger(hour=8, minute=0),
        id='alerta_dinamica_materiales',
        replace_existing=True
    )
    
    # Tu reporte de IA de Tutores se queda intacto los viernes
    scheduler.add_job(
        reporte_semanal_tutores,
        trigger=CronTrigger(day_of_week='fri', hour=15, minute=0),
        id='alerta_ia_tutores_viernes',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Motor Predictivo de Tareas Automáticas (APScheduler) INICIADO.")