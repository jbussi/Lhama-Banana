// Menu Mobile Toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    const body = document.body;
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            menuToggle.classList.toggle('menu-active');
            navLinks.classList.toggle('active');
            body.classList.toggle('menu-open');
        });
    }
    
    // Fechar o menu ao clicar em um link
    const navItems = document.querySelectorAll('.nav-links a');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth <= 1024) {
                menuToggle.classList.remove('menu-active');
                navLinks.classList.remove('active');
                body.classList.remove('menu-open');
            }
        });
    });
    
    // Ajustar altura do main quando o menu estiver aberto
    function adjustMainHeight() {
        const header = document.querySelector('header');
        const main = document.querySelector('main');
        if (header && main) {
            if (window.innerWidth <= 1024 && navLinks.classList.contains('active')) {
                main.style.minHeight = `calc(100vh - ${header.offsetHeight}px)`;
            } else {
                main.style.minHeight = `calc(100vh - ${header.offsetHeight}px)`;
            }
        }
    }
    
    // Chamar a função no carregamento e no redimensionamento
    window.addEventListener('load', adjustMainHeight);
    window.addEventListener('resize', adjustMainHeight);
});