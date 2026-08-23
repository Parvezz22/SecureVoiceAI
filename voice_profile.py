import librosa
import numpy as np
import json
import os


AUDIO_FILE = "Data/raw/voice1.wav"


print("Loading audio...")
audio, sample_rate = librosa.load(AUDIO_FILE, sr=16000)

print("Audio loaded successfully!")
print("Generating voice profile...")


# -----------------------------
# Basic Audio Information
# -----------------------------

duration = librosa.get_duration(y=audio, sr=sample_rate)


# -----------------------------
# Pitch
# -----------------------------

pitch, voiced_flag, voiced_probs = librosa.pyin(
    audio,
    fmin=50,
    fmax=500
)

average_pitch = np.nanmean(pitch)


# -----------------------------
# Energy
# -----------------------------

energy = np.mean(audio ** 2)


# -----------------------------
# Zero Crossing Rate
# -----------------------------

zcr = np.mean(librosa.feature.zero_crossing_rate(audio))


# -----------------------------
# Spectral Features
# -----------------------------

spectral_centroid = np.mean(
    librosa.feature.spectral_centroid(
        y=audio,
        sr=sample_rate
    )
)

spectral_bandwidth = np.mean(
    librosa.feature.spectral_bandwidth(
        y=audio,
        sr=sample_rate
    )
)


# -----------------------------
# MFCC
# -----------------------------

mfcc = librosa.feature.mfcc(
    y=audio,
    sr=sample_rate,
    n_mfcc=13
)

mfcc_mean = np.mean(mfcc, axis=1)


# -----------------------------
# Create Voice Profile
# -----------------------------

voice_profile = {
    "duration": float(duration),
    "sample_rate": int(sample_rate),
    "average_pitch": float(average_pitch),
    "energy": float(energy),
    "zero_crossing_rate": float(zcr),
    "spectral_centroid": float(spectral_centroid),
    "spectral_bandwidth": float(spectral_bandwidth),
    "mfcc": mfcc_mean.tolist()
}

# -----------------------------
# Save Voice Profile
# -----------------------------

profile_directory = "voice_profiles"

os.makedirs(profile_directory, exist_ok=True)

profile_path = os.path.join(
    profile_directory,
    "parvez_voice_profile.json"
)

with open(profile_path, "w") as file:
    json.dump(voice_profile, file, indent=4)

print()
print(f"Voice profile saved to: {profile_path}")


# -----------------------------
# Display Voice Profile
# -----------------------------

print()
print("----------------------------------------")
print("        SECUREVOICE AI")
print("          VOICE PROFILE")
print("----------------------------------------")

print(f"Duration:              {duration:.2f} seconds")
print(f"Sample Rate:           {sample_rate} Hz")
print(f"Average Pitch:         {average_pitch:.2f} Hz")
print(f"Average Energy:        {energy:.6f}")
print(f"Zero Crossing Rate:    {zcr:.6f}")
print(f"Spectral Centroid:     {spectral_centroid:.2f} Hz")
print(f"Spectral Bandwidth:    {spectral_bandwidth:.2f} Hz")

print()
print("MFCC Profile:")

for i, value in enumerate(mfcc_mean, start=1):
    print(f"MFCC {i:02d}:              {value:.4f}")

print("----------------------------------------")
print("Voice profile generated successfully!")
print("----------------------------------------")