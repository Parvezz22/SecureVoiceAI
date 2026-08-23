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
# 2. Audio loading function
# --------------------------------------------------

def load_audio(path):

    audio, sample_rate = sf.read(path)

    # Convert stereo to mono
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    audio = torch.tensor(
        audio,
        dtype=torch.float32
    )

    # Resample to 16 kHz
    if sample_rate != 16000:

        new_length = int(
            len(audio) * 16000 / sample_rate
        )

        audio = torch.nn.functional.interpolate(
            audio.unsqueeze(0).unsqueeze(0),
            size=new_length,
            mode="linear",
            align_corners=False
        ).squeeze()

    return audio


# --------------------------------------------------
# 3. Load registered voice profile
# --------------------------------------------------

print("Loading registered voice profile...")

registered_embedding = torch.load(
    "voice_profiles/parvez_voice.pt",
    weights_only=True
)

print("Registered voice profile loaded!")


# --------------------------------------------------
# 4. Load unknown voice
# --------------------------------------------------

print("Loading unknown voice...")

unknown_voice = load_audio(
    "Data/raw/unknown_voice.wav"
)

print("Unknown voice loaded successfully!")


# --------------------------------------------------
# 5. Generate embedding
# --------------------------------------------------

print("Generating unknown voice embedding...")

unknown_embedding = verification.encode_batch(
    unknown_voice.unsqueeze(0)
)

print("Unknown voice embedding generated!")


# --------------------------------------------------
# 6. Compare voices
# --------------------------------------------------

print("Comparing registered voice with unknown voice...")

score = torch.nn.functional.cosine_similarity(
    registered_embedding.squeeze(),
    unknown_embedding.squeeze(),
    dim=0
).item()


# --------------------------------------------------
# 7. Authentication decision
# --------------------------------------------------

threshold = 0.60

is_match = score >= threshold


# --------------------------------------------------
# 8. Display result
# --------------------------------------------------

print()
print("--------------------------------")
print("       SECUREVOICE AI")
print("--------------------------------")

print(f"Similarity score: {score:.4f}")
print(f"Threshold: {threshold:.2f}")

if is_match:

    print("Authentication: SUCCESS")
    print("Same speaker: YES")

else:

    print("Authentication: FAILED")
    print("Same speaker: NO")

print("--------------------------------")