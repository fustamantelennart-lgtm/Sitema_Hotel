const fechaEntrada    = document.getElementById('id_fecha_entrada');
const fechaSalida     = document.getElementById('id_fecha_salida');
const tipoHabitacion  = document.getElementById('id_tipo_habitacion');
const resumenNoches   = document.getElementById('resumenNoches');
const resumenTipo     = document.getElementById('resumenTipo');
const resumenTotal    = document.getElementById('resumenTotal');

function actualizarResumen() {
    // Noches
    if (fechaEntrada.value && fechaSalida.value) {
        const entrada = new Date(fechaEntrada.value);
        const salida  = new Date(fechaSalida.value);
        const noches  = Math.round((salida - entrada) / (1000 * 60 * 60 * 24));
        resumenNoches.textContent = noches > 0 ? noches + ' noche(s)' : '—';
    }

    // Tipo
    if (tipoHabitacion.value) {
        const texto = tipoHabitacion.options[tipoHabitacion.selectedIndex].text;
        resumenTipo.textContent = texto;
    }
}

function mostrarTab(tab, btn) {
    document.querySelectorAll('.tab-content').forEach(function(el) {
        el.style.display = 'none';
    });
    document.querySelectorAll('.tab-btn').forEach(function(b) {
        b.classList.remove('active');
    });
    document.getElementById('tab-' + tab).style.display = 'block';
    btn.classList.add('active');
}

fechaEntrada.addEventListener('change',   actualizarResumen);
fechaSalida.addEventListener('change',    actualizarResumen);
tipoHabitacion.addEventListener('change', actualizarResumen);