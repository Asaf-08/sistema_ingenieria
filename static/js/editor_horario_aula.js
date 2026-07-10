/**
 * ARCHIVO: editor_horario_aula.js
 * DESCRIPCIÓN: Controlador dinámico con Drag & Drop completo para armar el horario de un aula seleccionada.
 */

let calendarEditor = null;
const CODIGOS_DIAS = { 1: 'LU', 2: 'MA', 3: 'MI', 4: 'JU', 5: 'VI' };

$(document).ready(function() {
    inicializarCalendarioEditor();

    // Si cambia el periodo lectivo de trabajo, refrescamos los bloques del aula
    $('#periodoTrabajo').on('change', function() {
        if (calendarEditor) calendarEditor.refetchEvents();
    });

    // 💥 LÓGICA DE FILTRO DINÁMICO: Cargar cursos según docente
    $('#id_personal').on('change', function(event, idCursoPreseleccionado) {
        let docenteId = $(this).val();
        let $selectCurso = $('#id_curso');
        
        $selectCurso.empty().append('<option value="">Cargando asignaturas...</option>');
        
        if (docenteId) {
            $.get(`/academico/api/cursos-docente/${docenteId}/`, function(data) {
                $selectCurso.empty().append('<option value="">-- Seleccione una Asignatura --</option>');
                data.forEach(c => {
                    $selectCurso.append(`<option value="${c.id}">${c.nombre}</option>`);
                });
                
                // Si venimos de editar, auto-seleccionamos el curso
                if (idCursoPreseleccionado) {
                    $selectCurso.val(idCursoPreseleccionado);
                }
            });
        } else {
            $selectCurso.empty().append('<option value="">-- Elija un Docente Primero --</option>');
        }
    });
});

