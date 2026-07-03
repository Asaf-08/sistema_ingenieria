$(document).ready(function () {
    
    // Solo ejecutamos este código si estamos en la vista de Coordinación (donde existe el gráfico)
    if ($('#chart-asistencia').length) {
        
        try {
            // 1. EXTRAER DATOS SEGUROS (Con Fallbacks para evitar que el JS colapse si hay datos nulos)
            const diasSemana = JSON.parse($('#data-dias').text() || '[]');
            const asistenciasSemana = JSON.parse($('#data-asistencias').text() || '[]');
            const labelsBimestres = JSON.parse($('#data-labels-bimestres').text() || '[]');
            const valoresBimestres = JSON.parse($('#data-valores-bimestres').text() || '[]');
            const kmeansData = JSON.parse($('#data-kmeans').text() || '{"optimos": 0, "esfuerzo": 0, "riesgo": 0}');

            // 2. DIBUJAR GRÁFICO 1: ASISTENCIA
            var ctx1 = $('#chart-asistencia')[0].getContext("2d");
            new Chart(ctx1, {
                type: "bar",
                data: {
                    labels: diasSemana,
                    datasets: [{
                        label: "Presentes",
                        tension: 0.4,
                        borderWidth: 0,
                        borderRadius: 4,
                        backgroundColor: "rgba(255, 255, 255, 0.8)",
                        data: asistenciasSemana,
                        maxBarThickness: 15
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    interaction: { intersect: false, mode: 'index' },
                    scales: {
                        y: {
                            grid: { drawBorder: false, display: true, drawOnChartArea: true, drawTicks: false, borderDash: [5, 5], color: 'rgba(255, 255, 255, 0.2)' },
                            ticks: { suggestedMin: 0, padding: 10, font: { size: 14, lineHeight: 2 }, color: "#ffffff" },
                        },
                        x: {
                            grid: { drawBorder: false, display: false, drawOnChartArea: false, drawTicks: false, borderDash: [5, 5] },
                            ticks: { display: true, color: '#ffffff', padding: 10, font: { size: 14, lineHeight: 2 } },
                        },
                    },
                }
            });

            // 3. DIBUJAR GRÁFICO 2: RENDIMIENTO
            var ctx2 = $('#chart-rendimiento')[0].getContext("2d");
            new Chart(ctx2, {
                type: "line",
                data: {
                    labels: labelsBimestres,
                    datasets: [{
                        label: "Promedio Escolar",
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointBackgroundColor: "#ffffff",
                        pointBorderColor: "transparent",
                        borderColor: "#ffffff",
                        backgroundColor: "transparent",
                        fill: true,
                        data: valoresBimestres
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    interaction: { intersect: false, mode: 'index' },
                    scales: {
                        y: {
                            grid: { drawBorder: false, display: true, drawOnChartArea: true, drawTicks: false, borderDash: [4, 4], color: 'rgba(255, 255, 255, 0.2)' },
                            ticks: { display: true, padding: 10, color: '#ffffff', font: { size: 12, lineHeight: 2 } }
                        },
                        x: {
                            grid: { drawBorder: false, display: false, drawOnChartArea: false, drawTicks: false, borderDash: [5, 5] },
                            ticks: { display: true, color: '#ffffff', padding: 10, font: { size: 12, lineHeight: 2 } }
                        },
                    },
                }
            });

            // 4. DIBUJAR GRÁFICO 3: INTELIGENCIA ARTIFICIAL
            if (typeof ChartDataLabels !== 'undefined') {
                var ctx3 = $('#chart-kmeans')[0].getContext("2d");
                new Chart(ctx3, {
                    type: "doughnut",
                    plugins: [ChartDataLabels],
                    data: {
                        labels: ["Óptimo", "Esfuerzo", "Crítico"],
                        datasets: [{
                            data: [kmeansData.optimos, kmeansData.esfuerzo, kmeansData.riesgo],
                            backgroundColor: ["#4CAF50", "#FB8C00", "#F44336"],
                            borderWidth: 0
                        }],
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '70%',
                        plugins: {
                            legend: { display: true, position: 'bottom', labels: { color: '#fff' } },
                            datalabels: {
                                color: '#fff',
                                font: { weight: 'bold', size: 14 },
                                formatter: (value) => value > 0 ? value : '' 
                            }
                        }
                    }
                });
            }
            
        } catch (error) {
            console.error("Error al procesar y dibujar los gráficos del Dashboard Admin:", error);
        }
    }
});