import torch
import soundfile as sf

from speechbrain.inference.speaker import SpeakerRecognition


# --------------------------------------------------
# 1. Load the speaker recognition model
# --------------------------------------------------

print("Loading speaker recognition model...")

verification = SpeakerRecognition.from_hparams(
    source="models/ecapa"
)

print("Model loaded successfully!")


# --------------------------------------------------
# 2. Function to load audio
# --------------------------------------------------

def load_audio(path):

    audio, sample_rate = sf.read(path)

    # Convert stereo audio to mono
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    # Convert NumPy array to PyTorch tensor
    audio = torch.tensor(audio, dtype=torch.float32)

    # Resample to 16 kHz if required
    if sample_rate != 16000:

        audio = torch.nn.functional.interpolate(
            audio.unsqueeze(0).unsqueeze(0),
            size=int(len(audio) * 16000 / sample_rate),
            mode="linear",
            align_corners=False
        ).squeeze()

    return audio


# --------------------------------------------------
# 3. Register a voice
# --------------------------------------------------

print("Loading registration voice...")

voice = load_audio("Data/raw/voice1.wav")

print("Voice loaded successfully!")


# --------------------------------------------------
# 4. Generate voice embedding
# --------------------------------------------------

print("Generating voice profile...")

embedding = verification.encode_batch(
    voice.unsqueeze(0)
)

print("Voice profile generated successfully!")


# --------------------------------------------------
# 5. Save the voice profile
# --------------------------------------------------

profile_path = "voice_profiles/parvez_voice.pt"

torch.save(
    embedding,
    profile_path
)

print("Voice profile saved successfully!")


# --------------------------------------------------
# 6. Registration complete
# --------------------------------------------------

print()
print("--------------------------------")
print("      SECUREVOICE AI")
print("--------------------------------")
print("Voice registration successful!")
print(f"Profile saved at: {profile_path}")
print("--------------------------------")