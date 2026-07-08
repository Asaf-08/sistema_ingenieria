$(document).ready(function() {
    const html5QrCode = new Html5Qrcode("qr-reader");
    const btnIniciar = $('#btn-iniciar-camara');
    const btnReiniciar = $('#btn-reiniciar');
    const divResultado = $('#resultado-escaneo');
    const textoEspera = $('#texto-espera');
    const csrfToken = $('[name=csrfmiddlewaretoken]').val();
    
    let escaneoEnProceso = false;
    const config = { fps: 10, qrbox: { width: 250, height: 250 }, aspectRatio: 1.0 };

    const onScanSuccess = (decodedText, decodedResult) => {
        if (escaneoEnProceso) return;
        escaneoEnProceso = true;
        
        // APAGAR CÁMARA POR COMPLETO PARA AHORRAR BATERÍA
        html5QrCode.stop().then(() => {
            textoEspera.html("<i class='material-symbols-rounded text-success' style='font-size: 48px;'>check_circle</i><br>Cámara en reposo");
            textoEspera.removeClass('d-none');
        }).catch(err => console.error(err));
        
        Swal.fire({ title: 'Procesando...', allowOutsideClick: false, didOpen: () => { Swal.showLoading(); }});

        // 💥 TODO ESCANEO VA A LA RUTA PRINCIPAL
        let urlDestino = "/asistencia/api/registrar/"; 
        
        // Solo verificamos que sea un código de la institución para que no escaneen basura
        if (!decodedText.startsWith("PER-") && !decodedText.startsWith("DOC-") && !decodedText.startsWith("EST-")) {
            Swal.fire({ icon: 'error', title: 'Código Inválido', text: 'Este QR no pertenece a la institución.' });
            btnReiniciar.removeClass('d-none');
            return;
        }

        // 💥 Petición AJAX al estilo jQuery
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
                } else {
                    Swal.fire({ icon: 'error', title: 'Error', text: data.mensaje });
                }
            },
            error: function() {
                Swal.fire({ icon: 'error', title: 'Error', text: 'Problema de red o de servidor.' });
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
                btnReiniciar.addClass('d-none');
            });
        })
        .catch(function(err) {
            Swal.fire({ icon: 'error', title: 'Permiso Denegado', text: 'Permite el acceso a la cámara.' });
            btnIniciar.prop('disabled', false);
        });
    }

    btnIniciar.on('click', function() {
        $(this).html('<span class="spinner-border spinner-border-sm me-2"></span> Iniciando...');
        $(this).prop('disabled', true);
        encenderCamara();
    });

    btnReiniciar.on('click', function() {
        escaneoEnProceso = false;
        divResultado.html('');
        encenderCamara(); 
    });
});