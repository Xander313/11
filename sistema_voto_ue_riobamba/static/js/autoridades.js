// Script para la sección de autoridades con animaciones avanzadas
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando efectos avanzados de autoridades...');
    
    // Seleccionar todos los contenedores de autoridades
    const authorityCards = document.querySelectorAll('.authority-container');
    
    // Crear efecto de partículas en el fondo (opcional)
    const autoridadesSection = document.querySelector('.autoridades');
    if (autoridadesSection) {
        const particlesContainer = document.createElement('div');
        particlesContainer.classList.add('particles');
        autoridadesSection.appendChild(particlesContainer);
        
        // Crear partículas (opcional)
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.classList.add('particle');
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.width = Math.random() * 5 + 3 + 'px';
            particle.style.height = particle.style.width;
            particle.style.opacity = Math.random() * 0.5 + 0.1;
            particlesContainer.appendChild(particle);
            
            // Animar partículas con anime.js
            if (typeof anime !== 'undefined') {
                anime({
                    targets: particle,
                    translateX: () => anime.random(-30, 30) + 'px',
                    translateY: () => anime.random(-30, 30) + 'px',
                    opacity: [0.1, 0.5, 0.1],
                    scale: [1, 1.2, 1],
                    easing: 'easeInOutSine',
                    duration: () => anime.random(3000, 8000),
                    loop: true,
                    delay: anime.random(0, 2000)
                });
            }
        }
    }
    
    // El código de partículas se movió dentro de la verificación de autoridadSection
    // para evitar errores de referencia
    
    // Efecto de movimiento 3D al mover el mouse
    authorityCards.forEach((card, index) => {
        // Añadir un retraso escalonado a la animación de entrada
        anime({
            targets: card,
            opacity: [0, 1],
            translateY: [80, 0],
            scale: [0.9, 1],
            duration: 1200,
            easing: 'easeOutElastic(1, .6)',
            delay: index * 150
        });
        
        // Efecto de movimiento 3D al mover el mouse
        card.addEventListener('mousemove', function(e) {
            // Solo aplicar efecto 3D si no está volteada
            if (!card.querySelector('.authority-card').classList.contains('flipped')) {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const xRotation = 15 * ((y - rect.height / 2) / rect.height);
                const yRotation = -15 * ((x - rect.width / 2) / rect.width);
                
                // Aplicar transformación con animación suave
                anime({
                    targets: card.querySelector('.authority-card'),
                    rotateX: xRotation,
                    rotateY: yRotation,
                    translateZ: '10px',
                    duration: 400,
                    easing: 'easeOutQuad'
                });
                
                // Efecto de seguimiento para la imagen
                const image = card.querySelector('.authority-image');
                if (image) {
                    anime({
                        targets: image,
                        translateX: yRotation * -1.5,
                        translateY: xRotation * -1.5,
                        duration: 400,
                        easing: 'easeOutQuad'
                    });
                }
            }
        });
        
        // Restaurar posición al quitar el mouse
        card.addEventListener('mouseleave', function() {
            // Solo restaurar si no está volteada
            if (!card.querySelector('.authority-card').classList.contains('flipped')) {
                anime({
                    targets: card.querySelector('.authority-card'),
                    rotateX: 0,
                    rotateY: 0,
                    translateZ: 0,
                    duration: 600,
                    easing: 'easeOutElastic(1, .6)'
                });
                
                // Restaurar posición de la imagen
                const image = card.querySelector('.authority-image');
                if (image) {
                    anime({
                        targets: image,
                        translateX: 0,
                        translateY: 0,
                        duration: 600,
                        easing: 'easeOutElastic(1, .6)'
                    });
                }
            }
        });
        
        // Efecto de clic para voltear la tarjeta
        card.addEventListener('click', function() {
            const authCard = card.querySelector('.authority-card');
            const isFlipped = authCard.classList.contains('flipped');
            
            // Voltear con animación
            anime({
                targets: authCard,
                rotateY: isFlipped ? 0 : 180,
                duration: 800,
                easing: 'easeOutExpo',
                complete: function() {
                    // Actualizar clase después de la animación
                    if (isFlipped) {
                        authCard.classList.remove('flipped');
                    } else {
                        authCard.classList.add('flipped');
                    }
                }
            });
            
            // Efecto de brillo al hacer clic
            const shine = document.createElement('div');
            shine.classList.add('card-shine');
            card.appendChild(shine);
            
            setTimeout(() => {
                card.removeChild(shine);
            }, 1000);
        });
        
        // Animar los elementos de la lista de logros
        const achievements = card.querySelectorAll('.achievement-list li');
        achievements.forEach((item, i) => {
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';
            
            // Observador para animar cuando la tarjeta se voltea
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.attributeName === 'class') {
                        const isFlipped = card.querySelector('.authority-card').classList.contains('flipped');
                        if (isFlipped) {
                            setTimeout(() => {
                                anime({
                                    targets: item,
                                    opacity: [0, 1],
                                    translateX: [-20, 0],
                                    duration: 600,
                                    easing: 'easeOutQuad',
                                    delay: 300 + (i * 100)
                                });
                            }, 400);
                        }
                    }
                });
            });
            
            observer.observe(card.querySelector('.authority-card'), { attributes: true });
        });
    });
    
    // Función para detectar si un elemento está en el viewport
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top <= (window.innerHeight || document.documentElement.clientHeight) * 0.8 &&
            rect.bottom >= 0 &&
            rect.left >= 0 &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Animación al hacer scroll
    function animateOnScroll() {
        const section = document.querySelector('.autoridades');
        
        if (isInViewport(section) && !section.classList.contains('animated')) {
            section.classList.add('animated');
            
            // Animar título de sección
            anime({
                targets: '.autoridades .section-heading h2',
                opacity: [0, 1],
                translateY: [-30, 0],
                duration: 1000,
                easing: 'easeOutQuad'
            });
            
            // Animar línea decorativa
            anime({
                targets: '.autoridades .line-dec',
                width: [0, '80px'],
                opacity: [0, 1],
                duration: 1000,
                delay: 300,
                easing: 'easeInOutQuad'
            });
            
            // Animar subtítulo
            anime({
                targets: '.autoridades .subtitle',
                opacity: [0, 1],
                translateY: [20, 0],
                duration: 1000,
                delay: 500,
                easing: 'easeOutQuad'
            });
        }
    }
    
    // Iniciar animación al cargar la página
    setTimeout(animateOnScroll, 500);
    
    // Verificar animación al hacer scroll
    window.addEventListener('scroll', animateOnScroll);
});
