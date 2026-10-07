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

    // Escuchador dinámico para el botón de duplicar
    $(document).on('click', '.btn-duplicar-notas', function(e) {
        e.preventDefault();
        // Detenemos la redirección de la fila padre
        e.stopPropagation(); 
        
        let evaluacionId = $(this).data('evaluacion-id');
        let csrfToken = $('input[name="csrfmiddlewaretoken"]').val() || $('meta[name="csrf-token"]').attr('content');
        
        Swal.fire({
            title: '¿Duplicar notas al Libro?',
            text: "Se copiarán idénticamente todas las notas de este Cuaderno hacia el Libro. Si ya tenías notas en el libro, se sobrescribirán.",
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#17a2b8',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, duplicar',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                Swal.fire({ title: 'Clonando notas...', didOpen: () => { Swal.showLoading(); }});
                
                let formData = new FormData();
                formData.append('evaluacion_id', evaluacionId);
                formData.append('csrfmiddlewaretoken', csrfToken);

                // 💥 RECUERDA: Ajustar esta URL a la que pongas en tu urls.py
                fetch('/personal/evaluaciones/duplicar-cuaderno/', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        Swal.fire({
                            icon: 'success',
                            title: '¡Magia realizada!',
                            text: data.mensaje,
                            timer: 2500,
                            showConfirmButton: false
                        });
                    } else {
                        Swal.fire('No se pudo duplicar', data.mensaje, 'error');
                    }
                })
                .catch(error => {
                    Swal.fire('Error de Red', 'Problema al conectar con el servidor.', 'error');
                });
            }
        });
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
    // 💥 Lo capturamos directamente del botón pulsado. ¡100% seguro!
    let asignacion_id = btn.data('asignacion'); 

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
                url: '/personal/notas/toggle-cierre/', 
                type: 'POST',
                data: {
                    'asignacion_id': asignacion_id,
                    'bimestre': bimestre,
                    'accion': accion,
                    'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val() || $('[name=csrfmiddlewaretoken]').val()
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
                // 💥 Ahora el JS leerá el error real de Django
                error: function(xhr) {
                    let msg = (xhr.responseJSON && xhr.responseJSON.mensaje) 
                              ? xhr.responseJSON.mensaje 
                              : 'Error interno del servidor. Revisa los logs de Railway.';
                    Swal.fire('Error Crítico', msg, 'error');
                }
            });
        }
    });
});