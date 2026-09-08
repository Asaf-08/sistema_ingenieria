/**
 * ARCHIVO: personal.js (Optimizado Senior - Principio DRY)
 */

$(document).ready(function () {
    inicializarTablaPersonal();

    // ==============================================================
    // 💥 LÓGICA DE AUTO-GENERACIÓN DE DOCUMENTO (CÓDIGO INTERNO)
    // ==============================================================
    $('#id_tipo_documento').on('change', function() {
        let tipo = $(this).val();
        let inputDni = $('#id_dni');
        
        if (tipo === 'INT') {
            // Genera código único solo si el campo está vacío o no es un código INT previo.
            // La 'P' es de Personal (Ej: INT-P4829153)
            if (!inputDni.val().startsWith('INT-')) {
                let codigoAleatorio = 'INT-P' + Math.floor(Math.random() * 9000000 + 1000000);
                inputDni.val(codigoAleatorio);
            }
            inputDni.prop('readonly', true);
            inputDni.css('background-color', '#f8f9fa'); 
        } else {
            // Si elige DNI, CE, etc., limpiamos el campo y lo desbloqueamos
            if (inputDni.val().startsWith('INT-')) {
                inputDni.val('');
            }
            inputDni.prop('readonly', false);
            inputDni.css('background-color', 'transparent');
        }
    });
});

function inicializarTablaPersonal(){
    // 💥 1. Destruimos instancias previas para evitar duplicación al recargar (Ajax)
    if ($.fn.DataTable.isDataTable('.tabla-personal')) {
        $('.tabla-personal').DataTable().destroy();
    }

    // 💥 2. Usamos .each() para que cada tabla tenga su propio buscador independiente
    $('.tabla-personal').each(function() {
        $(this).DataTable({
            language: {
                url: "/static/plugins/datatables/js/es-ES.json",
                search: "_INPUT_",
                searchPlaceholder: "Buscar personal...",
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
            pageLength: 25,
            deferRender: true,
            lengthChange: true,
            ordering: true,
            info: true,
            autoWidth: false,
            responsive: true,
            dom: '<"d-flex justify-content-between align-items-center pt-3"f l>t<"d-flex justify-content-between align-items-center p-4"ip>',
            initComplete: function () {
                // 💥 3. Contextualizamos la búsqueda solo al wrapper de ESTA tabla específica
                let $wrapper = $(this).closest('.dataTables_wrapper');
                
                $wrapper.find('.dataTables_filter input')
                    .addClass('form-control border-bottom border-2 px-3 py-1')
                    .attr('placeholder', "Buscar personal...");
                    
                $wrapper.find('.dataTables_filter label').contents().filter(function () {
                    return this.nodeType === 3;
                }).remove();

                $wrapper.find('.dataTables_length select')
                    .addClass('form-control border-bottom border-2 px-2 py-1 mx-2')
                    .css({
                        'display': 'inline-block',
                        'width': 'auto',
                        'background-color': 'transparent'
                    });
            }
        });
    });

    // 💥 4. Solución al bug visual de Bootstrap Tabs: 
    // Recalcula el ancho de las columnas de DataTables al cambiar de pestaña
    $('button[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
        $.fn.dataTable.tables({ visible: true, api: true }).columns.adjust().responsive.recalc();
    });
}

function abrirModalCrearPersonal() {
    abrirModalMaestro({
        formId: '#formPersonal',
        inputId: '#personal_id',
        tituloId: '#modalTituloPersonal',
        headerId: '#modalHeaderPersonal',
        titulo: 'Nuevo Registro de Personal',
        modalId: '#modalPersonal'
    });
    // 💥 Al crear, forzamos que vuelva a DNI y se desbloquee la caja
    $('#id_tipo_documento').val('DNI').trigger('change');
}

function abrirModalEditarPersonal(id) {
    $.get('/personal/datos/' + id + '/', function (data) {
        $('#personal_id').val(data.id);
        
        // 💥 Leemos el tipo de documento de la Base de Datos
        $('#id_tipo_documento').val(data.tipo_documento); 
        $('#id_dni').val(data.dni);
        
        $('#id_nombres').val(data.nombres);
        $('#id_apellidos').val(data.apellidos);
        $('#id_cargo').val(data.cargo);
        $('#id_tipo_contrato').val(data.tipo_contrato);
        $('#id_fecha_ingreso').val(data.fecha_ingreso);
        $('#id_user').val(data.user);
        $('#id_telefono').val(data.telefono);
        $('#id_correo').val(data.correo);

        // 💥 Disparamos la lógica para bloquear/desbloquear según lo cargado
        $('#id_tipo_documento').trigger('change');

        $('#modalTituloPersonal').text('Editar Personal');
        $('#modalHeaderPersonal').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
        $('#modalPersonal').modal('show');
    });
}

function guardarPersonal() {
    guardarRegistroAjax({
        url: '/personal/guardar/',
        formId: '#formPersonal',
        modalId: '#modalPersonal',
        tableId: '.tabla-personal',
        textoBuscador: 'Buscar personal...'
    });
}

function confirmarEliminarPersonal(id, nombre) {
    confirmarEliminacionAjax({
        titulo: '¿Eliminar a ' + nombre + '?',
        texto: "Esta acción no se puede deshacer.",
        url: '/personal/eliminar/' + id + '/',
        tableId: '.tabla-personal',
        textoBuscador: 'Buscar personal...'
    });
}

// ==============================================================
// LÓGICA DE CAMBIO DE ESTADO RÁPIDO
// ==============================================================

function abrirModalEstado(id, estadoActual) {
    $('#personal_id_estado').val(id);
    $('#select_nuevo_estado').val(estadoActual);
    $('#modalEstado').modal('show');
}

