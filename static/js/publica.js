// ===== DROPDOWN HUÉSPEDES =====
const campHues    = document.getElementById('campHuespedes');
const huesDisplay = document.getElementById('huesDisplay');
const huesDropdown = document.getElementById('huesDropdown');

if (campHues) {
    huesDisplay.addEventListener('click', function(e) {
        e.stopPropagation();
        const visible = huesDropdown.style.display === 'block';
        huesDropdown.style.display = visible ? 'none' : 'block';
    });

    document.addEventListener('click', function() {
        if (huesDropdown) huesDropdown.style.display = 'none';
    });

    huesDropdown.addEventListener('click', function(e) {
        e.stopPropagation();
    });
}

let adultos = 2;
let ninos   = 0;

function actualizarDisplay() {
    const total = adultos + ninos;
    if (huesDisplay) {
        huesDisplay.textContent = `1 Habitación, ${total} Huésped${total !== 1 ? 'es' : ''}`;
    }
    const inputAdultos = document.getElementById('numAdultos');
    const inputNinos   = document.getElementById('numNinos');
    if (inputAdultos) inputAdultos.value = adultos;
    if (inputNinos)   inputNinos.value   = ninos;
    const adultoVal = document.getElementById('adultoVal');
    const ninoVal   = document.getElementById('ninoVal');
    if (adultoVal) adultoVal.textContent = adultos;
    if (ninoVal)   ninoVal.textContent   = ninos;
}

document.querySelectorAll('.pub-counter-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        const target = this.dataset.target;
        const action = this.dataset.action;
        if (target === 'adultos') {
            if (action === 'plus')  adultos = Math.min(adultos + 1, 10);
            if (action === 'minus') adultos = Math.max(adultos - 1, 1);
        } else {
            if (action === 'plus')  ninos = Math.min(ninos + 1, 10);
            if (action === 'minus') ninos = Math.max(ninos - 1, 0);
        }
        actualizarDisplay();
    });
});

// ===== VALIDAR FECHAS =====
const fechaEntrada = document.getElementById('fechaEntrada') || document.getElementById('id_fecha_entrada');
const fechaSalida  = document.getElementById('fechaSalida')  || document.getElementById('id_fecha_salida');

function validarFechas() {
    if (!fechaEntrada || !fechaSalida) return;
    const entrada = new Date(fechaEntrada.value);
    const salida  = new Date(fechaSalida.value);
    if (entrada && salida && salida <= entrada) {
        fechaSalida.setCustomValidity('La fecha de salida debe ser posterior a la entrada.');
    } else {
        fechaSalida.setCustomValidity('');
    }
}

if (fechaEntrada) fechaEntrada.addEventListener('change', validarFechas);
if (fechaSalida)  fechaSalida.addEventListener('change',  validarFechas);

// ===== SPINNER BUSCAR =====
const formBuscador  = document.getElementById('formBuscador');
const buscarTexto   = document.getElementById('buscarTexto');
const buscarSpinner = document.getElementById('buscarSpinner');

if (formBuscador) {
    formBuscador.addEventListener('submit', function() {
        if (buscarTexto)   buscarTexto.style.display   = 'none';
        if (buscarSpinner) buscarSpinner.style.display = 'inline-flex';
    });
}

