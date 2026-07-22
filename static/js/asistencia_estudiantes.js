$(document).ready(function () {
    // ==========================================================
    // 💥 LÓGICA DE FILTROS EN CASCADA (NIVEL -> AULA)
    // ==========================================================
    const selectNivel = $('#filtro-nivel');
    const selectAula = $('#filtro-aula');
    
    // 1. Guardamos una copia exacta de todas las opciones de Aulas al cargar
    const opcionesAulasOriginales = selectAula.html();

    // 2. Detectamos si ya hay un aula seleccionada (porque la página se recargó)
    // y ajustamos automáticamente el select de "Nivel" para que coincida.
    let nivelPreseleccionado = selectAula.find('option:selected').data('nivel');
    if (nivelPreseleccionado && nivelPreseleccionado !== 'TODOS') {
        selectNivel.val(nivelPreseleccionado);
    }

    // 3. Cuando la secretaria cambie el "Nivel"...
    selectNivel.on('change', function() {
        let nivelElegido = $(this).val();

        // A. Restauramos todas las aulas de la memoria
        selectAula.html(opcionesAulasOriginales);

        // B. Si eligió un nivel específico, ocultamos las aulas que NO son de ese nivel
        if (nivelElegido !== 'TODOS') {
            selectAula.find('option').each(function() {
                // Si el data-nivel de la opción no coincide y no es la opción vacía "-- Seleccione Aula --"
                if ($(this).data('nivel') !== nivelElegido && $(this).val() !== "") {
                    $(this).remove(); // La quitamos del select
                }
            });
        }
        
        // C. Reseteamos la selección del aula al primer valor vacío
        // IMPORTANTE: Al cambiarle el .val(""), NO dispara el "onchange" de HTML, 
        // por lo que NO recarga la página, solo limpia la casilla.
        selectAula.val(''); 
    });

    // Simulamos un click inicial oculto para que, si el sistema cargó con "Primaria" 
    // preseleccionado, el select de aulas se limpie automáticamente al arrancar.
    if (selectNivel.val() !== 'TODOS') {
        let aulaIdActual = selectAula.val(); // Guardamos el aula actual
        selectNivel.trigger('change');       // Filtramos
        selectAula.val(aulaIdActual);        // Le devolvemos su valor
    }
    
    // 💥 INICIALIZACIÓN AISLADA: Solo afecta a la matriz de asistencia
    if ($.fn.DataTable.isDataTable('#tabla-matriz-estudiantes')) {
        $('#tabla-matriz-estudiantes').DataTable().destroy();
    }

    $('#tabla-matriz-estudiantes').DataTable({
        language: {
            url: "/static/plugins/datatables/js/es-ES.json",
            search: "_INPUT_",
            searchPlaceholder: 'Buscar estudiante...',
            lengthMenu: "Mostrar _MENU_ registros",
            info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0 a 0 de 0 registros",
            zeroRecords: "No se encontraron resultados",
            paginate: {
                first: "Primero",
                last: "Último",
                next: '<i class="material-symbols-rounded" style="font-size: 18px;">chevron_right</i>',
                previous: '<i class="material-symbols-rounded" style="font-size: 18px;">chevron_left</i>'
            }
        },
        pageLength: 50,
        lengthChange: true,
        ordering: true,
        info: true,
        autoWidth: false,
        responsive: true,
        dom: '<"d-flex justify-content-between align-items-center px-4 pt-3"f l>t<"d-flex justify-content-between align-items-center p-4"ip>',
        initComplete: function () {
            $('.dataTables_filter input')
                .addClass('form-control border-bottom border-2 px-3 py-1')
                .attr('placeholder', 'Buscar estudiante...');
                
            $('.dataTables_filter label').contents().filter(function () {
                return this.nodeType === 3;
            }).remove();

            $('.dataTables_length select')
                .addClass('form-control border-bottom border-2 px-2 py-1 mx-2')
                .css({
                    'display': 'inline-block',
                    'width': 'auto',
                    'background-color': 'transparent'
                });
        }
    });

    $('[data-bs-toggle="tooltip"]').tooltip();

/*     // 1. Llamamos a tu función global para que le dé el idioma y el diseño
    inicializarTablaGlobal('#tabla-matriz-estudiantes', 'Buscar estudiante...');

    // 2. 💥 TRUCO MÁGICO: Le decimos a la tabla que cambie a 50 registros y se redibuje sola
    $('#tabla-matriz-estudiantes').DataTable().page.len(50).draw();

    // 3. Inicializamos los tooltips
    $('[data-bs-toggle="tooltip"]').tooltip(); */
});

// 1. DESBLOQUEAR LA TABLA (Modo Edición)
function habilitarModoEdicion() {
    $('.radio-asistencia').prop('disabled', false); // Quitamos el candado a los checks
    $('#btn-habilitar-edicion').addClass('d-none'); // Ocultamos este botón
    $('#btn-guardar-matriz, #btn-cancelar-edicion').removeClass('d-none'); // Mostramos los de guardar
    
    mostrarNotificacion('info', 'Modo edición activado. Puede marcar las casillas.');
}

