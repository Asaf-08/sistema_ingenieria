/**
 * ARCHIVO: comunicaciones_admin.js
 * Módulo de Gestión de Avisos Institucionales
 */
// Variable global
let tablaComunicados;

// 💥 1. Creamos una función exclusiva para esta tabla
function inicializarTablaComunicados() {
    if ($.fn.DataTable.isDataTable('#tabla-comunicados')) {
        $('#tabla-comunicados').DataTable().destroy();
    }

    tablaComunicados = $('#tabla-comunicados').DataTable({
        language: {
            url: "/static/plugins/datatables/js/es-ES.json",
            search: "_INPUT_",
            searchPlaceholder: "Buscar comunicados...",
            lengthMenu: "Mostrar _MENU_ registros",
            info: "Mostrando _START_ a _END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0 a 0 de 0 registros",
            zeroRecords: "No se encontraron resultados",
            paginate: {
                first: "Primero",
                last: "Último",
                next: '<i class="material-symbols-rounded" style="font-size: 18px;">chevron_right</i>',
                previous: '<i class="material-symbols-rounded" style="font-size: 18px;">chevron_left</i>'
            }
        },
        pageLength: 10,
        lengthChange: true,
        order: [[0, "desc"]], // Orden por fecha (columna 0)
        info: true,
        autoWidth: false,
        responsive: true,
        dom: '<"d-flex justify-content-between align-items-center px-4 pt-3"f l>t<"d-flex justify-content-between align-items-center p-4"ip>',
        initComplete: function () {
            $('.dataTables_filter input')
                .addClass('form-control border-bottom border-2 px-3 py-1')
                .attr('placeholder', 'Buscar comunicados...');
                
            $('.dataTables_filter label').contents().filter(function () {
                return this.nodeType === 3;
            }).remove();

            $('.dataTables_length select')
                .addClass('form-control border-bottom border-2 px-2 py-1 mx-2')
                .css({
                    'display': 'inline-block',
                    'width': 'auto',
                    'background-color': 'transparent'
                });
        }
    });
}

