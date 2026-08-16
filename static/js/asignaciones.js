$(document).ready(function() {
    // LLAMAMOS A LA FUNCIÓN MAESTRA QUE CREASTE EN BASE.HTML
    inicializarTablaGlobal('#tabla-asignaciones', 'Buscar asignación...');

    $('.aula-checkbox').on('change', verificarInterruptorMaestro);

    $('.aula-checkbox').on('change', function() {
        let totalAulas = $('.aula-checkbox').length;
        let aulasMarcadas = $('.aula-checkbox:checked').length;
        
        if (totalAulas === aulasMarcadas) {
            // Todas están marcadas
            $('#checkMarcarTodas').prop('checked', true);
            $('#textMarcar').text('Desmarcar Todas');
        } else {
            // Falta al menos una
            $('#checkMarcarTodas').prop('checked', false);
            $('#textMarcar').text('Marcar Todas');
        }
    });

    // Inicializa tooltips de Bootstrap
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

    // Buscador instantáneo para el acordeón
    $('#buscadorAcordeon').on('keyup', function() {
        let valor = $(this).val().toLowerCase();
        
        // Filtra cada tarjeta de profesor basándose en el texto que contiene (Nombre, Curso o Aula)
        $('.accordion-item').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(valor) > -1);
        });
    });
});

// La función de backend se mantiene idéntica, la magia está en el CSS
    function guardarAsignacionMasiva() {
        // Configurador instanciado DENTRO de la función para evitar crasheos de carga
        const SwalPremium = Swal.mixin({
            customClass: {
                popup: 'shadow-lg border-0',
                title: 'text-dark font-weight-bold',
                confirmButton: 'btn rounded-pill px-4 py-2 mb-0',
            },
            buttonsStyling: false
        });

        if (!$('#select_docente').val() || !$('#select_curso').val()) {
            SwalPremium.fire({
                title: 'Faltan Datos',
                text: 'Debes seleccionar un Docente y un Curso.',
                icon: 'warning',
                confirmButtonColor: '#3a4149',
                customClass: { confirmButton: 'btn bg-gradient-dark rounded-pill px-4 mb-0' }
            });
            return;
        }
        
        if ($('input[name="aula"]:checked').length === 0) {
            SwalPremium.fire({
                title: 'Aulas vacías',
                text: 'Enciende el interruptor de al menos un aula.',
                icon: 'info',
                confirmButtonColor: '#f57c00',
                customClass: { confirmButton: 'btn rounded-pill px-4 mb-0', confirmButton: 'btn text-white' },
                didOpen: () => { document.querySelector('.swal2-confirm').style.backgroundColor = '#f57c00'; }
            });
            return;
        }

        SwalPremium.fire({
            title: 'Asignando aulas',
            html: '<span class="text-sm text-secondary">Guardando configuración en la base de datos...</span>',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); }
        });

        $.ajax({
            url: '/academico/asignaciones/guardar/', 
            type: 'POST',
            data: $('#formAsignacionMasiva').serialize(),
            success: function(response) {
                if (response.status === 'ok') {
                    SwalPremium.fire({
                        title: '¡Éxito!',
                        text: response.message,
                        icon: 'success',
                        showCancelButton: true, // 💥 Activamos el segundo botón
                        confirmButtonText: 'Ir a la lista',
                        cancelButtonText: 'Seguir asignando',
                        reverseButtons: true, // 💥 Ponemos "Ir a la lista" a la derecha y "Seguir" a la izquierda
                        customClass: { 
                            confirmButton: 'btn bg-gradient-success rounded-pill px-4 mb-0 ms-2 text-white',
                            cancelButton: 'btn btn-outline-secondary rounded-pill px-4 mb-0'
                        }
                    }).then((result) => {
                        if (result.isConfirmed) {
                            // Si el usuario elige "Ir a la lista"
                            window.location.href = "/academico/asignaciones/";
                        }
                        // Si elige "Seguir asignando", no programamos nada. 
                        // El modal simplemente se cerrará y el usuario seguirá en la misma pantalla
                        // con el mismo profesor seleccionado para elegirle otro curso.
                    });
                } else {
                    SwalPremium.fire({
                        title: 'Error',
                        text: 'Hubo un problema al guardar los datos.',
                        icon: 'error',
                        customClass: { confirmButton: 'btn bg-gradient-danger rounded-pill px-4 mb-0 text-white' }
                    });
                }
            }
        });
    }

    // 1. Función conectada directamente al Interruptor Maestro
    function seleccionarTodas(estado) {
        // Enciende o apaga todos los checkboxes nativos
        $('.aula-checkbox').prop('checked', estado);
        
        // Actualiza el texto con una animación visual sutil
        if (estado) {
            $('#textMarcar').text('Desmarcar Todas');
        } else {
            $('#textMarcar').text('Marcar Todas');
        }
    }

