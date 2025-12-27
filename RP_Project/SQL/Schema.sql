-- Speech Enhancement System Database Schema
-- Create all 8 tables for the project

-- Table 1: Users (Session management)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: Upload Sessions
CREATE TABLE IF NOT EXISTS upload_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Table 3: Audio Files
CREATE TABLE IF NOT EXISTS audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    original_path TEXT NOT NULL,
    file_size INTEGER,
    duration_seconds REAL,
    sample_rate INTEGER,
    channels INTEGER,
    format TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES upload_sessions(id)
);

-- Table 4: Processing Jobs
CREATE TABLE IF NOT EXISTS processing_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    audio_file_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(audio_file_id) REFERENCES audio_files(id)
);

-- Table 5: Processing Results (Metrics)
CREATE TABLE IF NOT EXISTS processing_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    signal_power REAL,
    noise_power REAL,
    snr_input REAL,
    wiener_filter_gain REAL,
    spectral_subtraction_factor REAL,
    spectral_distance REAL,
    segmental_snr REAL,
    processing_duration REAL,
    processed_file_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(job_id) REFERENCES processing_jobs(id)
);

-- Table 6: Recording Sessions
CREATE TABLE IF NOT EXISTS recording_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recording_id TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    duration_seconds REAL,
    sample_rate INTEGER,
    recording_path TEXT,
    status TEXT DEFAULT 'recording',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Table 7: Download History
CREATE TABLE IF NOT EXISTS download_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(file_id) REFERENCES audio_files(id)
);

-- Table 8: System Logs
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_type TEXT,
    message TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_session ON users(session_id);
CREATE INDEX IF NOT EXISTS idx_job_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_job_id ON processing_results(job_id);
CREATE INDEX IF NOT EXISTS idx_audio_session ON audio_files(session_id);
CREATE INDEX IF NOT EXISTS idx_recording_user ON recording_sessions(user_id);
