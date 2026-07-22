$(document).ready(function () {
    // 1. Inicializar las dos matrices de auditoría
    if (typeof inicializarTablaGlobal === "function") {
        inicializarTablaGlobal('#tabla-auditoria-notas', 'Buscar en Notas...');
        inicializarTablaGlobal('#tabla-matriz-cumplimiento', 'Buscar en Materiales...');
    }

    // 2. Lógica del Filtro Dinámico de Materiales (Temas/Exámenes)
    $('#filtroTemaDinamico').on('change', function() {
        let valorFiltro = $(this).val();
        
        // Cambiamos el título de la columna
        if(valorFiltro === 'GENERAL') {
            $('#th-dinamico').text('Progreso General');
        } else {
            $('#th-dinamico').text('Estado: ' + $("#filtroTemaDinamico option:selected").text());
        }

        // Recorremos todas las filas de la tabla
        $('.celda-dinamica').each(function() {
            let temasData = $(this).data('temas'); // jQuery lee el JSON automáticamente
            let total = $(this).data('total');
            
            if (valorFiltro === 'GENERAL') {
                $(this).html(`<span class="badge bg-gradient-secondary">${total} envíos realizados</span>`);
            } else {
                // Buscamos si el tema o examen elegido existe en el JSON de esta fila
                if (temasData[valorFiltro]) {
                    $(this).html(`<span class="badge bg-gradient-success px-3"><i class="material-symbols-rounded text-sm align-middle me-1">check</i> Entregado</span>`);
                } else {
                    $(this).html(`<span class="badge bg-gradient-danger px-3"><i class="material-symbols-rounded text-sm align-middle me-1">close</i> Pendiente</span>`);
                }
            }
        });
    });
});

// 3. Función para abrir el historial de materiales
function abrirHistorialMateriales(asignacionId) {
    $('#modalHistorialMateriales').modal('show');
    $('#contenidoHistorial').html('<div class="text-center py-5"><div class="spinner-border text-info"></div></div>');
    
    $.get('/academico/supervision/auditoria-materiales/' + asignacionId + '/', function(response) {
        if(response.success) {
            let html = '';
            if(response.historial.length === 0) {
                html = '<div class="alert alert-dark text-center text-white">Aún no se han enviado materiales para esta clase.</div>';
            } else {
                response.historial.forEach(h => {
                    let archivosHtml = h.archivos.map(a => `<a href="${a.url}" target="_blank" class="badge bg-gradient-info text-white me-1 mb-1" style="text-transform: none;"><i class="material-symbols-rounded text-xs align-middle">download</i> ${a.tipo}</a>`).join('');
                    
                    html += `
                    <div class="card shadow-sm border-0 mb-3">
                        <div class="card-body p-3">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <h6 class="mb-0 text-dark font-weight-bold">${h.tema}</h6>
                                <span class="badge bg-gradient-secondary">${h.estado}</span>
                            </div>
                            <p class="text-xs text-muted mb-2"><i class="material-symbols-rounded text-xs align-middle">schedule</i> Enviado el ${h.fecha}</p>
                            <div class="mb-3">${archivosHtml}</div>
                            <p class="text-xs text-dark mb-0 bg-light p-2 border-radius-md" style="border-left: 3px solid #17c1e8;"><strong>Indicaciones:</strong> ${h.instrucciones}</p>
                        </div>
                    </div>`;
                });
            }
            $('#contenidoHistorial').html(html);
        }
    });
}