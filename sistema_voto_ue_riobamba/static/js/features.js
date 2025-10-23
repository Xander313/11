// Script simple para mostrar/ocultar el contenido con una transición suave
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando características...');
    
    // Seleccionar todos los elementos .features-post
    const featuresPosts = document.querySelectorAll('.features-post');
    console.log('Características encontradas:', featuresPosts.length);
    
    // Añadir eventos de hover a cada elemento
    featuresPosts.forEach(post => {
        // Obtener el elemento content-hide dentro de este post
        const contentHide = post.querySelector('.content-hide');
        
        // Añadir evento mouseenter
        post.addEventListener('mouseenter', function() {
            console.log('Mouse sobre característica');
            if (contentHide) {
                // Mostrar el contenido oculto con una transición suave usando jQuery
                $(contentHide).slideDown(400);
            }
        });
        
        // Añadir evento mouseleave
        post.addEventListener('mouseleave', function() {
            console.log('Mouse fuera de característica');
            if (contentHide) {
                // Ocultar el contenido con una transición suave usando jQuery
                $(contentHide).slideUp(400);
            }
        });
    });
});
