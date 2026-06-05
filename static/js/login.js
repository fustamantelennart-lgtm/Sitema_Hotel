document.getElementById('togglePassword').addEventListener('click', function () {
    const input   = document.getElementById('password');
    const eyeIcon = document.getElementById('eyeIcon');

    if (input.type === 'password') {
        input.type        = 'text';
        eyeIcon.className = 'bi bi-eye-slash';
    } else {
        input.type        = 'password';
        eyeIcon.className = 'bi bi-eye';
    }
});