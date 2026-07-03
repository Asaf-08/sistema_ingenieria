// 💥 TERCERA REGLA DE ORO: PARCHE DE SEGURIDAD
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

$(document).ready(function() {
    // 1. Lógica para que toda la fila sea clickeable
    $('.clickable-row').on('click', function() {
        let url = $(this).data('url');
        if (url) {
            window.location.href = url;
        }
    });
});

// 2. Lógica del Modal
function abrirModalNuevaEvaluacion() {
    $('#formEvaluacion')[0].reset();
    $('#modalEvaluacion').modal('show');
}

// 3. Lógica para Guardar (AJAX) blindada
function guardarEvaluacion() {
    const urlGuardar = "/personal/evaluaciones/guardar/";
    
    $.ajax({
        url: urlGuardar,
        type: "POST",
        data: $('#formEvaluacion').serialize(),
        success: function(response) {
            if (response.status === 'ok') {
                $('#modalEvaluacion').modal('hide');
                Swal.fire({
                    title: '¡Creado!',
                    text: escapeHTML(response.message),
                    icon: 'success',
                    confirmButtonColor: '#e91e63',
                    confirmButtonText: 'Ir a poner notas'
                }).then(() => {
                    window.location.href = "/personal/notas/" + response.evaluacion_id + "/";
                });
            } else {
                Swal.fire('Error', escapeHTML(response.message || 'No se pudo crear la evaluación.'), 'error');
            }
        },
        error: function() {
            Swal.fire('Error', 'Problema de conexión con el servidor.', 'error');
        }
    });
}