function confirmarEliminarAsignacion(id, nombre) {
    Swal.fire({
        title: '¿Eliminar asignación?',
        html: "Se quitará al docente de este curso.<br><br><b class='text-danger'>¡PELIGRO! Se eliminarán permanentemente todas las notas y asistencias registradas.</b>",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3a4149',
        cancelButtonColor: '#f57c00',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            $.ajax({
                url: '/academico/asignaciones/eliminar/' + id + '/',
                type: 'POST',
                data: {'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()},
                success: function() { 
                    // Recarga solo la tabla, ¡súper rápido!
                    $('.table-responsive').load(window.location.href + ' #tabla-asignaciones', function() {
                        inicializarTablaGlobal('#tabla-asignaciones');
                    });
                }
            });
        }
    });
}

// ==========================================
    // MAGIA DE AUTO-COMPLETADO DE AULAS
    // ==========================================
    
    // Escuchamos los cambios en los selects de Docente y Curso
    $('#select_docente, #select_curso').on('change', function() {
        let docenteId = $('#select_docente').val();
        let cursoId = $('#select_curso').val();
        let periodoId = $('input[name="periodo"]').val();

        // Solo hacemos la búsqueda si el usuario ya eligió ambos (Profesor y Curso)
        if (docenteId && cursoId) {
            
            // Mostramos un pequeño loader para que sepa que estamos buscando
            Swal.fire({
                title: 'Verificando carga actual...',
                toast: true, position: 'top-end', showConfirmButton: false, timer: 1000,
                didOpen: () => { Swal.showLoading(); }
            });

            $.get('/academico/asignaciones/aulas-asignadas/', {
                docente_id: docenteId,
                curso_id: cursoId,
                periodo_id: periodoId
            }, function(data) {
                if (data.status === 'ok') {
                    // 1. Apagamos todas las aulas primero (por si cambió de profe)
                    $('.aula-checkbox').prop('checked', false);
                    
                    // 2. Encendemos únicamente las aulas que devolvió la base de datos
                    data.aulas.forEach(function(aulaId) {
                        $('input[value="' + aulaId + '"].aula-checkbox').prop('checked', true);
                    });
                    
                    // 3. Verificamos el interruptor maestro por si el profe ya tiene todas las aulas
                    verificarInterruptorMaestro();
                }
            });
        }
    });

    // Función auxiliar para que el interruptor maestro reaccione bien
    function verificarInterruptorMaestro() {
        let totalAulas = $('.aula-checkbox').length;
        let aulasMarcadas = $('.aula-checkbox:checked').length;
        
        let btnCheck = $('#checkMarcarTodas');
        let textCheck = $('#textMarcar');

        if (totalAulas === aulasMarcadas && totalAulas > 0) {
            btnCheck.prop('checked', true);
            textCheck.text('Desmarcar Todas').removeClass('text-secondary').addClass('text-dark');
        } else {
            btnCheck.prop('checked', false);
            textCheck.text('Marcar Todas').removeClass('text-dark').addClass('text-secondary');
        }
    }