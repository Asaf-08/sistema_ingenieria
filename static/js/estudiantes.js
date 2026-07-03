$(document).ready(function () {
    inicializarTablaGlobal('#tabla-estudiantes', 'Buscar estudiante...');
});

// 💥 USANDO LA FUNCIÓN MAESTRA DEL CEREBRO
function confirmarEliminarEstudiante(id, nombre) {
    confirmarEliminacionAjax({
        titulo: '¿Eliminar a ' + nombre + '?',
        texto: "Se borrará toda su información permanentemente. Esta acción no se puede deshacer.",
        url: '/academico/estudiantes/eliminar/' + id + '/',
        tableId: '#tabla-estudiantes',
        textoBuscador: 'Buscar estudiante...'
    });
}

function abrirModalCambiarEstado(id, estadoActual) {
    $('#formEstadoEstudiante')[0].reset();
    $('#estudiante_id_estado').val(id);
    $('#select_nuevo_estado').val(estadoActual);
    $('#modalEstado').modal('show');
}

function guardarNuevoEstado() {
    let id = $('#estudiante_id_estado').val();
    let nuevo_estado = $('#select_nuevo_estado').val();

    // 💥 VALIDACIÓN DE FRONTEND
    if (!nuevo_estado) {
        mostrarErroresModal({'Estado': ['Debe seleccionar un estado válido de la lista.']});
        return;
    }

    $.ajax({
        url: '/academico/estudiantes/cambiar-estado/' + id + '/',
        type: 'POST',
        data: { 'nuevo_estado': nuevo_estado },
        success: function (response) {
            if (response.status === 'ok') {
                $('#modalEstado').modal('hide');
                mostrarNotificacionExito(response.message || 'Estado actualizado con éxito.');
                
                // Recarga limpia
                $('.table-responsive').load(window.location.href + ' #tabla-estudiantes', function () {
                    inicializarTablaGlobal('#tabla-estudiantes', 'Buscar estudiante...');
                    // Reactivar tooltips de Bootstrap si existen
                    $('[data-bs-toggle="tooltip"]').tooltip();
                });
            } else {
                mostrarErroresModal(response.errors || {'Error': ['No se pudo actualizar el estado.']});
            }
        },
        error: function () {
            mostrarErroresModal({'Conexión': ['Error de comunicación con el servidor. Intente nuevamente.']});
        }
    });
}