$(document).ready(function() {
    
    // 1. Configuración maestra del Toast de SweetAlert2
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end', // Esquina superior derecha
        showConfirmButton: false,
        timer: 4000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer);
            toast.addEventListener('mouseleave', Swal.resumeTimer);
        }
    });

    // 2. Buscamos los mensajes renderizados por Django
    let $messages = $('.system-message');
    
    if ($messages.length > 0) {
        $messages.each(function() {
            let type = $(this).data('type'); // tags de Django ('success', 'error', etc.)
            let text = $(this).data('text');
            
            // 3. Mapeamos los tags de Django a los iconos de SweetAlert2
            let swalIcon = 'info';
            if (type.includes('success')) {
                swalIcon = 'success';
            } else if (type.includes('error') || type.includes('danger')) {
                swalIcon = 'error';
            } else if (type.includes('warning')) {
                swalIcon = 'warning';
            }

            // 4. Disparamos la notificación
            Toast.fire({
                icon: swalIcon,
                title: text
            });
        });
    }

    // Efecto visual UX al enviar el formulario de contraseña
    $('button[name="btn_cambiar_password"]').on('click', function() {
        let $form = $(this).closest('form');
        if ($form[0].checkValidity()) {
            $(this).html('<i class="material-symbols-rounded align-middle me-1 text-sm text-white spin" style="animation: spin 2s linear infinite;">autorenew</i> Procesando...');
            $(this).addClass('disabled');
        }
    });
});