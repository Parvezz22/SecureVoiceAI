import os
import sys
import torch
import torchaudio
import torchcodec


# ============================================================
# SECUREVOICE AI
# VOICE ENROLLMENT ENGINE
# ============================================================

MODEL_PATH = "models/ecapa"
PROFILE_DIRECTORY = "voice_profiles"

TARGET_SAMPLE_RATE = 16000


# ============================================================
# PREPARE AUDIO
# ============================================================

def prepare_audio(voice_path):

    print("Loading enrollment voice...")

    try:

        audio, sample_rate = torchaudio.load(
            voice_path
        )

    except Exception as e:

        raise RuntimeError(
            f"Could not load audio file: {e}"
        )

    print("Enrollment voice loaded successfully!")

    print(
        f"Original sample rate: {sample_rate} Hz"
    )

    # --------------------------------------------------------
    # Convert stereo to mono
    # --------------------------------------------------------

    if audio.shape[0] > 1:

        print(
            f"Converting {audio.shape[0]} "
            "audio channels to mono..."
        )

        audio = torch.mean(
            audio,
            dim=0,
            keepdim=True
        )

        print("Mono conversion completed!")

    # --------------------------------------------------------
    # Resample
    # --------------------------------------------------------

    if sample_rate != TARGET_SAMPLE_RATE:

        print(
            f"Resampling audio from "
            f"{sample_rate} Hz to "
            f"{TARGET_SAMPLE_RATE} Hz..."
        )

        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate,
            new_freq=TARGET_SAMPLE_RATE
        )

        audio = resampler(audio)

        sample_rate = TARGET_SAMPLE_RATE

        print("Resampling completed!")

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if audio.numel() == 0:

        raise RuntimeError(
            "Audio file contains no usable audio data."
        )

    print("Audio prepared successfully!")

    print(
        f"Final sample rate: {sample_rate} Hz"
    )

    print(
        f"Audio shape: {audio.shape}"
    )

    return audio


# ============================================================
# LOAD SPEAKER MODEL
# ============================================================

def load_model():

    print("\nLoading speaker recognition model...")

    # Import SpeechBrain only after TorchCodec
    # and Torchaudio have been initialized.

    from speechbrain.inference.speaker import (
        SpeakerRecognition
    )

    verification = SpeakerRecognition.from_hparams(
        source=MODEL_PATH,
        savedir=MODEL_PATH
    )

    print("Model loaded successfully!")

    return verification


# ============================================================
# GENERATE VOICE EMBEDDING
# ============================================================

def generate_embedding(
    verification,
    audio
):

    print("\nGenerating voice embedding...")

    with torch.no_grad():

        embedding = verification.encode_batch(
            audio
        )

    print(
        "Voice embedding generated successfully!"
    )

    print(
        f"Embedding shape: {embedding.shape}"
    )

    print(
        f"Embedding dtype: {embedding.dtype}"
    )

    return embedding


# ============================================================
# SAVE VOICE PROFILE
# ============================================================

def save_profile(
    embedding,
    username
):

    # --------------------------------------------------------
    # Create profile directory if it doesn't exist
    # --------------------------------------------------------

    os.makedirs(
        PROFILE_DIRECTORY,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Generate profile filename
    # --------------------------------------------------------

    profile_path = os.path.join(
        PROFILE_DIRECTORY,
        f"{username}_voice.pt"
    )

    # --------------------------------------------------------
    # Save embedding
    # --------------------------------------------------------

    torch.save(
        embedding.cpu(),
        profile_path
    )

    return profile_path


# ============================================================
# MAIN ENROLLMENT PROCESS
# ============================================================

def main():

    # --------------------------------------------------------
    # Check arguments
    # --------------------------------------------------------

    if len(sys.argv) < 3:

        print("\nUsage:")

        print(
            "python enrollment_engine.py "
            "<username> <voice_file>"
        )

        print("\nExample:")

        print(
            "python enrollment_engine.py "
            "parvez Data/raw/voice1.wav"
        )

        sys.exit(1)

    username = sys.argv[1]

    voice_path = sys.argv[2]

    # --------------------------------------------------------
    # Basic username validation
    # --------------------------------------------------------

    if not username.strip():

        print("ERROR: Username cannot be empty.")

        sys.exit(1)

    try:

        print("\n")
        print("----------------------------------------")
        print("          SECUREVOICE AI")
        print("          VOICE ENROLLMENT")
        print("----------------------------------------")

        print(
            f"User: {username}"
        )

        print(
            f"Voice file: {voice_path}"
        )

        # ----------------------------------------------------
        # Prepare audio
        # ----------------------------------------------------

        audio = prepare_audio(
            voice_path
        )

        # ----------------------------------------------------
        # Load model
        # ----------------------------------------------------

        verification = load_model()

        # ----------------------------------------------------
        # Generate embedding
        # ----------------------------------------------------

        embedding = generate_embedding(
            verification,
            audio
        )

        # ----------------------------------------------------
        # Save profile
        # ----------------------------------------------------

        print("\nSaving voice profile...")

        profile_path = save_profile(
            embedding,
            username
        )

        print(
            "Voice profile saved successfully!"
        )

        # ----------------------------------------------------
        # Verify saved profile
        # ----------------------------------------------------

        saved_embedding = torch.load(
            profile_path,
            map_location="cpu"
        )

        print(
            f"Saved profile shape: "
            f"{saved_embedding.shape}"
        )

        print(
            f"Saved profile dtype: "
            f"{saved_embedding.dtype}"
        )

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        print("\n")
        print("----------------------------------------")
        print("          ENROLLMENT SUCCESSFUL")
        print("----------------------------------------")

        print(
            f"User:          {username}"
        )

        print(
            f"Profile:       {profile_path}"
        )

        print(
            f"Embedding:     {saved_embedding.shape}"
        )

        print(
            "Status:        REGISTERED"
        )

        print("----------------------------------------")

    except Exception as e:

        print("\n")
        print("----------------------------------------")
        print("          SECUREVOICE AI")
        print("              ERROR")
        print("----------------------------------------")

        print(
            f"Error: {e}"
        )

        print("----------------------------------------")

        sys.exit(1)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()