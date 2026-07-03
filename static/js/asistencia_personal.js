$(document).ready(function () {
    inicializarTablaGlobal('#tabla-asistencia-docentes', 'Buscar personal...');
    $('[data-bs-toggle="tooltip"]').tooltip();

    // LÓGICA DINÁMICA: Mostrar/Ocultar Justificación
    $('#id_estado').on('change', function () {
        if ($(this).val() === 'J') {
            $('#div_justificacion').slideDown();
        } else {
            $('#div_justificacion').slideUp();
            $('#id_justificacion').val(''); 
        }
    });
});

function abrirModalCrear() {
    $('#formAsistencia')[0].reset();
    $('#asistencia_id').val('');
    $('#id_docente').prop('disabled', false); 
    $('#div_justificacion').hide();

    $('#modalTitulo').text('Nuevo Registro Manual');
    $('#modalHeaderColor').removeClass('bg-gradient-info').addClass('bg-gradient-primary');
    $('#btnGuardar').text('Guardar Registro').removeClass('bg-gradient-info').addClass('bg-gradient-primary');
    $('#modalAsistencia').modal('show');
}

function abrirModalEditar(id, docente_id, entrada, salida, estado, justificacion = '', tipo_act = 'REGULAR', obs = '') {
    $('#formAsistencia')[0].reset();
    $('#asistencia_id').val(id);
    $('#id_docente').val(docente_id).prop('disabled', true); 
    $('#id_hora_entrada').val(entrada);
    $('#id_hora_salida').val(salida);
    $('#id_estado').val(estado);
    $('#id_tipo_actividad').val(tipo_act);
    $('#id_observaciones').val(obs);

    if (estado === 'J') {
        $('#div_justificacion').show();
        $('#id_justificacion').val(justificacion);
    } else {
        $('#div_justificacion').hide();
        $('#id_justificacion').val('');
    }

    $('#modalTitulo').text('Editar Asistencia');
    $('#modalHeaderColor').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
    $('#btnGuardar').text('Actualizar').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
    $('#modalAsistencia').modal('show');
}

function guardarAsistencia() {
    let data = {
        id: $('#asistencia_id').val(),
        personal_id: $('#id_docente').val(),
        hora_entrada: $('#id_hora_entrada').val(),
        hora_salida: $('#id_hora_salida').val(),
        estado: $('#id_estado').val(),
        justificacion: $('#id_justificacion').val(),
        tipo_actividad: $('#id_tipo_actividad').val(),
        observaciones: $('#id_observaciones').val()
    };

    if (data.estado === 'J' && data.justificacion.trim() === '') {
        Swal.fire('Atención', 'Debe ingresar una justificación.', 'warning');
        return;
    }

    $.ajax({
        url: '/asistencia/api/guardar-personal/',
        type: 'POST',
        data: JSON.stringify(data),
        contentType: 'application/json',
        headers: { 'X-CSRFToken': $('input[name=csrfmiddlewaretoken]').val() },
        success: function (response) {
            if (response.success) {
                $('#modalAsistencia').modal('hide');
                mostrarNotificacionExito(response.mensaje);
                
                $('#tabla-asistencia-docentes').load(window.location.href + ' #tabla-asistencia-docentes > *', function () {
                    if (typeof inicializarTablaGlobal === 'function') {
                        inicializarTablaGlobal('#tabla-asistencia-docentes', 'Buscar personal...');
                    }
                    $('[data-bs-toggle="tooltip"]').tooltip();
                });
            } else {
                Swal.fire('Error', response.mensaje, 'error');
            }
        },
        error: function () {
            Swal.fire('Error', 'Ocurrió un problema en el servidor.', 'error');
        }
    });
}

// 💥 AQUÍ APLICAMOS LA REUTILIZACIÓN DE CÓDIGO (DRY)
function confirmarEliminacion(id) {
    // Usamos tu función global exacta sin cambiar el nombre de esta función local
    confirmarEliminacionAjax({
        titulo: '¿Eliminar asistencia?',
        texto: "Esta acción no se puede deshacer.",
        url: '/asistencia/api/eliminar-personal/' + id + '/',
        tableId: '#tabla-asistencia-docentes',
        textoBuscador: 'Buscar personal...'
    });
}