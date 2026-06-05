document.querySelectorAll('.habitacion-celda').forEach(function(celda) {
    celda.addEventListener('click', function() {
        document.getElementById('modalNumero').textContent = this.dataset.numero;
        document.getElementById('modalTipo').textContent   = this.dataset.tipo;
        document.getElementById('modalEstado').textContent = this.dataset.estado;
        document.getElementById('modalPrecio').textContent = this.dataset.precio;

        new bootstrap.Modal(document.getElementById('modalHab')).show();
    });
});