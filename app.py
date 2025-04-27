from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1035@localhost:5432/blueM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0")
