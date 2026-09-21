$(document).ready(function () {
    // Inicialización de DataTables
    let tabla = $('#tabla-imprenta').DataTable({
        "language": {
            "url": "/static/plugins/datatables/js/es-ES.json",
            "paginate": {
                "previous": "<i class='material-symbols-rounded' style='font-size: 18px;'>chevron_left</i>",
                "next": "<i class='material-symbols-rounded' style='font-size: 18px;'>chevron_right</i>"
            }
        },
        "columnDefs": [
            { width: "1px", targets: 0 },
            { width: "1px", targets: 1 }, // Se expandirá dinámicamente hasta el contenido más largo
            { "orderable": false, "targets": 0 }
        ],
        "responsive": true,
        "order": [
            [3, "desc"]  // SEGUNDO: Ordena por Fecha (Los más recientes primero)
        ],
        "pageLength": 10,
        "dom": '<"d-flex justify-content-between align-items-center px-4 pt-3"f l>t<"d-flex justify-content-between align-items-center"ip>',
        "initComplete": function () {
            // Estilos para el BUSCADOR (Inyectamos el texto dinámicamente)
            $('.dataTables_filter input')
                .addClass('form-control border-bottom border-2 px-3 py-1')
                .attr('placeholder');

            // Estilos para el SELECTOR DE CANTIDAD
            $('.dataTables_length select')
                .addClass('form-control border-bottom border-2 px-2 py-1 mx-2')
                .css({
                    'display': 'inline-block',
                    'width': 'auto',
                    'background-color': 'transparent'
                });
        }
    });
    // 2. MAGIA: Enumeración visual descendente automática
    tabla.on('order.dt search.dt', function () {
        let totalRegistros = tabla.rows({ search: 'applied' }).nodes().length;
        tabla.column(0, { search: 'applied', order: 'applied' }).nodes().each(function (cell, i) {
            // El primero tendrá el número máximo, y va bajando hasta 1
            cell.innerHTML = `<span class="text-xs font-weight-bold">${totalRegistros - i}</span>`;
        });
    }).draw();
});

function cambiarEstadoAsistente(selectElement) {
    const id = selectElement.getAttribute('data-id');
    const valor = selectElement.value;
    const csrfToken = document.getElementById('csrf_token_global').value;

    // Cambios visuales instantáneos
    selectElement.classList.remove('bg-warning', 'bg-success');

    if (valor === 'LISTO' || valor === 'ENTREGADO') {
        selectElement.classList.add('bg-success');
        document.getElementById(`icon-${id}`).innerHTML = '<i class="material-symbols-rounded text-success" style="font-size: 24px;">check_circle</i>';
    } else {
        selectElement.classList.add('bg-warning');
        document.getElementById(`icon-${id}`).innerHTML = '<i class="material-symbols-rounded text-warning animate__animated animate__flash animate__infinite" style="font-size: 24px;">schedule</i>';
    }

    // Petición AJAX
    const formData = new FormData();
    formData.append('estado', valor);
    formData.append('csrfmiddlewaretoken', csrfToken);

    fetch(`/academico/imprenta/actualizar/${id}/`, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Estado actualizado', showConfirmButton: false, timer: 1500 });
            }
        });
}

function verInstrucciones(btnElement) {
    const nota = btnElement.getAttribute('data-nota');
    Swal.fire({ title: 'Instrucciones del Docente', text: nota, icon: 'info', confirmButtonColor: '#fb8c00' });
}

