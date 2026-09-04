/**
 * ARCHIVO: mi_aula.js
 * DESCRIPCIÓN: Gestión modular de "Mi Aula" (Dashboard Predictivo del Tutor),
 * integrando el diagnóstico de Gemini IA y el Clustering (K-Means).
 */

$(document).ready(function () {
    incializarTablaPredictiva('#tablaPredictiva', 'Buscar alumno por DNI o Apellidos...');
    registrarEventosDashboard();
});

function incializarTablaPredictiva() {
    $('#tablaPredictiva').DataTable({
        language: {
            url: "/static/plugins/datatables/js/es-ES.json",
            search: "_INPUT_",
            searchPlaceholder: "Buscar alumno por DNI o Apellidos...",
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
        pageLength: 50,
        deferRender: true,
        lengthChange: true,
        ordering: true,
        info: true,
        autoWidth: false,
        responsive: true,
        dom: '<"d-flex justify-content-between align-items-center pt-3"f l>t<"d-flex justify-content-between align-items-center p-4"ip>',
        initComplete: function () {
            $('.dataTables_filter input')
                .addClass('form-control border-bottom border-2 px-3 py-1')
                .attr('placeholder', "Buscar alumno por DNI o Apellidos...");
                
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

function registrarEventosDashboard() {
    // =============================================================
    // EVENTOS PARA GEMINI IA
    // =============================================================
    
    // 1. Botón principal de Diagnóstico IA (Solucionado Bug de Evento AJAX)
    $(document).on('click', '.btn-diagnostico', function (e) {
        e.preventDefault();
        const btn = $(this);
        const matriculaId = btn.data('matricula-id');
        const nombreAlumno = btn.data('nombre');
        const urlEndPoint = btn.data('url');

        // 💥 NUEVO: Siempre leer el selector actual en el momento del clic
        const selector = $('#select-curso-aula');
        const cursoId = selector.val() || '';
        
        // Limpiamos los emojis para inyectar el texto en el footer
        const contextoTexto = selector.find(':selected').text().replace('📊', '').replace('📘', '').trim();
        $('#contexto-curso-modal-diag').html(`<i class="material-symbols-rounded text-sm align-middle me-1">school</i> Evaluando: ${contextoTexto}`);

        if (!matriculaId) return;

        const claveCache = 'diagnostico_ia_alumno_' + matriculaId + '_curso_' + (cursoId || 'general');
        const diagnosticoGuardado = localStorage.getItem(claveCache);

        if (diagnosticoGuardado) {
            prepararModalRapido(nombreAlumno);
            renderizarRespuestaExitosa(diagnosticoGuardado, btn, matriculaId, cursoId);
        } else {
            prepararModalCarga(nombreAlumno);
            solicitarDiagnosticoBackend(matriculaId, cursoId, nombreAlumno, urlEndPoint, btn);
        }
    });

    // 2. Botón de "Generar otra versión"
    $(document).on('click', '#btnRegenerarIA', function(e) {
        e.preventDefault();
        const btnOriginal = $(this).data('btn-referencia');
        const matriculaId = btnOriginal.data('matricula-id');
        const cursoId = btnOriginal.data('curso-id') || 'general'; 
        
        localStorage.removeItem('diagnostico_ia_alumno_' + matriculaId + '_curso_' + cursoId);
        prepararModalCarga(btnOriginal.data('nombre'));
        solicitarDiagnosticoBackend(matriculaId, cursoId, btnOriginal.data('nombre'), btnOriginal.data('url'), btnOriginal);
    });

    // 3. Botón de Copiar al portapapeles
    $(document).on('click', '#btnCopiarIA', function(e) {
        e.preventDefault();
        const btn = $(this);
        const textoLimpio = document.getElementById('textoDiagnostico').innerText;

        navigator.clipboard.writeText(textoLimpio).then(() => {
            const htmlOriginal = btn.html();
            btn.html('<i class="material-symbols-rounded align-middle me-1 text-sm">check</i> ¡Copiado!');
            btn.removeClass('btn-outline-info').addClass('btn-success text-white');
            setTimeout(() => {
                btn.html(htmlOriginal);
                btn.removeClass('btn-success text-white').addClass('btn-outline-info');
            }, 2000);
        }).catch(err => alert('Error al copiar el texto.'));
    });

    // =============================================================
    // EVENTOS PARA MACHINE LEARNING (K-Means Clustering)
    // =============================================================
    
    // 💥 MANTENEMOS TU ID ORIGINAL: #btn-analisis-ia
    $(document).on('click', '#btn-analisis-ia', function (e) {
        e.preventDefault();
        let aulaId = $(this).data('aula-id');
        let periodoId = $(this).data('periodo-id');

        // 💥 NUEVO: Atrapamos el curso seleccionado y su texto
        const selector = $('#select-curso-aula');
        const cursoId = selector.val() || '';
        const contextoTexto = selector.find(':selected').text().replace('📊', '').replace('📘', '').trim();

        // 💥 NUEVO: Inyectamos el texto en el footer del modal
        $('#contexto-curso-modal-kmeans').html(`<i class="material-symbols-rounded text-sm align-middle me-1">school</i> Evaluando: ${contextoTexto}`);

        // Pasamos el cursoId a la función
        ejecutarClusteringKMeans(aulaId, periodoId, cursoId);
    });

    // -------------------------------------------------------------
    // EVENTO AJAX: CAMBIO DE CURSO DINÁMICO
    // -------------------------------------------------------------
    $(document).on('change', '#select-curso-aula', function() {
        let cursoId = $(this).val();
        let asignacionId = $(this).find(':selected').data('asignacion'); 
        
        let btnSabana = $('#btn-sabana-notas');
        let baseUrl = btnSabana.data('base-url');

        // 1. Actualización inteligente del botón Sábana de Notas
        if (asignacionId) {
            btnSabana.attr('href', baseUrl + '&asignacion_id=' + asignacionId);
        } else {
            btnSabana.attr('href', baseUrl);
        }

        // 2. Construimos la URL de la petición
        let urlObj = new URL(window.location.href);
        if (cursoId) {
            urlObj.searchParams.set('curso_id', cursoId);
        } else {
            urlObj.searchParams.delete('curso_id');
        }
        let urlAjax = urlObj.toString();

        // 3. Pantalla de carga fluida
        Swal.fire({
            title: 'Analizando rendimiento...',
            text: 'Calculando tendencias y semáforos de la IA',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); }
        });

        // 4. Inyección Múltiple (Tarjetas + Tabla) usando $.get
        $.get(urlAjax, function(data) {
            // Extraemos y reemplazamos solo el contenido de las tarjetas
            let nuevoDashboard = $(data).find('#dashboard-dinamico-aula').html();
            $('#dashboard-dinamico-aula').html(nuevoDashboard);

            // Extraemos y reemplazamos solo el contenido de la tabla
            let nuevaTabla = $(data).find('#tablaPredictiva').html();
            $('#tablaPredictiva').html(nuevaTabla);

            Swal.close();
            
            // Actualizamos la URL del navegador en silencio
            window.history.replaceState(null, null, urlAjax);
            
        }).fail(function() {
            Swal.fire('Error', 'Hubo un problema al cargar los datos del curso.', 'error');
        });
    });

    // 💥 EJECUCIÓN INICIAL: Forzamos la asignación del botón al cargar la página por primera vez
    if ($('#select-curso-aula').val()) {
        let asignacionInicial = $('#select-curso-aula').find(':selected').data('asignacion');
        if (asignacionInicial) {
            let btn = $('#btn-sabana-notas');
            btn.attr('href', btn.data('base-url') + '&asignacion_id=' + asignacionInicial);
        }
    }
}

// =========================================================================
// FUNCIONES DE GEMINI IA
// =========================================================================

function prepararModalCarga(nombreAlumno) {
    $('#nombreAlumnoModal').text(nombreAlumno);
    $('#modalDiagnosticoIA').modal('show');
    $('#contenidoDiagnostico').html(`
        <div class="text-center py-4">
            <div class="spinner-border text-warning mb-3" role="status" style="width: 3rem; height: 3rem;"></div>
            <h6 class="text-dark font-weight-bold">Google Gemini está analizando los datos...</h6>
            <p class="text-sm text-secondary">Redactando recomendaciones psicopedagógicas.</p>
        </div>
    `);
}

function prepararModalRapido(nombreAlumno) {
    $('#nombreAlumnoModal').text(nombreAlumno);
    $('#modalDiagnosticoIA').modal('show');
}

function solicitarDiagnosticoBackend(matriculaId, cursoId, nombreAlumno, urlDestino, btnOriginal) {
    // 💥 AJAX LIMPIO: Ya no pasamos el CSRF manual. El Cerebro (main.js) lo inyecta por ti.
    $.ajax({
        url: urlDestino,
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ matricula_id: matriculaId, curso_id: cursoId, nombre_alumno: nombreAlumno }), 
        success: function (response) {
            if (response.status === 'success') {
                const textoProcesado = formatearTextoIA(response.diagnostico);
                const claveCache = 'diagnostico_ia_alumno_' + matriculaId + '_curso_' + cursoId;
                localStorage.setItem(claveCache, textoProcesado);
                renderizarRespuestaExitosa(textoProcesado, btnOriginal, matriculaId, cursoId);
            } else {
                renderizarRespuestaError(response.mensaje);
            }
        },
        error: function (jqXHR, textStatus, errorThrown) {
            renderizarRespuestaError('Fallo crítico en el servidor. Inténtalo de nuevo.');
        }
    });
}

function renderizarRespuestaExitosa(htmlTexto, btnOriginal, matriculaId) {
    $('#contenidoDiagnostico').html(`
        <div class="alert alert-light text-dark border-left-warning border-4 p-3 mb-3 shadow-xs" id="textoDiagnostico" style="font-size: 0.95rem; line-height: 1.6; text-align: justify; background-image: linear-gradient(45deg, #ffffff 0%, #ffffff 100%) !important;">
            ${htmlTexto}
        </div>
        <div class="d-flex justify-content-between align-items-center">
            <button class="btn btn-sm btn-outline-info mb-0 me-2" id="btnCopiarIA">
                <i class="material-symbols-rounded align-middle me-1 text-sm">content_copy</i>
                Copiar texto
            </button>
            <button class="btn btn-sm btn-outline-secondary mb-0" id="btnRegenerarIA">
                <i class="material-symbols-rounded align-middle me-1 text-sm">refresh</i>
                Generar otra versión
            </button>
        </div>
    `);
    $('#btnRegenerarIA').data('btn-referencia', btnOriginal);
}

function renderizarRespuestaError(mensajeError) {
    let mensajeAmigable = mensajeError;
    if (mensajeError.includes('503') || mensajeError.includes('UNAVAILABLE') || mensajeError.includes('high demand')) {
        mensajeAmigable = "Los servidores de Inteligencia Artificial están experimentando alta demanda. Por favor, espera unos segundos y haz clic en 'Generar nueva versión'.";
    }
    $('#contenidoDiagnostico').html(`
        <div class="alert alert-danger text-white border-radius-md p-3">
            <div class="d-flex align-items-center">
                <i class="material-symbols-rounded me-2">error</i>
                <strong>Aviso del Sistema:</strong>
            </div>
            <p class="text-sm mb-0 mt-2 opacity-9">${mensajeAmigable}</p>
        </div>
    `);
}

function formatearTextoIA(texto) {
    let html = texto.replace(/\n/g, '<br>'); 
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); 
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>'); 
    return html;
}

