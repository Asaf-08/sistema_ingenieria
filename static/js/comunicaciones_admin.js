/**
 * ARCHIVO: comunicaciones_admin.js
 * Módulo de Gestión de Avisos Institucionales
 */

$(document).ready(function() {
    inicializarTablaGlobal('#tabla-comunicados', 'Buscar comunicados...');

    // 💥 LÓGICA DEL DRAG & DROP DE IMÁGENES/PDF 
    const dropzone = $('#dropzone-adjunto');
    const inputAdjunto = $('#id_archivo_adjunto'); 
    const previewContainer = $('#contenedor-preview-adjunto');
    const imgPreview = $('#img-preview-adjunto');
    const pdfPreview = $('#pdf-preview-adjunto');
    const btnRemover = $('#btn-remover-adjunto');

    // Efecto de color al arrastrar
    inputAdjunto.on('dragenter dragover', function () {
        dropzone.css('background-color', '#e1f5fe'); 
    });

    inputAdjunto.on('dragleave drop', function () {
        dropzone.css('background-color', '#f8f9fa'); 
    });

    // Detectar cuando el usuario elige un archivo
    inputAdjunto.on('change', function () {
        const archivo = this.files[0];
        if (archivo) {
            // Genera una URL temporal en memoria para previsualizar el PDF o la Imagen
            let fileURL = URL.createObjectURL(archivo);
            
            if (archivo.type.startsWith('image/')) {
                imgPreview.attr('src', fileURL).removeClass('d-none');
                pdfPreview.addClass('d-none').attr('src', '#');
            } else if (archivo.type === 'application/pdf') {
                pdfPreview.attr('src', fileURL).removeClass('d-none');
                imgPreview.addClass('d-none').attr('src', '#');
            } else {
                Swal.fire('Formato no soportado', 'Por favor, sube una imagen o un documento PDF.', 'warning');
                removerAdjunto();
                return;
            }

            previewContainer.removeClass('d-none');
            dropzone.addClass('d-none'); 
        } else {
            removerAdjunto();
        }
    });

    btnRemover.on('click', removerAdjunto);

    function removerAdjunto() {
        inputAdjunto.val(''); 
        previewContainer.addClass('d-none');
        imgPreview.attr('src', '#').addClass('d-none');
        pdfPreview.attr('src', '#').addClass('d-none');
        dropzone.removeClass('d-none'); 
    }
});

function abrirModalComunicado() {
    $('#formComunicado')[0].reset();
    $('#comunicado_id').val('');
    
    $('.modal-title').html('<i class="material-symbols-rounded opacity-10 me-2 align-middle">campaign</i> Publicar Nuevo Comunicado');
    $('#btnGuardarComunicado').html('<i class="material-symbols-rounded align-middle text-sm me-1">send</i> Publicar Anuncio');
    $('#div_activo').hide();
    
    // Resetear dropzone
    $('#id_archivo_adjunto').val(''); 
    $('#contenedor-preview-adjunto').addClass('d-none');
    $('#dropzone-adjunto').removeClass('d-none');
    $('#img-preview-adjunto').attr('src', '#').addClass('d-none');
    $('#pdf-preview-adjunto').attr('src', '#').addClass('d-none');
    
    $('#modalCrearComunicado').modal('show');
}

function abrirModalEditarComunicado(id) {
    $.get(`/comunicaciones/gestion/datos/${id}/`, function(data) {
        $('#formComunicado')[0].reset();
        $('#comunicado_id').val(data.id);
        
        $('#id_titulo').val(data.titulo);
        $('#id_mensaje').val(data.mensaje);
        $('#id_importancia').val(data.importancia);
        $('#id_activo').prop('checked', data.activo);
        
        // 💥 Si el backend nos manda la URL del archivo viejo, lo previsualizamos
        if (data.archivo_url && data.archivo_url !== 'None' && data.archivo_url !== '') {
            $('#dropzone-adjunto').addClass('d-none');
            $('#contenedor-preview-adjunto').removeClass('d-none');
            
            if (data.es_imagen === 'True' || data.es_imagen === true) {
                $('#img-preview-adjunto').attr('src', data.archivo_url).removeClass('d-none');
                $('#pdf-preview-adjunto').attr('src', '#').addClass('d-none');
            } else if (data.es_pdf === 'True' || data.es_pdf === true) {
                $('#pdf-preview-adjunto').attr('src', data.archivo_url).removeClass('d-none');
                $('#img-preview-adjunto').attr('src', '#').addClass('d-none');
            }
        } else {
            $('#contenedor-preview-adjunto').addClass('d-none');
            $('#dropzone-adjunto').removeClass('d-none');
            $('#img-preview-adjunto').attr('src', '#').addClass('d-none');
            $('#pdf-preview-adjunto').attr('src', '#').addClass('d-none');
        }
        
        $('.modal-title').html('<i class="material-symbols-rounded opacity-10 me-2 align-middle">edit</i> Editar Comunicado');
        $('#btnGuardarComunicado').html('<i class="material-symbols-rounded align-middle text-sm me-1">save</i> Guardar Cambios');
        $('#div_activo').show();
        
        $('#modalCrearComunicado').modal('show');
    }).fail(function() {
        Swal.fire('Error', 'No se pudieron cargar los datos.', 'error');
    });
}

