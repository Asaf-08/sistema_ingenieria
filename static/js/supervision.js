/**
 * ARCHIVO: supervision.js (Optimizado Senior - DRY)
 */

$(document).ready(function () {
    inicializarTablaGlobal('#tabla-supervision', 'Buscar en evidencias...');

    // 💥 INICIALIZAR EL DRAG & DROP PARA MATERIALES (Coordinador)
    setupDropzone('id_archivo', 'dropzone-material', 'contenedor-preview-material', 'img-preview-material', 'pdf-preview-material', 'doc-preview-material', 'doc-name-material', 'btn-remover-material');
    
    // 💥 INICIALIZAR EL DRAG & DROP PARA EVIDENCIAS (Docente)
    setupDropzone('id_archivo_evidencia', 'dropzone-evidencia', 'contenedor-preview-evidencia', 'img-preview-evidencia', 'pdf-preview-evidencia', 'doc-preview-evidencia', 'doc-name-evidencia', 'btn-remover-evidencia');

    if ($('#tabla-matriz-cumplimiento').length) {
        var tablaAuditoria = $('#tabla-matriz-cumplimiento').DataTable({
            "language": { "url": "/static/plugins/datatables/js/es-ES.json",
                paginate: {
                    first: "Primero",
                    last: "Último",
                    next: '<i class="material-symbols-rounded" style="font-size: 18px;">chevron_right</i>',
                    previous: '<i class="material-symbols-rounded" style="font-size: 18px;">chevron_left</i>'
                },
             },
            "responsive": true,
            "pageLength": 15,
            "dom": '<"d-flex justify-content-between px-4 pt-3"f>t<"d-flex justify-content-between px-4 pb-3"ip>'
        });
        
        // Estilizar buscador nativo
        $('#tabla-matriz-cumplimiento_filter input').addClass('form-control border-bottom border-2 px-3 py-1').attr('placeholder', 'Buscar docente...');
        $('#tabla-matriz-cumplimiento_filter label').contents().filter(function() { return this.nodeType === 3; }).remove();

        // 💥 AUTO-LLENAR LOS SELECTS DE AULA Y CURSO LEYENDO LA TABLA
        // Columna 1 es Aula, Columna 2 es Curso
        tablaAuditoria.column(1).data().unique().sort().each(function(d, j) {
            $('#filtroAulaAuditoria').append('<option value="'+d+'">'+d+'</option>');
        });
        tablaAuditoria.column(2).data().unique().sort().each(function(d, j) {
            $('#filtroCursoAuditoria').append('<option value="'+d+'">'+d+'</option>');
        });

        // 💥 MOTOR DE BÚSQUEDA PERSONALIZADA PARA LOS SEMÁFOROS Y SELECTS
        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
            if (settings.nTable.id !== 'tabla-matriz-cumplimiento') return true;

            let fAula = $('#filtroAulaAuditoria').val();
            let fCurso = $('#filtroCursoAuditoria').val();
            let fFicha = $('#filtroFichaAuditoria').val();   // "SI" o "NO"
            let fExamen = $('#filtroExamenAuditoria').val(); // "SI" o "NO"

            // Las columnas en 'data[]' inician en 0:
            // data[1] = Aula, data[2] = Curso, data[4] = Ficha, data[6] = Examen
            if (fAula && data[1].indexOf(fAula) === -1) return false;
            if (fCurso && data[2].indexOf(fCurso) === -1) return false;
            
            // Evaluamos los checks (recuerda el <span class="d-none"> oculto que pusimos)
            if (fFicha && data[4].indexOf(fFicha) === -1) return false;
            if (fExamen && data[6].indexOf(fExamen) === -1) return false;

            return true;
        });

        // Evento para que la tabla reaccione al instante cuando se cambia cualquier Select
        $('#filtroAulaAuditoria, #filtroCursoAuditoria, #filtroFichaAuditoria, #filtroExamenAuditoria').on('change', function() {
            tablaAuditoria.draw();
        });
    }

    // 💥 1. REACTIVIDAD: Transformar la columna según el Select
    $('#filtroTemaDinamico').on('change', function() {
        let valorFiltro = $(this).val();
        
        // Cambiamos el título de la columna
        if(valorFiltro === 'GENERAL') {
            $('#th-dinamico').text('Progreso General');
        } else {
            $('#th-dinamico').text('Estado: ' + $("#filtroTemaDinamico option:selected").text());
        }

        // Recorremos todas las filas de la tabla
        $('.celda-dinamica').each(function() {
            let temasData = $(this).data('temas'); // jQuery lee el JSON automáticamente
            let total = $(this).data('total');
            
            if (valorFiltro === 'GENERAL') {
                $(this).html(`<span class="badge bg-gradient-secondary">${total} envíos realizados</span>`);
            } else {
                // Buscamos si el tema o examen elegido existe en el JSON de esta fila
                if (temasData[valorFiltro]) {
                    $(this).html(`<span class="badge bg-gradient-success px-3"><i class="material-symbols-rounded text-sm align-middle me-1">check</i> Entregado</span>`);
                } else {
                    $(this).html(`<span class="badge bg-gradient-danger px-3"><i class="material-symbols-rounded text-sm align-middle me-1">close</i> Pendiente</span>`);
                }
            }
        });
    });
});