// =========================================================================
// FUNCIONES DE MACHINE LEARNING (K-Means)
// =========================================================================

function ejecutarClusteringKMeans(aulaId, periodoId, cursoId) { // 💥 Agregamos cursoId aquí
    if (!aulaId || !periodoId) {
        Swal.fire('Error', 'Faltan datos de contexto (Aula o Periodo).', 'error');
        return;
    }

    Swal.fire({
        title: 'Ejecutando K-Means...',
        html: 'La Inteligencia Artificial está procesando las notas y conductas del aula.<br><br><b>Descubriendo patrones...</b>',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    $.ajax({
        url: '/academico/api/clustering-ia/', 
        type: 'POST',
        data: JSON.stringify({
            'aula_id': aulaId,
            'periodo_id': periodoId,
            'curso_id': cursoId // 💥 AQUÍ ENVIAMOS EL CURSO AL BACKEND
        }),
        contentType: 'application/json',
        success: function (response) {
            if (response.status === 'success') {
                Swal.close(); 
                renderizarPerfiles(response.clusters);
                $('#modalClusteringIA').modal('show');
            } else {
                Swal.fire('Atención', response.mensaje, 'warning');
            }
        },
        error: function () {
            Swal.fire('Error', 'Hubo un problema al ejecutar el algoritmo. Revisa la consola.', 'error');
        }
    });
}

function renderizarPerfiles(clusters) {
    let contenedor = $('#contenedor-perfiles-ia');
    contenedor.empty(); 

    // 1. Lógica de distribución inteligente de columnas
    let totalGrupos = clusters.length;
    let claseColumna = "col-12 col-md-6 col-lg-4"; // Por defecto para 3 o más grupos

    if (totalGrupos === 1) {
        claseColumna = "col-12"; // Ocupa todo el ancho
    } else if (totalGrupos === 2) {
        claseColumna = "col-12 col-lg-6"; // Mitad y mitad
    }

    clusters.forEach(function (cluster) {
        let colorCard = "dark";
        let icono = "hub"; 
        
        // Asignación de colores e íconos con estética de IA
        if (cluster.perfil.includes("Alto Rendimiento")) {
            colorCard = "primary"; // Azul/Morado para los de excelencia
            icono = "emoji_events"; // Ícono de trofeo
        } else if (cluster.perfil.includes("Óptimo")) {
            colorCard = "success"; // Verde para el grupo bueno/estable
            icono = "auto_awesome"; // Estrellas IA
        } else if (cluster.perfil.includes("Riesgo") || cluster.perfil.includes("Integral")) {
            colorCard = "danger"; // Rojo para casos críticos
            icono = "warning";
        } else if (cluster.perfil.includes("Esfuerzo") || cluster.perfil.includes("Talento")) {
            colorCard = "warning"; // Amarillo para alertas de seguimiento
            icono = "insights"; 
        } else {
            colorCard = "info"; // Celeste para los estables regulares
            icono = "psychology"; 
        }

        let listaAlumnosHTML = '<ul class="list-group list-group-flush bg-transparent border-radius-lg">';
        cluster.alumnos.forEach(function(alumno) {
            listaAlumnosHTML += `
                <li class="list-group-item d-flex justify-content-between align-items-center text-sm py-3 px-3 bg-transparent border-bottom">
                    <div class="d-flex align-items-center">
                        <div class="icon icon-shape icon-sm shadow border-radius-sm bg-gradient-${colorCard} text-center me-3 d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
                            <i class="material-symbols-rounded text-white" style="font-size: 16px; top:0;">person</i>
                        </div>
                        <span class="font-weight-bold text-xs text-dark" style="max-width: 150px;">${alumno.nombre}</span>
                    </div>
                    <div class="text-end d-flex gap-2">
                        <span class="badge bg-white text-dark border border-${colorCard} border-radius-md px-2 py-1 shadow-sm" title="Promedio Académico (A)">
                            <i class="material-symbols-rounded text-xxs align-middle me-1">menu_book</i>A: ${alumno.promedio_academico}
                        </span>
                        <span class="badge bg-white text-dark border border-${colorCard} border-radius-md px-2 py-1 shadow-sm" title="Promedio Conductual (C)">
                            <i class="material-symbols-rounded text-xxs align-middle me-1">psychology</i>C: ${alumno.promedio_actitudinal}
                        </span>
                    </div>
                </li>`;
        });
        listaAlumnosHTML += '</ul>';

        // 2. Construcción de la tarjeta con estilo limpio y decoraciones
        let cardHTML = `
            <div class="${claseColumna} mb-4">
                <div class="card h-100 shadow-lg border-0 overflow-hidden" style="background: linear-gradient(145deg, #ffffff, #f8f9fa);">
                    <div class="card-header pb-3 p-4 bg-gradient-${colorCard} position-relative">
                        <!-- Decoración de fondo semitransparente -->
                        <div class="position-absolute top-0 end-0 opacity-2 pt-2 pe-3">
                            <i class="material-symbols-rounded" style="font-size: 4rem;">${icono}</i>
                        </div>
                        
                        <h6 class="mb-0 text-white d-flex align-items-center text-md font-weight-bolder position-relative z-index-1">
                            <i class="material-symbols-rounded me-2 bg-white text-${colorCard} p-1 border-radius-md shadow-sm" style="font-size: 18px;">${icono}</i>
                            ${cluster.perfil.split('(')[0].trim()} <!-- Corta el nombre principal para más limpieza -->
                        </h6>
                        <p class="text-xs text-white opacity-9 mb-0 mt-2 position-relative z-index-1 fw-bold">
                            <i class="material-symbols-rounded text-xs align-middle me-1">group</i> 
                            ${cluster.cantidad} estudiante(s) perfilados
                        </p>
                    </div>
                    <div class="card-body p-2" style="max-height: 350px; overflow-y: auto;">
                        ${cluster.cantidad > 0 ? listaAlumnosHTML : '<p class="text-xs text-center text-secondary my-4">No hay alumnos con este perfil.</p>'}
                    </div>
                </div>
            </div>
        `;
        
        contenedor.append(cardHTML);
    });
}

function iniciarSincronizacion() {
    document.getElementById('pantallaCarga').style.display = 'flex';
}