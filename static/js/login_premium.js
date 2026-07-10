// static/js/login_premium.js

document.addEventListener("DOMContentLoaded", function() {
    // Control de etiquetas flotantes para Material Design
    const inputs = document.querySelectorAll('.form-control');
    
    inputs.forEach(input => {
        // Validación inicial por si el navegador autocompleta credenciales
        if (input.value !== '') {
            input.parentElement.classList.add('is-filled');
        }

        input.addEventListener('focus', () => {
            input.parentElement.classList.add('is-focused');
        });
        
        input.addEventListener('blur', () => {
            input.parentElement.classList.remove('is-focused');
            if (input.value !== '') {
                input.parentElement.classList.add('is-filled');
            } else {
                input.parentElement.classList.remove('is-filled');
            }
        });
    });

    // ==========================================
    // Lógica para Mostrar/Ocultar Contraseña
    // ==========================================
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('passwordInput');
    const toggleIcon = document.getElementById('toggleIcon');

    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function () {
            // Alternar el atributo type del input
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Alternar el ícono (ojo abierto / ojo cerrado)
            toggleIcon.textContent = type === 'password' ? 'visibility' : 'visibility_off';
            
            // Opcional: mantener el color del ícono más oscuro cuando se está viendo la clave
            if (type === 'text') {
                toggleIcon.classList.remove('text-secondary');
                toggleIcon.classList.add('text-dark');
            } else {
                toggleIcon.classList.remove('text-dark');
                toggleIcon.classList.add('text-secondary');
            }
        });
    }
});