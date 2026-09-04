/**
 * ARCHIVO: reporte_progresivo_aula.js
 * DESCRIPCIÓN: Controlador para renderizar en lote los gráficos de barras y exportarlos en un único documento PDF.
 */

document.addEventListener("DOMContentLoaded", function() {
    const canvasElements = document.querySelectorAll('.graficoLote');
    let instanciasCharts = [];

    // 1. Inicializar todas las gráficas mediante bucle
    canvasElements.forEach(canvas => {
        const notasBase20 = [
            parseFloat(canvas.getAttribute('data-puntualidad')) || 0,
            parseFloat(canvas.getAttribute('data-presentacion')) || 0,
            parseFloat(canvas.getAttribute('data-participacion')) || 0,
            parseFloat(canvas.getAttribute('data-disciplina')) || 0,
            parseFloat(canvas.getAttribute('data-responsabilidad')) || 0,
            parseFloat(canvas.getAttribute('data-apoyo-ppff')) || 0
        ];
        
        const porcentajes = notasBase20.map(n => n * 5);
        const colores = porcentajes.map(p => {
            if (p === 0) return '#e9ecef';
            if (p <= 50) return '#dc3545';
            if (p <= 65) return '#fd7e14';
            if (p <= 80) return '#ffc107';
            if (p <= 90) return '#0d6efd';
            return '#198754';
        });

        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Puntualidad', 'Presentación', 'Participación', 'Disciplina', 'Responsabilidad', 'Apoyo PPFF'],
                datasets: [{ data: porcentajes, backgroundColor: colores, borderWidth: 1, borderColor: '#333333', borderRadius: 4 }]
            },
            options: {
                devicePixelRatio: 4,
                responsive: true, 
                maintainAspectRatio: false, 
                animation: { duration: 1000 },
                scales: { y: { beginAtZero: true, max: 100, ticks: { stepSize: 20 } } },
                plugins: { legend: { display: false } }
            }
        });
        instanciasCharts.push(chart);
    });

    // 2. Exportación a PDF Lote (Método Anti-Colapso de Lienzo)
    const btnExportarLote = document.getElementById('btn-exportar-lote');
    
    if(btnExportarLote) {
        btnExportarLote.addEventListener('click', function() {
            const btn = this;
            const originalText = btn.innerHTML;
            const grado = btn.getAttribute('data-grado') || 'Grado';
            const seccion = btn.getAttribute('data-seccion') || 'Seccion';
            
            // 💥 EN LUGAR DEL PADRE, SELECCIONAMOS TODAS LAS HOJAS INDIVIDUALES
            const paginas = document.querySelectorAll('.a4-container');

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm align-middle me-2"></span> Procesando PDF, espere, por favor...';

            instanciasCharts.forEach(c => { c.options.animation = false; c.update(); });

            // Forzamos el scroll arriba para que la cámara no se desfase
            window.scrollTo(0, 0);

            const opt = {
                margin: 0,
                filename: `Informes_Aula_${grado}_${seccion}.pdf`,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { 
                    scale: 4, 
                    letterRendering: true,
                    useCORS: true, 
                    logging: false,
                    scrollY: 0
                },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };

            // 💥 PROCESAMIENTO EN BUCLE (Evita el límite de altura de Chrome)
            // Iniciamos el PDF con el primer alumno
            let worker = html2pdf().set(opt).from(paginas[0]).toPdf();

            // Iteramos sobre el resto de alumnos agregando una página nueva por cada uno
            for (let i = 1; i < paginas.length; i++) {
                worker = worker.get('pdf').then(pdf => {
                    pdf.addPage();
                }).from(paginas[i]).toContainer().toCanvas().toPdf();
            }

            // Finalmente guardamos el archivo consolidado
            worker.save().then(() => {
                btn.disabled = false;
                btn.innerHTML = originalText;
                instanciasCharts.forEach(c => { c.options.animation = { duration: 1000 }; c.update(); });
            });
        });
    }
});