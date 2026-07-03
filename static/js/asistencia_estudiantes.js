$(document).ready(function () {
    inicializarTablaGlobal('#tabla-asistencia-estudiantes', 'Buscar estudiante...');
    $('[data-bs-toggle="tooltip"]').tooltip();

    // LÓGICA DINÁMICA: Mostrar/Ocultar Justificación Estudiante
    $('#id_estado_est').on('change', function () {
        if ($(this).val() === 'J') {
            $('#div_justificacion_est').slideDown();
        } else {
            $('#div_justificacion_est').slideUp();
            $('#id_justificacion_est').val(''); 
        }
    });
});

function abrirModalCrearEstudiante() {
    $('#formAsistenciaEstudiante')[0].reset();
    $('#asistencia_est_id').val('');
    $('#id_estudiante').prop('disabled', false); 
    $('#div_justificacion_est').hide();

    $('#modalTituloEstudiante').text('Nueva Asistencia Estudiante');
    $('#modalAsistenciaEstudiante').modal('show');
}

function abrirModalEditarEstudiante(id, estudiante_id, hora, estado, justificacion = '', observaciones = '') {
    $('#formAsistenciaEstudiante')[0].reset();
    $('#asistencia_est_id').val(id);
    $('#id_estudiante').val(estudiante_id).prop('disabled', true); 
    $('#id_hora_registro').val(hora);
    $('#id_estado_est').val(estado);
    $('#id_observaciones_est').val(observaciones);

    if (estado === 'J') {
        $('#div_justificacion_est').show();
        $('#id_justificacion_est').val(justificacion);
    } else {
        $('#div_justificacion_est').hide();
        $('#id_justificacion_est').val('');
    }

    $('#modalTituloEstudiante').text('Editar Asistencia Estudiante');
    $('#modalAsistenciaEstudiante').modal('show');
}

function guardarAsistenciaEstudiante() {
    let data = {
        id: $('#asistencia_est_id').val(),
        estudiante_id: $('#id_estudiante').val(),
        hora_registro: $('#id_hora_registro').val(),
        estado: $('#id_estado_est').val(),
        justificacion: $('#id_justificacion_est').val(),
        observaciones: $('#id_observaciones_est').val()
    };

    if (data.estado === 'J' && data.justificacion.trim() === '') {
        Swal.fire('Atención', 'Debe ingresar una justificación.', 'warning');
        return;
    }

    $.ajax({
        url: '/asistencia/api/guardar-estudiante/',
        type: 'POST',
        data: JSON.stringify(data),
        contentType: 'application/json',
        headers: { 'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val() },
        success: function (response) {
            if (response.success) {
                $('#modalAsistenciaEstudiante').modal('hide');
                mostrarNotificacionExito(response.mensaje);
                
                $('#tabla-asistencia-estudiantes').load(window.location.href + ' #tabla-asistencia-estudiantes > *', function () {
                    inicializarTablaGlobal('#tabla-asistencia-estudiantes', 'Buscar estudiante...');
                    $('[data-bs-toggle="tooltip"]').tooltip();
                });
            } else {
                Swal.fire('Error', response.mensaje, 'error');
            }
        }
    });
}

// 💥 AQUÍ APLICAMOS LA REUTILIZACIÓN DE CÓDIGO (DRY)
function confirmarEliminacionEstudiante(id) {
    // Usamos tu función global exacta sin cambiar el nombre de esta función local
    confirmarEliminacionAjax({
        titulo: '¿Eliminar registro?',
        texto: "Esta acción no se puede deshacer.",
        url: '/asistencia/api/eliminar-estudiante/' + id + '/',
        tableId: '#tabla-asistencia-estudiantes',
        textoBuscador: 'Buscar estudiante...'
    });
}