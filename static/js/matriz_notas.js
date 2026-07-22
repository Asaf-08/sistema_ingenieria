$(document).ready(function() {
    
    // ========================================================
    // 1. MICRO-SCROLL INICIAL (Solo si vienes desde otra página)
    // ========================================================
    if (window.location.search.includes('asignacion_id=')) {
        setTimeout(function() {
            let zonaMatriz = document.getElementById('zona-matriz-detalle');
            if (zonaMatriz) {
                zonaMatriz.scrollIntoView({ behavior: 'auto', block: 'start' });
            }
        }, 10); 
    }

    // ========================================================
    // 2. FUNCIÓN MAESTRA PARA CONSTRUIR EL DATATABLES
    // ========================================================
    function iniciarDataTableMatriz() {
        if ($('#tablaMatriz').length) {
            // Si la tabla ya existe (porque hicimos AJAX), la destruimos para evitar duplicados
            if ($.fn.DataTable.isDataTable('#tablaMatriz')) {
                $('#tablaMatriz').DataTable().destroy();
            }

            let tabla = $('#tablaMatriz').DataTable({
                paging: false,       
                info: false,         
                ordering: false,     
                language: { 
                    url: "/static/plugins/datatables/js/es-ES.json",
                    emptyTable: "No hay alumnos matriculados o evaluaciones registradas en este curso."
                },
                dom: "<'row mb-3 align-items-center px-4'<'col-sm-12 col-md-6 text-start'f><'col-sm-12 col-md-6 text-end'B>>" +
                     "<'row'<'col-sm-12'tr>>" +
                     "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
                buttons: [
                    { extend: 'excelHtml5', text: '<i class="material-symbols-rounded align-middle me-1">table_view</i> Excel', className: 'btn btn-sm bg-gradient-success mb-0', title: 'Sábana de Notas' },
                    { extend: 'pdfHtml5', text: '<i class="material-symbols-rounded align-middle me-1">picture_as_pdf</i> PDF', className: 'btn btn-sm bg-gradient-danger mb-0', title: 'Sábana de Notas', orientation: 'landscape', pageSize: 'LEGAL' },
                    { extend: 'print', text: '<i class="material-symbols-rounded align-middle me-1">print</i> Imprimir', className: 'btn btn-sm bg-gradient-info mb-0' }
                ]
            });

            // Generar la numeración de los alumnos automáticamente
            tabla.on('order.dt search.dt', function () {
                tabla.column(0, { search: 'applied', order: 'applied' }).nodes().each(function (cell, i) {
                    cell.innerHTML = i + 1;
                });
            }).draw();
        }
    }

    // Inicializamos la tabla al cargar la página por primera vez
    iniciarDataTableMatriz();

    // --------------------------------------------------------
    // 3. LA MAGIA: CAMBIAR DE CURSO O BIMESTRE POR AJAX
    // --------------------------------------------------------
    $('#select-curso, #hidden_bimestre').on('change', function() {
        let aulaId = $('#hidden_aula_id').val();
        let bimestre = $('#hidden_bimestre').val();
        let asignacionId = $('#select-curso').val();
        
        // Verificamos si estamos en "Modo Tutor" (oculto)
        let origen = $('#hidden_origen').length ? '&origen=' + $('#hidden_origen').val() : '';

        // Construimos la URL silenciosa manteniendo el origen
        let urlAjax = window.location.pathname + '?aula_id=' + aulaId + '&bimestre=' + bimestre + '&asignacion_id=' + asignacionId + origen;

        if ($.fn.DataTable.isDataTable('#tablaMatriz')) {
            $('#tablaMatriz').DataTable().destroy();
        }

        Swal.fire({
            title: 'Cargando matriz...',
            text: 'Obteniendo calificaciones del servidor',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); }
        });

        // Hacemos el reemplazo del fragmento HTML
        $('#contenedor-tabla-matriz').load(urlAjax + ' #contenedor-tabla-matriz > *', function(response, status, xhr) {
            if (status == "error") {
                Swal.fire('Error', 'Hubo un problema al cargar los datos.', 'error');
            } else {
                try {
                    iniciarDataTableMatriz();
                    Swal.close();
                    // Actualizamos la URL silenciosamente
                    window.history.replaceState(null, null, urlAjax);
                } catch (e) {
                    console.error("Error al construir la tabla:", e);
                    Swal.fire('Atención', 'Hubo un problema al organizar las columnas.', 'warning');
                }
            }
        });
    });
});