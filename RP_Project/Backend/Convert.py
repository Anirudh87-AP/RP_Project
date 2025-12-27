"""
Convert.py - Audio Conversion Functions
Handles MP3 to WAV conversion, metadata extraction, resampling, and channel conversion
"""

import os
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AudioConverter:
    """Audio conversion utilities"""
    
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.supported_formats = {'.mp3', '.wav', '.flac', '.ogg'}
    
    def convert_mp3_to_wav(self, input_path, output_path=None, sample_rate=None):
        """
        Convert MP3 file to WAV format
        
        Args:
            input_path (str): Path to input MP3 file
            output_path (str): Path to output WAV file (optional)
            sample_rate (int): Target sample rate (optional)
        
        Returns:
            dict: {
                'success': bool,
                'output_path': str,
                'sample_rate': int,
                'duration': float,
                'channels': int
            }
        """
        try:
            if sample_rate is None:
                sample_rate = self.sample_rate
            
            # Load audio file
            audio_data, sr = librosa.load(input_path, sr=sample_rate, mono=False)
            
            # Generate output path if not provided
            if output_path is None:
                base_name = Path(input_path).stem
                output_path = f"{base_name}.wav"
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # Save as WAV
            sf.write(output_path, audio_data.T if audio_data.ndim > 1 else audio_data, sr)
            
            # Get file info
            duration = librosa.get_duration(filename=output_path)
            channels = audio_data.ndim
            
            logger.info(f"Converted {input_path} to {output_path}")
            
            return {
                'success': True,
                'output_path': output_path,
                'sample_rate': sr,
                'duration': duration,
                'channels': channels
            }
        
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_audio_metadata(self, audio_path):
        """
        Extract metadata from audio file
        
        Args:
            audio_path (str): Path to audio file
        
        Returns:
            dict: {
                'duration': float (seconds),
                'sample_rate': int,
                'channels': int,
                'format': str,
                'file_size': int (bytes)
            }
        """
        try:
            # Get file size
            file_size = os.path.getsize(audio_path)
            
            # Get file format
            file_format = Path(audio_path).suffix[1:].lower()
            
            # Load audio to get metadata
            audio_data, sr = librosa.load(audio_path, sr=None)
            
            # Get duration
            duration = librosa.get_duration(y=audio_data, sr=sr)
            
            # Get channels (mono = 1, stereo = 2)
            channels = 1 if audio_data.ndim == 1 else audio_data.shape[0]
            
            logger.info(f"Metadata extracted for {audio_path}")
            
            return {
                'duration': duration,
                'sample_rate': sr,
                'channels': channels,
                'format': file_format,
                'file_size': file_size
            }
        
        except Exception as e:
            logger.error(f"Metadata extraction error: {str(e)}")
            return {
                'error': str(e)
            }
    
    def resample_audio(self, input_path, target_sr=16000, output_path=None):
        """
        Resample audio to target sample rate
        
        Args:
            input_path (str): Path to input audio file
            target_sr (int): Target sample rate
            output_path (str): Path to output file (optional)
        
        Returns:
            dict: {
                'success': bool,
                'output_path': str,
                'original_sr': int,
                'target_sr': int
            }
        """
        try:
            # Load audio
            audio_data, original_sr = librosa.load(input_path, sr=None)
            
            if original_sr == target_sr:
                return {
                    'success': True,
                    'message': 'Audio already at target sample rate',
                    'original_sr': original_sr,
                    'target_sr': target_sr
                }
            
            # Resample
            resampled = librosa.resample(audio_data, orig_sr=original_sr, target_sr=target_sr)
            
            # Generate output path if not provided
            if output_path is None:
                base_name = Path(input_path).stem
                output_path = f"{base_name}_resampled.wav"
            
            # Save resampled audio
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            sf.write(output_path, resampled, target_sr)
            
            logger.info(f"Resampled {input_path} from {original_sr} to {target_sr}")
            
            return {
                'success': True,
                'output_path': output_path,
                'original_sr': original_sr,
                'target_sr': target_sr
            }
        
        except Exception as e:
            logger.error(f"Resampling error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def convert_stereo_to_mono(self, input_path, output_path=None, method='average'):
        """
        Convert stereo audio to mono
        
        Args:
            input_path (str): Path to input audio file
            output_path (str): Path to output file (optional)
            method (str): 'average' (default) or 'left' or 'right'
        
        Returns:
            dict: {
                'success': bool,
                'output_path': str,
                'original_channels': int,
                'method': str
            }
        """
        try:
            # Load audio
            audio_data, sr = librosa.load(input_path, sr=None, mono=False)
            
            # Check if already mono
            if audio_data.ndim == 1:
                return {
                    'success': True,
                    'message': 'Audio already mono',
                    'original_channels': 1
                }
            
            original_channels = audio_data.shape[0]
            
            # Convert based on method
            if method == 'average':
                mono_audio = np.mean(audio_data, axis=0)
            elif method == 'left':
                mono_audio = audio_data[0]
            elif method == 'right':
                mono_audio = audio_data[1]
            else:
                return {
                    'success': False,
                    'error': f"Unknown method: {method}"
                }
            
            # Generate output path if not provided
            if output_path is None:
                base_name = Path(input_path).stem
                output_path = f"{base_name}_mono.wav"
            
            # Save mono audio
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            sf.write(output_path, mono_audio, sr)
            
            logger.info(f"Converted {input_path} from stereo to mono using {method}")
            
            return {
                'success': True,
                'output_path': output_path,
                'original_channels': original_channels,
                'method': method
            }
        
        except Exception as e:
            logger.error(f"Stereo to mono conversion error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Convenience functions
def convert_mp3_to_wav(input_path, output_path=None):
    """Convenience function for MP3 to WAV conversion"""
    converter = AudioConverter()
    return converter.convert_mp3_to_wav(input_path, output_path)

def get_audio_metadata(audio_path):
    """Convenience function to get audio metadata"""
    converter = AudioConverter()
    return converter.get_audio_metadata(audio_path)

def resample_audio(input_path, target_sr=16000, output_path=None):
    """Convenience function for audio resampling"""
    converter = AudioConverter()
    return converter.resample_audio(input_path, target_sr, output_path)

def convert_stereo_to_mono(input_path, output_path=None, method='average'):
    """Convenience function for stereo to mono conversion"""
    converter = AudioConverter()
    return converter.convert_stereo_to_mono(input_path, output_path, method)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test conversion
    converter = AudioConverter()
    result = converter.get_audio_metadata('test_audio.mp3')
    print("Audio metadata:", result)