function inicializarCalendarioEditor() {
    let $calendarEl = $('#calendar-editor-aula');
    if ($calendarEl.length === 0) return;

    calendarEditor = new FullCalendar.Calendar($calendarEl[0], {
        locale: 'es',
        initialView: 'timeGridWeek',
        initialDate: '2024-01-01', // Semana ficticia ancla para permitir edición fluida
        
        headerToolbar: false,
        allDaySlot: false,
        hiddenDays: [0, 6], // Lunes a Viernes únicamente
        dayHeaderFormat: { weekday: 'long' },
        
        // 💥 ESPECIFICACIONES DE HORARIO SOLICITADAS
        slotMinTime: '08:00:00',
        slotMaxTime: '14:30:00',
        slotLabelFormat: { hour: 'numeric', minute: '2-digit', meridiem: 'short', hour12: true },
        eventTimeFormat: { hour: 'numeric', minute: '2-digit', meridiem: 'short', hour12: true },

        // Habilitar interactividad total de fábrica
        selectable: true,
        editable: true,
        selectMirror: true,

        // ==========================================
        // 📱 AJUSTES DE SENSIBILIDAD PARA MÓVILES
        // ==========================================
        longPressDelay: 200,       // Tiempo para considerar un toque como un "clic" general
        selectLongPressDelay: 200, // Tiempo para activar la selección de celdas vacías
        eventLongPressDelay: 200,  // Tiempo para poder arrastrar un evento existente

        // 💥 CONTROL DEL ALTO: Ajuste exacto para que se corte en la última hora (18:00)
        height: 'auto', // Esto obliga a las celdas a tener el alto exacto de sus slots sin estirarse abajo
        contentHeight: 'auto',

        // Cargar clases exclusivas de esta aula y periodo
        events: function(info, successCallback, failureCallback) {
            $.ajax({
                url: '/academico/api/horario-fijo/',
                data: {
                    aula_id: AULA_ID,
                    periodo_id: $('#periodoTrabajo').val()
                },
                success: function(data) { successCallback(data); },
                error: function() { failureCallback(); }
            });
        },

        // ==========================================
        // ACCIÓN 1: ARRASTRAR MOUSE PARA CREAR BLOQUE
        // ==========================================
        select: function(info) {
            $('#formAsignarClase')[0].reset();
            $('#horario_id').val('');
            $('#btnEliminarClaseEditor').hide();

            // Setear variables contextuales ocultas de forma automática
            $('#id_periodo_fijo').val($('#periodoTrabajo').val());
            $('#id_dia_semana_fijo').val(CODIGOS_DIAS[info.start.getDay()]);

            let hInicio = String(info.start.getHours()).padStart(2, '0') + ':' + String(info.start.getMinutes()).padStart(2, '0');
            let hFin = String(info.end.getHours()).padStart(2, '0') + ':' + String(info.end.getMinutes()).padStart(2, '0');

            $('#id_hora_inicio_e').val(hInicio);
            $('#id_hora_fin_e').val(hFin);

            $('#tituloModalEditor').text('Asignar Clase a este Bloque');
            $('#modalAsignarClase').modal('show');
            calendarEditor.unselect();
        },

        // ==========================================
        // ACCIÓN 2: MOVER O CAMBIAR TAMAÑO (DRAG / RESIZE)
        // ==========================================
        // 💥 Solo debes mapearlos así:
        eventDrop: function(info) {
            actualizarMovimientoHorario(info);
        },
        eventResize: function(info) {
            actualizarMovimientoHorario(info);
        },

        // ==========================================
        // ACCIÓN 3: ENTRAR A EDITAR UN BLOQUE EXISTENTE
        // ==========================================
        eventClick: function(info) {
            let props = info.event.extendedProps;
            $('#formAsignarClase')[0].reset();
            
            $('#horario_id').val(props.db_id);
            $('#id_periodo_fijo').val($('#periodoTrabajo').val());
            $('#id_dia_semana_fijo').val(props.dia_semana);
            
            // 💥 AUTO-ASIGNACIÓN CON EVENTO CASCADA
            // Ponemos el docente y disparamos el 'change' pasando el ID del curso como parámetro extra
            $('#id_personal').val(props.personal_id).trigger('change', [props.curso_id]);
            
            // Auto-asignamos el color
            if(props.color_raw) $('#id_color').val(props.color_raw);

            let hInicio = String(info.event.start.getHours()).padStart(2, '0') + ':' + String(info.event.start.getMinutes()).padStart(2, '0');
            let hFin = String(info.event.end.getHours()).padStart(2, '0') + ':' + String(info.event.end.getMinutes()).padStart(2, '0');

            $('#id_hora_inicio_e').val(hInicio);
            $('#id_hora_fin_e').val(hFin);

            $('#btnEliminarClaseEditor').show();
            $('#tituloModalEditor').text('Modificar Bloque Académico');
            $('#modalAsignarClase').modal('show');
        },

        // ==========================================
        // RENDERS: SOLUCIÓN AL BUG DEL RECUADRO VACÍO
        // ==========================================
        eventContent: function(arg) {
            let props = arg.event.extendedProps;
            let $div = $('<div>').addClass('p-1 w-100 text-center text-white d-flex flex-column justify-content-center h-100');
            
            if (!props.db_id) {
                $div.addClass('bg-dark border-radius-sm');
                $div.append($('<b>').addClass('text-xs').text(arg.timeText)); // 💥 Imprime Horario del fantasma
                return { domNodes: [$div[0]] };
            }

            // 💥 Imprime Horario, Curso y Docente de los reales
            $div.append($('<b>').addClass('text-xs mb-1 opacity-8').text(arg.timeText));
            $div.append($('<span>').addClass('text-sm font-weight-bold').text(props.curso));
            $div.append($('<span>').addClass('text-xxs').text(props.docente));
            return { domNodes: [$div[0]] };
        }
    });

    calendarEditor.render();
}

// ============================================================
// TRANSACCIONES ASÍNCRONAS AJAX (CRUD EN CALIENTE)
// ============================================================

