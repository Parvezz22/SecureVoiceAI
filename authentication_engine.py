import os
import sys
import time

import torch
import torchaudio
import torchcodec


# ============================================================
# SECUREVOICE AI
# MULTI-USER AUTHENTICATION ENGINE
# ============================================================

MODEL_PATH = "models/ecapa"
PROFILE_DIRECTORY = "voice_profiles"

TARGET_SAMPLE_RATE = 16000
THRESHOLD = 0.60


# ============================================================
# PREPARE AUDIO
# ============================================================

def prepare_audio(voice_path):

    print("Loading new voice...")

    try:

        audio, sample_rate = torchaudio.load(
            voice_path
        )

    except Exception as e:

        raise RuntimeError(
            f"Could not load audio file: {e}"
        )

    print("New voice loaded successfully!")

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
    # Validate audio
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
# LOAD USER PROFILE
# ============================================================

def load_profile(username):

    profile_path = os.path.join(
        PROFILE_DIRECTORY,
        f"{username}_voice.pt"
    )

    if not os.path.exists(profile_path):

        raise FileNotFoundError(
            f"No voice profile found for user "
            f"'{username}'."
        )

    print(
        f"Loading voice profile for user "
        f"'{username}'..."
    )

    try:

        registered_embedding = torch.load(
            profile_path,
            map_location="cpu"
        )

    except Exception as e:

        raise RuntimeError(
            f"Could not load voice profile: {e}"
        )

    if not isinstance(
        registered_embedding,
        torch.Tensor
    ):

        raise RuntimeError(
            "Voice profile does not contain "
            "a valid tensor."
        )

    if registered_embedding.numel() == 0:

        raise RuntimeError(
            "Voice profile is empty."
        )

    print(
        "Voice profile loaded successfully!"
    )

    print(
        f"Profile shape: "
        f"{registered_embedding.shape}"
    )

    return registered_embedding


# ============================================================
# GENERATE VOICE EMBEDDING
# ============================================================

def generate_embedding(
    verification,
    audio
):

    print("\nGenerating voice embedding...")

    with torch.no_grad():

        new_embedding = verification.encode_batch(
            audio
        )

    print(
        "Voice embedding generated successfully!"
    )

    return new_embedding


# ============================================================
# COMPARE VOICES
# ============================================================

def compare_embeddings(
    registered_embedding,
    new_embedding
):

    print("\nComparing registered voice "
          "with new voice...\n")

    score = torch.nn.functional.cosine_similarity(
        registered_embedding.flatten(),
        new_embedding.flatten(),
        dim=0
    ).item()

    return score


# ============================================================
# AUTHENTICATION DECISION
# ============================================================

def authenticate(score):

    if score >= THRESHOLD:

        authentication = "SUCCESS"
        same_speaker = "YES"

        if score >= 0.85:

            confidence = "VERY HIGH"

        elif score >= 0.70:

            confidence = "HIGH"

        else:

            confidence = "MODERATE"

    else:

        authentication = "FAILED"
        same_speaker = "NO"
        confidence = "LOW"

    return (
        authentication,
        same_speaker,
        confidence
    )


# ============================================================
# MAIN AUTHENTICATION PROCESS
# ============================================================

def main():

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # Check arguments
    # --------------------------------------------------------

    if len(sys.argv) < 3:

        print("\nUsage:")
        print(
            "python authentication_engine.py "
            "<username> <voice_file>"
        )

        print("\nExample:")
        print(
            "python authentication_engine.py "
            "testuser Data/raw/voice1.wav"
        )

        sys.exit(1)

    username = sys.argv[1]
    voice_path = sys.argv[2]

    try:

        # ----------------------------------------------------
        # Validate voice file
        # ----------------------------------------------------

        if not os.path.exists(voice_path):

            raise FileNotFoundError(
                f"Voice file not found: {voice_path}"
            )

        # ----------------------------------------------------
        # Prepare audio
        # ----------------------------------------------------

        audio = prepare_audio(
            voice_path
        )

        # ----------------------------------------------------
        # Load speaker model
        # ----------------------------------------------------

        verification = load_model()

        # ----------------------------------------------------
        # Load registered profile
        # ----------------------------------------------------

        registered_embedding = load_profile(
            username
        )

        # ----------------------------------------------------
        # Generate embedding
        # ----------------------------------------------------

        new_embedding = generate_embedding(
            verification,
            audio
        )

        # ----------------------------------------------------
        # Compare voices
        # ----------------------------------------------------

        score = compare_embeddings(
            registered_embedding,
            new_embedding
        )

        # ----------------------------------------------------
        # Authentication decision
        # ----------------------------------------------------

        (
            authentication,
            same_speaker,
            confidence
        ) = authenticate(score)

        # ----------------------------------------------------
        # Processing time
        # ----------------------------------------------------

        processing_time = (
            time.perf_counter() - start_time
        )

        # ----------------------------------------------------
        # Display result
        # ----------------------------------------------------

        print("\n")
        print("----------------------------------------")
        print("          SECUREVOICE AI")
        print("       AUTHENTICATION ENGINE")
        print("----------------------------------------")

        print(
            f"Timestamp:             "
            f"{time.strftime('%Y-%m-%dT%H:%M:%S')}"
        )

        print(
            f"User:                  {username}"
        )

        print(
            f"Voice file:            {voice_path}"
        )

        print(
            f"Similarity score:      {score:.4f}"
        )

        print(
            f"Threshold:             {THRESHOLD:.2f}"
        )

        print(
            f"Confidence:            {confidence}"
        )

        print(
            f"Authentication:        {authentication}"
        )

        print(
            f"Same speaker:          {same_speaker}"
        )

        print(
            f"Processing time:       "
            f"{processing_time:.4f} seconds"
        )

        print("----------------------------------------")

        if authentication == "SUCCESS":

            print(
                "RESULT: Voice authentication successful."
            )

        else:

            print(
                "RESULT: Voice authentication failed."
            )

        print("----------------------------------------")

    except FileNotFoundError as e:

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