function guardarNuevoEstado() {
    const id = $('#personal_id_estado').val();
    const estado = $('#select_nuevo_estado').val();

    $.ajax({
        url: '/personal/cambiar-estado/' + id + '/',
        type: 'POST',
        data: { 'nuevo_estado': estado },
        success: function (response) {
            if (response.status === 'ok' || response.success) {
                $('#modalEstado').modal('hide');
                mostrarNotificacionExito(response.message || response.mensaje || 'Estado actualizado con éxito.');
                
                $('.tabla-personal').load(window.location.href + ' .tabla-personal > *', function () {
                    inicializarTablaPersonal();
                    
                    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
                    tooltipTriggerList.map(function (tooltipTriggerEl) {
                        return new bootstrap.Tooltip(tooltipTriggerEl);
                    });
                });
            } else {
                mostrarErroresModal(response.errors || { 'Error': [response.mensaje || 'No se pudo actualizar el estado.'] });
            }
        },
        error: function () {
            mostrarErroresModal({'Servidor': ['Error al intentar conectar con el servidor.']});
        }
    });
}

// ==============================================================
// 💥 FUNCIÓN PARA VER DETALLES EN MODAL DE SOLO LECTURA
// ==============================================================
function verDetallesPersonal(id, btn) {
    let $btn = $(btn);
    
    // 1. LIMPIEZA TOTAL: Ocultamos usando d-none y quitamos d-flex para evitar conflictos
    $('#box_tutoria, #box_cursos, #box_niveles').removeClass('d-flex').addClass('d-none');
    $('#det_tutoria, #det_cursos, #det_niveles').html('-');

    // 2. Extraemos los datos infalibles directamente del HTML
    let tutoriaHtml = $btn.data('tutoria');
    let cursosHtml = $btn.data('cursos');
    let nivelesHtml = String($btn.data('niveles'));
    let estadoReal = $btn.data('estado');
    let cargoReal = $btn.data('cargo');
    let contratoReal = $btn.data('contrato');

    // 💥 NUEVO: Filtro inteligente para eliminar niveles duplicados
    if (nivelesHtml && nivelesHtml !== 'None' && nivelesHtml !== '-') {
        // Convertimos el texto "Secundaria, Secundaria" en un arreglo, 
        // usamos Set() para borrar repetidos y lo volvemos a unir.
        let nivelesArray = nivelesHtml.split(',').map(n => n.trim());
        nivelesHtml = [...new Set(nivelesArray)].join(', ');
    }

    // 3. Pintamos el Estado Inmediatamente
    let $estadoBadge = $('#det_estado_badge');
    if (estadoReal === 'Activo') {
        $estadoBadge.text('ACTIVO').removeClass('bg-gradient-secondary').addClass('bg-gradient-success');
    } else {
        $estadoBadge.text('INACTIVO').removeClass('bg-gradient-success').addClass('bg-gradient-secondary');
    }

    // 4. LÓGICA ACADÉMICA ESTRICTA (Solo si es DOCENTE)
    if (cargoReal === 'DOC') { 
        
        if (contratoReal === 'Fijo') {
            // Es Docente Fijo: Ve Tutoría y Nivel.
            $('#det_tutoria').html(tutoriaHtml && tutoriaHtml !== 'None' ? tutoriaHtml : '<span class="text-secondary fw-normal">Sin aula asignada</span>');
            $('#det_niveles').html(nivelesHtml && nivelesHtml !== 'None' ? nivelesHtml : '-');
            
            // Mostramos devolviendo el d-flex
            $('#box_tutoria, #box_niveles').removeClass('d-none').addClass('d-flex');
            
        } else if (contratoReal === 'Por Horas') {
            // Es Docente Por Horas: Ve Cursos apilados y Nivel.
            let cursosStr = String(cursosHtml);
            let cursosApilados = (cursosStr && cursosStr !== 'None' && cursosStr !== 'undefined') ? cursosStr.split(', ').join('<br>') : '-';
            
            $('#det_cursos').html(cursosApilados);
            $('#det_niveles').html(nivelesHtml && nivelesHtml !== 'None' ? nivelesHtml : '-');
            
            // Mostramos devolviendo el d-flex
            $('#box_cursos, #box_niveles').removeClass('d-none').addClass('d-flex');
        }
    } 

    // 5. Consumimos la API solo para los datos de texto (nombres, contactos, etc.)
    $.get('/personal/datos/' + id + '/', function (data) {
        
        $('#det_nombre_completo').text(data.nombres + ' ' + data.apellidos);
        $('#det_dni').text(data.tipo_documento + ' - ' + data.dni);
        
        // Mapeo exhaustivo de los cargos
        let cargoTexto = data.cargo;
        if(cargoReal === 'DOC') cargoTexto = 'Docente';
        else if(cargoReal === 'DIR') cargoTexto = 'Director(a)';
        else if(cargoReal === 'COO') cargoTexto = 'Coordinador(a)';
        else if(cargoReal === 'SEC') cargoTexto = 'Secretaria(o)';
        else if(cargoReal === 'ASI') cargoTexto = 'Asistente';
        else if(cargoReal === 'AUX') cargoTexto = 'Auxiliar';
        else if(cargoReal === 'MAN') cargoTexto = 'Mantenimiento';
        
        $('#det_cargo').text(cargoTexto);
        $('#det_contrato_badge').text(contratoReal); 
        
        $('#det_telefono').text(data.telefono ? data.telefono : 'No registrado');
        $('#det_correo').text(data.correo ? data.correo : 'No registrado');
        $('#det_ingreso').text(data.fecha_ingreso ? data.fecha_ingreso : 'No registrada');

        $('#modalDetallesPersonal').modal('show');
    }).fail(function() {
        mostrarErroresModal({'Error': ['No se pudo cargar la información de contacto del personal.']});
    });
}