async function procesarCambioTiempoDrag(info) {
    let evento = info.event;
    let db_id = evento.extendedProps.db_id;
    let nuevoDia = CODIGOS_DIAS[evento.start.getDay()];
    
    let nuevaHoraInicio = String(evento.start.getHours()).padStart(2, '0') + ':' + String(evento.start.getMinutes()).padStart(2, '0');
    let nuevaHoraFin = String(evento.end.getHours()).padStart(2, '0') + ':' + String(evento.end.getMinutes()).padStart(2, '0');

    let formData = new FormData();
    formData.append('horario_id', db_id);
    formData.append('dia_semana', nuevoDia);
    formData.append('hora_inicio', nuevaHoraInicio);
    formData.append('hora_fin', nuevaHoraFin);
    formData.append('csrfmiddlewaretoken', $('input[name=csrfmiddlewaretoken]').val());

    try {
        const response = await fetch('/academico/api/horario/drag-drop/', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await response.json();

        if (data.success) {
            mostrarNotificacionExito('Bloque reubicado con éxito.');
        } else {
            Swal.fire('Conflicto de Horario', data.mensaje, 'warning');
            info.revert(); // Rebota el bloque a su sitio original si colisiona con otro profesor
        }
    } catch (e) {
        Swal.fire('Error', 'Fallo de comunicación con el servidor.', 'error');
        info.revert();
    }
}

function guardarBloqueClaseEditor() {
    // 💥 Validación rápida para evitar enviar basura a la base de datos
    if (!$('#id_curso').val() || !$('#id_personal').val()) {
        mostrarErroresModal({'Faltan Datos': ['Por favor, selecciona un docente y un curso.']});
        return;
    }

    $.ajax({
        url: '/academico/cronograma/horario/guardar/',
        type: 'POST',
        data: $('#formAsignarClase').serialize(),
        success: function(data) {
            if (data.success) {
                $('#modalAsignarClase').modal('hide');
                calendarEditor.refetchEvents(); // Magia de FullCalendar
                mostrarNotificacionExito(data.mensaje || 'Bloque guardado con éxito.');
            } else {
                mostrarErroresModal(data.errors || {'Error': [data.mensaje || 'No se pudo guardar el bloque.']});
            }
        },
        error: function() {
            mostrarErroresModal({'Servidor': ['Error de red al intentar guardar la clase.']});
        }
    });
}

function eliminarBloqueClase() {
    let id = $('#horario_id').val();
    if (!id) return;

    Swal.fire({
        title: '¿Eliminar bloque?',
        text: 'Esta clase desaparecerá del horario de los alumnos. ¡No se puede deshacer!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#333333',
        cancelButtonColor: '#f57c00',
        confirmButtonText: 'Sí, borrar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: `/academico/cronograma/horario/eliminar/${id}/`,
                type: 'POST',
                // El token ya NO se envía aquí porque main.js lo inyecta por ti
                success: function(data) {
                    if (data.success) {
                        $('#modalAsignarClase').modal('hide');
                        calendarEditor.refetchEvents();
                        mostrarNotificacionExito(data.mensaje || 'Bloque eliminado correctamente.');
                    } else {
                        mostrarErroresModal({'Error': [data.mensaje || 'No se pudo eliminar el bloque.']});
                    }
                },
                error: function() {
                    mostrarErroresModal({'Servidor': ['Fallo de comunicación con el servidor.']});
                }
            });
        }
    });
}

// 💥 FUNCIÓN MAESTRA UNIFICADA PARA DRAG & DROP Y RESIZE (DRY)
function actualizarMovimientoHorario(info) {
    const event = info.event;
    
    // 1. Obtener el código del día (1 = LU, 2 = MA, etc.) usando tu diccionario existente
    const numeroDia = event.start.getDay();
    const codigoDia = CODIGOS_DIAS[numeroDia];
    
    // 2. Formatear las horas al formato HH:MM que espera Django
    const horaInicio = event.start.toTimeString().split(' ')[0].substring(0, 5);
    const horaFin = event.end ? event.end.toTimeString().split(' ')[0].substring(0, 5) : '';

    // 3. Petición asíncrona limpia
    $.ajax({
        url: '/academico/api/horario/drag-drop/',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            id: event.id,
            dia_semana: codigoDia,
            hora_inicio: horaInicio,
            hora_fin: horaFin
        }),
        success: function(data) {
            if (data.success) {
                mostrarNotificacionExito(data.mensaje || 'Horario actualizado en tiempo real.');
            } else {
                mostrarErroresModal({'Conflicto de Horario': [data.mensaje || 'No se pudo mover la clase.']});
                info.revert(); // 💥 REVERSIÓN AUTOMÁTICA: Si el backend rechaza (ej: cruce de profesor), la clase regresa a su sitio
            }
        },
        error: function() {
            mostrarErroresModal({'Servidor': ['Fallo de conexión. El cambio se revertirá.']});
            info.revert(); // Revierte si el servidor se cae
        }
    });
}