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
        pageLength: 10,
        lengthChange: true,
        ordering: true,
        info: true,
        autoWidth: false,
        responsive: true,
        dom: '<"d-flex justify-content-between align-items-center px-4 pt-3"f l>t<"d-flex justify-content-between align-items-center p-4"ip>',
        initComplete: function () {
            $('.dataTables_filter input')
                .addClass('form-control border-bottom border-2 px-3 py-1')
                .attr('placeholder', textoBuscador);
                
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
                    
                    if (config.tablaInstancia && config.filaId) {
                        config.tablaInstancia.row($(`#${config.filaId}`)).remove().draw(false);
                    } else if (config.tableId) {
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
// 5. MODAL GLOBAL DE CONFIRMACIÓN (Eliminar / Salir)
// ==========================================
function showConfirmModal(title, message, action, type = 'danger', btnText = 'Confirmar') {
    
    // 1. Asignar textos
    $('#modalTitle').text(title);
    $('#modalMessage').text(message);
    $('#modalBtnText').text(btnText);

    // 2. Lógica Inteligente para el Botón de Confirmar
    const $form = $('#modalForm');
    const $confirmBtn = $('#modalConfirmBtn');

    // Limpiamos eventos de clics anteriores para que no se crucen
    $confirmBtn.off('click');
    
    if (typeof action === 'string') {
      // CASO A: Es una URL de Django (Ej. Cerrar Sesión)
      $form.attr('action', action);
      $confirmBtn.attr('type', 'submit'); 
    } else if (typeof action === 'function') {
      // CASO B: Es una función JavaScript (Ej. eliminarAula)
      $form.attr('action', 'javascript:void(0);');
      $confirmBtn.attr('type', 'button'); 
      
      // Si hacen clic, ejecutamos tu función y cerramos el modal
      $confirmBtn.on('click', function() {
        action(); 
        
        var myModalEl = document.getElementById('dynamicConfirmModal');
        var modal = bootstrap.Modal.getInstance(myModalEl);
        modal.hide();
      });
    }

    // 3. Capturar los elementos visuales
    const $iconContainer = $('#modalIconContainer');
    const $modalIcon = $('#modalIcon');
    const $btnIcon = $('#modalBtnIcon');

    // Limpiar clases anteriores
    $iconContainer.attr('class', 'text-center border-radius-2xl mb-3 d-flex align-items-center justify-content-center mx-auto');
    $confirmBtn.attr('class', 'btn btn-sm mb-0 px-3');

    // Configurar colores e íconos
    if (type === 'danger') {
      $iconContainer.addClass('bg-gradient-danger shadow-danger');
      $confirmBtn.addClass('bg-gradient-danger');
      $modalIcon.text('warning');
      $btnIcon.text('delete_forever'); 
    } 
    else if (type === 'warning') {
      $iconContainer.addClass('bg-gradient-warning shadow-warning');
      $confirmBtn.addClass('bg-gradient-warning');
      $modalIcon.text('error_outline');
      $btnIcon.text('warning');
    }
    else if (type === 'success') {
      $iconContainer.addClass('bg-gradient-success shadow-success');
      $confirmBtn.addClass('bg-gradient-success');
      $modalIcon.text('check_circle');
      $btnIcon.text('done');
    }

    if (btnText.toLowerCase().includes('salir') || btnText.toLowerCase().includes('cerrar')) {
      $btnIcon.text('logout');
    }

    // 4. Mostrar el Modal
    var myModal = new bootstrap.Modal($('#dynamicConfirmModal')[0]);
    myModal.show();
}

// ==========================================
// 6. LÓGICA DE COMUNICADOS (MARCAR LEÍDO)
// ==========================================
function marcarAvisoLeidoSilencioso(comunicadoId, elementoBoton) {
    const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfTokenInput) {
        console.error("No se encontró el token CSRF.");
        return;
    }

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
            elementoBoton.classList.remove('bg-gray-100');
            elementoBoton.removeAttribute('onclick');

            const burbujaRoja = document.querySelector('.badge.bg-danger');
            if (burbujaRoja) {
                let numeroActual = parseInt(burbujaRoja.innerText.replace('+', ''));
                if (!isNaN(numeroActual) && numeroActual > 0) {
                    let nuevoNumero = numeroActual - 1;
                    if (nuevoNumero === 0) {
                        burbujaRoja.remove(); 
                    } else {
                        burbujaRoja.innerText = nuevoNumero; 
                    }
                }
            }
        }
    })
    .catch(error => console.error("Error al marcar como leído:", error));
}

// ==========================================
// 7. SCRIPT PARA EL SIDEBAR EN DESKTOP
// ==========================================
$(document).ready(function() {
    const $iconSidenavDesktop = $("#iconSidenavDesktop");
    const $body = $("body");

    if ($iconSidenavDesktop.length) {
      const $iconMaterial = $iconSidenavDesktop.find('i');
      
      $iconSidenavDesktop.on("click", function() {
        if ($body.hasClass("g-sidenav-hidden")) {
          $body.removeClass("g-sidenav-hidden").addClass("g-sidenav-pinned");
          if ($iconMaterial.length) $iconMaterial.text('menu_open');
        } else {
          $body.removeClass("g-sidenav-pinned").addClass("g-sidenav-hidden");
          if ($iconMaterial.length) $iconMaterial.text('menu');
        }
      });
    }
});

$(window).on('load', function() {
    // El Material Dashboard inicializa un plugin llamado PerfectScrollbar que causa
    // que la ruedita del ratón se trabe. Esta técnica "clona" el contenedor, 
    // destruyendo los rastreadores de eventos invisibles del plugin, dejando libre
    // tu scroll nativo que ya estilizaste en custom.css.
    
    let sidebarContenedor = document.getElementById('sidenav-collapse-main');
    
    if (sidebarContenedor) {
        // Clonamos el nodo con todo su contenido
        let clone = sidebarContenedor.cloneNode(true);
        // Reemplazamos el infectado por el clon limpio
        sidebarContenedor.parentNode.replaceChild(clone, sidebarContenedor);
        // Le quitamos la clase 'ps' para que el plugin no intente revivir
        clone.classList.remove('ps'); 
    }
});