// 2. ATRAER JUSTIFICACIONES (Cuando hacen clic en la 'J')
$(document).on('change', '.input-justificado', function() {
    if ($(this).is(':checked')) {
        let hiddenInput = $(this).siblings('.justificacion-text');
        
        // Lanzamos un modal nativo de SweetAlert para pedir el texto
        Swal.fire({
            title: 'Motivo de la Falta',
            text: 'Ingrese la justificación del estudiante',
            input: 'text',
            inputValue: hiddenInput.val(), // Carga lo que ya tenía si es edición
            showCancelButton: true,
            confirmButtonText: 'Guardar Motivo',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#333333',
            cancelButtonColor: '#fb8c00',
            inputValidator: (value) => {
                if (!value) { return '¡Necesitas escribir un motivo!' }
            }
        }).then((result) => {
            if (result.isConfirmed) {
                hiddenInput.val(result.value); // Guardamos silenciosamente en la fila
            } else {
                $(this).prop('checked', false); // Si canceló, le quitamos el check
            }
        });
    }
});

// 3. RECOLECTAR Y ENVIAR MASIVAMENTE (El Bucle de Guardado)
function guardarMatrizAsistencia() {
    let registros = [];
    let fechaMatriz = $('#fecha_filtro_matriz').val();

    // Recorremos todas las filas buscando qué check está marcado
    // Nota: Usamos DataTable().$ para atrapar incluso a los alumnos en otras páginas
    $('#tabla-matriz-estudiantes').DataTable().$('.fila-estudiante').each(function() {
        let est_id = $(this).data('estudiante-id');
        let estadoChecked = $(this).find('input[type="radio"]:checked').val();
        let justificacion = $(this).find('.justificacion-text').val();

        if (estadoChecked) {
            registros.push({
                estudiante_id: est_id,
                estado: estadoChecked,
                justificacion: justificacion
            });
        }
    });

    if(registros.length === 0) {
        Swal.fire('Atención', 'No ha marcado la asistencia de ningún alumno.', 'warning');
        return;
    }

    Swal.fire({ title: 'Guardando Asistencia...', didOpen: () => { Swal.showLoading(); }});

    $.ajax({
        url: '/asistencia/api/guardar-masiva/',
        type: 'POST',
        data: JSON.stringify({ 'fecha': fechaMatriz, 'registros': registros }),
        contentType: 'application/json',
        headers: { 'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val() },
        success: function (response) {
            if (response.success) {
                Swal.close();
                // Usamos SessionStorage para recargar la página y que salga la notificación verde
                sessionStorage.setItem('asistenciaGuardada', 'true');
                location.reload();
            } else {
                Swal.fire('Error', response.mensaje, 'error');
            }
        },
        error: function () {
            Swal.fire('Error de Red', 'Problema al conectar con el servidor.', 'error');
        }
    });
}

// 4. Mostrar alerta después de recargar
$(window).on('load', function() {
    if (sessionStorage.getItem('asistenciaGuardada')) {
        mostrarNotificacionExito('Matriz de asistencia guardada correctamente.');
        sessionStorage.removeItem('asistenciaGuardada');
    }
});

// ===============================================
// 💥 LÓGICA PARA EDITAR LA HORA
// ===============================================

function abrirModalEditarHora(id, horaActual) {
    $('#hora_asistencia_id').val(id);
    $('#hora_registro_nueva').val(horaActual);
    $('#modalEditarHora').modal('show');
}

function guardarNuevaHora() {
    let id = $('#hora_asistencia_id').val();
    let nuevaHora = $('#hora_registro_nueva').val();

    if (!nuevaHora) {
        Swal.fire('Atención', 'Debe ingresar una hora válida.', 'warning');
        return;
    }

    Swal.fire({ title: 'Actualizando hora...', didOpen: () => { Swal.showLoading(); }});

    $.ajax({
        url: '/asistencia/api/editar-hora-estudiante/',
        type: 'POST',
        data: JSON.stringify({ id: id, hora_registro: nuevaHora }),
        contentType: 'application/json',
        headers: { 'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val() },
        success: function (response) {
            if (response.success) {
                $('#modalEditarHora').modal('hide');
                Swal.close();
                // Usamos Storage para el "parpadeo" limpio
                sessionStorage.setItem('horaGuardada', response.mensaje);
                location.reload();
            } else {
                Swal.fire('Error', response.mensaje, 'error');
            }
        },
        error: function () {
            Swal.fire('Error', 'Problema al conectar con el servidor.', 'error');
        }
    });
}

// Interceptamos la recarga de página para mostrar el toast verde de la hora
$(window).on('load', function() {
    if (sessionStorage.getItem('horaGuardada')) {
        mostrarNotificacionExito(sessionStorage.getItem('horaGuardada'));
        sessionStorage.removeItem('horaGuardada');
    }
});