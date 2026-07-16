// ===== MODO REGISTRO NUEVA RESERVA =====
let modoManualNR = false;

function setModoNR(modo) {
    const campoDni      = document.getElementById('camposDniNR');
    const campoExt      = document.getElementById('camposExtranjeroNR');
    const nombres       = document.getElementById('id_nombres');
    const apellidos     = document.getElementById('id_apellidos');
    const feedback      = document.getElementById('dniFeedback');

    if (modo === 'peruano') {
        campoDni.style.display = '';
        campoExt.style.display = 'none';
        modoManualNR = false;
        if (nombres)   { nombres.readOnly = true;  nombres.value = ''; }
        if (apellidos) { apellidos.readOnly = true; apellidos.value = ''; }
        if (feedback)  feedback.textContent = '';
        const inputDoc = document.getElementById('id_num_doc');
        if (inputDoc) inputDoc.value = '';
    } else {
        campoDni.style.display = 'none';
        campoExt.style.display = '';
        modoManualNR = true;
        if (nombres)   { nombres.readOnly = false; nombres.placeholder = 'Ingresa nombres'; }
        if (apellidos) { apellidos.readOnly = false; apellidos.placeholder = 'Ingresa apellidos'; }
    }
}

function desbloquearManualNR() {
    const nombres   = document.getElementById('id_nombres');
    const apellidos = document.getElementById('id_apellidos');
    const feedback  = document.getElementById('dniFeedback');
    modoManualNR = true;
    if (nombres)   { nombres.readOnly = false; nombres.placeholder = 'Ingresa nombres'; nombres.focus(); }
    if (apellidos) { apellidos.readOnly = false; apellidos.placeholder = 'Ingresa apellidos'; }
    if (feedback)  { feedback.textContent = 'Completa los datos manualmente.'; feedback.style.color = 'var(--color-primary)'; }
}

document.addEventListener('DOMContentLoaded', function() {

// ===== TOGGLE EXTRANJERO =====
    const btnPeruanoNR    = document.getElementById('btnModoPeruanoNR');
    const btnExtranjeroNR = document.getElementById('btnModoExtranjeroNR');
    if (btnPeruanoNR) {
        btnPeruanoNR.addEventListener('click', function() {
            setModoNR('peruano');
        });
    }
    if (btnExtranjeroNR) {
        btnExtranjeroNR.addEventListener('click', function() {
            setModoNR('extranjero');
        });
    }

    // ===== LINK FORZAR MANUAL =====
const toggleManualNR = document.getElementById('toggleManualNR');
    if (toggleManualNR) {
        toggleManualNR.addEventListener('change', function() {
            if (this.checked) {
                desbloquearManualNR();
            } else {
                modoManualNR = false;
                const nombres   = document.getElementById('id_nombres');
                const apellidos = document.getElementById('id_apellidos');
                const feedback  = document.getElementById('dniFeedback');
                if (nombres)   { nombres.readOnly = true;  nombres.value = ''; nombres.placeholder = 'Se autocompleta con DNI'; }
                if (apellidos) { apellidos.readOnly = true; apellidos.value = ''; apellidos.placeholder = 'Se autocompleta con DNI'; }
                if (feedback)  feedback.textContent = '';
                const inputDoc = document.getElementById('id_num_doc');
                if (inputDoc)  inputDoc.value = '';
            }
        });
    }

    // ===== AUTOCOMPLETE DNI =====
    const inputDni       = document.getElementById('id_num_doc');
    const feedback       = document.getElementById('dniFeedback');
    const inputNombres   = document.getElementById('id_nombres');
    const inputApellidos = document.getElementById('id_apellidos');

    if (inputDni) {
        inputDni.addEventListener('input', function() {
            if (modoManualNR) return;
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
                                feedback.innerHTML = '❌ DNI no encontrado. <a href="#" id="btnManualDniNR" style="color:var(--color-primary); font-weight:600;">Ingresar manualmente</a>';
                                feedback.style.color = 'var(--color-danger)';
                                const btn = document.getElementById('btnManualDniNR');
                                if (btn) btn.addEventListener('click', function(e) { e.preventDefault(); desbloquearManualNR(); });
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
                            feedback.innerHTML = '❌ No encontrado en RENIEC. <a href="#" id="btnManualDniNR" style="color:var(--color-primary); font-weight:600;">Ingresar manualmente</a>';
                            feedback.style.color = 'var(--color-danger)';
                            const btn = document.getElementById('btnManualDniNR');
                            if (btn) btn.addEventListener('click', function(e) { e.preventDefault(); desbloquearManualNR(); });
                        }
                    });
            }
        });
    }

    // ===== RESUMEN DINÁMICO =====
    const selectTipo    = document.getElementById('id_tipo_habitacion');
    const inputEntrada  = document.getElementById('id_fecha_entrada');
    const inputSalida   = document.getElementById('id_fecha_salida');
    const resumenNoches = document.getElementById('resumenNoches');
    const resumenTipo   = document.getElementById('resumenTipo');
    const resumenPrecio = document.getElementById('resumenPrecioNoche');
    const resumenTotal  = document.getElementById('resumenTotal');

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