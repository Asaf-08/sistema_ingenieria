let tablaInventarioGeneral;
let tablaInventarioDocente;

// 💥 TERCERA REGLA DE ORO: PARCHE DE SEGURIDAD (XSS)
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

$(document).ready(function() {
    // 1. DATATABLES: Vista Coordinadora (Con Paginación y AJAX)
    if ($('#tablaInventarioGeneral').length) {
        tablaInventarioGeneral = $('#tablaInventarioGeneral').DataTable({
            ajax: {
                url: '/academico/api/inventario/general/',
                dataSrc: 'data',
                data: function(d) {
                    d.aula_id = $('#filtroAula').val();
                }
            },
            columns: [
                { data: null, orderable: false, searchable: false, className: 'text-center font-weight-bold text-dark' }, // 💥 Columna N°
                { 
                    data: 'nombre', 
                    className: 'text-start px-4 font-weight-bold text-dark',
                    render: function(data) { return escapeHTML(data); } // Protección XSS
                },
                { data: 'bueno', render: data => `<span class="badge badge-sm bg-gradient-success px-3 fs-6">${escapeHTML(String(data))}</span>` },
                { data: 'regular', render: data => `<span class="badge badge-sm bg-gradient-warning px-3 fs-6">${escapeHTML(String(data))}</span>` },
                { data: 'malo', render: data => `<span class="badge badge-sm bg-gradient-danger px-3 fs-6">${escapeHTML(String(data))}</span>` },
                { data: 'requerido', render: data => `<span class="badge badge-sm bg-gradient-info px-3 fs-6">${escapeHTML(String(data))}</span>` },
                {
                    data: null,
                    orderable: false,
                    searchable: false,
                    render: function(data, type, row) {
                        const safeName = escapeHTML(row.nombre).replace(/'/g, "\\'");
                        return `
                            <div class="d-flex justify-content-center gap-2">
                                <button
                                    class="btn btn-icon-only bg-gradient-dark rounded-circle mb-0 me-2 d-inline-flex align-items-center justify-content-center"
                                    style="width: 36px; height: 36px;"
                                    onclick="abrirEditar('${row.id}', '${safeName}')">
                                    <i class="material-symbols-rounded text-white" style="font-size: 18px;">
                                        edit
                                    </i>
                                </button>
                                <button
                                    class="btn btn-icon-only bg-gradient-dark rounded-circle mb-0 me-2 d-inline-flex align-items-center justify-content-center"
                                    style="width: 36px; height: 36px;"
                                    onclick="eliminarMaterial('${row.id}')">
                                    <i class="material-symbols-rounded text-white" style="font-size: 18px;">
                                        delete
                                    </i>
                                </button>
                            </div>
                        `;
                    }
                }
            ],
            "language": {
            "url": "https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json",
            "paginate": {
                "previous": "<i class='material-symbols-rounded' style='font-size: 18px;'>chevron_left</i>",
                "next": "<i class='material-symbols-rounded' style='font-size: 18px;'>chevron_right</i>"
            }
        },
        "responsive": true,
        "order": [[1, "asc"]],
        "dom": '<"d-flex justify-content-between align-items-center px-4 pt-3"f l>t<"d-flex justify-content-between align-items-center p-4"ip>',
        "initComplete": function () {
            $('.dataTables_filter input')
                .addClass('form-control border-bottom border-2 px-3 py-1')
                .attr('placeholder', "Buscar...")
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

        // 💥 MAGIA: Genera los números dinámicamente aunque se filtre, busque o recargue
        tablaInventarioGeneral.on('draw.dt order.dt search.dt', function () {
            tablaInventarioGeneral.column(0, { search: 'applied', order: 'applied' }).nodes().each(function (cell, i) {
                cell.innerHTML = i + 1;
            });
        }).draw();

        // 💥 NUEVO: Escuchar el select de aulas para recargar la tabla por AJAX
        $('#filtroAula').on('change', function() {
            tablaInventarioGeneral.ajax.reload();
        });
    }

    // 2. DATATABLES: Vista Docente (Solo Buscador, SIN paginación)
    if ($('#tablaInventarioDocente').length) {
        tablaInventarioDocente = $('#tablaInventarioDocente').DataTable({
            paging: false,
            info: false,
            "dom": '<"d-flex justify-content-between align-items-center px-4 pt-3"f l>',
            language: {
                url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json'
            },
            columnDefs: [
                { orderable: false, searchable: false, targets: 0 },
                { orderable: false, targets: [2, 3, 4, 5] }
            ],
            order: [[1, 'asc']]
        });

        // 💥 MAGIA: Números dinámicos también para la tabla del docente
        tablaInventarioDocente.on('order.dt search.dt', function () {
            tablaInventarioDocente.column(0, { search: 'applied', order: 'applied' }).nodes().each(function (cell, i) {
                cell.innerHTML = i + 1;
            });
        }).draw();
    }
});

// ==========================================
// CONTROL DEL MODAL ÚNICO (CREAR / EDITAR)
// ==========================================

function abrirModalCrear() {
    $('#formMaterial')[0].reset();               // Limpia el formulario
    $('#materialId').val('');                    // Vacía el ID oculto (Modo Crear)
    
    // UI: Diseño de Creación
    $('#modalMaterialHeader').removeClass('bg-gradient-warning').addClass('bg-gradient-dark');
    $('#modalMaterialTitle').html('📦 Agregar Nuevo Material');
    $('#btnSubmitMaterial').removeClass('bg-gradient-warning').addClass('bg-gradient-dark').text('Guardar Material');
    
    $('#modalMaterial').modal('show');
}

function abrirEditar(id, nombre) {
    $('#formMaterial')[0].reset();
    $('#materialId').val(id);                    // Llena el ID oculto (Modo Edición)
    $('#nombreMaterial').val(nombre);            // Llena el input de texto
    
    // UI: Diseño de Edición
    $('#modalMaterialHeader').removeClass('bg-gradient-dark').addClass('bg-gradient-warning');
    $('#modalMaterialTitle').html('✏️ Editar Material');
    $('#btnSubmitMaterial').removeClass('bg-gradient-dark').addClass('bg-gradient-warning').text('Actualizar Material');
    
    $('#modalMaterial').modal('show');
}

// ==========================================
// PETICIONES AJAX AL SERVIDOR
// ==========================================

async function guardarCatalogo(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);

    try {
        const res = await fetch(form.action, {
            method: 'POST', body: formData, headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        const data = await res.json();
        
        if (data.success) {
            $('#modalMaterial').modal('hide');
            if (tablaInventarioGeneral) { tablaInventarioGeneral.ajax.reload(null, false); }
            Swal.fire('Éxito', escapeHTML(data.mensaje), 'success');
        } else {
            Swal.fire('Error', escapeHTML(data.mensaje), 'error');
        }
    } catch (error) {
        Swal.fire('Error', 'Fallo de conexión', 'error');
    }
}

async function eliminarMaterial(id) {
    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: "Esta acción no se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (result.isConfirmed) {
        // 💥 EL SECRETO: Capturamos el token de seguridad directamente del HTML
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        const formData = new FormData();
        formData.append('id', id);
        
        try {
            const res = await fetch('/academico/inventario/catalogo/eliminar/', {
                method: 'POST', 
                body: formData, 
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken  // 💥 Se lo enviamos a Django en la cabecera
                }
            });
            const data = await res.json();
            
            if (data.success) {
                if (tablaInventarioGeneral) { tablaInventarioGeneral.ajax.reload(null, false); }
                Swal.fire('Eliminado', escapeHTML(data.mensaje || 'Material eliminado del colegio.'), 'success');
            } else {
                Swal.fire('Atención', escapeHTML(data.mensaje), 'warning'); // Muestra la alerta si ya hay aulas usándolo
            }
        } catch (error) {
            Swal.fire('Error', 'Hubo un error de red.', 'error');
        }
    }
}

// ==========================================
// GUARDAR INVENTARIO DOCENTE (SIN RECARGAR)
// ==========================================

$('#formInventarioDocente').on('submit', async function(e) {
    e.preventDefault(); // Evita la recarga de la página
    
    const form = this;
    const formData = new FormData(form);
    const btnSubmit = $(form).find('button[type="submit"]');
    
    // UX: Cambiamos el texto del botón mientras procesa
    const originalText = btnSubmit.html();
    btnSubmit.html('<span class="spinner-border spinner-border-sm me-2"></span> Guardando...');
    btnSubmit.prop('disabled', true);

    try {
        // window.location.href envía los datos a la misma URL donde estamos
        const res = await fetch(window.location.href, { 
            method: 'POST', 
            body: formData, 
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        });
        const data = await res.json();
        
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: '¡Guardado!',
                text: escapeHTML(data.mensaje),
                timer: 2000, // Se cierra solo en 2 segundos
                showConfirmButton: false
            });
        } else {
            Swal.fire('Error', escapeHTML(data.mensaje || 'Error al guardar.'), 'error');
        }
    } catch (error) {
        Swal.fire('Error', 'Fallo de conexión con el servidor.', 'error');
    } finally {
        // Restauramos el botón a la normalidad
        btnSubmit.html(originalText);
        btnSubmit.prop('disabled', false);
    }
});