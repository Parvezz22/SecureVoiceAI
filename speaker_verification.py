import torch
import soundfile as sf

from speechbrain.inference.speaker import SpeakerRecognition


# --------------------------------------------------
# 1. Load the pretrained speaker recognition model
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

    # Convert stereo → mono
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    # Convert NumPy → PyTorch tensor
    audio = torch.tensor(audio, dtype=torch.float32)

    # Resample to 16 kHz if necessary
    if sample_rate != 16000:

        audio = torch.nn.functional.interpolate(
            audio.unsqueeze(0).unsqueeze(0),
            size=int(len(audio) * 16000 / sample_rate),
            mode="linear",
            align_corners=False
        ).squeeze()

    return audio


# --------------------------------------------------
# 3. Load voice recordings
# --------------------------------------------------

print("Loading audio files...")

voice1 = load_audio("data/raw/voice1.wav")
voice2 = load_audio("data/raw/voice2.wav")

print("Audio files loaded successfully!")


# --------------------------------------------------
# 4. Extract voice embeddings
# --------------------------------------------------

print("Extracting voice embeddings...")

embedding1 = verification.encode_batch(
    voice1.unsqueeze(0)
)

embedding2 = verification.encode_batch(
    voice2.unsqueeze(0)
)

print("Voice embeddings extracted successfully!")


# --------------------------------------------------
# 5. Compare the voices
# --------------------------------------------------

print("Comparing voices...")

score = torch.nn.functional.cosine_similarity(
    embedding1,
    embedding2,
    dim=-1
)

similarity = score.item()


# --------------------------------------------------
# 6. Display result
# --------------------------------------------------

print()
print("--------------------------------")
print("      SECUREVOICE AI")
print("--------------------------------")

print(f"Similarity score: {similarity:.4f}")

if similarity >= 0.25:
    print("Same speaker: YES")
else:
    print("Same speaker: NO")

print("--------------------------------")