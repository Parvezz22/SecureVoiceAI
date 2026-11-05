import os
import sys
import torch
import torchaudio
import torchcodec

from database import add_user


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

        audio, sample_rate = torchaudio.load(voice_path)

    except Exception as e:

        raise RuntimeError(
            f"Could not load audio file: {e}"
        )

    print("Enrollment voice loaded successfully!")

    print(f"Original sample rate: {sample_rate} Hz")

    # Convert stereo to mono
    if audio.shape[0] > 1:

        print("Converting audio to mono...")

        audio = torch.mean(
            audio,
            dim=0,
            keepdim=True
        )

        print("Mono conversion completed!")

    # Resample audio
    if sample_rate != TARGET_SAMPLE_RATE:

        print(
            f"Resampling audio from {sample_rate} Hz "
            f"to {TARGET_SAMPLE_RATE} Hz..."
        )

        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate,
            new_freq=TARGET_SAMPLE_RATE
        )

        audio = resampler(audio)

        sample_rate = TARGET_SAMPLE_RATE

        print("Resampling completed!")

    # Validate audio
    if audio.numel() == 0:

        raise RuntimeError(
            "Audio file contains no usable audio data."
        )

    print("Audio prepared successfully!")

    print(f"Final sample rate: {sample_rate} Hz")
    print(f"Audio shape: {audio.shape}")

    return audio


# ============================================================
# LOAD SPEAKER MODEL
# ============================================================

def load_model():

    print("\nLoading speaker recognition model...")

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

def generate_embedding(verification, audio):

    print("\nGenerating voice embedding...")

    with torch.no_grad():

        embedding = verification.encode_batch(audio)

    print("Voice embedding generated successfully!")

    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding dtype: {embedding.dtype}")

    return embedding


# ============================================================
# SAVE VOICE PROFILE
# ============================================================

def save_profile(embedding, username):

    os.makedirs(
        PROFILE_DIRECTORY,
        exist_ok=True
    )

    profile_path = os.path.join(
        PROFILE_DIRECTORY,
        f"{username}_voice.pt"
    )

    torch.save(
        embedding.cpu(),
        profile_path
    )

    return profile_path


# ============================================================
# REGISTER USER IN DATABASE
# ============================================================

def register_enrolled_user(username, profile_path):

    try:

        add_user(username)

        print(
            "User registered in database successfully!"
        )

    except Exception:

        # Remove profile if database registration fails
        if os.path.exists(profile_path):

            os.remove(profile_path)

        raise


# ============================================================
# REUSABLE ENROLLMENT FUNCTION FOR FASTAPI
# ============================================================

def enroll_voice(username, voice_path, verification):

    import re
    import time

    start_time = time.perf_counter()

    # Validate username
    if not re.fullmatch(
        r"[a-zA-Z0-9_-]{3,30}",
        username
    ):

        raise ValueError(
            "Username must be 3-30 characters and contain "
            "only letters, numbers, underscores or hyphens."
        )

    # Check audio file
    if not os.path.exists(voice_path):

        raise FileNotFoundError(
            f"Voice file not found: {voice_path}"
        )

    # Prevent duplicate enrollment
    profile_path = os.path.join(
        PROFILE_DIRECTORY,
        f"{username}_voice.pt"
    )

    if os.path.exists(profile_path):

        raise FileExistsError(
            f"User '{username}' is already enrolled."
        )

    # Prepare audio
    audio = prepare_audio(voice_path)

    # Generate embedding
    embedding = generate_embedding(
        verification,
        audio
    )

    # Save voice profile
    saved_path = save_profile(
        embedding,
        username
    )

    # Register user in SQLite
    register_enrolled_user(
        username,
        saved_path
    )

    processing_time = (
        time.perf_counter() - start_time
    )

    return {
        "username": username,
        "status": "ENROLLED",
        "profile": saved_path,
        "embedding_dimensions": embedding.shape[-1],
        "processing_time": round(processing_time, 4)
    }

# ============================================================
# TWO-RECORDING LIVE ENROLLMENT
# ============================================================

def enroll_voice_from_recordings(
    username,
    voice_path1,
    voice_path2,
    verification
):

    import re
    import time

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # VALIDATE USERNAME
    # --------------------------------------------------------

    if not re.fullmatch(
        r"[a-zA-Z0-9_-]{3,30}",
        username
    ):

        raise ValueError(
            "Username must be 3-30 characters and contain "
            "only letters, numbers, underscores or hyphens."
        )

    # --------------------------------------------------------
    # VALIDATE RECORDING FILES
    # --------------------------------------------------------

    for path in [voice_path1, voice_path2]:

        if not os.path.exists(path):

            raise FileNotFoundError(
                f"Recording not found: {path}"
            )

    # --------------------------------------------------------
    # PREVENT DUPLICATE ENROLLMENT
    # --------------------------------------------------------

    profile_path = os.path.join(
        PROFILE_DIRECTORY,
        f"{username}_voice.pt"
    )

    if os.path.exists(profile_path):

        raise FileExistsError(
            f"User '{username}' is already enrolled."
        )

    # --------------------------------------------------------
    # PREPARE FIRST RECORDING
    # --------------------------------------------------------

    print("\nPreparing first voice recording...")

    audio1 = prepare_audio(voice_path1)

    duration1 = audio1.shape[-1] / TARGET_SAMPLE_RATE

    if duration1 < 5 or duration1 > 30:

        raise ValueError(
            "First recording must be between 5 and 30 seconds."
        )

    # --------------------------------------------------------
    # PREPARE SECOND RECORDING
    # --------------------------------------------------------

    print("\nPreparing second voice recording...")

    audio2 = prepare_audio(voice_path2)

    duration2 = audio2.shape[-1] / TARGET_SAMPLE_RATE

    if duration2 < 5 or duration2 > 30:

        raise ValueError(
            "Second recording must be between 5 and 30 seconds."
        )

    # --------------------------------------------------------
    # GENERATE FIRST EMBEDDING
    # --------------------------------------------------------

    print("\nGenerating first voice embedding...")

    embedding1 = generate_embedding(
        verification,
        audio1
    )

    # --------------------------------------------------------
    # GENERATE SECOND EMBEDDING
    # --------------------------------------------------------

    print("\nGenerating second voice embedding...")

    embedding2 = generate_embedding(
        verification,
        audio2
    )

    # --------------------------------------------------------
    # COMBINE EMBEDDINGS
    # --------------------------------------------------------

    print("\nCombining voice embeddings...")

    if embedding1.shape != embedding2.shape:

        raise RuntimeError(
            "The two voice embeddings have different shapes."
        )

    combined_embedding = (
        embedding1 + embedding2
    ) / 2

    # Normalize combined embedding
    combined_embedding = torch.nn.functional.normalize(
        combined_embedding,
        p=2,
        dim=-1
    )

    # --------------------------------------------------------
    # SAVE COMBINED VOICE PROFILE
    # --------------------------------------------------------

    saved_path = save_profile(
        combined_embedding,
        username
    )

    # --------------------------------------------------------
    # REGISTER USER IN DATABASE
    # --------------------------------------------------------

    register_enrolled_user(
        username,
        saved_path
    )

    processing_time = (
        time.perf_counter() - start_time
    )

    print("\nTwo-recording enrollment completed!")

    return {
        "username": username,
        "status": "ENROLLED",
        "profile": saved_path,
        "embedding_dimensions": combined_embedding.shape[-1],
        "recordings_used": 2,
        "recording_durations": [
            round(duration1, 2),
            round(duration2, 2)
        ],
        "processing_time": round(processing_time, 4)
    }

# ============================================================
# MAIN ENROLLMENT PROCESS
# ============================================================

def main():

    if len(sys.argv) < 3:

        print("\nUsage:")

        print(
            "python enrollment_engine.py "
            "<username> <voice_file>"
        )

        print("\nExample:")

        print(
            "python enrollment_engine.py "
            "parvez data/raw/voice1.wav"
        )

        sys.exit(1)

    username = sys.argv[1]

    voice_path = sys.argv[2]

    if not username.strip():

        print("ERROR: Username cannot be empty.")

        sys.exit(1)

    try:

        print("\n")
        print("----------------------------------------")
        print("          SECUREVOICE AI")
        print("          VOICE ENROLLMENT")
        print("----------------------------------------")

        print(f"User: {username}")
        print(f"Voice file: {voice_path}")

        # Prepare audio
        audio = prepare_audio(voice_path)

        # Load model
        verification = load_model()

        # Generate embedding
        embedding = generate_embedding(
            verification,
            audio
        )

        # Save voice profile
        print("\nSaving voice profile...")

        profile_path = save_profile(
            embedding,
            username
        )

        print("Voice profile saved successfully!")

        # Register user in SQLite
        register_enrolled_user(
            username,
            profile_path
        )

        # Verify saved profile
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

        # Final result
        print("\n")
        print("----------------------------------------")
        print("          ENROLLMENT SUCCESSFUL")
        print("----------------------------------------")

        print(f"User:          {username}")
        print(f"Profile:       {profile_path}")
        print(f"Embedding:     {saved_embedding.shape}")
        print("Status:        REGISTERED")
        print("Database:      UPDATED")

        print("----------------------------------------")

    except Exception as e:

        print("\n")
        print("----------------------------------------")
        print("          SECUREVOICE AI")
        print("              ERROR")
        print("----------------------------------------")

        print(f"Error: {e}")

        print("----------------------------------------")

        sys.exit(1)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()