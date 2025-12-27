from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    """User model for session management"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    upload_sessions = relationship('UploadSession', back_populates='user')
    recording_sessions = relationship('RecordingSession', back_populates='user')
    
    def __repr__(self):
        return f'<User {self.username}>'

class UploadSession(Base):
    """Model for upload sessions"""
    __tablename__ = 'upload_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='upload_sessions')
    audio_files = relationship('AudioFile', back_populates='upload_session')
    
    def __repr__(self):
        return f'<UploadSession {self.filename}>'

class AudioFile(Base):
    """Model for audio files"""
    __tablename__ = 'audio_files'
    
    id = Column(Integer, primary_key=True)
    upload_session_id = Column(Integer, ForeignKey('upload_sessions.id'), nullable=False)
    file_path = Column(String(500), nullable=False)
    format = Column(String(10), nullable=False)  # mp3, wav, flac, ogg
    duration = Column(Float, nullable=True)  # seconds
    sample_rate = Column(Integer, nullable=True)  # Hz
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    
    upload_session = relationship('UploadSession', back_populates='audio_files')
    processing_jobs = relationship('ProcessingJob', back_populates='audio_file')
    recording_sessions = relationship('RecordingSession', back_populates='audio_file')
    
    def __repr__(self):
        return f'<AudioFile {self.format} {self.id}>'

class ProcessingJob(Base):
    """Model for processing jobs"""
    __tablename__ = 'processing_jobs'
    
    id = Column(Integer, primary_key=True)
    audio_file_id = Column(Integer, ForeignKey('audio_files.id'), nullable=False)
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    audio_file = relationship('AudioFile', back_populates='processing_jobs')
    processing_results = relationship('ProcessingResult', back_populates='processing_job')
    
    def __repr__(self):
        return f'<ProcessingJob {self.id} {self.status}>'

class ProcessingResult(Base):
    """Model for processing results (8 formulas)"""
    __tablename__ = 'processing_results'
    
    id = Column(Integer, primary_key=True)
    processing_job_id = Column(Integer, ForeignKey('processing_jobs.id'), nullable=False)
    
    # 8 Formula Results
    signal_power = Column(Float, nullable=True)  # Formula 1: dB
    noise_power = Column(Float, nullable=True)  # Formula 2: dB
    snr_input = Column(Float, nullable=True)  # Formula 3: dB
    wiener_gain = Column(Float, nullable=True)  # Formula 4: linear
    spectral_subtraction_factor = Column(Float, nullable=True)  # Formula 5
    spectral_distance = Column(Float, nullable=True)  # Formula 6
    segmental_snr = Column(Float, nullable=True)  # Formula 7: dB
    processing_duration = Column(Float, nullable=True)  # Formula 8: seconds
    
    # Output
    output_file_path = Column(String(500), nullable=True)
    result_timestamp = Column(DateTime, default=datetime.utcnow)
    
    processing_job = relationship('ProcessingJob', back_populates='processing_results')
    
    def __repr__(self):
        return f'<ProcessingResult {self.id}>'

class RecordingSession(Base):
    """Model for recording sessions"""
    __tablename__ = 'recording_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    audio_file_id = Column(Integer, ForeignKey('audio_files.id'), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)
    
    user = relationship('User', back_populates='recording_sessions')
    audio_file = relationship('AudioFile', back_populates='recording_sessions')
    
    def __repr__(self):
        return f'<RecordingSession {self.id}>'

class DownloadHistory(Base):
    """Model for download history"""
    __tablename__ = 'download_history'
    
    id = Column(Integer, primary_key=True)
    processing_job_id = Column(Integer, ForeignKey('processing_jobs.id'), nullable=False)
    download_timestamp = Column(DateTime, default=datetime.utcnow)
    download_count = Column(Integer, default=1)
    
    def __repr__(self):
        return f'<DownloadHistory {self.id}>'

class SystemLog(Base):
    """Model for system logs"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    log_level = Column(String(20))  # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    module = Column(String(100), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f'<SystemLog {self.log_level} {self.timestamp}>'

# Initialize database function
def init_db(database_url='sqlite:///database/speech_enhancement.db'):
    """Initialize database with all tables"""
    from sqlalchemy import create_engine
    
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    
    # Load SQL schema if available
    schema_file = 'SQL/Schema.sql'
    if os.path.exists(schema_file):
        try:
            with open(schema_file, 'r') as f:
                sql_content = f.read()
                # Note: SQLAlchemy ORM creates tables, schema.sql is for reference
        except Exception as e:
            print(f"Warning: Could not load schema file: {e}")
    
    return engine
