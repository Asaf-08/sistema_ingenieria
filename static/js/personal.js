/**
 * ARCHIVO: personal.js (Optimizado Senior - Principio DRY)
 */

$(document).ready(function () {
    inicializarTablaGlobal('#tabla-personal', 'Buscar personal...');
});

function abrirModalCrearPersonal() {
    abrirModalMaestro({
        formId: '#formPersonal',
        inputId: '#personal_id',
        tituloId: '#modalTituloPersonal',
        headerId: '#modalHeaderPersonal',
        titulo: 'Nuevo Registro de Personal',
        modalId: '#modalPersonal'
    });
}

function abrirModalEditarPersonal(id) {
    $.get('/personal/datos/' + id + '/', function (data) {
        $('#personal_id').val(data.id);
        $('#id_dni').val(data.dni);
        $('#id_nombres').val(data.nombres);
        $('#id_apellidos').val(data.apellidos);
        
        $('#id_cargo').val(data.cargo);
        $('#id_tipo_contrato').val(data.tipo_contrato);
        $('#id_fecha_ingreso').val(data.fecha_ingreso);
        $('#id_user').val(data.user);
        
        $('#id_telefono').val(data.telefono);
        $('#id_correo').val(data.correo);

        $('#modalTituloPersonal').text('Editar Personal');
        $('#modalHeaderPersonal').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
        $('#modalPersonal').modal('show');
    });
}

function guardarPersonal() {
    guardarRegistroAjax({
        url: '/personal/guardar/',
        formId: '#formPersonal',
        modalId: '#modalPersonal',
        tableId: '#tabla-personal',
        textoBuscador: 'Buscar personal...'
    });
}

function confirmarEliminarPersonal(id, nombre) {
    confirmarEliminacionAjax({
        titulo: '¿Eliminar a ' + nombre + '?',
        texto: "Esta acción no se puede deshacer.",
        url: '/personal/eliminar/' + id + '/',
        tableId: '#tabla-personal',
        textoBuscador: 'Buscar personal...'
    });
}

// ==============================================================
// LÓGICA DE CAMBIO DE ESTADO RÁPIDO
// ==============================================================

function abrirModalEstado(id, estadoActual) {
    $('#personal_id_estado').val(id);
    $('#select_nuevo_estado').val(estadoActual);
    $('#modalEstado').modal('show');
}

function guardarNuevoEstado() {
    const id = $('#personal_id_estado').val();
    const estado = $('#select_nuevo_estado').val();

    // AJAX directo porque no usa formulario completo, solo un select
    $.ajax({
        url: '/personal/cambiar-estado/' + id + '/',
        type: 'POST',
        data: { 'nuevo_estado': estado },
        success: function (response) {
            if (response.status === 'ok' || response.success) {
                $('#modalEstado').modal('hide');
                mostrarNotificacionExito(response.message || response.mensaje || 'Estado actualizado con éxito.');
                
                $('#tabla-personal').load(window.location.href + ' #tabla-personal > *', function () {
                    inicializarTablaGlobal('#tabla-personal', 'Buscar personal...');
                    
                    // Reactivar Tooltips
                    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                    tooltipTriggerList.map(function (tooltipTriggerEl) {
                        return new bootstrap.Tooltip(tooltipTriggerEl);
                    });
                });
            } else {
                mostrarErroresModal(response.errors || { 'Error': [response.mensaje || 'No se pudo actualizar el estado.'] });
            }
        },
        error: function () {
            mostrarErroresModal({'Servidor': ['Error al intentar conectar con el servidor.']});
        }
    });
}