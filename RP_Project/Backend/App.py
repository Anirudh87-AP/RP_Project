from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
import logging
from Backend.Database import Base, User, UploadSession, AudioFile, ProcessingJob, ProcessingResult, RecordingSession, SystemLog
from Backend.Processing.Convert import convert_mp3_to_wav, get_audio_metadata
from Backend.Processing.Processing import process_audio_pipeline
from Backend.Config import Config
import traceback

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine(app.config['DATABASE_URL'], echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        
        # Load schema from file if exists
        schema_file = 'SQL/Schema.sql'
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                sql_commands = f.read()
                # Execute SQL if needed
        
        return True
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        return False

# Initialize database on startup
if not os.path.exists('database'):
    os.makedirs('database')

init_db()

# ==================== API ENDPOINTS ====================

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'Speech Enhancement System Backend',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/upload', methods=['POST'])
def upload_audio():
    """Upload audio file endpoint"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file size
        if len(file.read()) > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': 'File too large'}), 413
        
        file.seek(0)
        
        # Save file
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get metadata
        metadata = get_audio_metadata(filepath)
        
        # Create database records
        session = SessionLocal()
        try:
            upload_session = UploadSession(
                filename=filename,
                original_filename=file.filename,
                file_size=os.path.getsize(filepath),
                upload_timestamp=datetime.now()
            )
            session.add(upload_session)
            session.commit()
            
            audio_file = AudioFile(
                upload_session_id=upload_session.id,
                file_path=filepath,
                format=file.filename.split('.')[-1],
                duration=metadata.get('duration', 0),
                sample_rate=metadata.get('sample_rate', 0)
            )
            session.add(audio_file)
            session.commit()
            
            return jsonify({
                'success': True,
                'file_id': audio_file.id,
                'upload_session_id': upload_session.id,
                'metadata': metadata
            }), 200
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/record', methods=['POST'])
def init_recording():
    """Initialize recording session"""
    try:
        session = SessionLocal()
        try:
            recording_session = RecordingSession(
                start_time=datetime.now()
            )
            session.add(recording_session)
            session.commit()
            
            return jsonify({
                'success': True,
                'recording_session_id': recording_session.id,
                'timestamp': datetime.now().isoformat()
            }), 200
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Recording init error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/record/save', methods=['POST'])
def save_recording():
    """Save recorded audio"""
    try:
        if 'audio_data' not in request.files:
            return jsonify({'error': 'No audio data'}), 400
        
        audio_file = request.files['audio_data']
        recording_session_id = request.form.get('recording_session_id')
        
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        filename = f"recording_{datetime.now().timestamp()}.wav"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)
        
        session = SessionLocal()
        try:
            metadata = get_audio_metadata(filepath)
            
            upload_session = UploadSession(
                filename=filename,
                original_filename=filename,
                file_size=os.path.getsize(filepath),
                upload_timestamp=datetime.now()
            )
            session.add(upload_session)
            session.commit()
            
            audio_obj = AudioFile(
                upload_session_id=upload_session.id,
                file_path=filepath,
                format='wav',
                duration=metadata.get('duration', 0),
                sample_rate=metadata.get('sample_rate', 0)
            )
            session.add(audio_obj)
            session.commit()
            
            if recording_session_id:
                recording = session.query(RecordingSession).filter_by(
                    id=recording_session_id
                ).first()
                if recording:
                    recording.end_time = datetime.now()
                    recording.audio_file_id = audio_obj.id
                    session.commit()
            
            return jsonify({
                'success': True,
                'file_id': audio_obj.id,
                'metadata': metadata
            }), 200
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Save recording error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_audio():
    """Start audio processing"""
    try:
        file_id = request.json.get('file_id')
        
        if not file_id:
            return jsonify({'error': 'No file_id provided'}), 400
        
        session = SessionLocal()
        try:
            audio_file = session.query(AudioFile).filter_by(id=file_id).first()
            
            if not audio_file:
                return jsonify({'error': 'File not found'}), 404
            
            # Create processing job
            processing_job = ProcessingJob(
                audio_file_id=file_id,
                status='processing',
                start_time=datetime.now()
            )
            session.add(processing_job)
            session.commit()
            
            job_id = processing_job.id
            
            # Process audio
            try:
                results = process_audio_pipeline(audio_file.file_path)
                
                # Save results
                processing_result = ProcessingResult(
                    processing_job_id=job_id,
                    signal_power=results.get('signal_power'),
                    noise_power=results.get('noise_power'),
                    snr_input=results.get('snr_input'),
                    wiener_gain=results.get('wiener_gain'),
                    spectral_subtraction_factor=results.get('spectral_subtraction_factor'),
                    spectral_distance=results.get('spectral_distance'),
                    segmental_snr=results.get('segmental_snr'),
                    processing_duration=results.get('processing_duration'),
                    output_file_path=results.get('output_file_path')
                )
                session.add(processing_result)
                
                processing_job.status = 'completed'
                processing_job.end_time = datetime.now()
                session.commit()
                
                return jsonify({
                    'success': True,
                    'job_id': job_id,
                    'status': 'completed',
                    'results': {
                        'signal_power': results.get('signal_power'),
                        'noise_power': results.get('noise_power'),
                        'snr_input': results.get('snr_input'),
                        'wiener_gain': results.get('wiener_gain'),
                        'spectral_subtraction_factor': results.get('spectral_subtraction_factor'),
                        'spectral_distance': results.get('spectral_distance'),
                        'segmental_snr': results.get('segmental_snr'),
                        'processing_duration': results.get('processing_duration')
                    }
                }), 200
            
            except Exception as e:
                processing_job.status = 'failed'
                processing_job.end_time = datetime.now()
                session.commit()
                logger.error(f"Processing error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Process endpoint error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process/<int:job_id>/status', methods=['GET'])
def get_processing_status(job_id):
    """Get processing job status"""
    try:
        session = SessionLocal()
        try:
            job = session.query(ProcessingJob).filter_by(id=job_id).first()
            
            if not job:
                return jsonify({'error': 'Job not found'}), 404
            
            return jsonify({
                'job_id': job.id,
                'status': job.status,
                'start_time': job.start_time.isoformat() if job.start_time else None,
                'end_time': job.end_time.isoformat() if job.end_time else None
            }), 200
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<int:job_id>', methods=['GET'])
def get_results(job_id):
    """Get processing results"""
    try:
        session = SessionLocal()
        try:
            result = session.query(ProcessingResult).filter_by(
                processing_job_id=job_id
            ).first()
            
            if not result:
                return jsonify({'error': 'Results not found'}), 404
            
            return jsonify({
                'job_id': job_id,
                'signal_power': result.signal_power,
                'noise_power': result.noise_power,
                'snr_input': result.snr_input,
                'wiener_gain': result.wiener_gain,
                'spectral_subtraction_factor': result.spectral_subtraction_factor,
                'spectral_distance': result.spectral_distance,
                'segmental_snr': result.segmental_snr,
                'processing_duration': result.processing_duration,
                'output_file_path': result.output_file_path
            }), 200
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Results retrieval error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    """Download processed audio file"""
    try:
        session = SessionLocal()
        try:
            result = session.query(ProcessingResult).filter_by(
                processing_job_id=file_id
            ).first()
            
            if not result or not result.output_file_path:
                return jsonify({'error': 'File not found'}), 404
            
            if not os.path.exists(result.output_file_path):
                return jsonify({'error': 'File not found on disk'}), 404
            
            return send_file(
                result.output_file_path,
                as_attachment=True,
                download_name='enhanced_audio.wav'
            )
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Speech Enhancement System Backend")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )
