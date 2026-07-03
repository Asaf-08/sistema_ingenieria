// Almacenamiento independiente de archivos por cada sección
let tablaPersonal;
const fileStore = {};
let seccionCounter = 0;

// 💥 PARCHE DE SEGURIDAD (XSS)
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

$(document).ready(function () {
    // 1. Inicializar DataTables
    tablaPersonal = $('#tabla-personal-materiales').DataTable({
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json",
            "paginate": {
                "previous": "<i class='material-symbols-rounded' style='font-size: 18px;'>chevron_left</i>",
                "next": "<i class='material-symbols-rounded' style='font-size: 18px;'>chevron_right</i>"
            }
        },
        "columnDefs": [
            { width: "1px", targets: 0 },
            { "orderable": false, "targets": 0 }
        ],
        "responsive": true,
        "order": [
            [4, "asc"], 
            [2, "desc"] 
        ],
        "pageLength": 10,
        "dom": '<"d-flex justify-content-between align-items-center px-4 pt-3"f l>t<"d-flex justify-content-between align-items-center"ip>',
        "initComplete": function () {
            $('.dataTables_filter input')
                .addClass('form-control border-bottom border-2 px-3 py-1')
                .attr('placeholder');

            $('.dataTables_length select')
                .addClass('form-control border-bottom border-2 px-2 py-1 mx-2')
                .css({
                    'display': 'inline-block',
                    'width': 'auto',
                    'background-color': 'transparent'
                });
        }
    });

    // 2. MAGIA: Enumeración Descendente Automática (4, 3, 2, 1)
    tablaPersonal.on('order.dt search.dt', function () {
        let total = tablaPersonal.rows({ search: 'applied' }).count();
        tablaPersonal.column(0, { search: 'applied', order: 'applied' }).nodes().each(function (cell, i) {
            cell.innerHTML = `<span class="text-xs font-weight-bold">${total - i}</span>`;
        });
    }).draw();

    // 💥 3. LÓGICA VISUAL DRAG & DROP CORREGIDA
    $(document).on('dragenter dragover', '.drop-zone input[type="file"]', function (e) {
        $(this).closest('.drop-zone').addClass('drag-active');
    });

    $(document).on('dragleave drop mouseleave', '.drop-zone input[type="file"]', function (e) {
        $(this).closest('.drop-zone').removeClass('drag-active');
    });

    // Inicializar secciones
    crearNuevaSeccion();

    // Lógica del Formulario
    document.getElementById('mainForm').addEventListener('submit', enviarMateriales);
});

async function enviarMateriales(e) {
    e.preventDefault();
    const form = e.target;

    // Validar si hay archivos
    let hasFiles = Object.keys(fileStore).some(k => fileStore[k].files.length > 0);
    if (!hasFiles) {
        Swal.fire('Error', 'Debes adjuntar al menos un archivo.', 'error');
        return;
    }

    Swal.fire({ title: 'Enviando...', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

    const formData = new FormData(form);
    const totalSeccionesVal = parseInt(document.getElementById('total_secciones').value);
    for (let i = 0; i < totalSeccionesVal; i++) {
        if (fileStore[i]) {
            Array.from(fileStore[i].files).forEach(f => formData.append(`archivos_${i}`, f));
        }
    }

    try {
        const endpoint = form.action || window.location.href;
        const response = await fetch(endpoint, { method: 'POST', body: formData, headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const data = await response.json();

        if (data.success) {
            Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Materiales enviados', showConfirmButton: false, timer: 3000 });

            insertarFilaEnDataTable(data.registro);

            form.reset();
            document.getElementById('secciones-container').innerHTML = '';
            Object.keys(fileStore).forEach(k => delete fileStore[k]);
            seccionCounter = 0;
            crearNuevaSeccion();
            
        } else {
            Swal.fire({
                icon: 'warning',
                title: 'No permitido',
                text: data.mensaje || 'Ocurrió un problema al enviar los archivos.',
                confirmButtonColor: '#3a4149'
            });
        }
    } catch (error) {
        Swal.fire('Error', 'No se pudo conectar con el servidor.', 'error');
    }
}

// ==========================================
// LÓGICA DE SECCIONES Y ARCHIVOS (CON "X")
// ==========================================

function crearNuevaSeccion() {
    const container = document.getElementById('secciones-container');
    const id = seccionCounter;

    fileStore[id] = new DataTransfer();

    const div = document.createElement('div');
    div.className = "card border shadow-none p-3 animate__animated animate__fadeInUp";
    div.id = `seccion_${id}`;

    div.innerHTML = `
      <div class="row align-items-center mb-3">
          <div class="col-md-6">
              <div class="input-group input-group-static">
                  <label class="text-info font-weight-bold">Tipo de Material</label>
                  <select name="tipo_${id}" class="form-control" required>
                      <option value="FICHA">Ficha Aplicativa</option>
                      <option value="SESION">Sesión de Aprendizaje</option>
                      <option value="DESAFIO">Desafío Diario</option>
                      <option value="CALIDAD">Control de Calidad</option>
                      <option value="ISO">Examen ISO</option>
                      <option value="ADICIONAL">Adicional</option>
                  </select>
              </div>
          </div>
          <div class="col-md-6 text-end">
              <button type="button" class="btn btn-link text-danger mb-0" onclick="eliminarSeccion(${id})">
                  <i class="material-symbols-rounded align-middle">delete</i> Eliminar Bloque
              </button>
          </div>
      </div>

      <div class="drop-zone border-2 border-dashed border-radius-lg p-4 text-center bg-gray-100 position-relative" style="transition: 0.3s;">
          <i class="material-symbols-rounded text-secondary mb-2" style="font-size: 32px;">upload_file</i>
          <p class="text-sm mb-0 font-weight-bold">Arrastra tus archivos aquí o haz clic para buscar</p>
          <p class="text-xs text-secondary">Imágenes, PDF o Word permitidos</p>
          
          <input type="file" id="input_${id}" multiple accept="image/*,.pdf,.doc,.docx" onchange="manejarSeleccionArchivos(this, ${id})" 
                 style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; z-index: 10;">
      </div>
      
      <div id="lista_archivos_${id}" class="mt-3 d-flex flex-column gap-2"></div>
    `;

    container.appendChild(div);
    seccionCounter++;
    document.getElementById('total_secciones').value = seccionCounter;
    document.getElementById('submit-all').disabled = false;
}

function eliminarSeccion(id) {
    document.getElementById(`seccion_${id}`).remove();
    delete fileStore[id];

    if (Object.keys(fileStore).length === 0) {
        document.getElementById('submit-all').disabled = true;
    }
}

function manejarSeleccionArchivos(input, id) {
    Array.from(input.files).forEach(file => {
        fileStore[id].items.add(file);
    });
    input.value = ""; 
    renderizarListaArchivos(id);
}

function quitarArchivo(seccionId, fileIndex) {
    const dt = fileStore[seccionId];
    const newDt = new DataTransfer();

    Array.from(dt.files).forEach((file, index) => {
        if (index !== fileIndex) newDt.items.add(file);
    });

    fileStore[seccionId] = newDt;
    renderizarListaArchivos(seccionId);
}

function renderizarListaArchivos(id) {
    const lista = document.getElementById(`lista_archivos_${id}`);
    lista.innerHTML = '';

    Array.from(fileStore[id].files).forEach((file, index) => {
        const item = document.createElement('div');
        item.className = "d-flex justify-content-between align-items-center bg-white border border-radius-sm p-2 shadow-sm";
        item.innerHTML = `
            <span class="text-sm text-dark font-weight-bold text-truncate" style="max-width: 85%;">
                <i class="material-symbols-rounded text-info text-sm align-middle me-1">description</i> 
                ${escapeHTML(file.name)}
            </span>
            <button type="button" class="btn btn-link text-danger p-0 m-0" onclick="quitarArchivo(${id}, ${index})" title="Quitar archivo">
                <i class="material-symbols-rounded">close</i>
            </button>
        `;
        lista.appendChild(item);
    });
}

// ==========================================
// LÓGICA DE LA TABLA (AJAX & SWEETALERT)
// ==========================================

function insertarFilaEnDataTable(reg) {
    let materialesHTML = '';
    reg.materiales.forEach(m => {
        materialesHTML += `<span class="text-xs text-dark font-weight-bold d-block">
            <i class="material-symbols-rounded text-info text-xs align-middle">check</i> ${escapeHTML(m.tipo)} <br>
            <span class="text-secondary ms-3">${escapeHTML(String(m.cant))} archivos</span></span>`;
    });

    const botonesAccion = `
        <div class="d-flex gap-2 justify-content-center">
            <button type="button" class="btn bg-white shadow-sm border-radius-md p-2 m-0 text-info" 
                    style="width: 35px; height: 35px;" data-id="${reg.id}" 
                    onclick="abrirModalArchivosPersonal(this)" title="Ver archivos enviados">
                <i class="material-symbols-rounded" style="font-size: 18px;">visibility</i>
            </button>
            <button type="button" class="btn bg-white shadow-sm border-radius-md p-2 m-0 text-danger" 
                    style="width: 35px; height: 35px;" data-id="${reg.id}" data-url="${reg.url_eliminar}" 
                    onclick="confirmarEliminacion(this)" title="Eliminar envío">
                <i class="material-symbols-rounded" style="font-size: 18px;">delete_forever</i>
            </button>
        </div>`;

    const filaHTML = `
        <tr id="fila-solicitud-${reg.id}">
            <td class="ps-4">
                <span class="text-xs font-weight-bold"></span>
            </td>
            <td>
                <div class="d-flex px-3 py-1 flex-column justify-content-center">
                    <h6 class="mb-0 text-sm">${escapeHTML(reg.curso)}</h6>
                    <p class="text-xs text-secondary mb-0">${escapeHTML(reg.tema)}</p>
                </div>
            </td>
            <td><span class="text-xs font-weight-bold">${escapeHTML(reg.fecha)}</span></td>
            <td>
                <div class="d-flex flex-column gap-1">
                    ${materialesHTML}
                </div>
            </td>
            <td class="align-middle text-center" data-order="0">
                <span class="badge badge-sm bg-gradient-secondary">${escapeHTML(reg.estado)}</span>
            </td>
            <td class="align-middle text-center">
                ${botonesAccion}
            </td>
        </tr>
    `;

    tablaPersonal.row.add($(filaHTML)).draw(false);
}

function confirmarEliminacion(btn) {
    const solicitudId = btn.getAttribute('data-id');
    const url = btn.getAttribute('data-url');

    Swal.fire({
        title: '¿Estás seguro?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e91e63',
        cancelButtonColor: '#adb5bd',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then(async (result) => {
        if (result.isConfirmed) {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const response = await fetch(url, { method: 'POST', headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrfToken } });
            const data = await response.json();

            if (data.success) {
                Swal.fire({
                    toast: true,
                    position: 'top-end',
                    icon: 'info', 
                    title: 'Envío cancelado y eliminado',
                    showConfirmButton: false,
                    timer: 3000,
                    timerProgressBar: true,
                    background: '#f57c00', 
                    color: '#fff', 
                    iconColor: '#fff' 
                });
                tablaPersonal.row($(`#fila-solicitud-${solicitudId}`)).remove().draw();
            } else {
                Swal.fire('Error', data.mensaje, 'error');
            }
        }
    });
}

function abrirModalArchivosPersonal(btn) {
    const id = btn.getAttribute('data-id');
    const lista = document.getElementById('lista-archivos-personal-modal');
    const myModal = new bootstrap.Modal(document.getElementById('modalVerArchivosPersonal'));
    
    lista.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-info"></div></div>';
    myModal.show();

    fetch(`/academico/obtener-archivos/${id}/`)
    .then(r => r.json())
    .then(data => {
        lista.innerHTML = '';
        data.archivos.forEach(arc => {
            const li = document.createElement('li');
            li.className = "list-group-item d-flex justify-content-between align-items-center p-3";
            li.innerHTML = `
                <div class="text-truncate" style="max-width: 65%;">
                    <h6 class="mb-0 text-sm font-weight-bold">${escapeHTML(arc.nombre)}</h6>
                    <small class="text-secondary">${escapeHTML(arc.tipo)}</small>
                </div>
                <div class="d-flex gap-2">
                    <a href="${arc.url}" target="_blank" class="btn btn-outline-info btn-sm mb-0 px-3" title="Ver archivo">
                        <i class="material-symbols-rounded text-md align-middle">visibility</i> Ver
                    </a>
                    <a href="${arc.url}" class="btn bg-gradient-info btn-sm mb-0 px-3" download title="Descargar archivo">
                        <i class="material-symbols-rounded text-md align-middle">download</i>
                    </a>
                </div>
            `;
            lista.appendChild(li);
        });
    })
    .catch(err => {
        lista.innerHTML = '<li class="list-group-item text-center text-danger">Error al cargar archivos</li>';
    });
}