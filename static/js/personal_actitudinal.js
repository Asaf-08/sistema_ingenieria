// 💥 TERCERA REGLA DE ORO: PARCHE DE SEGURIDAD
function escapeHTML(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Extracción segura del Token
function getCSRFToken() {
    const tokenInput = document.getElementById('csrfToken');
    return tokenInput ? tokenInput.value : '';
}

$(document).ready(function() {
    
    // Obtenemos la URL que Django renderizó en el HTML
    const urlGuardar = $('#urlGuardarActitudinal').val();

    $('.input-actitudinal').on('blur', async function() {
        let inputEl = $(this);
        let evalId = inputEl.data('id');
        let campo = inputEl.data('campo');
        let valorString = String(inputEl.val()).trim();

        // 💥 VALIDACIÓN SEGURA: Bloqueamos números irreales
        if (valorString !== '' && (Number(valorString) < 0 || Number(valorString) > 20)) {
            Swal.fire({
                icon: 'warning',
                title: 'Puntaje inválido',
                text: 'La calificación actitudinal debe estar entre 0 y 20.',
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 2500
            });
            inputEl.val('');
            inputEl.addClass('border-danger');
            return;
        }

        // Efecto visual: procesando (borde azul)
        inputEl.removeClass('border-danger border-success').addClass('border-info');

        try {
            const params = new URLSearchParams();
            params.append('eval_id', evalId);
            params.append('campo', campo);
            params.append('valor', valorString);

            // 💥 FETCH MODERNO CON ASYNC/AWAIT
            const response = await fetch(urlGuardar, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCSRFToken()
                },
                body: params
            });
            
            const data = await response.json();

            if (data.status === 'ok' || data.success) {
                // Éxito: Actualiza color y promedio en vivo
                inputEl.removeClass('border-info').addClass('border-success');
                $('#promedio-' + evalId).text('Promedio: ' + Math.round(data.nuevo_promedio));
                
                // Quitamos el borde verde después de segundo y medio
                setTimeout(() => inputEl.removeClass('border-success'), 1500);
            } else {
                // Error reportado por el backend
                inputEl.removeClass('border-info').addClass('border-danger');
                Swal.fire({
                    icon: 'error',
                    title: 'Atención',
                    text: escapeHTML(data.message || 'No se pudo guardar la calificación.'),
                    toast: true,
                    position: 'top-end',
                    showConfirmButton: false,
                    timer: 3000
                });
            }
        } catch (error) {
            // Error de caída de red o servidor muerto
            inputEl.removeClass('border-info').addClass('border-danger');
            console.error("Error de conexión al guardar:", error);
        }
    });
});