// Menú móvil independiente
document.addEventListener('DOMContentLoaded', function() {
    // Crear el botón del menú móvil
    const menuButton = document.createElement('button');
    menuButton.className = 'mobile-menu-button';
    menuButton.innerHTML = '<i class="fa fa-bars"></i>';
    
    // Crear el contenedor del menú móvil
    const menuContainer = document.createElement('div');
    menuContainer.className = 'mobile-menu-container';
    
    // Crear el botón de cierre
    const closeButton = document.createElement('button');
    closeButton.className = 'mobile-menu-close';
    closeButton.innerHTML = '&times;';
    
    // Crear el menú
    const mobileMenu = document.createElement('div');
    mobileMenu.className = 'mobile-menu';
    
    // Contenido del menú (puedes personalizarlo según tus necesidades)
    mobileMenu.innerHTML = `
        <ul>
            <li><a href="/" class="external"><i class="fa fa-home"></i> Inicio</a></li>
            <li><a href="/mision-vision/" class="external"><i class="fa fa-bullseye"></i> Misión y Visión</a></li>
            <li><a href="/nosotros/" class="external"><i class="fa fa-users"></i> Nosotros</a></li>
            <li><a href="/docentes-nuevo/" class="external"><i class="fa fa-chalkboard-teacher"></i> Nuestros Docentes</a></li>
            <li><a href="/noticias/" class="external"><i class="fa fa-newspaper"></i> Noticias</a></li>
            <li><a href="#" class="login-link" data-bs-toggle="modal" data-bs-target="#loginModal"><i class="fa fa-sign-in-alt"></i> Login</a></li>
        </ul>
    `;
    
    // Agregar elementos al contenedor
    menuContainer.appendChild(closeButton);
    menuContainer.appendChild(mobileMenu);
    
    // Agregar elementos al cuerpo del documento
    document.body.appendChild(menuButton);
    document.body.appendChild(menuContainer);
    
    // Función para alternar el menú
    function toggleMenu() {
        menuContainer.classList.toggle('active');
        const icon = menuButton.querySelector('i');
        
        if (menuContainer.classList.contains('active')) {
            icon.classList.remove('fa-bars');
            icon.classList.add('fa-times');
        } else {
            icon.classList.remove('fa-times');
            icon.classList.add('fa-bars');
        }
    }
    
    // Eventos
    menuButton.addEventListener('click', function(e) {
        e.preventDefault();
        toggleMenu();
    });
    
    closeButton.addEventListener('click', function(e) {
        e.preventDefault();
        toggleMenu();
    });
    
    // Cerrar menú al hacer clic fuera de él
    menuContainer.addEventListener('click', function(e) {
        if (e.target === menuContainer) {
            toggleMenu();
        }
    });
    
    // Cerrar menú al hacer clic en un enlace
    const menuLinks = mobileMenu.querySelectorAll('a');
    menuLinks.forEach(link => {
        link.addEventListener('click', function() {
            toggleMenu();
        });
    });
});
