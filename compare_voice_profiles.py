import librosa
import numpy as np
import sys


# --------------------------------
# Check Command-Line Arguments
# --------------------------------

if len(sys.argv) != 3:
    print()
    print("Usage:")
    print(
        "python compare_voice_profiles.py "
        "<voice1.wav> <voice2.wav>"
    )
    print()
    sys.exit(1)


VOICE_1 = sys.argv[1]
VOICE_2 = sys.argv[2]


# --------------------------------
# Generate Voice Profile
# --------------------------------

def generate_voice_profile(audio_file):

    audio, sample_rate = librosa.load(
        audio_file,
        sr=16000
    )

    # Pitch
    pitch, voiced_flag, voiced_probs = librosa.pyin(
        audio,
        fmin=50,
        fmax=500
    )

    average_pitch = np.nanmean(pitch)

    # Energy
    energy = np.mean(audio ** 2)

    # Zero Crossing Rate
    zcr = np.mean(
        librosa.feature.zero_crossing_rate(audio)
    )

    # Spectral Centroid
    spectral_centroid = np.mean(
        librosa.feature.spectral_centroid(
            y=audio,
            sr=sample_rate
        )
    )

    # Spectral Bandwidth
    spectral_bandwidth = np.mean(
        librosa.feature.spectral_bandwidth(
            y=audio,
            sr=sample_rate
        )
    )

    # MFCC
    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=sample_rate,
        n_mfcc=13
    )

    mfcc_mean = np.mean(mfcc, axis=1)

    return {
        "pitch": average_pitch,
        "energy": energy,
        "zcr": zcr,
        "spectral_centroid": spectral_centroid,
        "spectral_bandwidth": spectral_bandwidth,
        "mfcc": mfcc_mean
    }


# --------------------------------
# Similarity Function
# --------------------------------

def calculate_similarity(value1, value2):

    difference = abs(value1 - value2)

    maximum = max(
        abs(value1),
        abs(value2),
        1e-10
    )

    similarity = 1 - (difference / maximum)

    return max(0, similarity)


# --------------------------------
# Generate Profiles
# --------------------------------

print("Loading first voice...")
profile1 = generate_voice_profile(VOICE_1)

print("First voice profile generated!")

print("Loading second voice...")
profile2 = generate_voice_profile(VOICE_2)

print("Second voice profile generated!")


# --------------------------------
# Compare Features
# --------------------------------

pitch_similarity = calculate_similarity(
    profile1["pitch"],
    profile2["pitch"]
)

energy_similarity = calculate_similarity(
    profile1["energy"],
    profile2["energy"]
)

zcr_similarity = calculate_similarity(
    profile1["zcr"],
    profile2["zcr"]
)

centroid_similarity = calculate_similarity(
    profile1["spectral_centroid"],
    profile2["spectral_centroid"]
)

bandwidth_similarity = calculate_similarity(
    profile1["spectral_bandwidth"],
    profile2["spectral_bandwidth"]
)


# --------------------------------
# MFCC Similarity
# --------------------------------

mfcc_distance = np.linalg.norm(
    profile1["mfcc"] - profile2["mfcc"]
)

mfcc_similarity = 1 / (
    1 + mfcc_distance / 100
)


# --------------------------------
# Overall Similarity
# --------------------------------

overall_similarity = (
    pitch_similarity * 0.15 +
    energy_similarity * 0.10 +
    zcr_similarity * 0.10 +
    centroid_similarity * 0.15 +
    bandwidth_similarity * 0.10 +
    mfcc_similarity * 0.40
)


overall_percentage = overall_similarity * 100


# --------------------------------
# Display Results
# --------------------------------

print()
print("----------------------------------------")
print("       SECUREVOICE AI")
print("    VOICE PROFILE COMPARISON")
print("----------------------------------------")

print(
    f"Voice 1: {VOICE_1}"
)

print(
    f"Voice 2: {VOICE_2}"
)

print()

print(
    f"Pitch similarity:          "
    f"{pitch_similarity * 100:.2f}%"
)

print(
    f"Energy similarity:         "
    f"{energy_similarity * 100:.2f}%"
)

print(
    f"ZCR similarity:            "
    f"{zcr_similarity * 100:.2f}%"
)

print(
    f"Spectral centroid:         "
    f"{centroid_similarity * 100:.2f}%"
)

print(
    f"Spectral bandwidth:        "
    f"{bandwidth_similarity * 100:.2f}%"
)

print(
    f"MFCC similarity:           "
    f"{mfcc_similarity * 100:.2f}%"
)

print("----------------------------------------")

print(
    f"Overall similarity:        "
    f"{overall_percentage:.2f}%"
)

if overall_percentage >= 70:
    print("Voice characteristics: SIMILAR")
else:
    print("Voice characteristics: DIFFERENT")

print("----------------------------------------")