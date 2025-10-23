document.addEventListener('DOMContentLoaded', function () {
    const toggleButtons = document.querySelectorAll('.toggle-password');

    toggleButtons.forEach(button => {
        button.addEventListener('click', function () {
            const passwordSpan = this.previousElementSibling; // El <span> con la contraseña
            const originalPassword = passwordSpan.getAttribute('data-password');
            const isHidden = passwordSpan.textContent === '••••••••';

            if (isHidden) {
                // Mostrar contraseña
                passwordSpan.textContent = originalPassword;
                this.querySelector('i').classList.remove('fa-eye-slash');
                this.querySelector('i').classList.add('fa-eye');
            } else {
                // Ocultar contraseña
                passwordSpan.textContent = '••••••••';
                this.querySelector('i').classList.remove('fa-eye');
                this.querySelector('i').classList.add('fa-eye-slash');
            }
        });
    });
});