// ===============================================
// FUNCIÓN MAESTRA DE PREVISUALIZACIÓN (DRAG & DROP)
// ===============================================
function setupDropzone(inputId, dropzoneId, previewContainerId, imgPreviewId, pdfPreviewId, docPreviewId, docNameId, btnRemoverId) {
    const input = $(`#${inputId}`);
    const dropzone = $(`#${dropzoneId}`);
    const previewContainer = $(`#${previewContainerId}`);
    const imgPreview = $(`#${imgPreviewId}`);
    const pdfPreview = $(`#${pdfPreviewId}`);
    const docPreview = $(`#${docPreviewId}`);
    const docName = $(`#${docNameId}`);
    const btnRemover = $(`#${btnRemoverId}`);

    if (input.length === 0) return;

    // Efecto visual al arrastrar archivo por encima
    $(document).on('dragenter dragover', `#${inputId}`, function () {
        dropzone.addClass('drag-active');
    });

    $(document).on('dragleave drop mouseleave', `#${inputId}`, function () {
        dropzone.removeClass('drag-active');
    });

    // Detectar archivo cargado y previsualizar según el tipo
    input.on('change', function () {
        const archivo = this.files[0];
        if (archivo) {
            let fileURL = URL.createObjectURL(archivo);
            
            // Ocultamos todos los contenedores visuales primero
            imgPreview.addClass('d-none').attr('src', '#');
            pdfPreview.addClass('d-none').attr('src', '#');
            docPreview.addClass('d-none');

            // Lógica de detección ("solo si se ve claro")
            if (archivo.type.startsWith('image/')) {
                imgPreview.attr('src', fileURL).removeClass('d-none');
            } else if (archivo.type === 'application/pdf') {
                pdfPreview.attr('src', fileURL).removeClass('d-none');
            } else {
                // Si es un Word, Excel o archivo crudo, muestra un icono bonito y el nombre
                docName.text(archivo.name);
                docPreview.removeClass('d-none');
            }

            // Escondemos la zona de Drop y mostramos el cuadro de vista previa
            previewContainer.removeClass('d-none');
            dropzone.addClass('d-none'); 
        } else {
            btnRemover.click();
        }
    });

    // Acción de quitar archivo
    btnRemover.on('click', function() {
        input.val(''); 
        previewContainer.addClass('d-none');
        imgPreview.attr('src', '#').addClass('d-none');
        pdfPreview.attr('src', '#').addClass('d-none');
        docPreview.addClass('d-none');
        dropzone.removeClass('d-none'); 
    });
}

// ===============================================
// VISUALIZADOR GLOBAL DE DOCUMENTOS (Para las Listas)
// ===============================================
function verDocumentoEnModal(url, titulo) {
    $('#modalVerDocumentoTitulo').text(titulo);
    
    // Limpiamos los tres marcos por seguridad
    $('#preview-img-global').addClass('d-none').attr('src', '');
    $('#preview-pdf-global').addClass('d-none').attr('src', '');
    $('#preview-other-global').addClass('d-none');
    $('#btn-descargar-doc-global').attr('href', url);

    // Identificamos el tipo de archivo analizando la extensión de su URL
    const ext = url.split('.').pop().toLowerCase();
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) {
        $('#preview-img-global').removeClass('d-none').attr('src', url);
    } else if (ext === 'pdf') {
        $('#preview-pdf-global').removeClass('d-none').attr('src', url);
    } else {
        // Archivos Word, Excel, ZIP, etc. que el navegador no puede dibujar nativamente
        $('#preview-other-global').removeClass('d-none');
    }
    
    $('#modalVerDocumento').modal('show');
}


// ===============================================
// MODALES Y PETICIONES AL SERVIDOR
// ===============================================
function abrirModalMaterial() {
    $('#formMaterial')[0].reset();
    $('#btn-remover-material').click(); // Limpia la previsualización al abrir
    $('#modalMaterial').modal('show');
}

function abrirModalEvidencia() {
    $('#formEvidencia')[0].reset();
    $('#btn-remover-evidencia').click(); // Limpia la previsualización al abrir
    $('#modalEvidencia').modal('show');
}

function abrirModalRevision(id, titulo, docente, feedback) {
    $('#formRevision')[0].reset();
    $('#revision_id').val(id);
    $('#revision_titulo').text(`${titulo} (Docente: ${docente})`);
    $('#revision_feedback').val(feedback);
    $('#modalRevision').modal('show');
}

