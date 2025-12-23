import streamlit as st
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import sounddevice as sd
import soundfile as sf
import audiofile as audio
from scipy.signal import stft, istft

import base64

def set_white_text():
    st.markdown(
        """
        <style>
        /* Main text */
        html, body, [class*="css"] {
            color: white !important;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: white !important;
        }

        /* Sidebar */
        .stSidebar, .stSidebar * {
            color: white !important;
        }

        /* Radio buttons, sliders, labels */
        label, span, div {
            color: white !important;
        }

        /* Metrics */
        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"] {
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def set_bg(img_file):
    with open(img_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg(r"C:\Users\nhkai\OneDrive\Desktop\C++\bg.jpg")
set_white_text()

# -----------------------------
# Utility Functions
# -----------------------------
def record_audio(duration, fs):
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    return audio.flatten()

def compute_snr(clean, processed):
    noise = clean - processed
    return 10 * np.log10(np.sum(clean**2) / np.sum(noise**2))

def adaptive_wiener(noisy_signal, fs, alpha=0.98):
    n_fft = 1024
    hop = n_fft // 2

    f, t, noisy_stft = stft(noisy_signal, fs, nperseg=n_fft, noverlap=hop)

    noise_psd = np.mean(np.abs(noisy_stft[:, :5])**2, axis=1, keepdims=True)
    enhanced_stft = np.zeros_like(noisy_stft)

    for k in range(noisy_stft.shape[1]):
        current_psd = np.abs(noisy_stft[:, k:k+1])**2

        # Adaptive noise update
        noise_psd = alpha * noise_psd + (1 - alpha) * current_psd

        speech_psd = np.maximum(current_psd - noise_psd, 1e-10)
        H = speech_psd / (speech_psd + noise_psd)

        enhanced_stft[:, k:k+1] = H * noisy_stft[:, k:k+1]

    _, enhanced_signal = istft(enhanced_stft, fs, nperseg=n_fft, noverlap=hop)
    enhanced_signal = enhanced_signal / np.max(np.abs(enhanced_signal))

    return enhanced_signal, noisy_stft, enhanced_stft

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Advanced Speech Enhancement", layout="wide")

st.title("🎧 Adaptive Speech Enhancement using Random Process Theory")
st.write("Live Input | Adaptive Wiener Filtering | Communication Systems")

input_mode = st.radio("Select Input Mode", ["Upload WAV File", "Live Microphone"])

fs = 16000

if input_mode == "Upload WAV File":
    uploaded_file = st.file_uploader("Upload clean speech (.wav)", type=["wav"])

    if uploaded_file is not None:
        speech, fs = librosa.load(uploaded_file, sr=None)
        speech = speech / np.max(np.abs(speech))
        noisy_speech = speech + 0.01 * np.random.randn(len(speech))

elif input_mode == "Live Microphone":
    duration = st.slider("Recording Duration (seconds)", 2, 10, 4)

    if st.button("🎙 Start Recording"):
        st.info("Recording...")
        noisy_speech = record_audio(duration, fs)
        noisy_speech = noisy_speech / np.max(np.abs(noisy_speech))
        speech = noisy_speech.copy()  # Reference unavailable in real-time
        st.success("Recording completed")

# -----------------------------
# Processing
# -----------------------------
if 'noisy_speech' in locals():

    st.subheader(" Adaptive Wiener Filtering")
    alpha = st.slider("Adaptation Factor (α)", 0.90, 0.999, 0.98)

    enhanced_speech, noisy_stft, enhanced_stft = adaptive_wiener(noisy_speech, fs, alpha)

    # Audio playback
    st.subheader(" Audio Output")
    st.audio(noisy_speech, sample_rate=fs)
    st.audio(enhanced_speech, sample_rate=fs)

    # Time-domain visualization
    fig, ax = plt.subplots()
    ax.plot(noisy_speech, label="Noisy")
    ax.plot(enhanced_speech, label="Enhanced", alpha=0.8)
    ax.legend()
    ax.set_title("Time Domain Signal")
    st.pyplot(fig)

    # Spectrograms
    st.subheader(" Spectrogram Comparison")

    fig, axs = plt.subplots(2, 1, figsize=(10, 6))

    librosa.display.specshow(
        librosa.amplitude_to_db(np.abs(noisy_stft)),
        sr=fs, y_axis='log', x_axis='time', ax=axs[0]
    )
    axs[0].set_title("Noisy Speech")

    librosa.display.specshow(
        librosa.amplitude_to_db(np.abs(enhanced_stft)),
        sr=fs, y_axis='log', x_axis='time', ax=axs[1]
    )
    axs[1].set_title("Enhanced Speech")

    plt.tight_layout()
    st.pyplot(fig)

    # Save output
    sf.write("adaptive_enhanced.wav", enhanced_speech, fs)
    with open("adaptive_enhanced.wav", "rb") as f:
        st.download_button("⬇ Download Enhanced Speech", f, "adaptive_enhanced.wav")
