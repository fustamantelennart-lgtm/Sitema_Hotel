const overlay = document.getElementById('modalOverlay');
const btnClose = document.getElementById('modalClose');

document.querySelectorAll('.hab-celda').forEach(function(celda) {
    celda.addEventListener('click', function() {
        document.getElementById('modalNumero').textContent = this.dataset.numero;
        document.getElementById('modalTipo').textContent   = this.dataset.tipo;
        document.getElementById('modalEstado').textContent = this.dataset.estado;
        document.getElementById('modalPrecio').textContent = this.dataset.precio;
        overlay.style.display = 'flex';
    });
});

btnClose.addEventListener('click', function() {
    overlay.style.display = 'none';
});

overlay.addEventListener('click', function(e) {
    if (e.target === overlay) overlay.style.display = 'none';
});