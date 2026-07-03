$(document).ready(function() {
    // Reutilizamos tu función global con la tabla del tablón
    if (typeof inicializarTablaGlobal === 'function') {
        inicializarTablaGlobal('#tabla-tablon', 'Buscar en el tablón...');
    }
});

function verComunicadoDocente(id, titulo, mensaje, fecha, archivoUrl, esImagen, esPdf, yaLeido) {
    // 1. Llenamos el Modal con los datos
    $('#verComTitulo').text(titulo);
    $('#verComMensaje').html(`<p class="mb-3">${mensaje}</p><hr><small class="text-muted"><i class="material-symbols-rounded align-middle text-sm me-1">calendar_month</i>Publicado el: ${fecha}</small>`);
    
    const adjuntoDiv = $('#verComAdjunto');
    adjuntoDiv.empty().removeClass('d-none');
    
    if (archivoUrl && archivoUrl !== 'None' && archivoUrl !== '') {
        if (esImagen === 'True' || esImagen === 'true') {
            adjuntoDiv.html(`<img src="${archivoUrl}" class="img-fluid rounded" style="max-height: 400px; object-fit: contain;" alt="Adjunto">`);
        } else if (esPdf === 'True' || esPdf === 'true') {
            adjuntoDiv.html(`<iframe src="${archivoUrl}" width="100%" height="400px" style="border: none;"></iframe>`);
        } else {
            adjuntoDiv.html(`<a href="${archivoUrl}" target="_blank" class="btn btn-outline-info mb-0">Ver Documento Adjunto</a>`);
        }
    } else {
        adjuntoDiv.addClass('d-none');
    }
    
    $('#modalVerComunicado').modal('show');

    // 2. MAGIA DE ARQUITECTO: Si no lo había leído, lo marcamos en BD silenciosamente
    if (yaLeido === 'False' || yaLeido === 'false') {
        const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        const token = csrfTokenInput ? csrfTokenInput.value : '';

        fetch('/comunicaciones/api/marcar-leido/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ 'comunicado_id': id })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizamos la etiqueta de la tabla a 'Leído' (Verde)
                $(`#td-estado-${id}`).html(`
                    <span class="badge badge-sm bg-gradient-success">
                        <i class="material-symbols-rounded text-xxs align-middle me-1">done_all</i> Leído
                    </span>
                `);
            }
        }).catch(err => console.error("Error al marcar como leído", err));
    }
}