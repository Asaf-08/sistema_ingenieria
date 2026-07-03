$(document).ready(function() {
    // LLAMAMOS A LA FUNCIÓN MAESTRA QUE CREASTE EN BASE.HTML
    inicializarTablaGlobal('#tabla-asignaciones', 'Buscar asignación...');
});

function abrirModalCrearAsignacion() {
    $('#formAsignacion')[0].reset();
    $('#asignacion_id').val('');
    $('#modalTituloAsignacion').text('Nueva Asignación');
    $('#modalHeaderAsignacion').removeClass('bg-gradient-info').addClass('bg-gradient-primary');
    $('#modalAsignacion').modal('show');
}

function abrirModalEditarAsignacion(id) {
    $.get('/academico/asignaciones/datos/' + id + '/', function(data) {
        $('#asignacion_id').val(data.id);
        $('#id_periodo').val(data.periodo);
        
        // 💥 CAMBIO AQUÍ: Usamos 'personal' en lugar de 'docente' para que coincida con tu vista y el form
        $('#id_personal').val(data.personal); 
        
        $('#id_curso').val(data.curso);
        $('#id_aula').val(data.aula);
        
        $('#modalTituloAsignacion').text('Editar Asignación');
        $('#modalHeaderAsignacion').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
        $('#modalAsignacion').modal('show');
    });
}

function guardarAsignacion() {
    $.ajax({
        url: '/academico/asignaciones/guardar/',
        type: 'POST',
        data: $('#formAsignacion').serialize(),
        success: function(response) {
            if (response.status === 'ok') {
                $('#modalAsignacion').modal('hide');
                mostrarNotificacionExito(response.message);
                
                // Recarga dinámica usando la función maestra
                $('.table-responsive').load(window.location.href + ' #tabla-asignaciones', function() {
                    inicializarTablaGlobal('#tabla-asignaciones');
                });
            } else {
                if (response.errors) mostrarErroresModal(response.errors);
            }
        }
    });
}

function confirmarEliminarAsignacion(id, nombre) {
    Swal.fire({
        title: '¿Eliminar asignación?',
        text: "Se quitará al docente de este curso y aula.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3a4149',
        cancelButtonColor: '#f57c00',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: '/academico/asignaciones/eliminar/' + id + '/',
                type: 'POST',
                data: {'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()},
                success: function() { location.reload(); }
            });
        }
    });
}