$(document).ready(function() {
    inicializarTablaComunicados();

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

    // 1. Mostrar modal y caja de resumen al seleccionar "PERSONALIZADO"
    $('#id_audiencia').on('change', function() {
        if ($(this).val() === 'PERSONALIZADO') {
            $('#modalPersonalizado').modal('show');
        } else {
            // Si elige otra opción, ocultamos la cajita y limpiamos el input oculto
            $('#div_resumen_personalizado').addClass('d-none');
            $('#input_destinatarios').val(''); 
        }
    });

    // 💥 SOLUCIÓN BLINDADA: Evento de cierre del modal personalizado
    $('#modalPersonalizado').on('hidden.bs.modal', function () {
        let $input = $('#input_destinatarios');
        
        // 1. Auditoría: Si el input no existe, avisamos en consola para detectarlo rápido
        if ($input.length === 0) {
            console.error("Error Arquitectura: No se encontró el <input id='input_destinatarios'> en tu HTML.");
            return; // Detenemos la función para que no te borre la interfaz
        }

        let destinatarios = $input.val() || '';
        
        // 2. Solo si el input está verdaderamente vacío, revertimos la interfaz a TODOS
        if ($('#id_audiencia').val() === 'PERSONALIZADO' && destinatarios.trim() === '') {
            $('#id_audiencia').val('TODOS');
            $('#div_resumen_personalizado').addClass('d-none');
        }
    });

    // 💥 LIMPIEZA TOTAL: Cuando se cierra el modal principal de Comunicados
    $('#modalCrearComunicado').on('hidden.bs.modal', function () {
        // 1. Reseteamos el formulario y los inputs ocultos
        $('#formComunicado')[0].reset();
        $('#comunicado_id').val('');
        $('#input_destinatarios').val('');
        
        // 2. Regresamos el select a la opción por defecto
        $('#id_audiencia').val('TODOS');
        
        // 3. Ocultamos y reseteamos la cajita de resumen personalizado
        $('#div_resumen_personalizado').addClass('d-none');
        $('#txt_cant_seleccionados').text('0');
        
        // 4. Ocultamos el switch de "Activo" (por si venía del modo edición)
        $('#div_activo').hide();
    });

    // 2. Inicializar el DataTable
    var tablaPers = $('#tablaPersonalizado').DataTable({
        "language": {
            url: "/static/plugins/datatables/js/es-ES.json",
            paginate: {
                first: "Primero",
                last: "Último",
                next: '<i class="material-symbols-rounded" style="font-size: 18px;">chevron_right</i>',
                previous: '<i class="material-symbols-rounded" style="font-size: 18px;">chevron_left</i>'
            },
        },
        "responsive": true,
        "pageLength": 10,
        "dom": '<"d-flex justify-content-between px-3 pt-2"f>t<"d-flex justify-content-between p-3"ip>',
        "order": [[1, "asc"]],
        "columnDefs": [
            { "orderable": false, "targets": 0 } // Desactiva ordenamiento en el checkbox
        ]
    });

    // 3. 💥 MAGIA: Lógica de Filtros Personalizados para DataTables
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        if (settings.nTable.id !== 'tablaPersonalizado') return true; // Solo afectar a esta tabla

        let fNivel = $('#filtroNivelPersonalizado').val().toLowerCase();
        let fContrato = $('#filtroContratoPersonalizado').val().toLowerCase();
        let fTutor = $('#filtroTutorPersonalizado').val(); // SI / NO

        // Las columnas de data[] se basan en el HTML: 1:Nombre, 2:Cargo, 3:Contrato, 4:Dicta, 5:Tutor
        let rowContrato = data[3].toLowerCase();
        let rowDicta = data[4].toLowerCase();
        let rowTutor = data[5].toLowerCase();

        // Evaluaciones
        if (fContrato && rowContrato.indexOf(fContrato) === -1) return false;
        if (fNivel && rowDicta.indexOf(fNivel) === -1) return false;
        if (fTutor === 'SI' && rowTutor.indexOf('no es tutor') !== -1) return false;
        if (fTutor === 'NO' && rowTutor.indexOf('no es tutor') === -1) return false;

        return true;
    });

    // Redibujar la tabla cuando cambie algún filtro desplegable
    $('#filtroNivelPersonalizado, #filtroContratoPersonalizado, #filtroTutorPersonalizado').on('change', function() {
        tablaPers.draw();
        actualizarCheckAllState(); // Actualiza visualmente el "Seleccionar Todos"
    });

    // 4. 💥 MAGIA: Seleccionar TODOS (Solo los filtrados visibles)
    $('#checkAllPersonalizado').on('change', function() {
        let isChecked = $(this).is(':checked');
        
        // .rows({ search: 'applied' }) te trae solo los que sobrevivieron al filtro
        tablaPers.rows({ search: 'applied' }).nodes().to$().find('.check-personal').prop('checked', isChecked);
        actualizarContador();
    });

    // Actualizar contador al marcar checks individuales
    $('#tablaPersonalizado tbody').on('change', '.check-personal', function() {
        actualizarContador();
        actualizarCheckAllState();
    });

    function actualizarContador() {
        let cont = $('#tablaPersonalizado').find('.check-personal:checked').length;
        $('#contadorSeleccionados').text(cont);
    }

    function actualizarCheckAllState() {
        let visibles = tablaPers.rows({ search: 'applied' }).nodes().to$().find('.check-personal').length;
        let marcadosVisibles = tablaPers.rows({ search: 'applied' }).nodes().to$().find('.check-personal:checked').length;
        $('#checkAllPersonalizado').prop('checked', visibles > 0 && visibles === marcadosVisibles);
    }
});

function abrirModalComunicado() {
    $('#formComunicado')[0].reset();
    $('#comunicado_id').val('');
    
    $('.titulo-modal').html('<i class="material-symbols-rounded opacity-10 me-2 align-middle">campaign</i> Publicar Nuevo Comunicado');
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
        
        $('.titulo-modal').html('<i class="material-symbols-rounded opacity-10 me-2 align-middle">edit</i> Editar Comunicado');
        $('#btnGuardarComunicado').html('<i class="material-symbols-rounded align-middle text-sm me-1">save</i> Guardar Cambios');
        $('#div_activo').show();
        
        $('#modalCrearComunicado').modal('show');
    }).fail(function() {
        Swal.fire('Error', 'No se pudieron cargar los datos.', 'error');
    });
}

