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
});