/**
 * ARCHIVO: cronograma.js (Blindado y a prueba de errores)
 */

let calendarGlobal = null; 

// 💥 AUTO-DETECCIÓN 100% SEGURA: Sin usar jQuery para evitar errores de carga temprana
const esCoordinadorActivo = (typeof ES_COORDINADOR !== 'undefined') ? ES_COORDINADOR : (document.querySelectorAll('button[onclick="abrirModalEvento()"]').length > 0);

$(document).ready(function() {
    if ($('#tabla-horarios').length) {
        inicializarTablaGlobal('#tabla-horarios', 'Buscar clase o docente...');
    }
    // 💥 RETRASO ESTRATÉGICO: Le damos 150ms al navegador para que termine de pintar el HTML
    // Esto evita que el calendario se rinda y se quede invisible.
    setTimeout(inicializarCalendario, 150);
});

function inicializarCalendario() {
    let $calendarEl = $('#calendario-visual');
    if ($calendarEl.length === 0) return;

    let esMovil = $(window).width() < 768;

    calendarGlobal = new FullCalendar.Calendar($calendarEl[0], {
        locale: 'es', 
        initialView: esCoordinadorActivo ? 'dayGridMonth' : (esMovil ? 'listWeek' : 'timeGridWeek'),
        buttonText: { today: 'Hoy', month: 'Mes', week: 'Semana', list: 'Agenda' },
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek'
        },
        
        // 💥 MODO DEBUG ACTIVADO: Si Django falla o no envía los eventos, el calendario te avisará
        events: {
            url: '/academico/api/calendario/',
            failure: function() {
                mostrarErroresModal({'Conexión': ['Django no pudo cargar los eventos. Revisa tu consola del servidor.']});
            }
        },
        
        editable: esCoordinadorActivo, 
        selectable: esCoordinadorActivo,
        height: 'auto',

        // ==========================================
        // 📱 AJUSTES DE SENSIBILIDAD PARA MÓVILES
        // ==========================================
        longPressDelay: 200,       // Tiempo para considerar un toque como un "clic" general
        selectLongPressDelay: 200, // Tiempo para activar la selección de celdas vacías
        eventLongPressDelay: 200,  // Tiempo para poder arrastrar un evento existente

        // 💥 DISEÑO PREMIUM (Íconos + Negrita)
        eventContent: function(arg) {
            let esTodoElDia = arg.event.allDay;
            // Elegimos el ícono: Reloj si tiene hora, Agenda si es todo el día
            let icono = esTodoElDia ? 'event_note' : 'schedule'; 
            
            let html = `
                <div class="d-flex align-items-center p-1 w-100 overflow-hidden text-white ps-2">
                    <i class="material-symbols-rounded text-xs me-1 opacity-8" style="font-size: 14px;">${icono}</i>
                    <span class="text-xs font-weight-bold text-truncate" style="letter-spacing: 0.3px;">
                        ${arg.timeText ? arg.timeText + ' - ' : ''} ${arg.event.title}
                    </span>
                </div>
            `;
            return { html: html };
        },

        eventDrop: function(info) { actualizarMovimientoAgenda(info); },
        eventResize: function(info) { actualizarMovimientoAgenda(info); },
        
        eventClick: function(info) {
            abrirModalDetalleEvento(info.event);
        },
        select: function(info) {
            if (esCoordinadorActivo) {
                abrirModalCrearEvento(info); 
            }
        }
    });

    calendarGlobal.render();
}

// 💥 FUNCIÓN MAESTRA ASÍNCRONA PARA ACTUALIZACIÓN DE EVENTOS
function actualizarMovimientoAgenda(info) {
    const evento = info.event;
    let fInicioStr = evento.start.toISOString().split('T')[0];
    let fFinStr = evento.end ? evento.end.toISOString().split('T')[0] : fInicioStr;
    let hInicio = String(evento.start.getHours()).padStart(2, '0') + ':' + String(evento.start.getMinutes()).padStart(2, '0');
    let hFin = evento.end ? String(evento.end.getHours()).padStart(2, '0') + ':' + String(evento.end.getMinutes()).padStart(2, '0') : hInicio;

    $.ajax({
        url: '/academico/cronograma/evento/drag-drop/',
        type: 'POST',
        data: {
            evento_id: evento.extendedProps.db_id,
            fecha_inicio: fInicioStr,
            fecha_fin: fFinStr,
            hora_inicio: hInicio,
            hora_fin: hFin
        },
        success: function(data) {
            if (data.success) {
                mostrarNotificacionExito(data.mensaje || 'Agenda actualizada.');
            } else {
                mostrarErroresModal({'Agenda': [data.mensaje || 'Cruce de horarios detectado.']});
                info.revert(); 
            }
        },
        error: function() {
            mostrarErroresModal({'Servidor': ['Error de conexión. El evento se restaurará.']});
            info.revert();
        }
    });
}

// =======================================================
// 💥 CONTROL DE MODALES Y ACCIONES CRUD
// =======================================================

function abrirModalEvento() {
    let hoyStr = new Date().toISOString().split('T')[0];
    abrirModalCrearEvento({
        startStr: hoyStr,
        endStr: hoyStr,
        allDay: true
    });
}

