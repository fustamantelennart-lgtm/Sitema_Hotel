document.addEventListener('DOMContentLoaded', function() {

    const el   = document.getElementById('dashData');
    const DASH = {
        meses_labels:    JSON.parse(el.dataset.mesesLabels),
        meses_ocupacion: JSON.parse(el.dataset.mesesOcupacion),
        estados_labels:  JSON.parse(el.dataset.estadosLabels),
        estados_data:    JSON.parse(el.dataset.estadosData),
        tipo_labels:     JSON.parse(el.dataset.tipoLabels),
        tipo_ingresos:   JSON.parse(el.dataset.tipoIngresos),
    };

    const PRIMARY = '#2D4A3E';
    const ACCENT  = '#C4A882';
    const DARK    = '#1a1a1a';
    const MUTED   = '#6b7280';

    new Chart(document.getElementById('grafReservas'), {
        type: 'line',
        data: {
            labels: DASH.meses_labels,
            datasets: [{
                label: 'Reservas',
                data: DASH.meses_ocupacion,
                borderColor: PRIMARY,
                backgroundColor: 'rgba(45,74,62,.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: PRIMARY,
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } },
                x: { grid: { display: false } }
            }
        }
    });

    new Chart(document.getElementById('grafEstados'), {
        type: 'doughnut',
        data: {
            labels: DASH.estados_labels,
            datasets: [{
                data: DASH.estados_data,
                backgroundColor: [PRIMARY, DARK, ACCENT, MUTED],
                borderWidth: 0,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 16, font: { size: 12 } }
                }
            }
        }
    });

    new Chart(document.getElementById('grafTipos'), {
        type: 'bar',
        data: {
            labels: DASH.tipo_labels,
            datasets: [{
                label: 'Ingresos (S/)',
                data: DASH.tipo_ingresos,
                backgroundColor: [PRIMARY, ACCENT, MUTED],
                borderRadius: 6,
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true },
                x: { grid: { display: false } }
            }
        }
    });

});