function abrirModalArchivos(btnElement) {
    const solicitudId = btnElement.getAttribute('data-id');
    const copiasTotal = btnElement.getAttribute('data-copias');
    const detalleStr = btnElement.getAttribute('data-detalle'); 

    // 1. 💥 Construimos el Dropdown Limpio (Sin títulos ni totales)
    let dropdownItems = '';
    
    if (detalleStr) {
        const aulas = detalleStr.split('|');
        aulas.forEach(item => {
            if (item) {
                const partes = item.split(':'); 
                dropdownItems += `
                <li class="d-flex justify-content-between align-items-center mb-1">
                    <span class="text-dark me-4 font-weight-bold">${partes[0]}</span>
                    <span class="text-info font-weight-bold">${partes[1]}</span>
                </li>`;
            }
        });
    }

    // 2. Lo inyectamos visualmente (Alineación natural y flecha corregida)
    document.getElementById('modal-badge-copias-container').innerHTML = `
        <div class="dropdown d-inline-block">
            <button class="btn btn-sm bg-white text-dark shadow-sm mb-0 px-3 d-flex align-items-center" type="button" data-bs-toggle="dropdown" aria-expanded="false" data-bs-auto-close="false">
                <span class="font-weight-bold fs-6">${copiasTotal}</span>
                <i class="material-symbols-rounded text-md ms-1 text-dark">keyboard_arrow_down</i>
            </button>
            <ul class="dropdown-menu dropdown-menu-center px-3 py-2 shadow-lg mt-1 border">
                ${dropdownItems}
            </ul>
        </div>
    `;

    const modal = new bootstrap.Modal(document.getElementById('modalArchivos'));
    const lista = document.getElementById('lista-archivos-modal');
    
    // ... AQUÍ CONTINÚA TU CÓDIGO ORIGINAL ...
    lista.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-info"></div></div>';
    modal.show();

    // Pide los archivos al servidor (Aquí es donde daba el error 404 antes)
    fetch(`/academico/obtener-archivos/${solicitudId}/`)
        .then(r => r.json())
        .then(data => {
            lista.innerHTML = ''; // Limpiamos el cargando

            if (data.archivos.length === 0) {
                lista.innerHTML = '<li class="list-group-item text-center text-secondary">No hay archivos.</li>';
                return;
            }

            data.archivos.forEach(arc => {
                const li = document.createElement('li');
                li.className = "list-group-item d-flex justify-content-between align-items-center";
                // (Fragmento dentro del data.archivos.forEach)
                li.innerHTML = `
                <div class="text-truncate" style="max-width: 60%;">
                    <h6 class="mb-0 text-sm"><i class="material-symbols-rounded text-info text-sm align-middle">description</i> ${arc.nombre}</h6>
                    <small class="text-secondary">${arc.tipo}</small>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-dark btn-sm mb-0" onclick="imprimirArchivo('${arc.url}')" title="Abrir para imprimir">
                        <i class="material-symbols-rounded text-md align-middle">print</i> Imprimir
                    </button>
                    
                    <!-- 💥 Cambiamos la etiqueta <a> por este <button> -->
                    <button class="btn bg-gradient-info btn-sm mb-0" onclick="forzarDescarga('${arc.url}', '${arc.nombre}')" title="Descargar PDF/Word">
                        <i class="material-symbols-rounded text-md align-middle">download</i>
                    </button>
                </div>
            `;
                lista.appendChild(li);
            });
        })
        .catch(error => {
            lista.innerHTML = '<li class="list-group-item text-center text-danger">Error al cargar archivos.</li>';
        });
}

function imprimirArchivo(url) {
    // Abre el archivo en una nueva pestaña. Si es PDF, el navegador mostrará su propio botón de imprimir.
    window.open(url, '_blank');
}

function forzarDescarga(url, nombreArchivo) {
    // 1. Mostramos una alerta de carga para archivos pesados
    Swal.fire({ 
        toast: true, 
        position: 'top-end', 
        title: 'Descargando archivo...', 
        showConfirmButton: false, 
        timerProgressBar: true, 
        didOpen: () => Swal.showLoading() 
    });

    // 2. Traemos el archivo desde Amazon S3
    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            // 3. Lo empaquetamos y forzamos la descarga local
            const urlBlob = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = urlBlob;
            a.download = nombreArchivo;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(urlBlob);
            Swal.close();
        })
        .catch(error => {
            Swal.close();
            // Plan B: Si la red falla o el archivo es muy masivo, lo abre en otra pestaña
            window.open(url, '_blank');
        });
}

// ========================================================
// 💥 DESCARGA MASIVA Y EMPAQUETADO ZIP EN EL CLIENTE
// ========================================================
async function descargarPaqueteZIP(solicitudId, nombreCarpeta) {
    // 1. Mostrar pantalla de carga amigable
    Swal.fire({ 
        title: 'Empaquetando archivos...', 
        text: 'Descargando desde la nube',
        allowOutsideClick: false, 
        didOpen: () => Swal.showLoading() 
    });

    try {
        // 2. Pedimos al servidor la lista de archivos (reutilizamos tu API existente)
        const response = await fetch(`/academico/obtener-archivos/${solicitudId}/`);
        const data = await response.json();

        if (!data.archivos || data.archivos.length === 0) {
            Swal.fire('Atención', 'Esta solicitud no tiene archivos adjuntos.', 'warning');
            return;
        }

        // 3. Inicializamos el empaquetador ZIP
        const zip = new JSZip();
        // Creamos la carpeta virtual adentro del ZIP con el nombre exacto que pediste
        const carpetaVirtual = zip.folder(nombreCarpeta);

        // 4. Descargamos todos los archivos en paralelo desde AWS S3
        const promesasDescarga = data.archivos.map(async (arc) => {
            const fileResp = await fetch(arc.url);
            const blob = await fileResp.blob();
            // Guardamos el archivo dentro de la carpeta virtual
            carpetaVirtual.file(arc.nombre, blob);
        });

        // Esperamos a que todos los archivos terminen de descargarse
        await Promise.all(promesasDescarga);

        Swal.update({ title: 'Generando archivo final...' });

        // 5. Generamos el ZIP y forzamos su descarga
        const zipBlob = await zip.generateAsync({ type: 'blob' });
        const urlBlob = window.URL.createObjectURL(zipBlob);
        
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = urlBlob;
        a.download = `${nombreCarpeta}.zip`;
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(urlBlob);

        Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Descarga completada', showConfirmButton: false, timer: 2500 });
        
    } catch (error) {
        console.error("Error al crear el ZIP:", error);
        Swal.fire('Error', 'Ocurrió un problema al empaquetar los archivos. Revisa tu conexión.', 'error');
    }
}