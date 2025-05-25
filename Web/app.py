from flask import Flask, abort, jsonify, render_template, request, redirect, url_for, flash, session, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import re
import random
import ytmusicapi
from ytmusicapi import YTMusic
import json
import requests
import vlc
import yt_dlp
import threading

app = Flask(__name__)
app.secret_key = 'your-secret-key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1035@localhost:5432/blueM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# YouTube Music API kimlik doğrulama
try:
    ytmusic = YTMusic('oauth.json')
    print("YouTube Music API bağlantısı başarılı!")
except Exception as e:
    print(f"YouTube Music API bağlantı hatası: {str(e)}")
    print("Lütfen önce setup_oauth.py dosyasını çalıştırın.")
    ytmusic = None

# VLC instance oluştur
instance = vlc.Instance()
player = instance.media_player_new()
player.audio_set_volume(50)  # Başlangıç ses seviyesini %50 olarak ayarla

# Aktif çalan şarkıyı takip etmek için
current_song = None
current_media = None
player_thread = None
current_playlist = None

def get_playlist_songs():
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': True,
            'force_generic_extractor': True
        }
        playlist_url = "https://www.youtube.com/playlist?list=PLYckB4eBGCzxwq9qskgYpCokYozzynUef"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            songs = []
            for entry in playlist_info['entries']:
                songs.append({
                    'id': entry.get('id', ''),
                    'video_id': entry.get('id', ''),
                    'title': entry.get('title', ''),
                    'artist': entry.get('uploader', ''),
                    'duration': entry.get('duration_string', ''),
                    'thumbnail_url': entry.get('thumbnail', '')
                })
            random.shuffle(songs)
            return songs
    except Exception as e:
        print(f"Playlist yükleme hatası: {str(e)}")
        return []

