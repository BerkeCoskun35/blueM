from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app import db

def migrate():
    # Eski favorites tablosunu sil
    db.session.execute('DROP TABLE IF EXISTS favorites')
    
    # Yeni favorites tablosunu oluştur
    db.session.execute('''
        CREATE TABLE favorites (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            video_id VARCHAR(255) NOT NULL,
            title VARCHAR(255) NOT NULL,
            artist VARCHAR(255) NOT NULL,
            thumbnail_url VARCHAR(255)
        )
    ''')
    
    db.session.commit()
    print("Veritabanı başarıyla güncellendi!")

if __name__ == '__main__':
    migrate() 