// 💥 NUEVA FUNCIÓN PARA PODER SUBIR ARCHIVOS (Ignorando guardarRegistroAjax)
async function guardarComunicado() {
    if (!$('#id_titulo').val() || !$('#id_mensaje').val()) {
        mostrarErroresModal({'Datos incompletos': ['El título y el mensaje son obligatorios.']});
        return;
    }

    const formElement = document.getElementById('formComunicado');
    const formData = new FormData(formElement); // Usamos FormData para empaquetar el PDF/Imagen
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    Swal.fire({ title: 'Publicando Anuncio...', allowOutsideClick: false, didOpen: () => { Swal.showLoading(); }});

    try {
        const response = await fetch('/comunicaciones/gestion/guardar/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: formData
        });
        const data = await response.json();

        if (data.success || data.status === 'ok') {
            $('#modalCrearComunicado').modal('hide');
            mostrarNotificacionExito(data.mensaje || 'Comunicado publicado con éxito.');
            
            $('.table-responsive').load(window.location.href + ' #tabla-comunicados', function() {
                if (typeof inicializarTablaGlobal === 'function') {
                    inicializarTablaGlobal('#tabla-comunicados', 'Buscar comunicados...');
                }
            });
        } else {
            if (data.errors) {
                mostrarErroresModal(data.errors);
            } else {
                Swal.fire('Error', data.mensaje || 'No se pudo guardar.', 'error');
            }
        }
    } catch (error) {
        Swal.fire('Error', 'Problema de conexión con el servidor al intentar subir el archivo.', 'error');
    }
}

function eliminarComunicado(id) {
    confirmarEliminacionAjax({
        titulo: '¿Eliminar comunicado?',
        texto: "Esta acción no se puede deshacer y desaparecerá del tablón de los docentes.",
        url: '/comunicaciones/gestion/eliminar/' + id + '/',
        tablaInstancia: typeof tablaComunicados !== 'undefined' ? tablaComunicados : null,
        filaId: 'fila-comunicado-' + id,
        tableId: '#tabla-comunicados',
        textoBuscador: 'Buscar comunicados...'
    });
}

function verComunicadoAsistente(titulo, mensaje, fecha, archivoUrl, esImagen, esPdf) {
    $('#verComTitulo').text(titulo);
    $('#verComMensaje').html(`<p class="mb-3">${mensaje}</p><hr><small class="text-muted"><i class="material-symbols-rounded align-middle text-sm me-1">calendar_month</i>Publicado el: ${fecha}</small>`);
    
    const adjuntoDiv = $('#verComAdjunto');
    adjuntoDiv.empty().removeClass('d-none');
    
    if (archivoUrl && archivoUrl !== 'None' && archivoUrl !== '') {
        if (esImagen === 'True') {
            adjuntoDiv.html(`<img src="${archivoUrl}" class="img-fluid rounded" style="max-height: 400px;" alt="Adjunto">`);
        } else if (esPdf === 'True') {
            adjuntoDiv.html(`<iframe src="${archivoUrl}" width="100%" height="400px" style="border: none;"></iframe>`);
        } else {
            adjuntoDiv.html(`<a href="${archivoUrl}" target="_blank" class="btn btn-outline-info mb-0">Ver Documento Adjunto</a>`);
        }
    } else {
        adjuntoDiv.addClass('d-none');
    }
    
    $('#modalVerComunicado').modal('show');
}