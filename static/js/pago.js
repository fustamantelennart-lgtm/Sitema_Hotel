document.addEventListener('DOMContentLoaded', function () {

    const metodoBtns       = document.querySelectorAll('.metodo-btn-row');
    const metodoPagoInput  = document.getElementById('metodoPago');
    const panelTarjeta     = document.getElementById('panelTarjeta');
    const panelYape        = document.getElementById('panelYape');
    const panelTransferencia = document.getElementById('panelTransferencia');
    const checkTarjeta     = document.getElementById('checkTarjeta');
    const checkYape        = document.getElementById('checkYape');
    const checkTransferencia = document.getElementById('checkTransferencia');

    function mostrarPanel(metodo) {
        // Ocultar todos los paneles
        panelTarjeta.style.display      = 'none';
        panelYape.style.display         = 'none';
        panelTransferencia.style.display = 'none';

        // Resetear todos los checks y botones
        metodoBtns.forEach(btn => btn.classList.remove('active'));
        checkTarjeta.className      = 'bi bi-circle';
        checkTarjeta.style.color    = '#E5DDD0';
        checkYape.className         = 'bi bi-circle';
        checkYape.style.color       = '#E5DDD0';
        checkTransferencia.className = 'bi bi-circle';
        checkTransferencia.style.color = '#E5DDD0';

        // Activar el seleccionado
        metodoPagoInput.value = metodo;

        if (metodo === 'tarjeta') {
            panelTarjeta.style.display   = 'block';
            checkTarjeta.className       = 'bi bi-check-circle-fill';
            checkTarjeta.style.color     = '#2D4A3E';
            document.querySelector('[data-metodo="tarjeta"]').classList.add('active');
        } else if (metodo === 'yape') {
            panelYape.style.display      = 'block';
            checkYape.className          = 'bi bi-check-circle-fill';
            checkYape.style.color        = '#2D4A3E';
            document.querySelector('[data-metodo="yape"]').classList.add('active');
        } else if (metodo === 'transferencia') {
            panelTransferencia.style.display = 'block';
            checkTransferencia.className     = 'bi bi-check-circle-fill';
            checkTransferencia.style.color   = '#2D4A3E';
            document.querySelector('[data-metodo="transferencia"]').classList.add('active');
        }
    }

    // Click en método de pago
    metodoBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            mostrarPanel(this.dataset.metodo);
        });
    });

    // Preview tarjeta
    const numeroTarjeta  = document.getElementById('numeroTarjeta');
    const nombreTarjeta  = document.getElementById('nombreTarjeta');
    const expiracion     = document.getElementById('expiracion');
    const numPreview     = document.getElementById('tarjetaNumeroPreview');
    const nomPreview     = document.getElementById('tarjetaNombrePreview');
    const expPreview     = document.getElementById('tarjetaExpPreview');
    const tipoPreview    = document.getElementById('tarjetaTipo');

    if (numeroTarjeta) {
        numeroTarjeta.addEventListener('input', function () {
            let val = this.value.replace(/\D/g, '').slice(0, 16);
            this.value = val.replace(/(.{4})/g, '$1 ').trim();
            numPreview.textContent = this.value || '•••• •••• •••• ••••';

            // Detectar tipo de tarjeta
            if (val.startsWith('4')) {
                tipoPreview.innerHTML = '<i class="bi bi-credit-card" style="color:#1a1f71;"></i>';
            } else if (val.startsWith('5')) {
                tipoPreview.innerHTML = '<i class="bi bi-credit-card" style="color:#eb001b;"></i>';
            } else {
                tipoPreview.innerHTML = '<i class="bi bi-credit-card"></i>';
            }
        });
    }

    if (nombreTarjeta) {
        nombreTarjeta.addEventListener('input', function () {
            nomPreview.textContent = this.value.toUpperCase() || 'NOMBRE APELLIDO';
        });
    }

    if (expiracion) {
        expiracion.addEventListener('input', function () {
            let val = this.value.replace(/\D/g, '').slice(0, 4);
            if (val.length >= 2) val = val.slice(0, 2) + '/' + val.slice(2);
            this.value = val;
            expPreview.textContent = val || 'MM/AA';
        });
    }

    // Iniciar con tarjeta
    mostrarPanel('tarjeta');
});