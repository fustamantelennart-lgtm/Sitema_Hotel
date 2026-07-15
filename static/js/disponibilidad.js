const filtroPiso = document.getElementById('filtroPiso');

if (filtroPiso) {
    filtroPiso.addEventListener('change', function() {
        const pisoSeleccionado = filtroPiso.value;
        document.querySelectorAll('.cal-fila').forEach(function(fila) {
            if (pisoSeleccionado === '' || fila.dataset.piso === pisoSeleccionado) {
                fila.style.display = '';
            } else {
                fila.style.display = 'none';
            }
        });
    });
}