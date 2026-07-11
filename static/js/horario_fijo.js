let calendarHorario = null;
let modoEdicionActivo = false;

// 💥 DICCIONARIO DE LA SEMANA ANCLA
const DIAS_ANCLA = { 1: 'LU', 2: 'MA', 3: 'MI', 4: 'JU', 5: 'VI' };

$(document).ready(function() {
    inicializarCalendarioHorario();

    // Comportamiento inteligente de filtros cruzados
    $('#filtroDocente').on('change', function() {
        if ($(this).val() !== "") {
            // Si busca por docente, deshabilitamos el aula para evitar distorsión
            $('#filtroAula').prop('disabled', true).css('opacity', '0.5');
        } else {
            $('#filtroAula').prop('disabled', false).css('opacity', '1');
        }
        calendarHorario.refetchEvents();
    });

    $('#filtroAula, #filtroPeriodo').on('change', function() {
        calendarHorario.refetchEvents();
    });

    // 💥 DETECTOR: Detecta cuando la coordinadora cambia el nivel en el modal de recreos
    $('#modalConfigurarRecreo select[name="nivel"]').on('change', function() {
        let nivelSeleccionado = $(this).val();
        let $inputInicio = $('#modalConfigurarRecreo input[name="hora_inicio"]');
        let $inputFin = $('#modalConfigurarRecreo input[name="hora_fin"]');

        if (nivelSeleccionado) {
            // Hacemos una consulta rápida a nuestra nueva API
            $.get(`/academico/api/horario/recreo/${nivelSeleccionado}/`, function(data) {
                if (data.success) {
                    // Si ya existe un recreo en la BD, auto-llenamos las horas para que pueda editarlas
                    $inputInicio.val(data.hora_inicio);
                    $inputFin.val(data.hora_fin);
                } else {
                    // Si es un nivel nuevo sin recreo, limpiamos los campos
                    $inputInicio.val('');
                    $inputFin.val('');
                }
            });
        } else {
            $inputInicio.val('');
            $inputFin.val('');
        }
    });
});

