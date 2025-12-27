/**
 * main.js - Speech Enhancement System Frontend
 * Handles all user interactions, API calls, and UI updates
 */

// ============================================================================
// GLOBAL STATE
// ============================================================================

const appState = {
    currentFile: null,
    currentFileId: null,
    currentJobId: null,
    recordingData: null,
    recordingDuration: 0,
    isRecording: false
};

const API_BASE = 'http://localhost:5000';

// ============================================================================
// DOM ELEMENTS
// ============================================================================

const elements = {
    // Navigation
    navLinks: document.querySelectorAll('.nav-link'),
    
    // Upload Section
    fileInput: document.getElementById('file-input'),
    selectFileBtn: document.getElementById('select-file-btn'),
    uploadBox: document.querySelector('.upload-box'),
    fileInfo: document.getElementById('file-info'),
    clearFileBtn: document.getElementById('clear-file-btn'),
    
    // File Info Display
    fileName: document.getElementById('file-name'),
    fileSize: document.getElementById('file-size'),
    fileFormat: document.getElementById('file-format'),
    fileDuration: document.getElementById('file-duration'),
    
    // Record Section
    startRecordingBtn: document.getElementById('start-recording-btn'),
    stopRecordingBtn: document.getElementById('stop-recording-btn'),
    recordingTimer: document.getElementById('recording-timer'),
    recordingInfo: document.getElementById('recording-info'),
    recordedAudio: document.getElementById('recorded-audio'),
    saveRecordingBtn: document.getElementById('save-recording-btn'),
    
    // Processing Section
    processBtn: document.getElementById('process-btn'),
    progressContainer: document.getElementById('progress-container'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),
    statusMessage: document.getElementById('status-message'),
    
    // Results Section
    resultsContainer: document.getElementById('results-container'),
    originalAudio: document.getElementById('original-audio'),
    enhancedAudio: document.getElementById('enhanced-audio'),
    downloadBtn: document.getElementById('download-btn'),
    
    // Metrics Display
    metrics: {
        signalPower: document.getElementById('metric-signal-power'),
        noisePower: document.getElementById('metric-noise-power'),
        snrInput: document.getElementById('metric-snr-input'),
        wienerGain: document.getElementById('metric-wiener-gain'),
        spectralSub: document.getElementById('metric-spectral-sub'),
        spectralDist: document.getElementById('metric-spectral-dist'),
        segmentalSnr: document.getElementById('metric-segmental-snr'),
        duration: document.getElementById('metric-duration')
    }
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded. Initializing app...');
    
    // Setup event listeners
    setupNavigationListeners();
    setupFileUploadListeners();
    setupRecordingListeners();
    setupProcessingListeners();
    setupDownloadListeners();
    
    console.log('App initialized successfully');
});

// ============================================================================
// NAVIGATION
// ============================================================================

function setupNavigationListeners() {
    elements.navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const tabName = link.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active from all nav links
    elements.navLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected section
    const section = document.querySelector(`[data-section="${tabName}"]`);
    if (section) {
        section.classList.add('active');
    }
    
    // Mark nav link as active
    const link = document.querySelector(`[data-tab="${tabName}"]`);
    if (link) {
        link.classList.add('active');
    }
}

// ============================================================================
// FILE UPLOAD
// ============================================================================

function setupFileUploadListeners() {
    // Select file button
    elements.selectFileBtn.addEventListener('click', () => {
        elements.fileInput.click();
    });
    
    // File input change
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    elements.uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadBox.style.borderColor = 'var(--color-primary-dark)';
    });
    
    elements.uploadBox.addEventListener('dragleave', () => {
        elements.uploadBox.style.borderColor = 'var(--color-primary)';
    });
    
    elements.uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadBox.style.borderColor = 'var(--color-primary)';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            elements.fileInput.files = files;
            handleFileSelect();
        }
    });
    
    // Clear file button
    elements.clearFileBtn.addEventListener('click', clearFile);
}

function handleFileSelect() {
    const file = elements.fileInput.files[0];
    if (!file) return;
    
    appState.currentFile = file;
    displayFileInfo(file);
    uploadFile(file);
}

function displayFileInfo(file) {
    // Show file info
    elements.fileInfo.classList.remove('hidden');
    
    // Format file size
    const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
    
    // Get file extension
    const extension = file.name.split('.').pop().toUpperCase();
    
    // Update display
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = `${fileSizeMB} MB`;
    elements.fileFormat.textContent = extension;
    
    // Try to get duration
    getAudioDuration(file);
}

