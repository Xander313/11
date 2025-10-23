// Inicialización del carrusel de docentes
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando carrusel de docentes...');
    
    // Inicializar el carrusel de OwlCarousel para los docentes
    $('.docentes-carousel').owlCarousel({
        loop: true,
        margin: 30,
        nav: true,
        dots: true,
        autoplay: true,
        autoplayTimeout: 5000,
        autoplayHoverPause: true,
        responsive: {
            0: {
                items: 1
            },
            600: {
                items: 2
            },
            1000: {
                items: 3
            }
        },
        navText: [
            '<i class="fa fa-angle-left"></i>',
            '<i class="fa fa-angle-right"></i>'
        ]
    });
});
