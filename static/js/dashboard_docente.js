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

document.addEventListener("DOMContentLoaded", function() {
    const contenedorDatos = document.getElementById('data-graficos-tutor');
    
    if (contenedorDatos) {
        // Parseamos todo el diccionario que envió Python
        const datosTutor = JSON.parse(contenedorDatos.textContent);
        
        let chartMapa = null;
        let chartCursos = null;
        
        const ctxMapa = document.getElementById("chart-mapa-riesgo").getContext("2d");
        const ctxCursos = document.getElementById("chart-cursos-criticos").getContext("2d");

        // Función constructora/actualizadora
        function renderizarGraficos(aulaId) {
            const dataActual = datosTutor[aulaId];

            // --- 1. RENDERIZAR MAPA (DONA) ---
            if (chartMapa) {
                chartMapa.data.datasets[0].data = dataActual.mapa;
                chartMapa.update();
            } else {
                chartMapa = new Chart(ctxMapa, {
                    type: "doughnut",
                    data: {
                        labels: ["Riesgo Crítico (<11)", "Observación (11-13)", "Estable (14-16)", "Sobresaliente (17-20)"],
                        datasets: [{
                            weight: 9,
                            cutout: '75%',
                            borderWidth: 2,
                            backgroundColor: ['#f53939', '#fb8c00', '#4caf50', '#1a73e8'],
                            data: dataActual.mapa,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: true, position: 'right' } }
                    },
                });
            }

            // --- 2. RENDERIZAR CURSOS (BARRAS) ---
            if (chartCursos) {
                chartCursos.data.labels = dataActual.cursos.labels;
                chartCursos.data.datasets[0].data = dataActual.cursos.data;
                chartCursos.update();
            } else {
                chartCursos = new Chart(ctxCursos, {
                    type: "bar",
                    data: {
                        labels: dataActual.cursos.labels,
                        datasets: [{
                            borderRadius: 4,
                            backgroundColor: '#fb8c00', 
                            data: dataActual.cursos.data,
                            maxBarThickness: 35
                        }]
                    },
                    options: {
                        indexAxis: 'y', 
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { grid: { display: false }, ticks: { color: '#9ca2b7' } },
                            x: { grid: { borderDash: [5, 5] }, ticks: { color: '#9ca2b7' }, min: 0, max: 20 },
                        },
                    },
                });
            }
        }

        // 💥 Carga Inicial (Arranca leyendo el primer option del select o el input oculto)
        const selectAula = document.getElementById('select-graficos-aula');
        
        if (selectAula && selectAula.value) {
            renderizarGraficos(selectAula.value);

            // Solo agregamos evento de "change" si es un select real (no un input oculto)
            if (selectAula.tagName.toLowerCase() === 'select') {
                selectAula.addEventListener('change', function(e) {
                    renderizarGraficos(e.target.value);
                });
            }
        }
    }
});