function getAudioDuration(file) {
    const url = URL.createObjectURL(file);
    const audio = new Audio();
    
    audio.addEventListener('loadedmetadata', () => {
        const duration = Math.floor(audio.duration);
        elements.fileDuration.textContent = `${duration} seconds`;
    });
    
    audio.src = url;
}

function clearFile() {
    appState.currentFile = null;
    appState.currentFileId = null;
    elements.fileInput.value = '';
    elements.fileInfo.classList.add('hidden');
    elements.processBtn.disabled = true;
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_name', `upload_${Date.now()}`);
    
    try {
        showStatusMessage('Uploading file...', 'info');
        
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            appState.currentFileId = data.file_id;
            elements.processBtn.disabled = false;
            showStatusMessage('File uploaded successfully!', 'success');
            console.log('File uploaded:', data);
        } else {
            showStatusMessage(`Upload failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatusMessage('Upload failed. Please try again.', 'error');
    }
}

// ============================================================================
// RECORDING
// ============================================================================

let mediaRecorder;
let audioChunks = [];

function setupRecordingListeners() {
    elements.startRecordingBtn.addEventListener('click', startRecording);
    elements.stopRecordingBtn.addEventListener('click', stopRecording);
    elements.saveRecordingBtn.addEventListener('click', saveRecording);
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        appState.recordingDuration = 0;
        
        mediaRecorder.addEventListener('dataavailable', (e) => {
            audioChunks.push(e.data);
        });
        
        mediaRecorder.addEventListener('stop', () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            elements.recordedAudio.src = audioUrl;
            elements.recordingInfo.classList.remove('hidden');
            
            appState.recordingData = audioBlob;
        });
        
        mediaRecorder.start();
        
        // Update UI
        elements.startRecordingBtn.classList.add('hidden');
        elements.stopRecordingBtn.classList.remove('hidden');
        elements.recordingTimer.classList.remove('hidden');
        
        // Start timer
        startRecordingTimer();
        
    } catch (error) {
        console.error('Recording error:', error);
        showStatusMessage('Failed to start recording. Please check microphone permissions.', 'error');
    }
}

function stopRecording() {
    if (mediaRecorder) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    
    elements.startRecordingBtn.classList.remove('hidden');
    elements.stopRecordingBtn.classList.add('hidden');
    elements.recordingTimer.classList.add('hidden');
}

let recordingInterval;
function startRecordingTimer() {
    recordingInterval = setInterval(() => {
        appState.recordingDuration++;
        const minutes = Math.floor(appState.recordingDuration / 60);
        const seconds = appState.recordingDuration % 60;
        elements.recordingTimer.textContent = 
            `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }, 1000);
}

