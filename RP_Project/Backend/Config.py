import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration for Speech Enhancement System"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Database Configuration
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'sqlite:///database/speech_enhancement.db'
    )
    
    # Upload Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg', 'm4a'}
    
    # Processing Configuration
    SAMPLE_RATE = 16000  # Hz
    FRAME_LENGTH = 512
    HOP_LENGTH = 160
    N_FFT = 512
    
    # Processing Paths
    SCHEMA_FILE = 'SQL/Schema.sql'  # Database schema file
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'output')
    TEMP_FOLDER = os.getenv('TEMP_FOLDER', 'temp')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # Processing Parameters
    SNR_THRESHOLD = 0.1
    WIENER_NOISE_POWER_THRESHOLD = 0.01
    SPECTRAL_SUBTRACTION_ALPHA = 2.0
    
    def __init__(self):
        """Initialize configuration"""
        # Create necessary directories
        for folder in [self.UPLOAD_FOLDER, self.OUTPUT_FOLDER, self.TEMP_FOLDER, 'database']:
            if not os.path.exists(folder):
                os.makedirs(folder)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'

# Select configuration based on environment
config_name = os.getenv('FLASK_ENV', 'development')
if config_name == 'production':
    app_config = ProductionConfig()
elif config_name == 'testing':
    app_config = TestingConfig()
else:
    app_config = DevelopmentConfig()
