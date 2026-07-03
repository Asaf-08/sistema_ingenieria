// 💥 TERCERA REGLA DE ORO: PARCHE DE SEGURIDAD (XSS Y RUTEO SEGURO)
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Obtención segura del Token CSRF sin depender de jQuery
function getCSRFToken() {
    const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return tokenInput ? tokenInput.value : '';
}

$(document).ready(function () {
    if (typeof inicializarTablaGlobal === 'function') {
        inicializarTablaGlobal('#tabla-preguntas', 'Buscar pregunta...');
    }
    // --- LÓGICA DEL DRAG & DROP DE IMÁGENES ---
    const dropzone = $('#dropzone-imagen');
    const inputImagen = $('#id_imagen');
    const previewContainer = $('#contenedor-preview');
    const imgPreview = $('#img-preview');
    const btnRemover = $('#btn-remover-imagen');

    inputImagen.on('dragenter dragover', function () {
        dropzone.css('background-color', '#e1f5fe'); 
    });

    inputImagen.on('dragleave drop', function () {
        dropzone.css('background-color', '#f8f9fa'); 
    });

    inputImagen.on('change', function () {
        const archivo = this.files[0];
        if (archivo) {
            let lector = new FileReader();
            lector.onload = function(evento){
                imgPreview.attr('src', evento.target.result); 
                previewContainer.removeClass('d-none');
                dropzone.addClass('d-none'); 
            }
            lector.readAsDataURL(archivo);
        } else {
            removerImagen();
        }
    });

    btnRemover.on('click', removerImagen);

    function removerImagen() {
        inputImagen.val(''); 
        previewContainer.addClass('d-none');
        imgPreview.attr('src', '#');
        dropzone.removeClass('d-none'); 
    }

    // 💥 CAPTURADOR: Botón para Declarar el Curso como Listo (Optimizado con Fetch y Async/Await)
    $('.btn-finalizar-curso').on('click', function() {
        const btn = $(this);
        const cursoId = btn.data('curso');
        const simulacroId = btn.data('simulacro');

        Swal.fire({
            title: '¿Terminaste con este curso?',
            text: "El progreso se guardará y la coordinadora sabrá que ya terminaste de subir las preguntas.",
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#4CAF50', 
            cancelButtonColor: '#3a4149',  
            confirmButtonText: 'Sí, declarar listo',
            cancelButtonText: 'Aún no'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const response = await fetch('/academico/simulacros/finalizar-curso/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': getCSRFToken()
                        },
                        body: JSON.stringify({
                            'simulacro_id': simulacroId,
                            'curso_id': cursoId
                        })
                    });
                    const data = await response.json();
                    
                    if (data.status === 'ok' || data.success) {
                        window.location.reload(); 
                    } else {
                        // Prevenimos inyecciones XSS en los mensajes del servidor
                        Swal.fire('Error', escapeHTML(data.message || 'Ocurrió un error al guardar.'), 'error');
                    }
                } catch (error) {
                    Swal.fire('Error', 'No se pudo conectar con el servidor.', 'error');
                }
            }
        });
    });

    // 💥 CAPTURADOR: Botón para REABRIR el Curso (Optimizado con Fetch y Async/Await)
    $('.btn-reabrir-curso').on('click', function() {
        const btn = $(this);
        const cursoId = btn.data('curso');
        const simulacroId = btn.data('simulacro');

        Swal.fire({
            title: '¿Desbloquear este curso?',
            text: "Podrás volver a editar, agregar o eliminar preguntas de esta materia.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#17c1e8', 
            cancelButtonColor: '#3a4149',
            confirmButtonText: 'Sí, reabrir edición',
            cancelButtonText: 'Cancelar'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const response = await fetch('/academico/simulacros/reabrir-curso/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': getCSRFToken()
                        },
                        body: JSON.stringify({
                            'simulacro_id': simulacroId,
                            'curso_id': cursoId
                        })
                    });
                    const data = await response.json();
                    
                    if (data.status === 'ok' || data.success) {
                        window.location.reload(); 
                    } else {
                        Swal.fire('Atención', escapeHTML(data.message), 'warning');
                    }
                } catch (error) {
                    Swal.fire('Error', 'No se pudo conectar con el servidor.', 'error');
                }
            }
        });
    });
});

function abrirModalPregunta() {
    $('#formPregunta')[0].reset();
    $('#pregunta_id').val(''); 
    $('#contenedor-preview').addClass('d-none');
    $('#dropzone-imagen').removeClass('d-none');
    $('#img-preview').attr('src', '#');
    $('#modalPregunta').modal('show');
}

function abrirModalEditarPregunta(id) {
    // 💥 Rutas seguras y Fetch asíncrono
    fetch('/academico/simulacros/pregunta/datos/' + id + '/')
        .then(r => r.json())
        .then(data => {
            /* NOTA DE SEGURIDAD: Aquí NO usamos escapeHTML() porque jQuery (.val) 
               procesa estos datos como texto plano de forma nativa, bloqueando el XSS automáticamente. */
            $('#pregunta_id').val(data.id);
            $('#id_curso').val(data.curso_id);
            $('#id_enunciado').val(data.enunciado);
            $('#id_opcion_a').val(data.opcion_a);
            $('#id_opcion_b').val(data.opcion_b);
            $('#id_opcion_c').val(data.opcion_c);
            $('#id_opcion_d').val(data.opcion_d);
            $('#id_opcion_e').val(data.opcion_e);
            $('#id_respuesta_correcta').val(data.respuesta_correcta);

            if(data.imagen_url){
                $('#img-preview').attr('src', data.imagen_url); 
                $('#contenedor-preview').removeClass('d-none');
                $('#dropzone-imagen').addClass('d-none');
            } else {
                $('#contenedor-preview').addClass('d-none');
                $('#dropzone-imagen').removeClass('d-none');
            }

            $('#modalPregunta').modal('show');
        })
        .catch(err => {
            Swal.fire('Error', 'No se pudieron cargar los datos de la pregunta.', 'error');
        });
}

function eliminarPregunta(id) {
    // 💥 APLICANDO DRY: Eliminamos el código repetido y usamos tu función global
    // Nota: Asegúrate de tener la ruta '/academico/simulacros/pregunta/eliminar/<id>/' en tu views.py
    confirmarEliminacionAjax({
        titulo: '¿Eliminar esta pregunta?',
        texto: "Tendrás que volver a redactarla si cambias de opinión.",
        url: '/academico/simulacros/pregunta/eliminar/' + id + '/',
        tableId: '#tabla-preguntas', // Refrescará solo este bloque de tu HTML
        textoBuscador: 'Buscar pregunta...'
    });
}