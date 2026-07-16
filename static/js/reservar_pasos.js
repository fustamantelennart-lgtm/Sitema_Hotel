document.addEventListener('DOMContentLoaded', function () {

    const paso1 = document.getElementById('paso1');
    const paso2 = document.getElementById('paso2');
    const paso3 = document.getElementById('paso3');

    const ind1  = document.getElementById('pasoIndicador1');
    const ind2  = document.getElementById('pasoIndicador2');
    const ind3  = document.getElementById('pasoIndicador3');

    const btnPaso1   = document.getElementById('btnPaso1');
    const btnPaso2   = document.getElementById('btnPaso2');
    const btnVolver1 = document.getElementById('btnVolver1');
    const btnVolver2 = document.getElementById('btnVolver2');

    function mostrarPaso(n) {
        paso1.style.display = n === 1 ? 'block' : 'none';
        paso2.style.display = n === 2 ? 'block' : 'none';
        paso3.style.display = n === 3 ? 'block' : 'none';

        ind1.classList.toggle('active', n === 1);
        ind2.classList.toggle('active', n === 2);
        ind3.classList.toggle('active', n === 3);
        ind1.classList.toggle('done',   n > 1);
        ind2.classList.toggle('done',   n > 2);
    }

    function actualizarResumen() {
        const tipo    = document.querySelector('[name="tipo_habitacion"] option:checked')?.text || '';
        const entrada = document.querySelector('[name="fecha_entrada"]')?.value || '';
        const salida  = document.querySelector('[name="fecha_salida"]')?.value || '';
        const nombres = document.querySelector('[name="nombres"]')?.value || '';
        const apells  = document.querySelector('[name="apellidos"]')?.value || '';

        document.getElementById('resumenTipo').textContent     = tipo;
        document.getElementById('resumenEntrada').textContent  = entrada;
        document.getElementById('resumenSalida').textContent   = salida;
        document.getElementById('resumenNombre').textContent   = `${nombres} ${apells}`.trim();

// Calcular total directamente
        const preciosDiv = document.getElementById('tiposPrecios');
        const selectTipo = document.querySelector('[name="tipo_habitacion"]');
        const totalFinalEl = document.getElementById('resumenTotalFinal');
        if (preciosDiv && selectTipo && entrada && salida && totalFinalEl) {
            const fe      = new Date(entrada);
            const fs      = new Date(salida);
            const noches  = Math.round((fs - fe) / (1000 * 60 * 60 * 24));
            const tipoId  = selectTipo.value;
            try {
                const raw    = '{' + preciosDiv.dataset.precios.replace(/,$/, '') + '}';
                const precios = JSON.parse(raw);
                const precio  = precios[tipoId];
                if (precio && noches > 0) {
                    totalFinalEl.textContent = `S/ ${(precio * noches).toFixed(2)}`;
                } else {
                    totalFinalEl.textContent = 'S/ 0.00';
                }
            } catch(e) {
                const totalEl = document.getElementById('resumenTotal');
                if (totalEl) totalFinalEl.textContent = totalEl.textContent;
            }
        }
    }

    if (btnPaso1) {
        btnPaso1.addEventListener('click', function () {
            const entrada = document.querySelector('[name="fecha_entrada"]')?.value;
            const salida  = document.querySelector('[name="fecha_salida"]')?.value;
            if (!entrada || !salida) {
                alert('Por favor selecciona las fechas de entrada y salida.');
                return;
            }
            mostrarPaso(2);
        });
    }

    if (btnPaso2) {
        btnPaso2.addEventListener('click', function () {
            const nombres = document.querySelector('[name="nombres"]')?.value;
            const num_doc = document.querySelector('[name="num_doc"]')?.value;
            if (!nombres || !num_doc) {
                alert('Por favor completa tus datos personales.');
                return;
            }
            actualizarResumen();
            mostrarPaso(3);
        });
    }

    if (btnVolver1) {
        btnVolver1.addEventListener('click', function () {
            mostrarPaso(1);
        });
    }

    if (btnVolver2) {
        btnVolver2.addEventListener('click', function () {
            mostrarPaso(2);
        });
    }

    // Verificar si hay errores del servidor y mostrar paso correcto
    const errDiv = document.getElementById('formErrores');
    if (errDiv && errDiv.dataset.tieneErrores === '1') {
        if (errDiv.dataset.erroresPaso2.includes('1')) {
            mostrarPaso(2);
        } else {
            mostrarPaso(1);
        }
    } else {
        mostrarPaso(1);
    }

    // Precio en tiempo real
    const selectTipo  = document.querySelector('[name="tipo_habitacion"]');
    const inputEntrada = document.querySelector('[name="fecha_entrada"]');
    const inputSalida  = document.querySelector('[name="fecha_salida"]');
    const preciosDiv   = document.getElementById('tiposPrecios');
    const resumenDiv   = document.getElementById('resumenPrecio');
    const resumenNoches = document.getElementById('resumenNoches');
    const resumenTotal  = document.getElementById('resumenTotal');

    function calcularPrecio() {
        if (!selectTipo || !inputEntrada || !inputSalida || !preciosDiv) return;
        const tipoId  = selectTipo.value;
        const entrada = new Date(inputEntrada.value);
        const salida  = new Date(inputSalida.value);
        if (!tipoId || isNaN(entrada) || isNaN(salida)) return;

        const noches = Math.round((salida - entrada) / (1000 * 60 * 60 * 24));
        if (noches <= 0) return;

        // Parsear precios del data attribute
        const raw    = '{' + preciosDiv.dataset.precios.replace(/,$/, '') + '}';
        try {
            const precios = JSON.parse(raw);
            const precio  = precios[tipoId];
            if (precio) {
                resumenNoches.textContent = `${noches} noche(s)`;
                resumenTotal.textContent  = `S/ ${(precio * noches).toFixed(2)}`;
                resumenDiv.style.display  = 'block';
            }
        } catch (e) {}
    }

    if (selectTipo)   selectTipo.addEventListener('change', calcularPrecio);
    if (inputEntrada) inputEntrada.addEventListener('change', calcularPrecio);
    if (inputSalida)  inputSalida.addEventListener('change', calcularPrecio);

});