async function saveRecording() {
    if (!appState.recordingData) {
        showStatusMessage('No recording found', 'error');
        return;
    }
    
    // Convert blob to base64
    const reader = new FileReader();
    reader.readAsDataURL(appState.recordingData);
    
    reader.onload = async () => {
        try {
            showStatusMessage('Saving recording...', 'info');
            
            const response = await fetch(`${API_BASE}/record/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    recording_id: `rec_${Date.now()}`,
                    audio_data: reader.result
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                appState.currentFileId = data.file_id;
                elements.processBtn.disabled = false;
                showStatusMessage('Recording saved successfully!', 'success');
                console.log('Recording saved:', data);
                
                // Clear recording
                setTimeout(() => {
                    elements.recordingInfo.classList.add('hidden');
                    appState.recordingData = null;
                }, 2000);
            } else {
                showStatusMessage(`Save failed: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Save error:', error);
            showStatusMessage('Failed to save recording', 'error');
        }
    };
}

// ============================================================================
// PROCESSING
// ============================================================================

function setupProcessingListeners() {
    elements.processBtn.addEventListener('click', startProcessing);
}

async function startProcessing() {
    if (!appState.currentFileId) {
        showStatusMessage('Please upload or record audio first', 'error');
        return;
    }
    
    try {
        showStatusMessage('Starting audio processing...', 'info');
        elements.progressContainer.classList.remove('hidden');
        elements.processBtn.disabled = true;
        
        const response = await fetch(`${API_BASE}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: appState.currentFileId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            appState.currentJobId = data.job_id;
            showStatusMessage('Processing in progress...', 'info');
            
            // Poll for status
            pollProcessingStatus(data.job_id);
        } else {
            showStatusMessage(`Processing failed: ${data.error}`, 'error');
            elements.processBtn.disabled = false;
        }
    } catch (error) {
        console.error('Processing error:', error);
        showStatusMessage('Failed to start processing', 'error');
        elements.processBtn.disabled = false;
    }
}

async function pollProcessingStatus(jobId) {
    const maxAttempts = 30;
    let attempts = 0;
    
    const poll = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/process/${jobId}/status`);
            const data = await response.json();
            
            if (response.ok) {
                // Update progress
                const progress = data.progress || 0;
                elements.progressFill.style.width = `${progress}%`;
                elements.progressText.textContent = `${progress}%`;
                
                // Check if completed
                if (data.status === 'completed') {
                    clearInterval(poll);
                    showStatusMessage('Processing completed!', 'success');
                    
                    // Get results
                    setTimeout(() => getProcessingResults(jobId), 500);
                } else if (data.status === 'failed') {
                    clearInterval(poll);
                    showStatusMessage(`Processing failed: ${data.error_message}`, 'error');
                    elements.processBtn.disabled = false;
                }
            }
            
            attempts++;
            if (attempts >= maxAttempts) {
                clearInterval(poll);
                showStatusMessage('Processing timeout', 'error');
                elements.processBtn.disabled = false;
            }
        } catch (error) {
            console.error('Status check error:', error);
            attempts++;
        }
    }, 500);
}

async function getProcessingResults(jobId) {
    try {
        const response = await fetch(`${API_BASE}/results/${jobId}`);
        const data = response.json();
        
        if (response.ok) {
            displayResults(data);
            switchTab('results');
        } else {
            showStatusMessage('Failed to fetch results', 'error');
        }
    } catch (error) {
        console.error('Results error:', error);
        showStatusMessage('Failed to load results', 'error');
    }
}

function displayResults(data) {
    // Show results container
    elements.resultsContainer.classList.remove('hidden');
    elements.progressContainer.classList.add('hidden');
    
    // Update metrics
    if (data.metrics) {
        elements.metrics.signalPower.textContent = data.metrics.signal_power;
        elements.metrics.noisePower.textContent = data.metrics.noise_power;
        elements.metrics.snrInput.textContent = data.metrics.snr_input;
        elements.metrics.wienerGain.textContent = data.metrics.wiener_filter_gain;
        elements.metrics.spectralSub.textContent = data.metrics.spectral_subtraction_factor;
        elements.metrics.spectralDist.textContent = data.metrics.spectral_distance;
        elements.metrics.segmentalSnr.textContent = data.metrics.segmental_snr;
        elements.metrics.duration.textContent = `${data.metrics.processing_duration}s`;
    }
    
    // Mock audio sources (in production, use actual files)
    // elements.originalAudio.src = '/path/to/original.wav';
    // elements.enhancedAudio.src = '/path/to/enhanced.wav';
    
    console.log('Results displayed:', data);
}

// ============================================================================
// DOWNLOAD
// ============================================================================

function setupDownloadListeners() {
    elements.downloadBtn.addEventListener('click', downloadEnhancedAudio);
}

function downloadEnhancedAudio() {
    if (!appState.currentFileId) {
        showStatusMessage('No file to download', 'error');
        return;
    }
    
    // In production, construct actual download URL
    const downloadUrl = `${API_BASE}/download/${appState.currentFileId}`;
    
    try {
        fetch(downloadUrl)
            .then(response => response.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'enhanced_audio.wav';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                showStatusMessage('Download started!', 'success');
            });
    } catch (error) {
        console.error('Download error:', error);
        showStatusMessage('Download failed', 'error');
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showStatusMessage(message, type = 'info') {
    elements.statusMessage.textContent = message;
    elements.statusMessage.className = `status-message ${type}`;
    elements.statusMessage.classList.remove('hidden');
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        elements.statusMessage.classList.add('hidden');
    }, 3000);
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    showStatusMessage('An error occurred. Please refresh the page.', 'error');
});

// ============================================================================
// LOGGING
// ============================================================================

console.log('Speech Enhancement System Frontend - Loaded');
