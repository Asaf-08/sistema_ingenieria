$(document).ready(function () {
    // Inicializamos ambas tablas (la de directorio y la de matricular)
    inicializarTablaGlobal('#tabla-estudiantes-matricula', 'Buscar estudiante...');
    inicializarTablaGlobal('#tabla-lista-matriculas', 'Buscar en matriculados...');

    // Lógica para el checkbox maestro "Seleccionar Todos"
    $('#checkAll').on('click', function () {
        $('.check-estudiante').prop('checked', $(this).prop('checked'));
    });
});

// 💥 FUNCIÓN RESCATADA DEL HTML Y CONECTADA AL CEREBRO GLOBAL
function confirmarQuitarMatricula(id, nombre) {
    confirmarEliminacionAjax({
        titulo: '¿Quitar a ' + nombre + '?',
        texto: "El alumno ya no aparecerá en la lista de esta aula.",
        url: '/academico/matriculas/eliminar/' + id + '/',
        tableId: '#tabla-lista-matriculas',
        textoBuscador: 'Buscar en matriculados...'
    });
}

function matricularSeleccionados() {
    var periodo_id = $('#select_periodo').val();
    var aula_id = $('#select_aula').val();

    // 💥 VALIDACIONES ESTRICTAS DE NEGOCIO
    if (!periodo_id) {
        mostrarErroresModal({'Periodo Lectivo': ['Por favor, seleccione un año escolar antes de continuar.']});
        return;
    }
    if (!aula_id) {
        mostrarErroresModal({'Aula / Salón': ['Por favor, seleccione el aula destino.']});
        return;
    }

    // Recolectamos los IDs
    var estudiantes_ids = [];
    $('.check-estudiante:checked').each(function () {
        estudiantes_ids.push($(this).val());
    });

    // 💥 VALIDACIÓN DE LISTA VACÍA
    if (estudiantes_ids.length === 0) {
        mostrarErroresModal({'Selección Múltiple': ['Debe marcar al menos un estudiante de la tabla.']});
        return;
    }

    // Petición protegida
    $.ajax({
        url: "/academico/matriculas/masiva/procesar/",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({
            'periodo_id': periodo_id,
            'aula_id': aula_id,
            'estudiantes_ids': estudiantes_ids
        }),
        success: function (response) {
            if (response.status === 'ok') {
                Swal.fire({
                    title: '¡Matrícula Exitosa!',
                    text: response.message,
                    icon: 'success',
                    showCancelButton: true,
                    confirmButtonColor: '#333333', // Gris Pizarra
                    cancelButtonColor: '#f57c00',  // Naranja
                    confirmButtonText: 'Ir al Directorio',
                    cancelButtonText: 'Matricular más'
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.location.href = "/academico/matriculas/";
                    } else {
                        location.reload();
                    }
                });
            } else {
                mostrarErroresModal(response.errors || {'Error': [response.message]});
            }
        },
        error: function () {
            mostrarErroresModal({'Servidor': ['Ocurrió un problema técnico. Refresque la página e intente de nuevo.']});
        }
    });
}