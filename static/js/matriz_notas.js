$(document).ready(function() {
    
    // ========================================================
    // 1. MICRO-SCROLL INICIAL (Solo si vienes desde otra página)
    // ========================================================
    if (window.location.search.includes('asignacion_id=')) {
        setTimeout(function() {
            let zonaMatriz = document.getElementById('zona-matriz-detalle');
            if (zonaMatriz) {
                zonaMatriz.scrollIntoView({ behavior: 'auto', block: 'start' });
            }
        }, 10); 
    }

    // ========================================================
    // 2. FUNCIÓN MAESTRA PARA CONSTRUIR EL DATATABLES
    // ========================================================
    function iniciarDataTableMatriz() {
        if ($('#tablaMatriz').length) {
            // Si la tabla ya existe (porque hicimos AJAX), la destruimos para evitar duplicados
            if ($.fn.DataTable.isDataTable('#tablaMatriz')) {
                $('#tablaMatriz').DataTable().destroy();
            }

            let tabla = $('#tablaMatriz').DataTable({
                paging: false,       
                info: false,         
                ordering: false,     
                language: { 
                    url: "/static/plugins/datatables/js/es-ES.json",
                    emptyTable: "No hay alumnos matriculados o evaluaciones registradas en este curso."
                },
                dom: "<'row mb-3 align-items-center px-4'<'col-sm-12 col-md-6 text-start'f><'col-sm-12 col-md-6 text-end'B>>" +
                     "<'row'<'col-sm-12 px-0'<'table-responsive'tr>>>" + // 💥 LA SOLUCIÓN: El scroll envuelve SOLO a 'tr' (la tabla)
                     "<'row pt-3'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
                buttons: [
                    { 
                        text: '<i class="material-symbols-rounded align-middle me-1">table_view</i> Excel', 
                        className: 'btn btn-xs bg-gradient-success mb-0',
                        action: function (e, dt, node, config) {
                            let selectCurso = $('#select-curso');
                            let asignacionId = selectCurso.val();
                            let bimestre = $('#hidden_bimestre').val() || 'I';

                            // 💥 EXTRAEMOS LA URL LIMPIAMENTE DESDE EL ATRIBUTO DATA DEL HTML
                            let urlBase = selectCurso.data('url-base');
                            let urlFinal = urlBase.replace('999999', asignacionId) + "?bimestre=" + bimestre + "&blanco=0";

                            let enlaceTemporal = $('<a href="' + urlFinal + '" class="btn-descarga-excel" style="display:none;"></a>');
                            $('body').append(enlaceTemporal);
                            enlaceTemporal[0].click();
                            enlaceTemporal.remove();
                        }
                    },
                ]
            });

            // Generar la numeración de los alumnos automáticamente
            tabla.on('order.dt search.dt', function () {
                tabla.column(0, { search: 'applied', order: 'applied' }).nodes().each(function (cell, i) {
                    cell.innerHTML = i + 1;
                });
            }).draw();
        }
    }

    // Inicializamos la tabla al cargar la página por primera vez
    iniciarDataTableMatriz();

    // --------------------------------------------------------
    // 3. LA MAGIA: CAMBIAR DE CURSO O BIMESTRE POR AJAX
    // --------------------------------------------------------
    $('#select-curso, #hidden_bimestre').on('change', function() {
        let aulaId = $('#hidden_aula_id').val();
        let bimestre = $('#hidden_bimestre').val();
        let asignacionId = $('#select-curso').val();
        
        // Verificamos si estamos en "Modo Tutor" (oculto)
        let origen = $('#hidden_origen').length ? '&origen=' + $('#hidden_origen').val() : '';

        // Construimos la URL silenciosa manteniendo el origen
        let urlAjax = window.location.pathname + '?aula_id=' + aulaId + '&bimestre=' + bimestre + '&asignacion_id=' + asignacionId + origen;

        if ($.fn.DataTable.isDataTable('#tablaMatriz')) {
            $('#tablaMatriz').DataTable().destroy();
        }

        Swal.fire({
            title: 'Cargando matriz...',
            text: 'Obteniendo calificaciones del servidor',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); }
        });

        // Hacemos el reemplazo del fragmento HTML
        $('#contenedor-tabla-matriz').load(urlAjax + ' #contenedor-tabla-matriz > *', function(response, status, xhr) {
            if (status == "error") {
                Swal.fire('Error', 'Hubo un problema al cargar los datos.', 'error');
            } else {
                try {
                    iniciarDataTableMatriz();
                    Swal.close();
                    // Actualizamos la URL silenciosamente
                    window.history.replaceState(null, null, urlAjax);
                } catch (e) {
                    console.error("Error al construir la tabla:", e);
                    Swal.fire('Atención', 'Hubo un problema al organizar las columnas.', 'warning');
                }
            }
        });
    });
});

// ==========================================
// ANTI SCROLL-CHAINING (El Truco del Píxel)
// ==========================================
document.addEventListener("DOMContentLoaded", function() {
    const cajaDescargas = document.getElementById("caja-descargas");
    
    if (cajaDescargas) {
        // Función que mantiene el scroll a 1px de los bordes absolutos
        const despegarDeBordes = function() {
            // Calculamos el tope máximo de scroll hacia abajo
            const maxScroll = this.scrollHeight - this.clientHeight;
            
            // Solo actuamos si la caja realmente tiene barra de scroll
            if (maxScroll > 0) {
                if (this.scrollTop <= 0) {
                    // Si choca arriba, lo bajamos 1 píxel imperceptible
                    this.scrollTop = 1;
                } else if (this.scrollTop >= maxScroll) {
                    // Si choca abajo, lo subimos 1 píxel imperceptible
                    this.scrollTop = maxScroll - 1;
                }
            }
        };

        // 1. Damos el "empujón" apenas el mouse entra en la caja
        cajaDescargas.addEventListener("mouseenter", despegarDeBordes);
        
        // 2. Damos el "empujón" discretamente cuando el usuario termina de girar la rueda
        cajaDescargas.addEventListener("scroll", function() {
            clearTimeout(this.scrollTimeout);
            // Esperamos 100ms para no interrumpir el movimiento fluido de la rueda
            this.scrollTimeout = setTimeout(() => despegarDeBordes.call(this), 100);
        });
    }
});


// ========================================================
    // 4. DESCARGA DE EXCELS CON SWEETALERT Y FETCH
    // ========================================================
    $(document).on('click', '.btn-descarga-excel', async function(e) {
        e.preventDefault(); 
        
        let urlDescarga = $(this).attr('href');

        // Mostramos tu alerta personalizada
        Swal.fire({
            title: 'Generando Excel...',
            text: 'Por favor, espere un momento.',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); }
        });

        try {
            // Descargamos en segundo plano
            const response = await fetch(urlDescarga);
            if (!response.ok) throw new Error("Error en la respuesta del servidor");

            // Rescatamos el nombre real del archivo desde Python
            let filename = "Reporte_Academico.xlsx";
            const disposition = response.headers.get('Content-Disposition');
            if (disposition && disposition.includes('filename=')) {
                filename = disposition.split('filename=')[1].split(';')[0].replace(/['"]/g, '');
            }

            // Convertimos la data y forzamos la descarga nativa
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            
            // Limpiamos la memoria y cerramos el modal de éxito
            window.URL.revokeObjectURL(downloadUrl);
            a.remove();
            Swal.close();

        } catch (error) {
            console.error("Error en la descarga:", error);
            Swal.fire({
                icon: 'error',
                title: 'Error de servidor',
                text: 'Hubo un problema al generar el documento. Inténtelo nuevamente.'
            });
        }
    });