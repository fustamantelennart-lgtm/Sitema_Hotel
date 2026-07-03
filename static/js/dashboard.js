const overlay = document.getElementById('modalOverlay');
const btnClose = document.getElementById('modalClose');

document.querySelectorAll('.hab-celda').forEach(function(celda) {
    celda.addEventListener('click', function() {
        const numero = this.dataset.numero;
        const tipo   = this.dataset.tipo;
        const estado = this.dataset.estado;
        const precio = this.dataset.precio;
        const id     = this.dataset.id;

        document.getElementById('modalNumero').textContent = numero;
        document.getElementById('modalTipo').textContent   = tipo;
        document.getElementById('modalEstado').textContent = estado;
        document.getElementById('modalPrecio').textContent = precio;

        // Botones según estado
        const acciones = document.getElementById('modalAcciones');
        acciones.innerHTML = '';

        if (estado === 'Disponible') {
            const btnReservar = document.createElement('a');
            btnReservar.href      = `/reservas/nueva/?tipo=${id}`;
            btnReservar.className = 'btn-primary';
            btnReservar.style.cssText = 'justify-content:center; text-align:center;';
            btnReservar.innerHTML = '<i class="bi bi-calendar-plus"></i> Nueva reserva';
            acciones.appendChild(btnReservar);

            const btnDisponibilidad = document.createElement('a');
            btnDisponibilidad.href      = `/reservas/disponibilidad/?tipo=${id}`;
            btnDisponibilidad.className = 'btn-secondary';
            btnDisponibilidad.style.cssText = 'justify-content:center; text-align:center;';
            btnDisponibilidad.innerHTML = '<i class="bi bi-calendar3"></i> Ver disponibilidad';
            acciones.appendChild(btnDisponibilidad);
        }

        overlay.style.display = 'flex';
    });
});

btnClose.addEventListener('click', function() {
    overlay.style.display = 'none';
});

overlay.addEventListener('click', function(e) {
    if (e.target === overlay) overlay.style.display = 'none';
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') overlay.style.display = 'none';
});