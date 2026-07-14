$(document).ready(function() {
    if ($('#tablaMatriz').length) {
        let tabla = $('#tablaMatriz').DataTable({
            paging: false,       
            info: false,         
            ordering: false,     // Mantiene el orden alfabético estricto
            language: { 
                url: "/static/plugins/datatables/js/es-ES.json",
                emptyTable: "No hay alumnos matriculados o evaluaciones registradas en este bimestre."
            },
            
            // 💥 CONFIGURACIÓN DE BOTONES Y BUSCADOR
            // 'f' (Filter) a la izquierda, 'B' (Buttons) a la derecha
            dom: "<'row mb-3 align-items-center'<'col-sm-12 col-md-6 text-start'f><'col-sm-12 col-md-6 text-end'B>>" +
                 "<'row'<'col-sm-12'tr>>" +
                 "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
            buttons: [
                {
                    extend: 'excelHtml5',
                    text: '<i class="material-symbols-rounded align-middle me-1">table_view</i> Excel',
                    className: 'btn btn-sm bg-gradient-success mb-0',
                    title: 'Sábana de Notas - Consolidado General'
                },
                {
                    extend: 'pdfHtml5',
                    text: '<i class="material-symbols-rounded align-middle me-1">picture_as_pdf</i> PDF',
                    className: 'btn btn-sm bg-gradient-danger mb-0',
                    title: 'Sábana de Notas - Consolidado General',
                    orientation: 'landscape', // El PDF se pondrá en horizontal automáticamente
                    pageSize: 'LEGAL'
                },
                {
                    extend: 'print',
                    text: '<i class="material-symbols-rounded align-middle me-1">print</i> Imprimir',
                    className: 'btn btn-sm bg-gradient-info mb-0'
                }
            ]
        });

        // Generar los números de N° automáticamente
        tabla.on('order.dt search.dt', function () {
            tabla.column(0, { search: 'applied', order: 'applied' }).nodes().each(function (cell, i) {
                cell.innerHTML = i + 1;
            });
        }).draw();
    }
});