def play_song_in_background(video_id):
    global current_song, current_media
    try:
        if player.is_playing():
            player.stop()
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            current_media = instance.media_new(audio_url)
            player.set_media(current_media)
            player.play()
            while player.is_playing():
                pass
    except Exception as e:
        print(f"Şarkı çalma hatası: {str(e)}")

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Song(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    video_id = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.String(50))
    thumbnail_url = db.Column(db.String(255))

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    thumbnail_url = db.Column(db.String(255))
    user = db.relationship('User', backref=db.backref('favorites', lazy='dynamic'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email:
            flash('E-posta adresi gerekli!', 'error')
            return redirect(url_for('login'))

        if not password:
            flash('Şifre gerekli!', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Başarıyla giriş yaptınız!', 'success')
            return redirect(url_for('index'))
        else:
            flash('E-posta veya şifre hatalı!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')

        if not email:
            flash('E-posta adresi gerekli!', 'error')
            return redirect(url_for('register'))

        if not password:
            flash('Şifre gerekli!', 'error')
            return redirect(url_for('register'))

        if not confirm_password:
            flash('Şifre tekrarı gerekli!', 'error')
            return redirect(url_for('register'))

        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            flash('Geçerli bir e-posta adresi girin!', 'error')
            return redirect(url_for('register'))

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Bu e-posta adresi zaten kayıtlı!', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır!', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Şifreler eşleşmiyor!', 'error')
            return redirect(url_for('register'))

        try:
            hashed_password = generate_password_hash(password)
            new_user = User(email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            flash('Kayıt sırasında bir hata oluştu!', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/')
def api_index():
    return jsonify({'message': 'API Ana Sayfasına Hoşgeldiniz!'}), 200

@app.route('/api/login', methods=['POST'])
def api_login():
    if current_user.is_authenticated:
        return jsonify({'message': 'Zaten giriş yapmış durumdasınız!'}), 200

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON verisi eksik!'}), 400

    email = data.get('email')
    password = data.get('password')

    if not email:
        return jsonify({'error': 'E-posta adresi gerekli!'}), 400

    if not password:
        return jsonify({'error': 'Şifre gerekli!'}), 400

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({'message': 'Başarıyla giriş yaptınız!'}), 200
    else:
        return jsonify({'error': 'E-posta veya şifre hatalı!'}), 401

@app.route('/api/register', methods=['POST'])
def api_register():
    if current_user.is_authenticated:
        return jsonify({'message': 'Zaten giriş yapmış durumdasınız!'}), 200

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON verisi eksik!'}), 400

    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirmPassword')

    if not email:
        return jsonify({'error': 'E-posta adresi gerekli!'}), 400

    if not password:
        return jsonify({'error': 'Şifre gerekli!'}), 400

    if not confirm_password:
        return jsonify({'error': 'Şifre tekrarı gerekli!'}), 400

    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return jsonify({'error': 'Geçerli bir e-posta adresi girin!'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Bu e-posta adresi zaten kayıtlı!'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Şifre en az 6 karakter olmalıdır!'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Şifreler eşleşmiyor!'}), 400

    try:
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'Kayıt başarılı! Şimdi giriş yapabilirsiniz.'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Kayıt sırasında bir hata oluştu!'}), 500

@app.route('/api/profile')
@login_required
def api_profile():
    return jsonify({
        'id': current_user.id,
        'email': current_user.email
    }), 200

@app.route('/api/logout')
@login_required
def api_logout():
    logout_user()
    return jsonify({'message': 'Başarıyla çıkış yaptınız!'}), 200

@app.route('/stream')
def stream_audio():
    file_path = 'audio.mp3'
    if not os.path.exists(file_path):
        return "Ses dosyası bulunamadı.", 404

    file_size = os.stat(file_path).st_size
    range_header = request.headers.get('Range', None)

    if not range_header:
        def generate():
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    yield chunk
        return Response(generate(), mimetype="audio/mp3")

    range_match = re.search(r'(\d+)-(\d*)', range_header)
    if range_match:
        start_str, end_str = range_match.groups()
        start = int(start_str)
        end = int(end_str) if end_str else file_size - 1
    else:
        return abort(400)

    length = end - start + 1

    def generate():
        with open(file_path, 'rb') as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk_size = 4096 if remaining >= 4096 else remaining
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    rv = Response(stream_with_context(generate()), status=206, mimetype="audio/mp3")
    rv.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    return rv

@app.route('/api/songs')
def api_songs():
    # 5. Veritabanından rastgele 12 şarkı seç ve JSON olarak döndür
    songs = Song.query.order_by(db.func.random()).limit(12).all()
    data = []
    for s in songs:
        data.append({
            'id':            s.id,
            'title':         s.title,
            'artist':        s.artist,
            'duration':      s.duration,
            'video_id':      s.video_id,
            'thumbnail_url': s.thumbnail_url
        })

    return jsonify(data), 200

@app.route('/api/songs/update')
def update_songs():
    if not ytmusic:
        return jsonify({'error': 'YouTube Music API bağlantısı kurulamadı!'}), 500
    
    try:
        # YouTube Music'ten şarkıları çek
        search_results = ytmusic.search('müzik', filter='songs', limit=100)
        
        if not search_results:
            return jsonify({'error': 'Şarkılar alınamadı!'}), 404
        
        # Mevcut şarkıları temizle
        Song.query.delete()
        
        # Yeni şarkıları ekle
        for song in search_results:
            try:
                new_song = Song(
                    title=song['title'],
                    artist=song['artists'][0]['name'],
                    video_id=song['videoId'],
                    duration=song.get('duration', ''),
                    thumbnail_url=song.get('thumbnails', [{}])[0].get('url', '')
                )
                db.session.add(new_song)
            except Exception as e:
                print(f"Şarkı ekleme hatası: {str(e)}")
                continue
        
        db.session.commit()
        return jsonify({'message': 'Şarkılar başarıyla güncellendi!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Şarkı güncelleme hatası: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/playlist')
def api_playlist():
    songs = get_playlist_songs()
    return jsonify(songs)

@app.route('/api/play/<video_id>', methods=['POST'])
def api_play(video_id):
    global current_song, player_thread
    current_song = video_id
    data = request.get_json()
    title = data.get('title', '')
    artist = data.get('artist', '')
    duration = data.get('duration', 0)
    player_thread = threading.Thread(target=play_song_in_background, args=(video_id,))
    player_thread.daemon = True
    player_thread.start()
    return jsonify({
        'message': 'Çalıyor',
        'title': title,
        'artist': artist,
        'duration': duration
    })

@app.route('/api/stop')
def api_stop():
    global current_song
    if player.is_playing():
        player.stop()
    current_song = None
    return jsonify({'message': 'Durduruldu'})

@app.route('/api/songs/pause')
def pause_song():
    global current_song, current_media
    
    try:
        if player.is_playing():
            player.pause()
            return jsonify({'message': 'Şarkı duraklatıldı'})
        return jsonify({'message': 'Çalan şarkı yok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/resume')
def resume_song():
    global current_song, current_media
    
    try:
        if not player.is_playing() and current_song and current_media:
            player.play()
            return jsonify({'message': 'Şarkı devam ediyor'})
        return jsonify({'message': 'Duraklatılmış şarkı yok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/stop')
def stop_song():
    global current_song, current_media
    
    try:
        if player.is_playing() or current_song:
            player.stop()
            current_song = None
            current_media = None
            return jsonify({'message': 'Şarkı durduruldu'})
        return jsonify({'message': 'Çalan şarkı yok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/volume/<int:volume>')
def set_volume(volume):
    try:
        # VLC ses seviyesi 0-100 arasında
        volume = max(0, min(100, volume))
        player.audio_set_volume(volume)
        return jsonify({'message': f'Ses seviyesi {volume} olarak ayarlandı'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/status')
def get_status():
    try:
        return jsonify({
            'is_playing': player.is_playing(),
            'volume': player.audio_get_volume(),
            'current_song': current_song,
            'position': player.get_time() / 1000 if player.is_playing() else 0,
            'duration': player.get_length() / 1000 if player.get_length() > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/songs/seek/<int:position>')
def seek_song(position):
    try:
        if player.is_playing():
            player.set_time(position * 1000)  # VLC milisaniye cinsinden çalışır
            return jsonify({'message': 'Şarkı pozisyonu güncellendi'})
        return jsonify({'message': 'Çalan şarkı yok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/favorite/add', methods=['POST'])
@login_required
def add_favorite():
    data = request.get_json()
    video_id = data.get('song_id')
    title = data.get('title')
    artist = data.get('artist')
    thumbnail_url = data.get('thumbnail_url')
    
    if not video_id or not title or not artist:
        return jsonify({'error': 'Gerekli bilgiler eksik!'}), 400
        
    # Zaten favori mi?
    existing = Favorite.query.filter_by(user_id=current_user.id, video_id=video_id).first()
    if existing:
        return jsonify({'message': 'Zaten favorilerde!'}), 200
        
    fav = Favorite(
        user_id=current_user.id,
        video_id=video_id,
        title=title,
        artist=artist,
        thumbnail_url=thumbnail_url
    )
    db.session.add(fav)
    db.session.commit()
    return jsonify({'message': 'Favorilere eklendi!'}), 201

@app.route('/api/favorite/remove', methods=['POST'])
@login_required
def remove_favorite():
    data = request.get_json()
    video_id = data.get('song_id')
    if not video_id:
        return jsonify({'error': 'Video ID gerekli!'}), 400
        
    fav = Favorite.query.filter_by(user_id=current_user.id, video_id=video_id).first()
    if not fav:
        return jsonify({'message': 'Favorilerde yok!'}), 200
        
    db.session.delete(fav)
    db.session.commit()
    return jsonify({'message': 'Favorilerden çıkarıldı!'}), 200

@app.route('/api/favorites')
@login_required
def get_favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()
    songs = []
    for fav in favs:
        songs.append({
            'id': fav.video_id,
            'title': fav.title,
            'artist': fav.artist,
            'video_id': fav.video_id,
            'thumbnail_url': fav.thumbnail_url
        })
    return jsonify(songs), 200

@app.route('/library')
@login_required
def library():
    return render_template('library.html')

print('Tüm endpointler:')
print(app.url_map)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0")
