const togglePassword = document.getElementById('togglePassword');
const passwordInput  = document.getElementById('passwordInput');
const eyeIcon        = document.getElementById('eyeIcon');

if (togglePassword) {
    togglePassword.addEventListener('click', function() {
        const tipo = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = tipo;
        eyeIcon.className  = tipo === 'password' ? 'bi bi-eye' : 'bi bi-eye-slash';
    });
}