document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const sideMenu = document.getElementById('sideMenu');
    const content = document.querySelector('.content');
    
    menuToggle.addEventListener('click', function() {
        sideMenu.classList.toggle('open');
        content.classList.toggle('shifted');
    });
    
    // Sayfa dışına tıklandığında menüyü kapat
    document.addEventListener('click', function(event) {
        if (!sideMenu.contains(event.target) && event.target !== menuToggle) {
            sideMenu.classList.remove('open');
            content.classList.remove('shifted');
        }
    });
}); 