function abrirModalCrearEvento(info) {
    $('#formEvento')[0].reset();
    $('#evento_id').val('');
    $('#id_fecha_inicio').val(info.startStr.split('T')[0]);
    
    let fechaFin = info.endStr ? info.endStr.split('T')[0] : info.startStr.split('T')[0];
    if (info.allDay && info.end) {
        let dateEnd = new Date(info.end);
        dateEnd.setDate(dateEnd.getDate() - 1);
        fechaFin = dateEnd.toISOString().split('T')[0];
    }
    $('#id_fecha_fin').val(fechaFin);
    
    if (!info.allDay && info.start && info.end) {
        let hInicio = String(info.start.getHours()).padStart(2, '0') + ':' + String(info.start.getMinutes()).padStart(2, '0');
        let hFin = String(info.end.getHours()).padStart(2, '0') + ':' + String(info.end.getMinutes()).padStart(2, '0');
        $('#id_hora_inicio').val(hInicio);
        $('#id_hora_fin').val(hFin);
        $('#div_bloque_horas').show();
    } else {
        $('#id_hora_inicio').val('');
        $('#id_hora_fin').val('');
        $('#div_bloque_horas').hide();
    }
    
    $('#modalEventoTitulo').text('Registrar Nuevo Evento');
    $('#btnEliminarEventoModal').hide();
    $('#modalEvento').modal('show');
}

function abrirModalDetalleEvento(evento) {
    let props = evento.extendedProps;
    if (esCoordinadorActivo) {
        $('#formEvento')[0].reset();
        $('#evento_id').val(props.db_id);
        $('#id_titulo').val(evento.title);
        $('#id_fecha_inicio').val(evento.startStr.split('T')[0]);
        
        let fechaFin = evento.endStr ? evento.endStr.split('T')[0] : evento.startStr.split('T')[0];
        if (evento.allDay && evento.end) {
            let dateEnd = new Date(evento.end);
            dateEnd.setDate(dateEnd.getDate() - 1);
            fechaFin = dateEnd.toISOString().split('T')[0];
        }
        $('#id_fecha_fin').val(fechaFin);
        
        if (!evento.allDay && evento.start && evento.end) {
            let hInicio = String(evento.start.getHours()).padStart(2, '0') + ':' + String(evento.start.getMinutes()).padStart(2, '0');
            let hFin = String(evento.end.getHours()).padStart(2, '0') + ':' + String(evento.end.getMinutes()).padStart(2, '0');
            $('#id_hora_inicio').val(hInicio);
            $('#id_hora_fin').val(hFin);
            $('#div_bloque_horas').show();
        } else {
            $('#id_hora_inicio').val('');
            $('#id_hora_fin').val('');
            $('#div_bloque_horas').hide();
        }
        
        if (props.color_raw) $('#id_color').val(props.color_raw);
        if (props.aula_afectada_id) $('#id_aula_afectada').val(props.aula_afectada_id);
        if (props.descripcion) $('#id_descripcion').val(props.descripcion);
        
        $('#modalEventoTitulo').text('Editar Evento');
        $('#btnEliminarEventoModal').show();
        $('#modalEvento').modal('show');
    } else {
        Swal.fire({
            title: evento.title,
            text: props.descripcion || 'Sin indicaciones adicionales.',
            icon: 'info',
            confirmButtonColor: '#333333'
        });
    }
}

function guardarEvento() {
    const form = document.getElementById('formEvento');
    if (!form.checkValidity()) { form.reportValidity(); return; }

    $.ajax({
        url: '/academico/cronograma/evento/guardar/', 
        type: 'POST',
        data: $('#formEvento').serialize(),
        success: function(data) {
            if (data.success) {
                $('#modalEvento').modal('hide');
                calendarGlobal.refetchEvents(); 
                mostrarNotificacionExito(data.mensaje || 'Evento guardado correctamente.');
            } else {
                mostrarErroresModal({'Error': [data.mensaje || 'No se pudo guardar el evento.']});
            }
        },
        error: function() {
            mostrarErroresModal({'Servidor': ['Fallo de comunicación con el servidor.']});
        }
    });
}

function ejecutarEliminacionDesdeModal() {
    let id = $('#evento_id').val();
    if (!id) return;

    Swal.fire({
        title: '¿Eliminar Evento?',
        text: "Desaparecerá permanentemente de la agenda de todos.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#333333',  
        cancelButtonColor: '#f57c00',   
        confirmButtonText: 'Sí, borrar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: '/academico/cronograma/evento/eliminar/' + id + '/',
                type: 'POST',
                success: function(data) {
                    if (data.success) {
                        $('#modalEvento').modal('hide');
                        calendarGlobal.refetchEvents(); 
                        mostrarNotificacionExito(data.mensaje || 'Evento eliminado con éxito.');
                    } else {
                        mostrarErroresModal({'Error': [data.mensaje || 'No se pudo eliminar.']});
                    }
                },
                error: function() {
                    mostrarErroresModal({'Servidor': ['Fallo de red al intentar eliminar.']});
                }
            });
        }
    });
}

// 💥 FUNCIÓN RESTAURADA: Evita que el botón de Guardar Horario arroje un error
function guardarHorario(event) {
    event.preventDefault();
    $.ajax({
        url: '/academico/cronograma/horario/guardar/', 
        type: 'POST',
        data: $('#formHorario').serialize(),
        success: function(data) {
            if (data.success) {
                $('#modalHorario').modal('hide');
                mostrarNotificacionExito('Horario asignado exitosamente.');
            } else {
                mostrarErroresModal({'Error': [data.mensaje || 'No se pudo asignar el horario.']});
            }
        }
    });
}