// Calcular precio automáticamente al cambiar fechas o tipo de habitación
const fechaEntrada   = document.getElementById('id_fecha_entrada');
const fechaSalida    = document.getElementById('id_fecha_salida');
const precioDisplay  = document.getElementById('precio-calculado');

function calcularNoches() {
    if (!fechaEntrada || !fechaSalida || !precioDisplay) return;
    const entrada = new Date(fechaEntrada.value);
    const salida  = new Date(fechaSalida.value);
    if (entrada && salida && salida > entrada) {
        const noches = (salida - entrada) / (1000 * 60 * 60 * 24);
        precioDisplay.textContent = noches + ' noche(s)';
    }
}

if (fechaEntrada) fechaEntrada.addEventListener('change', calcularNoches);
if (fechaSalida)  fechaSalida.addEventListener('change',  calcularNoches);