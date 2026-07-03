$(document).ready(function () {
    inicializarTablaGlobal('#tabla-periodos', 'Buscar periodo...');
});

function abrirModalCrearPeriodo() {
    abrirModalMaestro({
        formId: '#formPeriodo', inputId: '#periodo_id',
        tituloId: '#modalTituloPeriodo', headerId: '#modalHeaderPeriodo',
        titulo: 'Nuevo Periodo Lectivo', modalId: '#modalPeriodo'
    });
}

function abrirModalEditarPeriodo(id) {
    $.get('/academico/periodos/datos/' + id + '/', function (data) {
        $('#periodo_id').val(data.id);
        $('#id_anio').val(data.anio);
        $('#id_activo').prop('checked', data.activo);
        $('#modalTituloPeriodo').text('Editar Periodo');
        $('#modalHeaderPeriodo').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
        $('#modalPeriodo').modal('show');
    });
}

function guardarPeriodo() {
    guardarRegistroAjax({
        url: '/academico/periodos/guardar/',
        formId: '#formPeriodo', modalId: '#modalPeriodo', tableId: '#tabla-periodos'
    });
}

function confirmarEliminarPeriodo(id, nombre) {
    confirmarEliminacionAjax({
        titulo: '¿Eliminar ' + nombre + '?',
        texto: "Se borrará este periodo lectivo del sistema.",
        url: '/academico/periodos/eliminar/' + id + '/', tableId: '#tabla-periodos'
    });
}