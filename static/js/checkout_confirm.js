const overlay      = document.getElementById('modalConfirmarCheckout');
const btnAbrir      = document.getElementById('btnAbrirConfirmacion');
const btnCerrar      = document.getElementById('modalConfirmarClose');
const btnCancelar    = document.getElementById('modalConfirmarCancelar');
const btnConfirmar   = document.getElementById('btnConfirmarDefinitivo');
const formCheckout   = btnAbrir.closest('form');

btnAbrir.addEventListener('click', function() {
    overlay.style.display = 'flex';
});
btnCerrar.addEventListener('click', function() {
    overlay.style.display = 'none';
});
btnCancelar.addEventListener('click', function() {
    overlay.style.display = 'none';
});
overlay.addEventListener('click', function(e) {
    if (e.target === overlay) overlay.style.display = 'none';
});
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') overlay.style.display = 'none';
});
btnConfirmar.addEventListener('click', function() {
    formCheckout.submit();
});