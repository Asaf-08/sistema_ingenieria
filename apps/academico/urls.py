from django.urls import path
from . import views

app_name = 'academico'

urlpatterns = [
    
    # ==========================================
    # 📚 MÓDULO DE ESTUDIANTES
    # ==========================================
    path('estudiantes/', views.lista_estudiantes, name='lista_estudiantes'),
    path('estudiantes/nuevo/', views.crear_estudiante, name='crear_estudiante'),
    path('estudiantes/editar/<int:pk>/', views.editar_estudiante, name='editar_estudiante'),
    path('estudiantes/eliminar/<int:pk>/', views.eliminar_estudiante_ajax, name='eliminar_estudiante_ajax'),
    path('estudiantes/cambiar-estado/<int:pk>/', views.cambiar_estado_estudiante_ajax, name='cambiar_estado_estudiante_ajax'),
    
    # ==========================================
    # 🏫 MÓDULO DE AULAS
    # ==========================================
    path('aulas/', views.lista_aulas, name='lista_aulas'),
    path('aulas/nueva/', views.crear_aula, name='crear_aula'),
    path('aulas/guardar/', views.guardar_aula_ajax, name='guardar_aula_ajax'),
    path('aulas/datos/<int:pk>/', views.obtener_aula_data, name='obtener_aula_data'),
    path('aulas/eliminar/<int:pk>/', views.eliminar_aula_ajax, name='eliminar_aula_ajax'),
    
    # ==========================================
    # 📅 MÓDULO DE PERIODOS LECTIVOS
    # ==========================================
    path('periodos/', views.lista_periodos, name='lista_periodos'),
    path('periodos/guardar/', views.guardar_periodo_ajax, name='guardar_periodo_ajax'),
    path('periodos/datos/<int:pk>/', views.obtener_periodo_data, name='obtener_periodo_data'),
    path('periodos/eliminar/<int:pk>/', views.eliminar_periodo_ajax, name='eliminar_periodo_ajax'),
    
    # ==========================================
    # 📖 MÓDULO DE CURSOS
    # ==========================================
    path('cursos/', views.lista_cursos, name='lista_cursos'),
    path('cursos/guardar/', views.guardar_curso_ajax, name='guardar_curso_ajax'),
    path('cursos/datos/<int:pk>/', views.obtener_curso_data, name='obtener_curso_data'),
    path('cursos/eliminar/<int:pk>/', views.eliminar_curso_ajax, name='eliminar_curso_ajax'),
    
    # ==========================================
    # 👨‍🏫 MÓDULO DE ASIGNACIONES (CARGA ACADÉMICA)
    # ==========================================
    path('asignaciones/', views.lista_asignaciones, name='lista_asignaciones'),
    path('asignaciones/guardar/', views.guardar_asignacion_ajax, name='guardar_asignacion_ajax'),
    path('asignaciones/datos/<int:pk>/', views.obtener_asignacion_data, name='obtener_asignacion_data'),
    path('asignaciones/eliminar/<int:pk>/', views.eliminar_asignacion_ajax, name='eliminar_asignacion_ajax'),
    
    # ==========================================
    # 📝 MÓDULO DE MATRÍCULAS
    # ==========================================
    path('matriculas/', views.lista_matriculas, name='lista_matriculas'),
    path('matriculas/masiva/', views.matricula_masiva, name='matricula_masiva'),
    path('matriculas/masiva/procesar/', views.procesar_matricula_masiva, name='procesar_matricula_masiva'),
    path('matriculas/eliminar/<int:pk>/', views.eliminar_matricula_ajax, name='eliminar_matricula_ajax'),
    
    # ==========================================
    # 🖨️ MÓDULO DE IMPRENTA Y SUPERVISIÓN
    # ==========================================
    path('imprenta/', views.panel_asistente_imprenta, name='panel_imprenta'),
    path('imprenta/actualizar/<int:solicitud_id>/', views.actualizar_estado_impresion, name='actualizar_estado_impresion'),
    path('obtener-archivos/<int:solicitud_id>/', views.obtener_archivos_solicitud, name='obtener_archivos'),
    
    path('supervision/', views.panel_supervision, name='panel_supervision'),
    path('supervision/material/guardar/', views.guardar_material_ajax, name='guardar_material_ajax'),
    path('supervision/material/eliminar/<int:pk>/', views.eliminar_material_ajax, name='eliminar_material_ajax'),
    path('supervision/evidencia/guardar/', views.guardar_evidencia_ajax, name='guardar_evidencia_ajax'),
    path('supervision/evidencia/revisar/', views.revisar_evidencia_ajax, name='revisar_evidencia_ajax'),
    path('supervision/auditoria-materiales/<int:asignacion_id>/', views.auditoria_materiales_ajax, name='auditoria_materiales_ajax'),
    
    # ==========================================
    # 🧠 MÓDULO DE TUTORÍA E INTELIGENCIA ARTIFICIAL
    # ==========================================
    path('tutor/mi-aula/', views.mi_aula, name='mi_aula'),
    path('matriculas/reporte-progresivo/<int:matricula_id>/', views.reporte_progresivo_pdf, name='reporte_progresivo'),
    
    path('api/diagnostico-ia/', views.generar_diagnostico_ajax, name='api_diagnostico_ia'),
    path('api/clustering-ia/', views.generar_clustering_ia_api, name='api_clustering_ia'),
    path('ajax/generar-recomendacion-ia/', views.generar_recomendacion_ajax, name='generar_recomendacion_ia'),
    
    # ==========================================
    # 🕒 MÓDULO DE TIEMPOS Y CRONOGRAMA DINÁMICO
    # ==========================================
    path('cronograma/', views.panel_cronograma, name='panel_cronograma'),
    path('cronograma/evento/guardar/', views.guardar_evento_ajax, name='guardar_evento_ajax'),
    path('cronograma/evento/eliminar/<int:pk>/', views.eliminar_evento_ajax, name='eliminar_evento_ajax'),
    path('cronograma/evento/drag-drop/', views.actualizar_evento_drag_ajax, name='actualizar_evento_drag'),
    path('api/calendario/', views.api_calendario_eventos, name='api_calendario'),
    
    # ==========================================
    # 🗓️ MÓDULO DE HORARIO ESCOLAR MAESTRO
    # ==========================================
    path('horario-maestro/', views.horario_maestro, name='horario_maestro'),
    path('horario/aula/<int:aula_id>/', views.gestionar_horario_aula, name='gestionar_horario_aula'),
    path('horario/exportar/excel/', views.exportar_horario_excel, name='exportar_horario_excel'),
    path('horario/recreo/guardar/', views.guardar_recreo_ajax, name='guardar_recreo_ajax'),
    
    path('cronograma/horario/guardar/', views.guardar_horario_ajax, name='guardar_horario_ajax'),
    path('cronograma/horario/eliminar/<int:pk>/', views.eliminar_horario_ajax, name='eliminar_horario_ajax'),
    
    path('api/horario-fijo/', views.api_horario_fijo, name='api_horario_fijo'),
    path('api/horario/drag-drop/', views.actualizar_horario_drag_ajax, name='actualizar_horario_drag'),
    path('api/horario/recreo/<str:nivel>/', views.obtener_recreo_nivel_ajax, name='obtener_recreo_nivel_ajax'),
    path('api/cursos-docente/<int:docente_id>/', views.api_cursos_docente, name='api_cursos_docente'),
    
    path('api/horario/clonar/', views.clonar_horario_ajax, name='clonar_horario_ajax'),
    
    # ==========================================
    # 📦 MÓDULO DE INVENTARIO Y LOGÍSTICA
    # ==========================================
    path('inventario/general/', views.inventario_general, name='inventario_general'),
    path('inventario/aula/<int:aula_id>/', views.gestionar_inventario_aula, name='gestionar_inventario_aula'),
    path('inventario/exportar/excel/', views.exportar_inventario_excel, name='exportar_inventario_excel'),
    
    path('inventario/catalogo/guardar/', views.guardar_material_ajax, name='guardar_material_ajax'),
    path('inventario/catalogo/eliminar/', views.eliminar_material_ajax, name='eliminar_material_ajax'),
    path('api/inventario/general/', views.api_inventario_general, name='api_inventario_general'),
    
    # ==========================================
    # 📋 MÓDULO DE SIMULACROS
    # ==========================================
    path('simulacros/', views.lista_simulacros, name='lista_simulacros'),
    path('simulacros/guardar/', views.guardar_simulacro_ajax, name='guardar_simulacro'),
    path('simulacros/datos/<int:pk>/', views.datos_simulacro_ajax, name='datos_simulacro'),
    path('simulacros/exportar/<int:simulacro_id>/', views.exportar_simulacro_word, name='exportar_simulacro'),
    path('simulacros/monitoreo/<int:simulacro_id>/', views.monitoreo_simulacro, name='monitoreo_simulacro'),
    
    path('simulacros/finalizar-curso/', views.finalizar_envio_curso_ajax, name='finalizar_envio_curso'),
    path('simulacros/reabrir-curso/', views.reabrir_envio_curso_ajax, name='reabrir_envio_curso'),
    
    # Rutas para el Docente
    path('mis-simulacros/', views.mis_simulacros_docente, name='mis_simulacros_docente'),
    path('mis-simulacros/cargar/<int:simulacro_id>/', views.cargar_preguntas_simulacro, name='cargar_preguntas_simulacro'),
    path('simulacros/pregunta/datos/<int:pk>/', views.datos_pregunta_ajax, name='datos_pregunta'),
    path('simulacros/pregunta/eliminar/<int:pregunta_id>/', views.eliminar_pregunta_simulacro, name='eliminar_pregunta_simulacro'),
    
    # ==========================================
    # ⚙️ CONFIGURACIÓN INSTITUCIONAL
    # ==========================================
    path('configuracion/', views.configuracion_institucion, name='configuracion'),
    path('api/pausar-alertas/', views.pausar_alertas_ajax, name='pausar_alertas_ajax'),
]