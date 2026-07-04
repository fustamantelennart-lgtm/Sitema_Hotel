document.addEventListener('DOMContentLoaded', function() {

    // ===== AUTOCOMPLETE DNI =====
    const inputDni   = document.getElementById('id_num_doc');
    const feedback   = document.getElementById('dniFeedback');
    const inputNombres   = document.getElementById('id_nombres');
    const inputApellidos = document.getElementById('id_apellidos');

    if (inputDni) {
        inputDni.addEventListener('input', function() {
            const dni = this.value.replace(/\D/g, '').slice(0, 8);
            this.value = dni;

            if (feedback) feedback.textContent = '';
            if (inputNombres)   inputNombres.value   = '';
            if (inputApellidos) inputApellidos.value  = '';

            if (dni.length === 8) {
                if (feedback) {
                    feedback.textContent = 'Consultando RENIEC...';
                    feedback.style.color = 'var(--color-text-muted)';
                }
                fetch(`/web/consultar-dni/?dni=${dni}`)
                    .then(r => r.ok ? r.json() : Promise.reject())
                    .then(data => {
                        if (data.error) {
                            if (feedback) {
                                feedback.textContent = '❌ DNI no encontrado';
                                feedback.style.color = 'var(--color-danger)';
                            }
                            return;
                        }
                        if (inputNombres)   inputNombres.value   = data.nombres;
                        if (inputApellidos) inputApellidos.value = data.apellido_paterno + ' ' + data.apellido_materno;
                        if (feedback) {
                            feedback.textContent = `✓ ${data.nombres} ${data.apellido_paterno}`;
                            feedback.style.color = 'var(--color-success)';
                        }
                    })
                    .catch(() => {
                        if (feedback) {
                            feedback.textContent = '❌ Error de conexión';
                            feedback.style.color = 'var(--color-danger)';
                        }
                    });
            }
        });
    }

    // ===== RESUMEN DINÁMICO =====
    const selectTipo     = document.getElementById('id_tipo_habitacion');
    const inputEntrada   = document.getElementById('id_fecha_entrada');
    const inputSalida    = document.getElementById('id_fecha_salida');
    const resumenNoches  = document.getElementById('resumenNoches');
    const resumenTipo    = document.getElementById('resumenTipo');
    const resumenPrecio  = document.getElementById('resumenPrecioNoche');
    const resumenTotal   = document.getElementById('resumenTotal');

    const precios = window.TIPO_PRECIOS || {};

    function actualizar() {
        if (!selectTipo || !inputEntrada || !inputSalida) return;
        const opt    = selectTipo.options[selectTipo.selectedIndex];
        const precio = precios[opt?.value] || 0;
        const texto  = opt?.text.split(' —')[0] || '—';
        const fe     = new Date(inputEntrada.value);
        const fs     = new Date(inputSalida.value);

        if (inputEntrada.value && inputSalida.value && fs > fe) {
            const n = Math.round((fs - fe) / 86400000);
            if (resumenNoches) resumenNoches.textContent = n;
            if (resumenTipo)   resumenTipo.textContent   = texto;
            if (resumenPrecio) resumenPrecio.textContent = precio ? `S/ ${precio.toFixed(2)}` : '—';
            if (resumenTotal)  resumenTotal.textContent  = `S/ ${(n * precio).toFixed(2)}`;
        } else {
            if (resumenNoches) resumenNoches.textContent = '—';
            if (resumenTipo)   resumenTipo.textContent   = texto;
            if (resumenPrecio) resumenPrecio.textContent = precio ? `S/ ${precio.toFixed(2)}` : '—';
            if (resumenTotal)  resumenTotal.textContent  = 'S/ —';
        }
    }

    if (selectTipo)   selectTipo.addEventListener('change', actualizar);
    if (inputEntrada) inputEntrada.addEventListener('change', actualizar);
    if (inputSalida)  inputSalida.addEventListener('change', actualizar);
    actualizar();
});