// 💥 1. Asegúrate de poner la palabra 'event' dentro de los paréntesis
async function guardarComunicado(event) {
    if (event) {
        event.preventDefault(); 
    }

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
            
            // 💥 2. LA SOLUCIÓN: Forzamos el cierre de la alerta de carga
            Swal.close(); 
            
            // Y ahora sí lanzamos nuestro Toast suave y elegante
            mostrarNotificacionExito(data.mensaje || 'Comunicado publicado con éxito.');
            
            // 💥 3. SOLUCIÓN SIMPLE Y ROBUSTA: Recargamos toda la página después de 1.5 segundos
            window.location.reload();
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

function eliminarComunicado(btn) {
    // 💥 1. Extraemos el ID numérico del botón que pasaste como "this"
    const id = btn.getAttribute('data-id');

    // 💥 2. Llamamos a tu función global INTACTA, ahora con el ID correcto
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

// 5. Función al Guardar la selección
function guardarSeleccionPersonalizada() {
    let seleccionados = [];
    // Obtenemos los marcados
    $('#tablaPersonalizado').DataTable().$('.check-personal:checked').each(function() {
        seleccionados.push($(this).val());
    });

    if(seleccionados.length === 0) {
        Swal.fire('Atención', 'Debes seleccionar al menos a una persona.', 'warning');
        return;
    }

    // 1. Guardamos en el input oculto
    $('#input_destinatarios').val(seleccionados.join(','));
    
    // 2. Actualizamos el número en la cajita y la mostramos
    $('#txt_cant_seleccionados').text(seleccionados.length);
    $('#div_resumen_personalizado').removeClass('d-none');
    
    // 3. Cerramos el modal
    $('#modalPersonalizado').modal('hide');
    mostrarNotificacionExito("Se seleccionaron " + seleccionados.length + " personas.");
}

// 💥 LA MAGIA DEL SWEETALERT (Diseño Premium)
function verSeleccionadosPersonalizados() {
    let nombresHTML = '';
    let contador = 0;
    
    // Extraemos los nombres y cargos directamente del DataTable
    $('#tablaPersonalizado').DataTable().$('.check-personal:checked').each(function() {
        let nombre = $(this).closest('tr').find('td:eq(1) p').text();
        let cargo = $(this).closest('tr').find('td:eq(2)').text().trim();
        
        nombresHTML += `
            <div class="d-flex align-items-center mb-2 p-2 border-radius-lg shadow-sm" style="background-color: #ffffff; border-left: 4px solid #17c1e8;">
                <div class="icon icon-shape icon-sm bg-gradient-info text-center border-radius-md me-3 d-flex align-items-center justify-content-center">
                    <i class="material-symbols-rounded text-white" style="font-size: 18px;">person</i>
                </div>
                <div class="d-flex flex-column text-start">
                    <h6 class="mb-0 text-sm font-weight-bold text-dark">${nombre}</h6>
                    <span class="text-xs text-secondary font-weight-bold">${cargo}</span>
                </div>
            </div>
        `;
        contador++;
    });

    Swal.fire({
        title: `<h5 class="text-info font-weight-bolder mb-0">Personal Seleccionado (${contador})</h5>`,
        html: `<div class="text-start m-0 p-3" style="max-height: 350px; overflow-y: auto; background-color: #f8fbff; border-radius: 12px; border: 1px dashed #17c1e8;">
                  ${nombresHTML}
               </div>`,
        showConfirmButton: true,
        confirmButtonColor: '#333333',
        confirmButtonText: '<i class="material-symbols-rounded text-sm align-middle me-1">close</i> Cerrar Lista',
        customClass: {
            popup: 'border-radius-xl'
        }
    });
}

// 💥 NUEVO: AUDITORÍA DE LECTURAS
function verReporteLecturas(comunicadoId) {
    // 1. Abrimos el modal con estado de carga
    $('#tbody-lecturas').html(`
        <tr>
            <td colspan="4" class="text-center py-4">
                <div class="spinner-border text-info" role="status"></div>
                <p class="text-sm mt-2 text-secondary mb-0">Obteniendo auditoría de lectura...</p>
            </td>
        </tr>
    `);
    $('#modalLecturas').modal('show');

    // 2. Disparamos la consulta al backend
    $.get('/comunicaciones/api/lecturas/' + comunicadoId + '/', function(response) {
        if (response.success) {
            let html = '';
            
            if (response.lecturas.length === 0) {
                html = '<tr><td colspan="4" class="text-center py-3 text-secondary text-sm">No hay destinatarios registrados para este comunicado.</td></tr>';
            } else {
                // 3. Pintamos cada fila dinámicamente
                response.lecturas.forEach(p => {
                    let badgeEstado = p.leido 
                        ? '<span class="badge badge-sm bg-gradient-success">Leído</span>' 
                        : '<span class="badge badge-sm bg-gradient-secondary">Pendiente</span>';
                    
                    let fecha = p.leido && p.fecha_lectura 
                        ? `<span class="text-xs text-secondary font-weight-bold"><i class="material-symbols-rounded text-sm align-middle me-1">calendar_today</i>${p.fecha_lectura}</span>` 
                        : '<span class="text-xs text-muted">-</span>';
                    
                    html += `
                    <tr>
                        <td class="ps-3"><h6 class="mb-0 text-sm text-dark">${p.nombre}</h6></td>
                        <td><p class="text-xs font-weight-bold mb-0">${p.cargo}</p></td>
                        <td class="text-center">${badgeEstado}</td>
                        <td class="text-center">${fecha}</td>
                    </tr>`;
                });
            }
            $('#tbody-lecturas').html(html);
        } else {
            $('#modalLecturas').modal('hide');
            Swal.fire('Error', 'No se pudo obtener el reporte de lecturas.', 'error');
        }
    }).fail(function() {
        $('#modalLecturas').modal('hide');
        Swal.fire('Error', 'Problema de conexión con el servidor al cargar la auditoría.', 'error');
    });
}