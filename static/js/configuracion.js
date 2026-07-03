// ==========================================
// LÓGICA DE PREVISUALIZACIÓN DE LOGO
// ==========================================

let intervaloWsp; // Creamos una variable global para el reloj

function previewImage(event) {
    var reader = new FileReader();
    reader.onload = function() {
        var output = document.getElementById('logoPreview');
        output.src = reader.result;
        document.getElementById('btnCancelLogo').style.display = 'inline-flex';
    };
    if(event.target.files && event.target.files[0]){
        reader.readAsDataURL(event.target.files[0]);
    }
}

function cancelarLogoNuevo() {
    // Usamos la URL original inyectada desde Django
    document.getElementById('logoPreview').src = window.ConfiguracionGlobal.logoOriginalUrl;
    document.getElementById('logoInput').value = ''; 
    document.getElementById('btnCancelLogo').style.display = 'none';
}

// ==========================================
// LÓGICA DE NOTIFICACIONES (KILL SWITCH)
// ==========================================
function pausarNotificacionesSistema(estaPausado) {
    const formData = new FormData();
    formData.append('pausar', estaPausado);
    
    // El Token CSRF también lo sacamos del objeto global
    formData.append('csrfmiddlewaretoken', window.ConfiguracionGlobal.csrfToken);

    fetch(window.ConfiguracionGlobal.urls.pausarAlertas, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (estaPausado) {
                mostrarNotificacionExito("⏸️ Alertas de WhatsApp PAUSADAS");
            } else {
                mostrarNotificacionExito("✅ Alertas de WhatsApp REACTIVADAS");
            }
        } else {
            Swal.fire('Error', 'No se pudo actualizar el estado.', 'error');
        }
    })
    .catch(error => console.error('Error AJAX:', error));
}

// ==========================================
// LÓGICA DEL ROBOT DE WHATSAPP (NODE.JS)
// ==========================================
function verificarEstadoWhatsApp() {
    fetch(window.ConfiguracionGlobal.urls.estadoWsp)
    .then(res => res.json())
    .then(data => {
        const badge = document.getElementById('badgeEstadoWsp');
        const btnConectar = document.getElementById('btnEscanearWsp');
        const btnDesconectar = document.getElementById('btnDesconectarWsp');
        const contenedorQR = document.getElementById('contenedorQR');

        if (data.success && data.data) {
            if (data.data.conectado) {
                badge.className = 'badge badge-sm bg-gradient-success';
                badge.innerText = 'CONECTADO';
                btnConectar.classList.add('d-none'); 
                btnDesconectar.classList.remove('d-none'); 
                $('#modalQRWsp').modal('hide'); 

                // 💥 LA OPTIMIZACIÓN: Si ya se conectó, apagamos el reloj preguntón
                if (intervaloWsp) {
                    clearInterval(intervaloWsp);
                    intervaloWsp = null;
                }
            } else {
                badge.className = 'badge badge-sm bg-gradient-danger';
                badge.innerText = 'DESCONECTADO';
                btnConectar.classList.remove('d-none'); 
                btnDesconectar.classList.add('d-none'); 
                
                if (data.data.qr) {
                    contenedorQR.innerHTML = `<img src="${data.data.qr}" class="img-fluid border-radius-md" alt="Código QR WhatsApp">`;
                } else {
                    contenedorQR.innerHTML = `<div class="spinner-border text-info mt-4" role="status"></div><p class="text-xs mt-2">Generando nuevo QR...</p>`;
                }

                // Si está desconectado, nos aseguramos de que el reloj esté encendido
                if (!intervaloWsp) {
                    intervaloWsp = setInterval(verificarEstadoWhatsApp, 5000);
                }
            }
        } else {
            badge.className = 'badge badge-sm bg-gradient-secondary';
            badge.innerText = 'SERVIDOR APAGADO';
            btnConectar.classList.add('d-none');
            btnDesconectar.classList.add('d-none');
        }
    })
    .catch(err => console.error(err));
}

function desconectarWhatsApp() {
    Swal.fire({
        title: '¿Cerrar sesión de WhatsApp?',
        text: "El robot dejará de enviar notificaciones hasta que se vuelva a escanear el QR.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f44336',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, desconectar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(window.ConfiguracionGlobal.urls.desconectarWsp, {
                method: 'POST',
                headers: { 
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': window.ConfiguracionGlobal.csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    mostrarNotificacionExito("Sesión de WhatsApp cerrada correctamente.");
                    verificarEstadoWhatsApp(); 
                } else {
                    Swal.fire('Error', 'No se pudo desconectar el servidor.', 'error');
                }
            });
        }
    });
}

// Inicialización cuando carga la página
document.addEventListener("DOMContentLoaded", function() {
    verificarEstadoWhatsApp();
    // Iniciamos el reloj la primera vez
    intervaloWsp = setInterval(verificarEstadoWhatsApp, 5000); 
});