// Script para la sección Cuadro de Honor con timeline y efectos interactivos
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando efectos del Cuadro de Honor...');
    
    // Manejar enlace de inicio
    const inicioLink = document.querySelector('a[href="#top"]');
    if (inicioLink) {
        inicioLink.addEventListener('click', function(e) {
            e.preventDefault();
            const topSection = document.getElementById('top');
            if (topSection) {
                topSection.scrollIntoView({ behavior: 'smooth' });
                // Ajustar el scroll para que no quede tapado por el header
                window.scrollBy(0, -document.querySelector('.main-header').offsetHeight);
            }
        });
    }
    
    // Inicializar filtros
    initializeFilters();
    
    // Inicializar efectos de timeline
    initializeTimeline();
    
    // Inicializar modal de logros
    initializeAchievementModal();
    
    // Efecto de partículas
    createParticles();
    
    // Animación inicial al cargar la página
    setTimeout(animateOnLoad, 500);
    
    // Ajustar posición al cambiar tamaño de ventana
    window.addEventListener('resize', function() {
        positionCards();
    });

    // Manejar menú móvil
    const menuLink = document.querySelector('.menu-link');
    const mainMenu = document.querySelector('.main-menu');
    
    menuLink.addEventListener('click', function(e) {
        e.preventDefault();
        mainMenu.classList.toggle('active');
    });

    // Cerrar menú al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (!menuLink.contains(e.target) && !mainMenu.contains(e.target)) {
            mainMenu.classList.remove('active');
        }
    });
});

// Función para inicializar los filtros
function initializeFilters() {
    const filters = document.querySelectorAll('.honor-filter');
    const timelineItems = document.querySelectorAll('.honor-timeline-item');
    
    filters.forEach(filter => {
        filter.addEventListener('click', function() {
            // Remover clase activa de todos los filtros
            filters.forEach(f => f.classList.remove('active'));
            
            // Agregar clase activa al filtro seleccionado
            this.classList.add('active');
            
            // Obtener categoría seleccionada
            const category = this.getAttribute('data-category');
            
            // Filtrar elementos del timeline
            timelineItems.forEach(item => {
                if (category === 'all') {
                    item.style.display = 'block';
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateY(0)';
                    }, 50);
                } else if (item.getAttribute('data-category') === category) {
                    item.style.display = 'block';
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateY(0)';
                    }, 50);
                } else {
                    item.style.opacity = '0';
                    item.style.transform = 'translateY(30px)';
                    setTimeout(() => {
                        item.style.display = 'none';
                    }, 300);
                }
            });
        });
    });
}

// Función para inicializar el timeline
function initializeTimeline() {
    const timelineItems = document.querySelectorAll('.honor-timeline-item');
    
    // Animación al hacer scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2,
        rootMargin: '0px 0px -100px 0px'
    });
    
    timelineItems.forEach(item => {
        observer.observe(item);
        
        // Efecto hover en las imágenes
        const image = item.querySelector('.honor-timeline-image img');
        if (image) {
            item.addEventListener('mouseenter', function() {
                image.style.transform = 'scale(1.1)';
            });
            
            item.addEventListener('mouseleave', function() {
                image.style.transform = 'scale(1)';
            });
        }
        
        // Botón para ver logros
        const viewBtn = item.querySelector('.honor-timeline-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const studentId = item.getAttribute('data-id');
                openAchievementModal(studentId, item);
            });
        }
    });
}

