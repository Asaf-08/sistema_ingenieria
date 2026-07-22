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

// 💥 CONTROL DEL CANDADO (CERRAR/ABRIR REGISTRO)
$(document).on('click', '.btn-toggle-cierre', function() {
    let btn = $(this);
    let bimestre = btn.data('bimestre');
    let accion = btn.data('accion');
    // Capturamos el ID de la asignación desde el input oculto que ya tienes en el modal
    let asignacion_id = $('input[name="asignacion_id"]').val(); 

    Swal.fire({
        title: accion === 'cerrar' ? '¿Finalizar Bimestre?' : '¿Reabrir Registro?',
        text: accion === 'cerrar' 
            ? 'Tus notas se enviarán a coordinación y los campos se bloquearán.' 
            : 'Volverás a habilitar la edición de notas.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: accion === 'cerrar' ? '#4CAF50' : '#FF9800',
        confirmButtonText: 'Sí, continuar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({ title: 'Procesando...', didOpen: () => { Swal.showLoading(); }});
            
            $.ajax({
                // Asegúrate de que esta URL coincida con la que pusiste en tu urls.py
                url: '/personal/notas/toggle-cierre/', 
                type: 'POST',
                data: {
                    'asignacion_id': asignacion_id,
                    'bimestre': bimestre,
                    'accion': accion,
                    'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
                },
                success: function(response) {
                    if (response.success) {
                        Swal.fire('¡Éxito!', response.mensaje, 'success').then(() => {
                            location.reload(); // Recargamos para que Django dibuje o quite los candados
                        });
                    } else {
                        Swal.fire('Error', response.mensaje, 'error');
                    }
                },
                error: function() {
                    Swal.fire('Error de Red', 'No se pudo conectar con el servidor.', 'error');
                }
            });
        }
    });
});