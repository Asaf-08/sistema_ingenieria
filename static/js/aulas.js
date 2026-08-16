// Inicializar DataTable
$(document).ready(function () {
    inicializarTablaAulas();
});

$(document).on('change', '#id_nivel', function() {
    filtrarGrados($(this).val());
});

function inicializarTablaAulas() {
    if ($.fn.DataTable.isDataTable('#tabla-aulas')) {
        $('#tabla-aulas').DataTable().destroy();
    }

    tablaAulas = $('#tabla-aulas').DataTable({
        language: {
            url: "/static/plugins/datatables/js/es-ES.json",
            search: "_INPUT_",
            searchPlaceholder: "Buscar aula...",
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
        // 💥 MAGIA DATATABLES: 1° por Nivel(1), 2° por Grado(0), 3° por Sección(2)
        order: [
            [1, "asc"], 
            [0, "asc"], 
            [2, "asc"]
        ],
        info: true,
        autoWidth: false,
        responsive: true,
        dom: '<"d-flex justify-content-between align-items-center px-4 pt-3"f l>t<"d-flex justify-content-between align-items-center p-4"ip>',
        initComplete: function () {
            $('.dataTables_filter input')
                .addClass('form-control border-bottom border-2 px-3 py-1')
                .attr('placeholder', 'Buscar aula...');
                
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

const gradosPorNivel = {
    'Inicial': ['3 Años', '4 Años', '5 Años'],
    'Primaria': ['1er Grado', '2do Grado', '3er Grado', '4to Grado', '5to Grado', '6to Grado'],
    'Secundaria': ['1er Año', '2do Año', '3er Año', '4to Año', '5to Año']
};

function abrirModalCrear() {
    $('#formAula')[0].reset();
    $('#aula_id').val('');
    $('#id_grado').empty().append('<option value="">Seleccione un nivel primero</option>'); // Reset grados
    
    $('#modalTitulo').text('Nueva Aula');
    $('#modalHeaderColor').removeClass('bg-gradient-info').addClass('bg-gradient-primary');
    $('#btnGuardar').text('Guardar').removeClass('bg-gradient-info').addClass('bg-gradient-primary');
    $('#modalAula').modal('show');
}

function abrirModalEditar(id) {
    $.get('/academico/aulas/datos/' + id + '/', function(data) {
        $('#aula_id').val(data.id);
        $('#id_nivel').val(data.nivel);
        
        // PRIMERO filtramos los grados según el nivel que viene de la BD
        // SEGUNDO le pasamos el grado actual para que lo deje seleccionado
        filtrarGrados(data.nivel, data.grado);
        
        $('#id_seccion').val(data.seccion);
        $('#id_denominacion').val(data.denominacion);
        $('#id_tutor').val(data.tutor);

        $('#modalTitulo').text('Editar Aula');
        $('#modalHeaderColor').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
        $('#btnGuardar').text('Actualizar').removeClass('bg-gradient-primary').addClass('bg-gradient-info');
        $('#modalAula').modal('show');
    });
}

function filtrarGrados(nivelSeleccionado, gradoASeleccionar = null) {
    const $selectGrado = $('#id_grado'); // ID que Django le pone por defecto en el form
    $selectGrado.empty(); // Limpiamos las opciones actuales
    $selectGrado.append('<option value="">Seleccione un grado</option>');

    if (nivelSeleccionado && gradosPorNivel[nivelSeleccionado]) {
        gradosPorNivel[nivelSeleccionado].forEach(grado => {
            const selected = (grado === gradoASeleccionar) ? 'selected' : '';
            $selectGrado.append(`<option value="${grado}" ${selected}>${grado}</option>`);
        });
    }
}

function guardarAula() {
    $.ajax({
        url: '/academico/aulas/guardar/', // Asegúrate de que esta URL sea correcta según tu urls.py
        type: 'POST',
        data: $('#formAula').serialize(),
        success: function (response) {
            if (response.status == 'ok') {
                $('#modalAula').modal('hide');
                //Llamar a la nueva función global de ÉXITO
                mostrarNotificacionExito(response.message || 'Aula guardada con éxito.');

                // Destruimos el DataTable actual
                $('#tabla-aulas').DataTable().destroy();

                // Recargamos SOLO la tabla trayendo el HTML actualizado del servidor
                $('.table-responsive').load(window.location.href + ' #tabla-aulas', function () {
                    inicializarTablaAulas(); // Volvemos a activar el buscador y paginación
                });

            } else {
                // Si Django manda errores (ej. duplicados), abrimos el modal de error
                if (response.errors) {
                    mostrarErroresModal(response.errors);
                } else {
                    mostrarErroresModal({'General': ['Ocurrió un error inesperado.']});
                }
            }
        },
        error: function () {
            mostrarErroresModal({'General': ['Error al intentar conectar con el servidor.']});
        }
    });
}

function confirmarEliminacion(id, nombre) {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "Vas a eliminar el aula: " + nombre + ". Esta acción no se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3a4149', // Tu Gris Pizarra
        cancelButtonColor: '#f57c00',  // Tu Anaranjado
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            eliminarAula(id);
        }
    })
}

function eliminarAula(id) {
    $.ajax({
        url: '/academico/aulas/eliminar/' + id + '/',
        type: 'POST',
        data: {
            'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.status == 'ok') {
                mostrarNotificacionExito(response.message || 'Aula eliminada con éxito.');
                
                // Actualizamos la tabla sin recargar
                $('#tabla-aulas').DataTable().destroy();
                $('.table-responsive').load(window.location.href + ' #tabla-aulas', function() {
                    inicializarTablaAulas();
                });
            } else {
                Swal.fire('Error', response.message, 'error');
            }
        },
        error: function() {
            mostrarErroresModal({'General': ['Error al intentar conectar con el servidor.']});
        }
    });
}