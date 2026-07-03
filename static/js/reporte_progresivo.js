/**
 * ARCHIVO: reporte_progresivo.js
 * DESCRIPCIÓN: Controlador para el Gráfico Actitudinal (BARRAS), PDF y Gemini IA.
 */

$(document).ready(function() {
    
    // ========================================================= 
    // 1. EXTRACCIÓN DE DATOS
    // ========================================================= 
    const $canvas = $('#graficoActitudinal');
    const $btnExportar = $('#btn-exportar');
    
    if ($canvas.length === 0) return; 

    const notasBase20 = [
        parseFloat($canvas.attr('data-puntualidad')) || 0,
        parseFloat($canvas.attr('data-presentacion')) || 0,
        parseFloat($canvas.attr('data-participacion')) || 0,
        parseFloat($canvas.attr('data-disciplina')) || 0,
        parseFloat($canvas.attr('data-responsabilidad')) || 0
    ];
    
    // ========================================================= 
    // 2. RENDERIZADO DEL GRÁFICO DE BARRAS (DINÁMICO POR NOTA)
    // ========================================================= 
    const ctx = $canvas[0].getContext('2d');
    const porcentajes = notasBase20.map(nota => nota * 5); 

    // 💥 LÓGICA DE COLORES EXACTA A TU LEYENDA HTML
    const coloresDinamicos = porcentajes.map(p => {
        if (p === 0) return '#e9ecef'; // Gris si aún no tiene nota
        if (p <= 50) return '#dc3545'; // EN PROCESO (0 - 50%)
        if (p <= 65) return '#fd7e14'; // REGULAR (51 - 65%)
        if (p <= 80) return '#ffc107'; // ADECUADO (66 - 80%)
        if (p <= 90) return '#0d6efd'; // BUENO (81 - 90%)
        return '#198754';              // EXCELENTE (91 - 100%)
    });

    const actitudinalChart = new Chart(ctx, {
        type: 'bar', 
        data: {
            labels: ['Puntualidad', 'Presentación', 'Participación', 'Disciplina', 'Responsabilidad'],
            datasets: [{
                label: 'Porcentaje de Logro (%)',
                data: porcentajes,
                backgroundColor: coloresDinamicos, // Asignamos los colores calculados
                borderWidth: 1,
                borderColor: '#333333',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 1000 }, 
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100, 
                    ticks: { stepSize: 20 }
                }
            },
            plugins: {
                legend: { display: false } 
            }
        }
    });

    // ========================================================= 
    // 3. GENERACIÓN DEL PDF
    // ========================================================= 
    $btnExportar.on('click', function() {
        const btn = $(this);
        const originalText = btn.html();
        const elementoA4 = document.querySelector('.a4-container'); 

        btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm align-middle me-2"></span> Procesando PDF...');

        actitudinalChart.options.animation = false;
        actitudinalChart.update();

        const opcionesPDF = {
            margin:       0,
            filename:     `Informe_Progresivo_${Date.now()}.pdf`,
            image:        { type: 'jpeg', quality: 1.0 }, 
            html2canvas:  { scale: 2, useCORS: true, logging: false },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };

        html2pdf().set(opcionesPDF).from(elementoA4).save().then(() => {
            btn.prop('disabled', false).html(originalText);
            actitudinalChart.options.animation = { duration: 1000 };
            actitudinalChart.update();
        }).catch(() => {
            btn.prop('disabled', false).html(originalText);
            mostrarErroresModal({'Generación de Documento': ['Hubo un problema al crear el PDF.']});
        });
    });

    // ========================================================= 
    // 4. MOTOR DE ANÁLISIS: GEMINI IA
    // ========================================================= 
    const $listaRecomendaciones = $('#lista-recomendaciones');
    const $loadingIa = $('#loading-ia');
    
    if ($listaRecomendaciones.length > 0 && $loadingIa.length > 0) {
        const evaluacionId = $listaRecomendaciones.data('evaluacion');
        
        $.ajax({
            url: '/academico/ajax/generar-recomendacion-ia/', 
            type: 'POST',
            data: JSON.stringify({ evaluacion_id: evaluacionId }),
            contentType: 'application/json',
            success: function(response) {
                if (response.status === 'success') {
                    $loadingIa.slideUp(300, function() {
                        $listaRecomendaciones.empty();
                        response.recomendaciones.forEach(function(rec) {
                            $listaRecomendaciones.append('<li>' + rec + '</li>');
                        });
                        $listaRecomendaciones.slideDown(300);
                    });
                } else {
                    $loadingIa.html('<p class="text-danger text-sm text-center"><i class="material-symbols-rounded align-middle text-sm me-1">error</i> La IA no pudo generar el análisis.</p>');
                }
            },
            error: function() {
                $loadingIa.html('<p class="text-danger text-sm text-center"><i class="material-symbols-rounded align-middle text-sm me-1">wifi_off</i> Fallo de conexión con el motor de IA.</p>');
            }
        });
    }
});