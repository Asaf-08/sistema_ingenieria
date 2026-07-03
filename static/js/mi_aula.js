/**
 * ARCHIVO: mi_aula.js
 * DESCRIPCIÓN: Gestión modular de "Mi Aula" (Dashboard Predictivo del Tutor),
 * integrando el diagnóstico de Gemini IA y el Clustering (K-Means).
 */

$(document).ready(function () {
    inicializarTablaGlobal('#tablaPredictiva', 'Buscar alumno por DNI o Apellidos...');
    registrarEventosDashboard();
});

function registrarEventosDashboard() {
    // =============================================================
    // EVENTOS PARA GEMINI IA
    // =============================================================
    
    // 1. Botón principal de Diagnóstico en la tabla (RESPETA TU CLASE .btn-diagnostico)
    $('#tablaPredictiva tbody').on('click', '.btn-diagnostico', function (e) {
        e.preventDefault();
        const btn = $(this);
        const matriculaId = btn.data('matricula-id');
        const cursoId = btn.data('curso-id') || 'general';
        const nombreAlumno = btn.data('nombre');
        const urlEndPoint = btn.data('url');

        if (!matriculaId) return;

        const claveCache = 'diagnostico_ia_alumno_' + matriculaId + '_curso_' + cursoId;
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
        ejecutarClusteringKMeans(aulaId, periodoId);
    });
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

function ejecutarClusteringKMeans(aulaId, periodoId) {
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

    // 💥 MANTENEMOS TU URL ORIGINAL EXACTA
    $.ajax({
        url: '/academico/api/clustering-ia/', 
        type: 'POST',
        data: JSON.stringify({
            'aula_id': aulaId,
            'periodo_id': periodoId
        }),
        contentType: 'application/json',
        success: function (response) {
            if (response.status === 'success') {
                Swal.close(); 
                renderizarPerfiles(response.clusters);
                // 💥 MANTENEMOS TU ID ORIGINAL DEL MODAL
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

    clusters.forEach(function (cluster) {
        let colorCard = "dark";
        let icono = "groups";
        
        if (cluster.perfil.includes("Óptimo") || cluster.perfil.includes("Alto") || cluster.perfil.includes("Excelente")) {
            colorCard = "success"; icono = "star";
        } else if (cluster.perfil.includes("Riesgo") || cluster.perfil.includes("Bajo")) {
            colorCard = "danger"; icono = "warning";
        } else if (cluster.perfil.includes("Esfuerzo") || cluster.perfil.includes("Talento") || cluster.perfil.includes("Regular")) {
            colorCard = "warning"; icono = "trending_flat";
        }

        let listaAlumnosHTML = '<ul class="list-group list-group-flush border-radius-lg">';
        cluster.alumnos.forEach(function(alumno) {
            listaAlumnosHTML += `
                <li class="list-group-item d-flex justify-content-between align-items-center text-sm py-2 px-3">
                    <span class="font-weight-bold text-dark text-truncate" style="max-width: 60%;">${alumno.nombre}</span>
                    <div class="text-end">
                        <span class="badge bg-light text-dark border me-1" title="Promedio Académico">A: ${alumno.promedio_academico.toFixed(1)}</span>
                        <span class="badge bg-light text-dark border" title="Promedio Conductual">C: ${alumno.promedio_actitudinal.toFixed(1)}</span>
                    </div>
                </li>`;
        });
        listaAlumnosHTML += '</ul>';

        let cardHTML = `
            <div class="col-12 col-md-6 col-xl-4 mb-4">
                <div class="card h-100 border border-${colorCard} border-2 shadow-sm">
                    <div class="card-header pb-0 p-3 bg-gradient-${colorCard}">
                        <h6 class="mb-0 text-white d-flex align-items-center text-sm">
                            <i class="material-symbols-rounded me-2">${icono}</i>
                            ${cluster.perfil}
                        </h6>
                        <p class="text-xs text-white opacity-8 mb-0 mt-1">
                            ${cluster.cantidad} estudiante(s) en este perfil
                        </p>
                    </div>
                    <div class="card-body p-0" style="max-height: 250px; overflow-y: auto;">
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