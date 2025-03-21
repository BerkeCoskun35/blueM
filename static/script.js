document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const menuIcon = document.querySelector('.menu-icon');
    const sideMenu = document.getElementById('sideMenu');
    const menuItems = document.querySelector('.side-menu ul');
    const content = document.querySelector('.content');
    
    // Sayfa yüklendiğinde menü öğelerini gizle
    menuItems.style.display = 'none';
    
    menuToggle.addEventListener('click', function(event) {
        event.stopPropagation();
        toggleMenu();
    });
    
    // Menü ikonuna tıklandığında da menüyü aç/kapat
    menuIcon.addEventListener('click', function(event) {
        event.stopPropagation();
        toggleMenu();
    });
    
    function toggleMenu() {
        sideMenu.classList.toggle('open');
        content.classList.toggle('shifted');
        
        // Menü açıksa öğeleri göster, kapalıysa gizle
        if (sideMenu.classList.contains('open')) {
            menuItems.style.display = 'block';
        } else {
            menuItems.style.display = 'none';
        }
    }
    
    // Sayfa dışına tıklandığında menüyü kapat
    document.addEventListener('click', function(event) {
        if (!sideMenu.contains(event.target) && event.target !== menuToggle && event.target !== menuIcon) {
            sideMenu.classList.remove('open');
            content.classList.remove('shifted');
            menuItems.style.display = 'none';
        }
    });
}); 