// 1. Guardar Material Institucional (Coordinadora)
function guardarMaterial() {
    const form = document.getElementById('formMaterial');
    const btn = document.getElementById('btnGuardarMaterial');

    if (!form.checkValidity()) { form.reportValidity(); return; }

    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Subiendo...';

    $.ajax({
        url: '/academico/supervision/material/guardar/',
        type: 'POST',
        data: new FormData(form),
        processData: false, 
        contentType: false, 
        success: function(data) {
            if (data.success) {
                $('#modalMaterial').modal('hide');
                mostrarNotificacionExito(data.mensaje || 'Archivo institucional publicado.');
                
                $('.table-responsive').load(window.location.href + ' #tabla-supervision', function() {
                    inicializarTablaGlobal('#tabla-supervision', 'Buscar en evidencias...');
                });
            } else {
                mostrarErroresModal({'Validación': [data.mensaje || 'Error al subir archivo.']});
            }
        },
        error: function() {
            mostrarErroresModal({'Servidor': ['Error de conexión al procesar el archivo.']});
        },
        complete: function() {
            btn.disabled = false;
            btn.innerHTML = textoOriginal;
        }
    });
}

// 2. Entregar Nueva Evidencia (Docente)
function guardarEvidencia() {
    const form = document.getElementById('formEvidencia');
    const btn = document.getElementById('btnGuardarEvidencia');

    if (!form.checkValidity()) { form.reportValidity(); return; }

    const textoOriginal = btn.innerHTML;
    btn.disabled = true;
    btn.innerText = 'Enviando a Coordinación...';

    $.ajax({
        url: '/academico/supervision/evidencia/entregar/',
        type: 'POST',
        data: new FormData(form),
        processData: false,
        contentType: false,
        success: function(data) {
            if (data.success) {
                $('#modalEvidencia').modal('hide');
                mostrarNotificacionExito(data.mensaje || 'Evidencia enviada con éxito.');
                
                $('.table-responsive').load(window.location.href + ' #tabla-supervision', function() {
                    inicializarTablaGlobal('#tabla-supervision', 'Buscar en evidencias...');
                });
            } else {
                mostrarErroresModal({'Error': [data.mensaje]});
            }
        },
        error: function() {
            mostrarErroresModal({'Servidor': ['No se pudo subir la evidencia. Intente reduciendo el tamaño del archivo.']});
        },
        complete: function() {
            btn.disabled = false;
            btn.innerText = textoOriginal;
        }
    });
}

// 3. Registrar Dictamen / Revisión (Coordinadora)
function guardarRevision(event) {
    if (event) event.preventDefault(); 
    const form = document.getElementById('formRevision');
    const btn = document.getElementById('btnGuardarRevision');

    btn.disabled = true;

    $.ajax({
        url: '/academico/supervision/evidencia/revisar/',
        type: 'POST',
        data: new FormData(form),
        processData: false,
        contentType: false,
        success: function(data) {
            if (data.success) {
                $('#modalRevision').modal('hide');
                mostrarNotificacionExito(data.mensaje || 'Dictamen registrado en el repositorio.');
                
                $('.table-responsive').load(window.location.href + ' #tabla-supervision', function() {
                    inicializarTablaGlobal('#tabla-supervision', 'Buscar en evidencias...');
                });
            } else {
                mostrarErroresModal({'Error': ['No se pudo guardar la evaluación.']});
            }
        },
        error: function() {
            mostrarErroresModal({'Servidor': ['Fallo en la red al procesar el dictamen.']});
        },
        complete: function() {
            btn.disabled = false;
        }
    });
}

// 💥 2. LA API PARA EL MODAL DE DETALLE
function abrirHistorialMateriales(asignacionId) {
    $('#modalHistorialMateriales').modal('show');
    $('#contenidoHistorial').html('<div class="text-center py-5"><div class="spinner-border text-info"></div></div>');
    
    $.get('/academico/supervision/auditoria-materiales/' + asignacionId + '/', function(response) {
        if(response.success) {
            let html = '';
            if(response.historial.length === 0) {
                html = '<div class="alert alert-dark text-center text-white">Aún no se han enviado materiales para esta clase.</div>';
            } else {
                response.historial.forEach(h => {
                    let archivosHtml = h.archivos.map(a => `<a href="${a.url}" target="_blank" class="badge bg-gradient-info text-white me-1 mb-1" style="text-transform: none;"><i class="material-symbols-rounded text-xs align-middle">download</i> ${a.tipo}</a>`).join('');
                    
                    html += `
                    <div class="card shadow-sm border-0 mb-3">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="mb-0 text-dark font-weight-bold">${h.tema}</h6>
                                <span class="badge bg-gradient-secondary">${h.estado}</span>
                            </div>
                            <p class="text-xs text-muted mb-2"><i class="material-symbols-rounded text-xs align-middle">schedule</i> Enviado el ${h.fecha}</p>
                            <div class="mb-3">${archivosHtml}</div>
                            <p class="text-xs text-dark mb-0 bg-light p-2 border-radius-md" style="border-left: 3px solid #17c1e8;"><strong>Indicaciones:</strong> ${h.instrucciones}</p>
                        </div>
                    </div>`;
                });
            }
            $('#contenidoHistorial').html(html);
        }
    });
}