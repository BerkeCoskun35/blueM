console.log("script.js yüklendi!");
document.addEventListener('DOMContentLoaded', function() {
 //   const menuToggle = document.getElementById('menuToggle');
//    const menuIcon = document.querySelector('.menu-icon');
//    const sideMenu = document.getElementById('sideMenu');
 //   const menuItems = document.querySelector('.side-menu ul');
 //   
 //   // Sayfa yüklendiğinde menü öğelerini gizle
 //   menuItems.style.display = 'none';
 //   
 //   menuToggle.addEventListener('click', function(event) {
 //       event.stopPropagation();
//        toggleMenu();
 //   });
//    
//    // Menü ikonuna tıklandığında da menüyü aç/kapat
//    menuIcon.addEventListener('click', function(event) {
//        event.stopPropagation();
//        toggleMenu();
//    });
////    
//    function toggleMenu() {
//        sideMenu.classList.toggle('open');
//        content.classList.toggle('shifted');
//        
//        // Menü açıksa öğeleri göster, kapalıysa gizle
//        if (sideMenu.classList.contains('open')) {
//            menuItems.style.display = 'block';
//        } else {
//            menuItems.style.display = 'none';
//        }
//    }
 //   
 //   // Sayfa dışına tıklandığında menüyü kapat
 //   document.addEventListener('click', function(event) {
 //       if (!sideMenu.contains(event.target) && event.target !== menuToggle && event.target !== menuIcon) {
 //           sideMenu.classList.remove('open');
 //           content.classList.remove('shifted');
//            menuItems.style.display = 'none';
//        }
 //   });
//
//    // Audio Kontrolleri
//const audioPlayer = document.getElementById('audioPlayer');
//
//function playAudio() {
//    audioPlayer.play();
//}
//
//function pauseAudio() {
//    audioPlayer.pause();
//}
//
//function setVolume(value) {
//    audioPlayer.volume = value;
//}
//
//
//
//document.addEventListener('DOMContentLoaded', function() {
//   const audioPlayer = document.getElementById('audioPlayer');
//    const volumeSlider = document.getElementById('volumeSlider');
//    const volumeIcon = document.querySelector('.volume-icon');
//
//    let previousVolume = 0.5;
//    audioPlayer.volume = previousVolume;
//    volumeSlider.value = previousVolume;
//
//    window.playAudio = function() {
//        audioPlayer.play();
//    };
//
//    window.pauseAudio = function() {
 //       audioPlayer.pause();
//    };
//
//    window.setVolume = function(value) {
//        audioPlayer.volume = value;
//        if (audioPlayer.volume == 0) {
//            volumeIcon.src = "/static/images/nonvolume-icon.png";
//        } else {
//            volumeIcon.src = "/static/images/volume-icon.png";
//        }
//    };
//
//    function toggleMute() {
//        if (audioPlayer.volume > 0) {
//           previousVolume = audioPlayer.volume;
//            audioPlayer.volume = 0;
//            volumeSlider.value = 0;
//            volumeIcon.src = "/static/images/nonvolume-icon.png";
//        } else {
//            audioPlayer.volume = previousVolume;
//            volumeSlider.value = previousVolume;
//            volumeIcon.src = "/static/images/volume-icon.png";
//        }
//    }
//
//    volumeIcon.addEventListener('click', toggleMute);
//});
//
//
//
//document.addEventListener('DOMContentLoaded', function() {
//    const musicGrid = document.getElementById('musicGrid');
//
//    for (let i = 1; i <= 50; i++) {
//       const card = document.createElement('div');
//        card.className = 'music-card';
//        card.style.backgroundImage = `url('/static/images/album${(i % 10) + 1}.png')`; // 10 farklı albüm varmış gibi döner
//
//        const info = document.createElement('div');
//        info.className = 'music-info';
//
//        const title = document.createElement('h3');
//        title.innerText = `Şarkı ${i}`;
//
//        const artist = document.createElement('p');
//        artist.innerText = `Sanatçı ${i}`;
//
//        info.appendChild(title);
//        info.appendChild(artist);
//        card.appendChild(info);
//        musicGrid.appendChild(card);
//    }
//});

let volumeChangeTimeout = null;

function updateNowPlaying(title, artist) {
    document.getElementById('nowPlayingTitle').textContent = `${title} - ${artist}`;
}

function updateTime(current, total) {
    document.getElementById('currentTime').textContent = formatTime(current);
    document.getElementById('totalTime').textContent = formatTime(total);
}

function formatTime(seconds) {
    if (isNaN(seconds)) return "00:00";
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
}

// Ses seviyesi slider'ı için debounce ile optimize kontrol
document.getElementById('volumeSlider').addEventListener('input', function(e) {
    const value = e.target.value;
    clearTimeout(volumeChangeTimeout);
    setVolume(value);
    volumeChangeTimeout = setTimeout(() => setVolume(value), 150);
});

// Ses ikonu ile mute/unmute
document.getElementById('volumeIcon').addEventListener('click', function() {
    const slider = document.getElementById('volumeSlider');
    if (slider.value > 0) {
        slider.value = 0;
        setVolume(0);
    } else {
        slider.value = 50;
        setVolume(50);
    }
});

// Periyodik olarak şarkı durumunu kontrol et
setInterval(async () => {
    if (currentSong) {
        try {
            const response = await fetch('/api/songs/status');
            const data = await response.json();
            if (response.ok) {
                isPlaying = data.is_playing;
                document.getElementById('playPauseIcon').textContent = isPlaying ? '⏸️' : '▶️';
                document.getElementById('volumeSlider').value = data.volume;
                updateTime(data.position, data.duration);
            }
        } catch (error) {
            console.error('Durum kontrolü hatası:', error);
        }
    }
}, 1000);

// playSong fonksiyonunda şunu ekle:
function showNowPlaying(title, artist) {
    updateNowPlaying(title, artist);
    const panel = document.querySelector('.music-panel');
    panel.classList.add('visible');
    panel.style.display = 'flex';
    console.log("Alt menü açıldı:", title, artist);
}

function hideNowPlaying() {
    const panel = document.querySelector('.music-panel');
    panel.classList.remove('visible');
    panel.style.display = 'none';
    updateNowPlaying("Şarkı Seçiniz", "");
    updateTime(0, 0);
}

}); 