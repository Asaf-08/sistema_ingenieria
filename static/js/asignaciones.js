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
                text: 'Elige al menos un aula.',
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
                    window.location.reload();
                }
            });
        }
    });
}

    // ==========================================
    // MAGIA DE AUTO-COMPLETADO Y VERIFICACIÓN
    // ==========================================
    let asignacionesAjenas = {}; // Guardaremos quién enseña en qué aula

    $('#select_docente, #select_curso').on('change', function() {
        let docenteId = $('#select_docente').val();
        let cursoId = $('#select_curso').val();
        let periodoId = $('input[name="periodo"]').val();

        if (docenteId) {
            // Solo mostramos el loader visual si ya eligió ambas cosas
            if (cursoId) {
                Swal.fire({
                    title: 'Verificando carga actual...',
                    toast: true, position: 'top-end', showConfirmButton: false, timer: 1000,
                    didOpen: () => { Swal.showLoading(); }
                });
            }

            $.get('/academico/asignaciones/aulas-asignadas/', {
                docente_id: docenteId,
                curso_id: cursoId || '', 
                periodo_id: periodoId
            }, function(data) {
                if (data.status === 'ok') {
                    // 1. Actualizamos el contador debajo del botón
                    $('#count-asignaciones').text(data.total_asignaciones);
                    $('#badge-asignaciones').fadeIn();

                    // 2. Si eligió curso, pintamos aulas y verificamos cruces
                    if (cursoId) {
                        $('.aula-checkbox').prop('checked', false);
                        data.aulas.forEach(function(aulaId) {
                            $('input[value="' + aulaId + '"].aula-checkbox').prop('checked', true);
                        });
                        
                        asignacionesAjenas = data.otras_asignaciones;
                        verificarInterruptorMaestro();
                        verificarConflictos();
                    }
                }
            });
        }
    });

    // Validar cruces al hacer clic manual en cualquier aula
    $('.aula-checkbox').on('change', function() {
        verificarInterruptorMaestro();
        verificarConflictos();
    });

    // 💥 NUEVA FUNCIÓN: Identifica si marcaste un aula de otro profe
    function verificarConflictos() {
        let conflictos = [];
        
        // Capturamos el texto (nombre) del curso que está seleccionado actualmente
        let nombreCurso = $('#select_curso option:selected').text();
        
        $('.aula-checkbox:checked').each(function() {
            let aulaId = $(this).val();
            
            // Si el ID del aula está en el diccionario de otros profes...
            if (asignacionesAjenas[aulaId]) {
                // Obtenemos el texto del grado y sección de la tarjeta visual
                let nombreAula = $(this).siblings('.aula-card').find('.grado-text').text() + ' ' + $(this).siblings('.aula-card').find('.seccion-text').text();
                
                // Agregamos el nombre del curso al mensaje de error
                conflictos.push(`- <u>${nombreCurso}</u> ya asignado a ${asignacionesAjenas[aulaId]} en <b>${nombreAula}</b>`);
            }
        });

        // Mostramos u ocultamos la alerta naranja
        if (conflictos.length > 0) {
            $('#texto-conflictos').html(conflictos.join('<br><br>')); // Doble salto de línea si hay más de una para que respire
            $('#alerta-conflictos').slideDown();
        } else {
            $('#alerta-conflictos').slideUp();
        }
    }

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