function inicializarCalendarioHorario() {
    let $calendarEl = $('#calendario-horario');
    if ($calendarEl.length === 0) return;

    calendarHorario = new FullCalendar.Calendar($calendarEl[0], {
        locale: 'es', 
        initialView: 'timeGridWeek',
        initialDate: '2024-01-01', // Conexión con la semana ficticia ancla
        
        headerToolbar: false, 
        allDaySlot: false,    
        hiddenDays: [0, 6],   
        dayHeaderFormat: { weekday: 'long' }, 
        
        slotMinTime: '08:00:00',
        slotMaxTime: '14:30:00',
        slotLabelFormat: { hour: 'numeric', minute: '2-digit', meridiem: 'short', hour12: true },
        eventTimeFormat: { hour: 'numeric', minute: '2-digit', meridiem: 'short', hour12: true },

        // 💥 CONTROL DEL ALTO: Ajuste exacto para que se corte en la última hora (18:00)
        height: $(window).height() * 0.55, // Esto obliga a las celdas a tener el alto exacto de sus slots sin estirarse abajo

        events: function(info, successCallback, failureCallback) {
            let docenteId = $('#filtroDocente').val();
            let aulaId = docenteId ? "" : $('#filtroAula').val(); // Si hay docente, anulamos el aula en el envío

            $.ajax({
                url: '/academico/api/horario-fijo/',
                data: { 
                    periodo_id: $('#filtroPeriodo').val(),
                    aula_id: aulaId,
                    docente_id: docenteId
                },
                success: function(data) { successCallback(data); },
                error: function() { failureCallback(); }
            });
        },

        // 💥 MOTOR DE INYECCIÓN DE TEXTO DINÁMICO SUPERIOR
        loading: function(isLoading) {
            if (!isLoading) {
                // Cuando termina de cargar los eventos, evaluamos qué filtros están activos
                let docenteSeleccionado = $('#filtroDocente option:selected').val();
                let docenteTexto = $('#filtroDocente option:selected').text();
                
                let aulaSeleccionada = $('#filtroAula option:selected').val();
                let aulaTexto = $('#filtroAula option:selected').text();
                
                let $panelInfo = $('#infoFiltroDinamico');
                
                if (docenteSeleccionado !== "") {
                    // Si se filtró por un docente en específico
                    $('#iconInfoFiltro').text('person');
                    $('#tituloInfoFiltro').html(`Horario Semanal: <span class="text-info">${docenteTexto}</span>`);
                    $panelInfo.slideDown(200);
                } else if (aulaSeleccionada !== "") {
                    // Si se filtró por un aula en específico
                    $('#iconInfoFiltro').text('holiday_village');
                    $('#tituloInfoFiltro').html(`Aula: <span class="text-dark-info" style="color: #1a73e8; font-weight: 800;">${aulaTexto}</span>`);
                    $panelInfo.slideDown(200);
                } else {
                    // Si por algún motivo no hay filtros puestos
                    $panelInfo.slideUp(200);
                }
            }
        },
        
        selectable: false,
        editable: false, 
        selectMirror: false,

        // ==========================================
        // 💥 CORRECCIÓN DE CLIC: SOLUCIÓN AL "UNDEFINED"
        // ==========================================
        eventClick: function(info) {
            let props = info.event.extendedProps;
            
            // Construcción manual infalible de horas formato 12h (AM/PM)
            let opcionesHora = { hour: 'numeric', minute: '2-digit', hour12: true };
            let tInicio = info.event.start.toLocaleTimeString('es-PE', opcionesHora);
            let tFin = info.event.end.toLocaleTimeString('es-PE', opcionesHora);
            let rangoHorarioExacto = `${tInicio} - ${tFin}`;

            Swal.fire({
                title: `<span class="text-info font-weight-bold">${props.curso !== undefined ? props.curso : '--'}</span>`,
                html: `<div class="text-start text-sm p-2 bg-light border-radius-md">
                        <b>🏢 Aula de clase:</b> ${props.aula !== undefined ? props.aula : '--'}<br>
                        <b>👨‍🏫 Docente a cargo:</b> ${props.docente !== undefined ? props.docente : '--'}<br>
                        <b>⏰ Horario asignado:</b> ${rangoHorarioExacto}<br>
                        <b>📅 Día de la semana:</b> ${info.event.start.toLocaleDateString('es-PE', {weekday: 'long'})}
                       </div>`,
                icon: 'info',
                confirmButtonText: 'Entendido',
                confirmButtonColor: '#333333'
            });
        },

        // ==========================================
        // 💥 DISEÑO PREMIUM DE LA TARJETA CON ICONOS
        // ==========================================
        // 💥 RENDERIZADO VISUAL CON PROTECCIÓN CONTRA EL "FANTASMA"
        eventContent: function(arg) {
            let props = arg.event.extendedProps;

            // 💥 CASO 1: ES UN EVENTO DE FONDO (RECREO)
            // 💥 CASO 1: ES UN EVENTO DE FONDO (RECREO)
            if (arg.event.display === 'background') {
                
                // 1. Extraemos y formateamos la hora del evento nativo
                let horaTexto = '';
                if (arg.event.start && arg.event.end) {
                    let opcionesFormato = { hour: 'numeric', minute: '2-digit', hour12: true };
                    let horaInicio = arg.event.start.toLocaleTimeString('es-PE', opcionesFormato);
                    let horaFin = arg.event.end.toLocaleTimeString('es-PE', opcionesFormato);
                    horaTexto = `${horaInicio} - ${horaFin}`;
                }

                // 2. Construimos la tarjeta con RECREO arriba y la HORA abajo
                let $divRecreo = $('<div>')
                    .addClass('d-flex flex-column align-items-center justify-content-center w-100 h-100')
                    .append(
                        $('<span>')
                            .addClass('texto-recreo-premium') /* Tu clase custom.css */
                            .text(arg.event.title)           
                    )
                    .append(
                        $('<span>')
                            .css({
                                'color': '#000000',          /* Naranja fuerte */
                                'font-size': '0.75rem',      /* Letra más pequeña */
                                'font-weight': '700',
                                'opacity': '0.9',
                                'margin-top': '2px'          /* Separación sutil */
                            })
                            .text(horaTexto)                 /* Imprime "10:00 AM - 10:30 AM" */
                    );
                
                return { domNodes: [$divRecreo[0]] };
            }

            // 💥 CASO 2: ES UNA CLASE NORMAL
            let $div = $('<div>').addClass('p-1 w-100 text-center text-white d-flex flex-column justify-content-center h-100');
            
            // Si el bloque NO tiene ID en BD, es un fantasma de arrastre
            if (!props.db_id) {
                $div.append($('<b>').addClass('text-xs mb-1').text(arg.timeText));
                $div.append($('<span>').addClass('text-xxs').text('Sincronizando...'));
                return { domNodes: [$div[0]] };
            }

            // Si es un bloque real de la BD
            $div.append($('<b>').addClass('text-xs mb-1 opacity-8').text(arg.timeText));
            $div.append($('<b>').addClass('text-xs mb-1').text(props.curso));
            $div.append($('<span>').addClass('text-xxs').text(props.aula));
            $div.append($('<span>').addClass('text-xxs opacity-8').text(props.docente));
            return { domNodes: [$div[0]] };
        }
    });
    
    calendarHorario.render();
}