// Función para inicializar el modal de logros
function initializeAchievementModal() {
    // Crear modal si no existe
    if (!document.querySelector('.honor-achievement-modal')) {
        const modal = document.createElement('div');
        modal.classList.add('honor-achievement-modal');
        
        modal.innerHTML = `
            <div class="honor-modal-content">
                <div class="honor-modal-close">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </div>
                <div class="honor-modal-header">
                    <div class="honor-modal-image">
                        <img src="" alt="Estudiante">
                    </div>
                    <div class="honor-modal-title">
                        <h3 class="honor-modal-name"></h3>
                        <p class="honor-modal-course"></p>
                        <span class="honor-modal-category"></span>
                    </div>
                </div>
                <div class="honor-modal-body">
                    <div class="honor-modal-section">
                        <h4>
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
                                <path d="M2 17l10 5 10-5"></path>
                                <path d="M2 12l10 5 10-5"></path>
                            </svg>
                            Logros Académicos
                        </h4>
                        <ul class="honor-achievement-list">
                            <!-- Los logros se cargarán dinámicamente -->
                        </ul>
                    </div>
                    <div class="honor-modal-section">
                        <h4>
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
                            </svg>
                            Rendimiento
                        </h4>
                        <div class="honor-modal-chart">
                            <!-- Aquí se cargará el gráfico de rendimiento -->
                        </div>
                    </div>
                    <div class="honor-modal-section">
                        <h4>
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                            </svg>
                            Mensaje del Docente
                        </h4>
                        <div class="honor-modal-quote">
                            <p class="honor-quote-text"></p>
                            <div class="honor-quote-signature"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Cerrar modal al hacer clic en el botón de cerrar
        const closeBtn = modal.querySelector('.honor-modal-close');
        closeBtn.addEventListener('click', closeAchievementModal);
        
        // Cerrar modal al hacer clic fuera del contenido
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeAchievementModal();
            }
        });
    }
}

// Función para abrir el modal de logros
function openAchievementModal(studentId, item) {
    const modal = document.querySelector('.honor-achievement-modal');
    
    // Obtener datos del estudiante
    const name = item.querySelector('.honor-timeline-name').textContent;
    const course = item.querySelector('.honor-timeline-course').textContent;
    const category = item.getAttribute('data-category');
    const imageSrc = item.querySelector('.honor-timeline-image img').src;
    
    // Actualizar datos en el modal
    modal.querySelector('.honor-modal-name').textContent = name;
    modal.querySelector('.honor-modal-course').textContent = course;
    modal.querySelector('.honor-modal-category').textContent = getCategoryName(category);
    modal.querySelector('.honor-modal-image img').src = imageSrc;
    
    // Cargar logros (simulados por ahora)
    const achievementsList = modal.querySelector('.honor-achievement-list');
    achievementsList.innerHTML = '';
    
    // Ejemplos de logros según la categoría
    const achievements = getAchievementsByCategory(category);
    
    achievements.forEach(achievement => {
        const li = document.createElement('li');
        li.textContent = achievement;
        achievementsList.appendChild(li);
    });
    
    // Cargar mensaje del docente (simulado)
    const quoteText = modal.querySelector('.honor-quote-text');
    const quoteSignature = modal.querySelector('.honor-quote-signature');
    
    quoteText.textContent = getRandomQuote();
    quoteSignature.textContent = 'Docente ' + getRandomTeacherName();
    
    // Mostrar modal con animación
    modal.classList.add('active');
    
    // Bloquear scroll del body
    document.body.style.overflow = 'hidden';
    
    // Simular carga de gráfico
    setTimeout(() => {
        renderChart(modal.querySelector('.honor-modal-chart'));
    }, 300);
}

// Función para cerrar el modal de logros
function closeAchievementModal() {
    const modal = document.querySelector('.honor-achievement-modal');
    
    // Ocultar modal con animación
    modal.classList.remove('active');
    
    // Restaurar scroll del body
    document.body.style.overflow = '';
}
    
// Función para crear partículas
function createParticles() {
    const honorBoard = document.querySelector('.honor-board');
    if (!honorBoard) {
        console.warn('No se encontró el elemento .honor-board para agregar partículas');
        return;
    }
    
    const particlesContainer = document.createElement('div');
    particlesContainer.classList.add('honor-particles');
    honorBoard.appendChild(particlesContainer);
    
    // Crear partículas
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.classList.add('honor-particle');
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.width = Math.random() * 5 + 3 + 'px';
        particle.style.height = particle.style.width;
        particle.style.opacity = Math.random() * 0.5 + 0.1;
        particlesContainer.appendChild(particle);
        
        // Animar partículas
        if (typeof anime !== 'undefined') {
            anime({
                targets: particle,
                translateX: () => anime.random(-50, 50) + 'px',
                translateY: () => anime.random(-50, 50) + 'px',
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

// Función para obtener el nombre de la categoría
function getCategoryName(category) {
    const categories = {
        'academic': 'Excelencia Académica',
        'sports': 'Destacado Deportivo',
        'arts': 'Talento Artístico',
        'leadership': 'Liderazgo',
        'innovation': 'Innovación',
        'values': 'Valores Institucionales'
    };
    
    return categories[category] || 'Destacado';
}

// Función para obtener logros según la categoría
function getAchievementsByCategory(category) {
    const achievementsByCategory = {
        'academic': [
            'Promedio de calificaciones superior a 9.5/10',
            'Primer lugar en Olimpiada de Matemáticas',
            'Participación destacada en concurso de Ciencias',
            'Reconocimiento por asistencia perfecta',
            'Mejor proyecto de investigación del año'
        ],
        'sports': [
            'Medalla de oro en competencia intercolegial',
            'Capitán del equipo de fútbol',
            'Representante provincial en juegos nacionales',
            'Mejor deportista del año',
            'Récord escolar en 100 metros planos'
        ],
        'arts': [
            'Primer lugar en concurso de pintura',
            'Solista destacado en el coro escolar',
            'Representante en festival nacional de danza',
            'Exposición individual de obras artísticas',
            'Reconocimiento por talento musical'
        ],
        'leadership': [
            'Presidente del Consejo Estudiantil',
            'Organizador de campaña solidaria escolar',
            'Líder de proyecto comunitario',
            'Mediador en resolución de conflictos',
            'Representante estudiantil ante el consejo directivo'
        ],
        'innovation': [
            'Creador de aplicación para beneficio escolar',
            'Proyecto innovador de reciclaje',
            'Solución tecnológica para problema comunitario',
            'Participación destacada en feria de ciencias',
            'Propuesta de mejora implementada en la institución'
        ],
        'values': [
            'Ejemplo de compañerismo y solidaridad',
            'Promotor de valores institucionales',
            'Voluntario destacado en proyectos sociales',
            'Reconocimiento por honestidad académica',
            'Embajador de la cultura institucional'
        ]
    };
    
    return achievementsByCategory[category] || [
        'Estudiante destacado del período académico',
        'Reconocimiento por excelencia integral',
        'Mención de honor por desempeño sobresaliente',
        'Ejemplo para la comunidad educativa',
        'Representante destacado de la institución'
    ];
}

// Función para obtener una cita aleatoria
function getRandomQuote() {
    const quotes = [
        'Un estudiante excepcional que demuestra pasión por el aprendizaje y dedicación constante en cada actividad que emprende.',
        'Su capacidad para superar desafíos y mantener una actitud positiva lo convierte en un ejemplo para todos sus compañeros.',
        'Demuestra un equilibrio admirable entre excelencia académica y desarrollo de habilidades sociales y emocionales.',
        'Su curiosidad intelectual y pensamiento crítico lo distinguen como un estudiante sobresaliente con gran potencial.',
        'Ha demostrado un crecimiento notable, no solo en lo académico, sino en su desarrollo como persona íntegra y responsable.',
        'Su liderazgo natural y capacidad para trabajar en equipo lo convierten en un pilar fundamental de nuestra comunidad educativa.',
        'Combina talento y esfuerzo de manera ejemplar, alcanzando logros que inspiran a toda la institución.'
    ];
    
    return quotes[Math.floor(Math.random() * quotes.length)];
}

// Función para obtener un nombre de docente aleatorio
function getRandomTeacherName() {
    const names = [
        'Carlos Mendoza',
        'María Sánchez',
        'Juan Pérez',
        'Ana Gómez',
        'Luis Rodríguez',
        'Patricia Flores',
        'Roberto Vega',
        'Claudia Morales'
    ];
    
    return names[Math.floor(Math.random() * names.length)];
}

// Función para renderizar un gráfico simple
function renderChart(container) {
    // Verificar si el contenedor existe
    if (!container) return;
    
    // Crear canvas para el gráfico
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);
    
    // Si Chart.js está disponible, crear un gráfico
    if (typeof Chart !== 'undefined') {
        new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['1er Parcial', '2do Parcial', '3er Parcial', 'Final'],
                datasets: [{
                    label: 'Rendimiento',
                    data: [8.7, 9.2, 9.5, 9.8],
                    borderColor: '#f5a425',
                    backgroundColor: 'rgba(245, 164, 37, 0.2)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 7,
                        max: 10,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)'
                        }
                    }
                }
            }
        });
    } else {
        // Fallback si Chart.js no está disponible
        container.innerHTML = `
            <div style="height: 100%; display: flex; align-items: center; justify-content: center; color: rgba(255,255,255,0.7);">
                <p>Rendimiento académico destacado</p>
            </div>
        `;
    }
}

// Función para animar elementos al cargar la página
function animateOnLoad() {
        // Animar título de sección
        anime({
            targets: '.honor-board .section-heading h2',
            opacity: [0, 1],
            translateY: [-30, 0],
            duration: 1000,
            easing: 'easeOutQuad'
        });
        
        // Animar línea decorativa
        anime({
            targets: '.honor-board .line-dec',
            width: [0, '80px'],
            opacity: [0, 1],
            duration: 1000,
            delay: 300,
            easing: 'easeInOutQuad'
        });
        
        // Animar subtítulo
        anime({
            targets: '.honor-board .honor-subtitle',
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 1000,
            delay: 500,
            easing: 'easeOutQuad'
        });
        
        // Animar entrada del carrusel
        anime({
            targets: '.honor-carousel',
            opacity: [0, 1],
            translateY: [50, 0],
            duration: 1000,
            delay: 700,
            easing: 'easeOutQuad'
        });
        
        // Animar controles
        anime({
            targets: ['.honor-controls', '.honor-indicators'],
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 800,
            delay: 1000,
            easing: 'easeOutQuad'
        });
    }

