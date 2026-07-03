$(document).ready(function () {
    inicializarTablaGlobal('#tabla-cursos', 'Buscar curso...');
});

function abrirModalCrearCurso() {
    abrirModalMaestro({
        formId: '#formCurso', inputId: '#curso_id',
        tituloId: '#modalTituloCurso', headerId: '#modalHeaderCurso',
        titulo: 'Nuevo Curso', modalId: '#modalCurso'
    });
}

function abrirModalEditarCurso(id) {
    $.get('/academico/cursos/datos/' + id + '/', function (data) {
        $('#curso_id').val(data.id);
        $('#id_nombre').val(data.nombre);
        // Rescatamos tu línea para seleccionar el área
        $('#id_area').val(data.area);
        $('#id_activo').prop('checked', data.activo);
        
        $('#modalTituloCurso').text('Editar Curso');
        $('#modalHeaderCurso').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
        $('#modalCurso').modal('show');
    });
}

function guardarCurso() {
    // Validamos que no envíen el formulario en blanco
    if (!$('#id_nombre').val().trim()) {
        mostrarErroresModal({'Curso': ['El nombre del curso no puede estar vacío.']});
        return;
    }

    guardarRegistroAjax({
        url: '/academico/cursos/guardar/',
        formId: '#formCurso', 
        modalId: '#modalCurso', 
        tableId: '#tabla-cursos'
    });
}

function confirmarEliminarCurso(id, nombre) {
    confirmarEliminacionAjax({
        titulo: '¿Eliminar ' + nombre + '?',
        texto: "Se borrará este curso del sistema. Esta acción no se puede deshacer.",
        url: '/academico/cursos/eliminar/' + id + '/', 
        tableId: '#tabla-cursos'
    });
}