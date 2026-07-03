document.addEventListener('DOMContentLoaded', function() {
    const track  = document.getElementById('carruselTrack');
    const dots   = document.getElementById('carruselDots');
    const btnPrev = document.getElementById('btnPrev');
    const btnNext = document.getElementById('btnNext');

    if (!track) return;

    const slides = track.querySelectorAll('.pub-carrusel-slide');
    if (slides.length === 0) return;

    let current = 0;

    // Crear dots
    slides.forEach(function(_, i) {
        const dot = document.createElement('button');
        dot.className = 'pub-carrusel-dot' + (i === 0 ? ' active' : '');
        dot.addEventListener('click', function() { goTo(i); });
        dots.appendChild(dot);
    });

    function goTo(index) {
        current = (index + slides.length) % slides.length;
        track.style.transform = `translateX(-${current * 100}%)`;
        dots.querySelectorAll('.pub-carrusel-dot').forEach(function(d, i) {
            d.classList.toggle('active', i === current);
        });
    }

    if (btnPrev) btnPrev.addEventListener('click', function() { goTo(current - 1); });
    if (btnNext) btnNext.addEventListener('click', function() { goTo(current + 1); });

    // Auto avance cada 4 segundos
    setInterval(function() { goTo(current + 1); }, 4000);
});