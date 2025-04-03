from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Session için gerekli, güvenli bir değer kullanın

# PostgreSQL bağlantı bilgileri
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1035@localhost:5432/blueM'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy ve LoginManager başlatma
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Kullanıcı modeli
class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Tablo adını açıkça belirtiyoruz
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ana sayfa
@app.route('/')
def index():
    return render_template('index.html')

# Login sayfası
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

# Register sayfası
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
        
        # E-posta formatı kontrolü
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            flash('Geçerli bir e-posta adresi girin!', 'error')
            return redirect(url_for('register'))
        
        # E-posta kontrolü
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Bu e-posta adresi zaten kayıtlı!', 'error')
            return redirect(url_for('register'))
        
        # Şifre kontrolü
        if len(password) < 6:
            flash('Şifre en az 6 karakter olmalıdır!', 'error')
            return redirect(url_for('register'))
            
        if password != confirm_password:
            flash('Şifreler eşleşmiyor!', 'error')
            return redirect(url_for('register'))
        
        try:
            # Yeni kullanıcı oluştur
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

# Profil sayfası
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# Çıkış yap
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# API Ana sayfası
@app.route('/api/')
def api_index():
    return jsonify({'message': 'API Ana Sayfasına Hoşgeldiniz!'}), 200

# API Login Endpoint (POST)
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

# API Register Endpoint (POST)
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

    # E-posta formatı kontrolü
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        return jsonify({'error': 'Geçerli bir e-posta adresi girin!'}), 400

    # E-posta kontrolü
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Bu e-posta adresi zaten kayıtlı!'}), 400

    # Şifre kontrolü
    if len(password) < 6:
        return jsonify({'error': 'Şifre en az 6 karakter olmalıdır!'}), 400

    if password != confirm_password:
        return jsonify({'error': 'Şifreler eşleşmiyor!'}), 400

    try:
        # Yeni kullanıcı oluşturma
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'Kayıt başarılı! Şimdi giriş yapabilirsiniz.'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Kayıt sırasında bir hata oluştu!'}), 500

# API Profil Endpoint (GET, giriş yapılmış kullanıcı için)
@app.route('/api/profile')
@login_required
def api_profile():
    return jsonify({
        'id': current_user.id,
        'email': current_user.email
    }), 200

# API Logout Endpoint (GET)
@app.route('/api/logout')
@login_required
def api_logout():
    logout_user()
    return jsonify({'message': 'Başarıyla çıkış yaptınız!'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Tablolar yoksa oluştur
    app.run(host="0.0.0.0") 




#Mobil için Login & Register sayfaları oluşturuldu ancak boyutu 500mb+ olduğu için github'a yükleyemedim. (Genel Android Studio boyutu)
#Mobil için design'da değişiklikler yapıldı. 03.04.2025