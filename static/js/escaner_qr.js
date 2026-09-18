$(document).ready(function() {
    const html5QrCode = new Html5Qrcode("qr-reader");
    const btnIniciar = $('#btn-iniciar-camara');
    const btnDetener = $('#btn-detener-camara'); // 💥 Seleccionamos el nuevo botón
    const btnReiniciar = $('#btn-reiniciar');
    const divResultado = $('#resultado-escaneo');
    const textoEspera = $('#texto-espera');
    const csrfToken = $('[name=csrfmiddlewaretoken]').val();
    
    let escaneoEnProceso = false;
    const config = { fps: 10, qrbox: { width: 250, height: 250 }, aspectRatio: 1.0 };

    function apagarCamara() {
        if (html5QrCode.isScanning) {
            html5QrCode.stop().then(() => {
                textoEspera.html("<i class='material-symbols-rounded text-secondary' style='font-size: 48px;'>videocam_off</i><br>Cámara apagada");
                textoEspera.removeClass('d-none');
                btnIniciar.removeClass('d-none').html('<i class="material-symbols-rounded align-middle me-1">photo_camera</i> Activar Cámara').prop('disabled', false);
                btnDetener.addClass('d-none');
                btnReiniciar.addClass('d-none');
            }).catch(err => console.error(err));
        }
    }

    const onScanSuccess = (decodedText, decodedResult) => {
        if (escaneoEnProceso) return;
        escaneoEnProceso = true;
        
        // APAGAR CÁMARA POR COMPLETO AL LEER
        html5QrCode.stop().then(() => {
            textoEspera.html("<i class='material-symbols-rounded text-success' style='font-size: 48px;'>check_circle</i><br>Procesando...");
            textoEspera.removeClass('d-none');
            btnDetener.addClass('d-none');
        });
        
        Swal.fire({ title: 'Procesando...', allowOutsideClick: false, didOpen: () => { Swal.showLoading(); }});

        let urlDestino = "/asistencia/api/registrar/"; 
        
        if (!decodedText.startsWith("PER-") && !decodedText.startsWith("DOC-") && !decodedText.startsWith("EST-")) {
            Swal.fire({ icon: 'error', title: 'Código Inválido', text: 'Este QR no pertenece a la institución.' });
            btnReiniciar.removeClass('d-none');
            return;
        }

        $.ajax({
            url: urlDestino,
            type: "POST",
            contentType: "application/json",
            headers: { 'X-CSRFToken': csrfToken },
            data: JSON.stringify({ codigo_qr: decodedText }),
            success: function(data) {
                if(data.status === 'success') {
                    Swal.fire({ icon: 'success', title: '¡Registrado!', text: `${data.tipo} a las ${data.hora} - ${data.mensaje}`, timer: 2000, showConfirmButton: false });
                    divResultado.html(`<span class="text-success text-lg">Último escaneo: ${data.hora}</span>`);
                } else if (data.status === 'warning') {
                    // 💥 Manejo amigable si el alumno ya se registró
                    Swal.fire({ icon: 'info', title: 'Atención', text: data.mensaje, timer: 3000, showConfirmButton: false });
                } else {
                    Swal.fire({ icon: 'error', title: 'Error', text: data.mensaje });
                }
            },
            error: function(xhr) {
                // 💥 Ahora lee el mensaje real de Django si choca
                let msg = (xhr.responseJSON && xhr.responseJSON.mensaje) ? xhr.responseJSON.mensaje : 'Problema de red o servidor.';
                Swal.fire({ icon: 'error', title: 'Error', text: msg });
            },
            complete: function() {
                btnReiniciar.removeClass('d-none');
            }
        });
    };

    function encenderCamara() {
        textoEspera.addClass('d-none');
        navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
        .then(function(stream) {
            stream.getTracks().forEach(track => track.stop());
            html5QrCode.start({ facingMode: "environment" }, config, onScanSuccess)
            .then(() => { 
                btnIniciar.addClass('d-none'); 
                btnDetener.removeClass('d-none'); // Mostrar botón de apagar
                btnReiniciar.addClass('d-none');
            });
        })
        .catch(function(err) {
            Swal.fire({ icon: 'error', title: 'Permiso Denegado', text: 'Permite el acceso a la cámara.' });
            btnIniciar.html('<i class="material-symbols-rounded align-middle me-1">photo_camera</i> Activar Cámara').prop('disabled', false);
        });
    }

    btnIniciar.on('click', function() {
        $(this).html('<span class="spinner-border spinner-border-sm me-2"></span> Iniciando...');
        $(this).prop('disabled', true);
        encenderCamara();
    });

    btnDetener.on('click', apagarCamara); // Evento para detener

    btnReiniciar.on('click', function() {
        escaneoEnProceso = false;
        divResultado.html('');
        encenderCamara(); 
    });
});