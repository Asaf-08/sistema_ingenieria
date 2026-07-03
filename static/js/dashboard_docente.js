$(document).ready(function () {
    
    // Verificamos si hay gráficos en esta pantalla (buscando cualquier canvas que su ID empiece con "chart-")
    if ($('canvas[id^="chart-"]').length) {
        
        // Recorremos dinámicamente cada gráfico que Django haya creado (ej: Primaria, Secundaria)
        $('canvas[id^="chart-"]').each(function () {
            
            let canvasId = $(this).attr('id'); // Extraemos el ID (ej: chart-Primaria)
            let nivel = canvasId.split('-')[1]; // Nos quedamos solo con la palabra (ej: Primaria)
            
            // Buscamos el JSON oculto que le corresponde a este nivel
            let dataElement = $('#data-' + nivel);
            
            if (dataElement.length && dataElement.text().trim() !== "") {
                try {
                    let chartData = JSON.parse(dataElement.text());
                    let ctx = $(this)[0].getContext("2d");
                    
                    new Chart(ctx, {
                        type: "bar",
                        data: {
                            labels: chartData.labels,
                            datasets: [{
                                label: "Promedio",
                                backgroundColor: "#4CAF50", // Verde vibrante
                                borderRadius: 4,
                                data: chartData.data,
                                maxBarThickness: 30
                            }],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    suggestedMax: 20, // Asumiendo notas base 20
                                    grid: { drawBorder: false, display: true, borderDash: [5, 5], color: '#e5e5e5' },
                                    ticks: { padding: 10, color: "#737373" }
                                },
                                x: {
                                    grid: { display: false },
                                    ticks: { color: '#737373', font: { size: 11 } }
                                }
                            }
                        }
                    });
                } catch (error) {
                    console.error(`Error al procesar el gráfico del nivel ${nivel}:`, error);
                }
            }
        });
    }
});