"""
Database.py - SQLAlchemy ORM Models for Speech Enhancement System
8 ORM Models for all database tables
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

# Model 1: Users
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    upload_sessions = db.relationship('UploadSession', backref='user', lazy=True)
    recording_sessions = db.relationship('RecordingSession', backref='user', lazy=True)
    download_history = db.relationship('DownloadHistory', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.session_id}>'

# Model 2: Upload Sessions
class UploadSession(db.Model):
    __tablename__ = 'upload_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    audio_files = db.relationship('AudioFile', backref='upload_session', lazy=True)
    
    def __repr__(self):
        return f'<UploadSession {self.session_name}>'

# Model 3: Audio Files
class AudioFile(db.Model):
    __tablename__ = 'audio_files'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('upload_sessions.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    duration_seconds = db.Column(db.Float)
    sample_rate = db.Column(db.Integer)
    channels = db.Column(db.Integer)
    format = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    processing_jobs = db.relationship('ProcessingJob', backref='audio_file', lazy=True)
    download_history = db.relationship('DownloadHistory', backref='audio_file', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_name': self.file_name,
            'duration_seconds': self.duration_seconds,
            'sample_rate': self.sample_rate,
            'format': self.format,
            'uploaded_at': self.uploaded_at.isoformat()
        }
    
    def __repr__(self):
        return f'<AudioFile {self.file_name}>'

# Model 4: Processing Jobs
class ProcessingJob(db.Model):
    __tablename__ = 'processing_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    audio_file_id = db.Column(db.Integer, db.ForeignKey('audio_files.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    progress = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    processing_results = db.relationship('ProcessingResult', backref='job', lazy=True, uselist=False)
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'status': self.status,
            'progress': self.progress,
            'created_at': self.created_at.isoformat(),
            'error_message': self.error_message
        }
    
    def __repr__(self):
        return f'<ProcessingJob {self.job_id}>'

# Model 5: Processing Results (Metrics)
class ProcessingResult(db.Model):
    __tablename__ = 'processing_results'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('processing_jobs.id'), nullable=False)
    
    # 8 Formulas / Metrics
    signal_power = db.Column(db.Float)  # Formula 1
    noise_power = db.Column(db.Float)   # Formula 2
    snr_input = db.Column(db.Float)     # Formula 3
    wiener_filter_gain = db.Column(db.Float)  # Formula 4
    spectral_subtraction_factor = db.Column(db.Float)  # Formula 5
    spectral_distance = db.Column(db.Float)  # Formula 6
    segmental_snr = db.Column(db.Float)  # Formula 7
    processing_duration = db.Column(db.Float)  # Formula 8
    
    processed_file_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'signal_power': self.signal_power,
            'noise_power': self.noise_power,
            'snr_input': self.snr_input,
            'wiener_filter_gain': self.wiener_filter_gain,
            'spectral_subtraction_factor': self.spectral_subtraction_factor,
            'spectral_distance': self.spectral_distance,
            'segmental_snr': self.segmental_snr,
            'processing_duration': self.processing_duration
        }
    
    def __repr__(self):
        return f'<ProcessingResult {self.job_id}>'

# Model 6: Recording Sessions
class RecordingSession(db.Model):
    __tablename__ = 'recording_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    recording_id = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    duration_seconds = db.Column(db.Float)
    sample_rate = db.Column(db.Integer)
    recording_path = db.Column(db.String(500))
    status = db.Column(db.String(50), default='recording')  # recording, saved, processing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'recording_id': self.recording_id,
            'duration_seconds': self.duration_seconds,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<RecordingSession {self.recording_id}>'

# Model 7: Download History
class DownloadHistory(db.Model):
    __tablename__ = 'download_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('audio_files.id'), nullable=False)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DownloadHistory {self.user_id}>'

# Model 8: System Logs
class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    log_type = db.Column(db.String(50))  # info, warning, error
    message = db.Column(db.String(500))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemLog {self.log_type}>'
