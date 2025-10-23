// Script personalizado para las secciones de video y contacto

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar animación para la sección de video
    initVideoSection();
    
    // Inicializar validación del formulario de contacto
    initContactForm();
    
    // Inicializar efecto de scroll suave para los enlaces internos
    initSmoothScroll();
});

// Función para inicializar la sección de video
function initVideoSection() {
    const videoLink = document.querySelector('.video-item .play');
    
    if (videoLink) {
        videoLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            const videoUrl = this.getAttribute('href');
            
            // Crear modal para el video
            const modal = document.createElement('div');
            modal.className = 'video-modal';
            modal.innerHTML = `
                <div class="video-modal-content">
                    <span class="close-video">&times;</span>
                    <div class="video-container">
                        <iframe width="100%" height="100%" src="${videoUrl.replace('watch?v=', 'embed/')}?autoplay=1" 
                        frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen></iframe>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Mostrar modal con animación
            setTimeout(() => {
                modal.classList.add('active');
            }, 10);
            
            // Cerrar modal al hacer clic en el botón de cerrar
            const closeBtn = modal.querySelector('.close-video');
            closeBtn.addEventListener('click', function() {
                modal.classList.remove('active');
                
                // Eliminar modal después de la animación
                setTimeout(() => {
                    document.body.removeChild(modal);
                }, 300);
            });
        });
    }
}

// Función para inicializar el formulario de contacto
function initContactForm() {
    const contactForm = document.getElementById('contact');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Obtener valores del formulario
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const message = document.getElementById('message').value;
            
            // Validar formulario
            if (name && email && message) {
                // Mostrar mensaje de éxito (simulado)
                const submitBtn = document.getElementById('form-submit');
                const originalText = submitBtn.textContent;
                
                submitBtn.disabled = true;
                submitBtn.textContent = 'Enviando...';
                
                // Simular envío (reemplazar con envío real en producción)
                setTimeout(() => {
                    // Mostrar mensaje de éxito
                    const successMessage = document.createElement('div');
                    successMessage.className = 'alert alert-success';
                    successMessage.textContent = '¡Mensaje enviado con éxito! Nos pondremos en contacto contigo pronto.';
                    
                    contactForm.insertBefore(successMessage, contactForm.firstChild);
                    
                    // Restablecer formulario
                    contactForm.reset();
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalText;
                    
                    // Ocultar mensaje después de 5 segundos
                    setTimeout(() => {
                        successMessage.style.opacity = '0';
                        setTimeout(() => {
                            contactForm.removeChild(successMessage);
                        }, 300);
                    }, 5000);
                }, 1500);
            }
        });
    }
}

// Función para inicializar scroll suave
function initSmoothScroll() {
    const scrollLinks = document.querySelectorAll('.scroll-to-section');
    
    scrollLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                window.scrollTo({
                    top: targetSection.offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}