// 💥 MOTOR AJAX PARA DRAG & DROP
async function procesarDragDrop(info) {
    let evento = info.event;
    let db_id = evento.extendedProps.db_id;
    let nuevoDia = DIAS_ANCLA[evento.start.getDay()];
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
            mostrarNotificacionExito('Horario movido con éxito');
        } else {
            Swal.fire('Cruce Detectado', data.mensaje, 'warning');
            info.revert(); // 💥 MAGIA: Si hay cruce en BD, la tarjeta rebota a su sitio original
        }
    } catch (e) {
        Swal.fire('Error', 'Fallo de conexión.', 'error');
        info.revert();
    }
}

function irAEditarAula() {
      let aulaSeleccionada = $('#filtroAula').val();
      if (!aulaSeleccionada) {
          Swal.fire('Atención', 'Por favor, selecciona un "Aula Específica" en los filtros para poder editar su horario.', 'info');
          return;
      }
      // Redirigir a la nueva pantalla independiente
      window.location.href = '/academico/horario/aula/' + aulaSeleccionada + '/';
  }

function descargarExcelHorario() {
    // Capturamos lo que el usuario tiene seleccionado actualmente en los filtros
    let periodo = $('#filtroPeriodo').val() || '';
    let aula = $('#filtroAula').val() || '';
    let docente = $('#filtroDocente').val() || '';

    // Construimos la URL con los parámetros GET dinámicos
    let url = `/academico/horario/exportar/excel/?periodo_id=${periodo}&aula_id=${aula}&docente_id=${docente}`;
    
    // Disparamos la descarga nativa del navegador sin recargar la página
    window.location.href = url;
}

function guardarRecreoGlobal() {
    // 💥 Validaciones front-end
    if (!$('#modalConfigurarRecreo input[name="hora_inicio"]').val() || !$('#modalConfigurarRecreo input[name="hora_fin"]').val()) {
        mostrarErroresModal({'Horario': ['Debes ingresar la hora de inicio y fin del recreo.']});
        return;
    }

    $.ajax({
        url: '/academico/horario/recreo/guardar/',
        type: 'POST',
        data: $('#formConfigurarRecreo').serialize(),
        success: function(data) {
            if (data.success) {
                $('#modalConfigurarRecreo').modal('hide');
                $('#formConfigurarRecreo')[0].reset();
                
                // Refrescamos el calendario instantáneamente
                if (typeof calendarHorario !== 'undefined' && calendarHorario) {
                    calendarHorario.refetchEvents();
                }
                mostrarNotificacionExito(data.mensaje || 'Recreo configurado con éxito.');
            } else {
                mostrarErroresModal({'Error': [data.mensaje || 'No se pudo guardar el recreo.']});
            }
        },
        error: function() {
            mostrarErroresModal({'Servidor': ['Error de conexión al intentar guardar.']});
        }
    });
}