// ===== MODALES + AUTOCOMPLETE DNI =====
document.addEventListener('DOMContentLoaded', function() {

    const modalLogin        = document.getElementById('modalLogin');
    const modalRegistro     = document.getElementById('modalRegistro');
    const btnAbrirLogin     = document.getElementById('btnAbrirLogin');
    const btnAbrirRegistro  = document.getElementById('btnAbrirRegistro');
    const btnCerrarLogin    = document.getElementById('btnCerrarLogin');
    const btnCerrarRegistro = document.getElementById('btnCerrarRegistro');
    const btnIrARegistro    = document.getElementById('btnIrARegistro');
    const btnIrALogin       = document.getElementById('btnIrALogin');

    function abrirModal() {
        if (modalLogin) modalLogin.classList.add('active');
    }

    function cerrarModal() {
        if (modalLogin) modalLogin.classList.remove('active');
    }

    function abrirRegistro() {
        if (modalRegistro) modalRegistro.classList.add('active');
    }

    function cerrarRegistro() {
        if (modalRegistro) modalRegistro.classList.remove('active');
    }

    if (btnAbrirLogin)     btnAbrirLogin.addEventListener('click', abrirModal);
    if (btnAbrirRegistro)  btnAbrirRegistro.addEventListener('click', abrirRegistro);
    if (btnCerrarLogin)    btnCerrarLogin.addEventListener('click', cerrarModal);
    if (btnCerrarRegistro) btnCerrarRegistro.addEventListener('click', cerrarRegistro);

    if (modalLogin) {
        modalLogin.addEventListener('click', function(e) {
            if (e.target === this) cerrarModal();
        });
    }

    if (modalRegistro) {
        modalRegistro.addEventListener('click', function(e) {
            if (e.target === this) cerrarRegistro();
        });
    }

    if (btnIrARegistro) btnIrARegistro.addEventListener('click', function(e) {
        e.preventDefault();
        cerrarModal();
        abrirRegistro();
    });

    if (btnIrALogin) btnIrALogin.addEventListener('click', function(e) {
        e.preventDefault();
        cerrarRegistro();
        abrirModal();
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') { cerrarModal(); cerrarRegistro(); }
    });

    if (modalLogin && modalLogin.dataset.abrirModal === '1') abrirModal();

    // ===== PROTEGER BOTONES RESERVAR =====
    const esCliente = document.body.dataset.esCliente === '1';

    document.querySelectorAll('.pub-btn-reservar-action').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!esCliente) {
                e.preventDefault();
                abrirModal();
            }
        });
    });

    // ===== AUTOCOMPLETE DNI =====
    const inputDni = document.getElementById('inputDni');

    if (inputDni) {
        inputDni.addEventListener('input', function() {
            const dni = this.value.replace(/\D/g, '').slice(0, 8);
            this.value = dni;

            const feedback      = document.getElementById('dniFeedback');
            const nombreInput   = document.getElementById('regFirstName');
            const apellidoInput = document.getElementById('regLastName');

            if (!feedback) return;

            if (dni.length === 8) {
                feedback.textContent = 'Consultando RENIEC...';
                feedback.style.color = '#6b7280';

                fetch(`/web/consultar-dni/?dni=${dni}`)
                    .then(function(r) {
                        if (!r.ok) throw new Error('no encontrado');
                        return r.json();
                    })
                    .then(function(data) {
                        if (data.error) {
                            feedback.textContent = '❌ ' + data.error;
                            feedback.style.color = '#c0392b';
                        } else {
                            if (nombreInput)   nombreInput.value   = data.nombres;
                            if (apellidoInput) apellidoInput.value = data.apellido_paterno + ' ' + data.apellido_materno;
                            feedback.textContent = '✓ ' + data.nombres + ' ' + data.apellido_paterno;
                            feedback.style.color = '#2D4A3E';
                        }
                    })
                    .catch(function() {
                        feedback.textContent = '❌ DNI no encontrado en RENIEC.';
                        feedback.style.color = '#c0392b';
                    });
            } else {
                feedback.textContent = '';
            }
        });
    }
    // Registro AJAX
const formRegistroAjax = document.getElementById('formRegistroAjax');
if (formRegistroAjax) {
    formRegistroAjax.addEventListener('submit', function(e) {
        e.preventDefault();

        // Limpiar errores previos
        document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
        document.querySelectorAll('.modal-input').forEach(el => el.classList.remove('modal-input-error'));

        const data = new FormData(this);
        const csrf = document.cookie.split(';')
        .find(c => c.trim().startsWith('csrftoken='))
        ?.split('=')[1] || '';

        fetch('/cuenta/registro/ajax/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrf },
            body: data,
        })
        .then(r => r.json())
        .then(res => {
            if (res.ok) {
                window.location.href = res.redirect || '/web/';
            } else {
                Object.entries(res.errores).forEach(([field, msg]) => {
                    const errorEl = document.querySelector(`.field-error[data-field="${field}"]`);
                    const inputEl = document.querySelector(`[name="${field}"]`);
                    if (errorEl) errorEl.textContent = msg;
                    if (inputEl) inputEl.classList.add('modal-input-error');
                });
            }
        })
        .catch(() => {
            const errDiv = document.getElementById('registroErrores');
            errDiv.style.display = 'block';
            errDiv.innerHTML = '<div class="modal-error">Error de conexión. Intenta de nuevo.</div>';
        });
    });
}

});