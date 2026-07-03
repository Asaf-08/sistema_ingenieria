/**
 * ARCHIVO: simulacros.js
 * Módulo de gestión y monitoreo de Simulacros (Integrado al Cerebro Global)
 */

$(document).ready(function () {
    // 1. Inicializa la tabla principal de simulacros
    if ($('#tabla-simulacros').length) {
        inicializarTablaGlobal('#tabla-simulacros', 'Buscar simulacro...');
    }
    
    // 2. 💥 Inicializa la tabla de monitoreo (si el usuario está en esa pantalla)
    if ($('#tabla-monitoreo').length) {
        inicializarTablaGlobal('#tabla-monitoreo', 'Buscar curso o docente...');
    }
});

function abrirModalCrearSimulacro() {
    abrirModalMaestro({
        formId: '#formSimulacro', 
        inputId: '#simulacro_id',
        tituloId: '#modalTituloSimulacro', 
        headerId: '#modalHeaderSimulacro',
        titulo: 'Configurar Nuevo Simulacro', 
        modalId: '#modalSimulacro'
    });
}

function abrirModalEditarSimulacro(id) {
    $.get('/academico/simulacros/datos/' + id + '/', function (data) {
        $('#simulacro_id').val(data.id);
        $('#id_titulo').val(data.titulo);
        $('#id_mes').val(data.mes);
        $('#id_grado').val(data.grado);
        $('#id_nivel').val(data.nivel);
        $('#id_fecha_examen').val(data.fecha_examen);
        $('#id_preguntas_esperadas').val(data.preguntas_esperadas);
        $('#id_activo').prop('checked', data.activo);
        
        $('#modalTituloSimulacro').text('Modificar Parámetros del Simulacro');
        $('#modalHeaderSimulacro').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
        $('#modalSimulacro').modal('show');
    });
}

function guardarSimulacro() {
    // Validación rápida de frontend para evitar enviar un simulacro sin título
    if (!$('#id_titulo').val() || !$('#id_fecha_examen').val()) {
        mostrarErroresModal({'Datos Incompletos': ['Por favor ingresa el título y la fecha del examen.']});
        return;
    }

    guardarRegistroAjax({
        url: '/academico/simulacros/guardar/',
        formId: '#formSimulacro',
        modalId: '#modalSimulacro',
        tableId: '#tabla-simulacros',
        textoBuscador: 'Buscar simulacro...'
    });
}

function confirmarEliminarSimulacro(id, titulo) {
    confirmarEliminacionAjax({
        titulo: '¿Eliminar ' + titulo + '?',
        texto: "Se borrará este simulacro y toda su configuración. Las preguntas subidas por los docentes también podrían perder su asociación.",
        url: '/academico/simulacros/eliminar/' + id + '/',
        tableId: '#tabla-simulacros',
        textoBuscador: 'Buscar simulacro...'
    });
}