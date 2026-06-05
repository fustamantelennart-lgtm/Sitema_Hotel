// Resaltar habitación seleccionada
document.querySelectorAll('.hab-celda input[type="radio"]').forEach(function(radio) {
    radio.addEventListener('change', function() {
        // Quitar selección anterior
        document.querySelectorAll('.hab-celda').forEach(function(celda) {
            celda.style.outline = 'none';
            celda.style.boxShadow = '';
        });
        // Resaltar la seleccionada
        this.closest('.hab-celda').style.outline = '2px solid var(--color-primary)';
        this.closest('.hab-celda').style.boxShadow = '0 0 0 4px rgba(45,74,62,.12)';
    });
});