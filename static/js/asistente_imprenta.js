$(document).ready(function () {
    // Inicialización de DataTables
    let tabla = $('#tabla-imprenta').DataTable({
        "language": {
            "url": "//cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json",
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

    const copias = btnElement.getAttribute('data-copias'); // Capturamos las copias
    
    // Inyectamos las copias en el título del modal
    document.getElementById('modal-badge-copias').innerText = `${copias} Copias`;

    const modal = new bootstrap.Modal(document.getElementById('modalArchivos'));
    const lista = document.getElementById('lista-archivos-modal');

    // Muestra un cargando mientras trae los datos
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
                li.innerHTML = `
                <div class="text-truncate" style="max-width: 60%;">
                    <h6 class="mb-0 text-sm"><i class="material-symbols-rounded text-info text-sm align-middle">description</i> ${arc.nombre}</h6>
                    <small class="text-secondary">${arc.tipo}</small>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-dark btn-sm mb-0" onclick="imprimirArchivo('${arc.url}')" title="Abrir para imprimir">
                        <i class="material-symbols-rounded text-md align-middle">print</i> Imprimir
                    </button>
                    <a href="${arc.url}" class="btn bg-gradient-info btn-sm mb-0" download title="Descargar PDF/Word">
                        <i class="material-symbols-rounded text-md align-middle">download</i>
                    </a>
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