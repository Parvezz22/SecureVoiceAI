import librosa
import numpy as np


# --------------------------------------------------
# 1. Load audio
# --------------------------------------------------

print("Loading audio...")

audio_path = "Data/raw/voice1.wav"

audio, sample_rate = librosa.load(
    audio_path,
    sr=16000
)

print("Audio loaded successfully!")


# --------------------------------------------------
# 2. Basic audio information
# --------------------------------------------------

duration = librosa.get_duration(
    y=audio,
    sr=sample_rate
)


# --------------------------------------------------
# 3. Pitch estimation
# --------------------------------------------------

f0, voiced_flag, voiced_probs = librosa.pyin(
    audio,
    fmin=librosa.note_to_hz("C2"),
    fmax=librosa.note_to_hz("C7")
)

valid_pitch = f0[~np.isnan(f0)]

if len(valid_pitch) > 0:
    average_pitch = np.mean(valid_pitch)
else:
    average_pitch = 0


# --------------------------------------------------
# 4. Energy
# --------------------------------------------------

rms = librosa.feature.rms(
    y=audio
)

average_energy = np.mean(rms)


# --------------------------------------------------
# 5. Zero Crossing Rate
# --------------------------------------------------

zcr = librosa.feature.zero_crossing_rate(
    audio
)

average_zcr = np.mean(zcr)


# --------------------------------------------------
# 6. Spectral Centroid
# --------------------------------------------------

spectral_centroid = librosa.feature.spectral_centroid(
    y=audio,
    sr=sample_rate
)

average_centroid = np.mean(
    spectral_centroid
)


# --------------------------------------------------
# 7. Spectral Bandwidth
# --------------------------------------------------

spectral_bandwidth = librosa.feature.spectral_bandwidth(
    y=audio,
    sr=sample_rate
)

average_bandwidth = np.mean(
    spectral_bandwidth
)


# --------------------------------------------------
# 8. MFCC features
# --------------------------------------------------

mfcc = librosa.feature.mfcc(
    y=audio,
    sr=sample_rate,
    n_mfcc=13
)

average_mfcc = np.mean(
    mfcc,
    axis=1
)


# --------------------------------------------------
# 9. Display results
# --------------------------------------------------

print()
print("----------------------------------------")
print("          SECUREVOICE AI")
print("          VOICE ANALYSIS")
print("----------------------------------------")

print(f"Duration:              {duration:.2f} seconds")
print(f"Sample Rate:           {sample_rate} Hz")
print(f"Average Pitch:         {average_pitch:.2f} Hz")
print(f"Average Energy:        {average_energy:.6f}")
print(f"Zero Crossing Rate:    {average_zcr:.6f}")
print(f"Spectral Centroid:     {average_centroid:.2f} Hz")
print(f"Spectral Bandwidth:     {average_bandwidth:.2f} Hz")

print()
print("MFCC Features:")

for i, value in enumerate(average_mfcc):
    print(f"MFCC {i + 1:02d}:             {value:.4f}")

print("----------------------------------------")