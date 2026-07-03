// static/js/main.js

// ==========================================
// 1. CONFIGURACIÓN GLOBAL (SEGURIDAD)
// ==========================================
// 💥 INYECCIÓN AUTOMÁTICA DEL CSRF TOKEN EN TODO EL SISTEMA
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", $('input[name=csrfmiddlewaretoken]').val());
        }
    }
});

// ==========================================
// 2. UTILIDADES GLOBALES (SweetAlert & Toasts)
// ==========================================
function mostrarNotificacionExito(mensaje) {
    $('#toastMensajeGlobal').text(mensaje || 'Acción realizada correctamente.');
    var toastEl = new bootstrap.Toast(document.getElementById('notificacionGlobalToast'));
    toastEl.show();
}

function mostrarErroresModal(erroresObj) {
    let htmlErrores = '<ul style="text-align: left; margin-top: 10px;">';
    for (let campo in erroresObj) {
        let nombreCampo = campo === '__all__' ? 'Error' : campo.charAt(0).toUpperCase() + campo.slice(1);
        htmlErrores += `<li><b>${nombreCampo}:</b> ${erroresObj[campo].join(', ')}</li>`;
    }
    htmlErrores += '</ul>';

    Swal.fire({
        title: 'No se pudo procesar',
        html: htmlErrores,
        icon: 'error',
        confirmButtonColor: '#333333',
        confirmButtonText: 'Entendido'
    });
}

// ==========================================
// 3. INICIALIZADOR DATATABLES
// ==========================================
function inicializarTablaGlobal(idTabla, textoBuscador = "Buscar...") {
    if ($.fn.DataTable.isDataTable(idTabla)) {
        $(idTabla).DataTable().destroy();
    }

    $(idTabla).DataTable({
        // 1. TEXTOS E IDIOMA (De tu versión nueva, mucho más limpios)
        language: {
            url: "https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json",
            search: "_INPUT_",
            searchPlaceholder: textoBuscador,
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
        // 2. CONFIGURACIÓN GENERAL
        pageLength: 10,
        lengthChange: true,
        ordering: true,
        info: true,
        autoWidth: false,
        responsive: true,
        
        // 💥 3. ESTRUCTURA VISUAL (Recuperada de tu versión antigua)
        // Coloca el buscador (f) a la izq y la cantidad (l) a la der
        dom: '<"d-flex justify-content-between align-items-center px-4 pt-3"f l>t<"d-flex justify-content-between align-items-center p-4"ip>',
        
        // 💥 4. INYECCIÓN DE ESTILOS MATERIAL DASHBOARD (Recuperado)
        initComplete: function () {
            // Estilos para la caja de texto del Buscador
            $('.dataTables_filter input')
                .addClass('form-control border-bottom border-2 px-3 py-1')
                .attr('placeholder', textoBuscador);
                
            // Eliminamos textos residuales del buscador
            $('.dataTables_filter label').contents().filter(function () {
                return this.nodeType === 3;
            }).remove();

            // Estilos para el select de cantidad de registros
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

// ==========================================
// 4. FUNCIONES MAESTRAS (CRUD DRY)
// ==========================================
function abrirModalMaestro(config) {
    $(config.formId)[0].reset();
    $(config.inputId).val('');
    $(config.tituloId).text(config.titulo);
    $(config.headerId).removeClass('bg-gradient-info').addClass('bg-gradient-primary');
    $(config.modalId).modal('show');
}

function guardarRegistroAjax(config) {
    $.ajax({
        url: config.url,
        type: 'POST',
        data: $(config.formId).serialize(),
        success: function(response) {
            if (response.status === 'ok' || response.success) {
                $(config.modalId).modal('hide');
                mostrarNotificacionExito(response.message || 'Registro guardado con éxito.');
                
                // Recarga dinámica de la tabla sin refrescar la página (cero parpadeos)
                $('.table-responsive').load(window.location.href + ' ' + config.tableId, function() {
                    if (typeof inicializarTablaGlobal === 'function') {
                        inicializarTablaGlobal(config.tableId, config.textoBuscador || "Buscar...");
                    }
                });
            } else {
                if (response.errors) mostrarErroresModal(response.errors);
            }
        },
        error: function() {
            mostrarErroresModal({'General': ['Ocurrió un error de conexión con el servidor.']});
        }
    });
}

function confirmarEliminacionAjax(config) {
    Swal.fire({
        title: config.titulo || '¿Estás seguro?',
        text: config.texto || "No podrás revertir esto.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#333333', 
        cancelButtonColor: '#f57c00',  
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then(async (result) => {
        if (result.isConfirmed) {
            const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
            const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';
            
            try {
                // Recuperamos tu método fetch ganador
                const response = await fetch(config.url, {
                    method: 'POST',
                    headers: { 
                        'X-Requested-With': 'XMLHttpRequest', 
                        'X-CSRFToken': csrfToken 
                    }
                });
                
                const data = await response.json();
                
                if (data.success || data.status === 'ok') {
                    mostrarNotificacionExito(data.mensaje || data.message || 'Eliminado correctamente.');
                    
                    // Magia para borrar en DataTables sin recargar la página
                    if (config.tablaInstancia && config.filaId) {
                        config.tablaInstancia.row($(`#${config.filaId}`)).remove().draw(false);
                    } else if (config.tableId) {
                        // Respaldo de seguridad: recargar el HTML de la tabla
                        $('.table-responsive').load(window.location.href + ' ' + config.tableId, function() {
                            if (typeof inicializarTablaGlobal === 'function') {
                                inicializarTablaGlobal(config.tableId, config.textoBuscador || "Buscar...");
                            }
                        });
                    }
                } else {
                    mostrarErroresModal({'General': [data.mensaje || data.message || 'No se pudo eliminar.']});
                }
            } catch (error) {
                mostrarErroresModal({'General': ['Error de conexión al intentar eliminar.']});
            }
        }
    });
}

// ==========================================
// 5. LÓGICA DE COMUNICADOS (MARCAR LEÍDO)
// ==========================================
function marcarAvisoLeidoSilencioso(comunicadoId, elementoBoton) {
    // 1. Buscamos la llave de seguridad de Django
    const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfTokenInput) {
        console.error("No se encontró el token CSRF.");
        return;
    }

    // 2. Enviamos el aviso al servidor de fondo
    fetch('/comunicaciones/api/marcar-leido/', {  
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfTokenInput.value,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ 'comunicado_id': comunicadoId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 3A. Magia visual: Quitamos el fondo gris
            elementoBoton.classList.remove('bg-gray-100');
            // Quitamos el onclick para que no vuelva a disparar peticiones al servidor
            elementoBoton.removeAttribute('onclick');

            // 3B. Magia visual: Actualizamos la campanita roja
            const burbujaRoja = document.querySelector('.badge.bg-danger');
            if (burbujaRoja) {
                // Sacamos el número actual (limpiando el "9+" si lo hubiera)
                let numeroActual = parseInt(burbujaRoja.innerText.replace('+', ''));
                if (!isNaN(numeroActual) && numeroActual > 0) {
                    let nuevoNumero = numeroActual - 1;
                    if (nuevoNumero === 0) {
                        burbujaRoja.remove(); // Borramos la burbuja roja si llega a 0
                    } else {
                        burbujaRoja.innerText = nuevoNumero; // Actualizamos el número
                    }
                }
            }
        }
    })
    .catch(error => console.error("Error al marcar como leído:", error));
}