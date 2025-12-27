import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///database/speech_enhancement.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 104857600))  # 100MB
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg'}
    
    # Audio settings
    SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', 16000))
    FFT_SIZE = int(os.getenv('FFT_SIZE', 2048))
    HOP_LENGTH = int(os.getenv('HOP_LENGTH', 512))
    N_MELS = int(os.getenv('N_MELS', 128))
    
    # Processing settings
    MAX_PROCESSING_TIME = int(os.getenv('MAX_PROCESSING_TIME', 600))
    NOISE_THRESHOLD = float(os.getenv('NOISE_THRESHOLD', 0.001))
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
