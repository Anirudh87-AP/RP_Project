"""
App.py - Flask Backend Server with 7 API Endpoints
Speech Enhancement System
"""

from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import logging

from Config import config, Config
from Database import db, User, UploadSession, AudioFile, ProcessingJob, ProcessingResult, RecordingSession, SystemLog

# Initialize Flask App
app = Flask(__name__)
app.config.from_object(config['development'])

# Initialize Extensions
db.init_app(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('database', exist_ok=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_or_create_user():
    """Get or create user session"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    user = User.query.filter_by(session_id=session['session_id']).first()
    if not user:
        user = User(session_id=session['session_id'])
        db.session.add(user)
        db.session.commit()
    return user

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def log_event(log_type, message, details=None):
    """Log system events"""
    log = SystemLog(log_type=log_type, message=message, details=details)
    db.session.add(log)
    db.session.commit()

# ============================================================================
# API ENDPOINTS (7 Total)
# ============================================================================

@app.route('/', methods=['GET'])
def home():
    """Home endpoint - Health check"""
    return jsonify({
        'status': 'running',
        'message': 'Speech Enhancement System Backend',
        'version': '1.0',
        'timestamp': datetime.now().isoformat()
    }), 200

# ============================================================================
# ENDPOINT 1: POST /upload - Upload audio file
# ============================================================================
@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload audio file
    Expected: 'file' (audio file), 'session_id' (optional)
    Returns: file_id, file_name, duration, sample_rate
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'}), 400
        
        # Get or create user
        user = get_or_create_user()
        
        # Create or get upload session
        session_name = request.form.get('session_name', f'upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        upload_session = UploadSession(user_id=user.id, session_name=session_name)
        db.session.add(upload_session)
        db.session.commit()
        
        # Save file
        filename = secure_filename(file.filename)
        filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        
        # Create audio file record
        audio_file = AudioFile(
            session_id=upload_session.id,
            file_name=file.filename,
            original_path=filepath,
            file_size=file_size,
            format=file.filename.rsplit('.', 1)[1].lower()
        )
        db.session.add(audio_file)
        db.session.commit()
        
        log_event('info', f'File uploaded: {file.filename}', f'File ID: {audio_file.id}')
        
        return jsonify({
            'success': True,
            'file_id': audio_file.id,
            'file_name': file.filename,
            'file_size': file_size,
            'upload_time': audio_file.uploaded_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        log_event('error', 'Upload failed', str(e))
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINT 2: POST /record - Initialize recording session
# ============================================================================
@app.route('/record', methods=['POST'])
def initialize_recording():
    """
    Initialize recording session
    Expected: duration_seconds (optional)
    Returns: recording_id, status
    """
    try:
        user = get_or_create_user()
        
        duration = request.json.get('duration_seconds', 30) if request.json else 30
        
        recording = RecordingSession(
            user_id=user.id,
            duration_seconds=duration,
            status='recording'
        )
        db.session.add(recording)
        db.session.commit()
        
        log_event('info', 'Recording initialized', f'Recording ID: {recording.recording_id}')
        
        return jsonify({
            'success': True,
            'recording_id': recording.recording_id,
            'duration_seconds': duration,
            'status': 'recording'
        }), 200
        
    except Exception as e:
        logger.error(f"Recording init error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINT 3: POST /record/save - Save recording
# ============================================================================
@app.route('/record/save', methods=['POST'])
def save_recording():
    """
    Save recording to file and create audio file record
    Expected: recording_id, audio_data (base64)
    Returns: file_id, status
    """
    try:
        recording_id = request.json.get('recording_id')
        
        recording = RecordingSession.query.filter_by(recording_id=recording_id).first()
        if not recording:
            return jsonify({'error': 'Recording not found'}), 404
        
        # Save recording file
        filename = f"recording_{recording_id}.wav"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # In production, decode base64 audio data and save
        # For now, just mark as saved
        recording.status = 'saved'
        recording.recording_path = filepath
        db.session.commit()
        
        # Create audio file record
        user = recording.user
        upload_session = UploadSession.query.filter_by(user_id=user.id).first()
        if not upload_session:
            upload_session = UploadSession(user_id=user.id, session_name='recording_session')
            db.session.add(upload_session)
            db.session.commit()
        
        audio_file = AudioFile(
            session_id=upload_session.id,
            file_name=filename,
            original_path=filepath,
            format='wav'
        )
        db.session.add(audio_file)
        db.session.commit()
        
        log_event('info', 'Recording saved', f'File ID: {audio_file.id}')
        
        return jsonify({
            'success': True,
            'file_id': audio_file.id,
            'recording_id': recording_id,
            'status': 'saved'
        }), 200
        
    except Exception as e:
        logger.error(f"Save recording error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINT 4: POST /process - Start audio processing
# ============================================================================
@app.route('/process', methods=['POST'])
def process_audio():
    """
    Start audio processing job
    Expected: file_id
    Returns: job_id, status
    """
    try:
        file_id = request.json.get('file_id')
        
        audio_file = AudioFile.query.get(file_id)
        if not audio_file:
            return jsonify({'error': 'File not found'}), 404
        
        # Create processing job
        job = ProcessingJob(
            audio_file_id=file_id,
            status='pending',
            progress=0
        )
        db.session.add(job)
        db.session.commit()
        
        # Create mock results (In production, call actual processing)
        result = ProcessingResult(
            job_id=job.id,
            signal_power=25.5,
            noise_power=5.2,
            snr_input=13.8,
            wiener_filter_gain=0.8,
            spectral_subtraction_factor=0.75,
            spectral_distance=0.12,
            segmental_snr=18.5,
            processing_duration=2.3
        )
        db.session.add(result)
        
        job.status = 'completed'
        job.progress = 100
        job.completed_at = datetime.utcnow()
        db.session.commit()
        
        log_event('info', 'Processing completed', f'Job ID: {job.job_id}')
        
        return jsonify({
            'success': True,
            'job_id': job.job_id,
            'status': 'started',
            'progress': 0
        }), 200
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINT 5: GET /process/<job_id>/status - Check processing status
# ============================================================================
@app.route('/process/<job_id>/status', methods=['GET'])
def check_status(job_id):
    """
    Check processing status
    Returns: job_id, status, progress, error_message
    """
    try:
        job = ProcessingJob.query.filter_by(job_id=job_id).first()
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'job_id': job.job_id,
            'status': job.status,
            'progress': job.progress,
            'error_message': job.error_message,
            'created_at': job.created_at.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINT 6: GET /results/<job_id> - Get processing results
# ============================================================================
@app.route('/results/<job_id>', methods=['GET'])
def get_results(job_id):
    """
    Get processing results (8 metrics)
    Returns: All 8 formula results
    """
    try:
        job = ProcessingJob.query.filter_by(job_id=job_id).first()
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != 'completed':
            return jsonify({'error': 'Processing not completed'}), 400
        
        result = job.processing_results
        if not result:
            return jsonify({'error': 'Results not found'}), 404
        
        return jsonify({
            'job_id': job.job_id,
            'status': job.status,
            'metrics': result.to_dict(),
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"Results retrieval error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ENDPOINT 7: GET /download/<file_id> - Download processed audio
# ============================================================================
@app.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    """
    Download audio file
    Returns: Audio file download
    """
    try:
        audio_file = AudioFile.query.get(file_id)
        if not audio_file:
            return jsonify({'error': 'File not found'}), 404
        
        if not os.path.exists(audio_file.original_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        user = get_or_create_user()
        
        log_event('info', 'File downloaded', f'File ID: {file_id}')
        
        return send_file(
            audio_file.original_path,
            as_attachment=True,
            download_name=audio_file.file_name
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        logger.info("Database initialized")

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
