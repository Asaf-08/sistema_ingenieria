/**
 * ARCHIVO: personal.js (Optimizado Senior - Principio DRY)
 */

$(document).ready(function () {
    inicializarTablaGlobal('#tabla-personal', 'Buscar personal...');

    // ==============================================================
    // 💥 LÓGICA DE AUTO-GENERACIÓN DE DOCUMENTO (CÓDIGO INTERNO)
    // ==============================================================
    $('#id_tipo_documento').on('change', function() {
        let tipo = $(this).val();
        let inputDni = $('#id_dni');
        
        if (tipo === 'INT') {
            // Genera código único solo si el campo está vacío o no es un código INT previo.
            // La 'P' es de Personal (Ej: INT-P4829153)
            if (!inputDni.val().startsWith('INT-')) {
                let codigoAleatorio = 'INT-P' + Math.floor(Math.random() * 9000000 + 1000000);
                inputDni.val(codigoAleatorio);
            }
            inputDni.prop('readonly', true);
            inputDni.css('background-color', '#f8f9fa'); 
        } else {
            // Si elige DNI, CE, etc., limpiamos el campo y lo desbloqueamos
            if (inputDni.val().startsWith('INT-')) {
                inputDni.val('');
            }
            inputDni.prop('readonly', false);
            inputDni.css('background-color', 'transparent');
        }
    });
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
    // 💥 Al crear, forzamos que vuelva a DNI y se desbloquee la caja
    $('#id_tipo_documento').val('DNI').trigger('change');
}

function abrirModalEditarPersonal(id) {
    $.get('/personal/datos/' + id + '/', function (data) {
        $('#personal_id').val(data.id);
        
        // 💥 Leemos el tipo de documento de la Base de Datos
        $('#id_tipo_documento').val(data.tipo_documento); 
        $('#id_dni').val(data.dni);
        
        $('#id_nombres').val(data.nombres);
        $('#id_apellidos').val(data.apellidos);
        $('#id_cargo').val(data.cargo);
        $('#id_tipo_contrato').val(data.tipo_contrato);
        $('#id_fecha_ingreso').val(data.fecha_ingreso);
        $('#id_user').val(data.user);
        $('#id_telefono').val(data.telefono);
        $('#id_correo').val(data.correo);

        // 💥 Disparamos la lógica para bloquear/desbloquear según lo cargado
        $('#id_tipo_documento').trigger('change');

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