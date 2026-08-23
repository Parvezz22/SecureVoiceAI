import sys
import time
from datetime import datetime

import torch
import torchaudio
import torchcodec


# ============================================================
# SECUREVOICE AI
# AUTHENTICATION ENGINE
# ============================================================

MODEL_PATH = "models/ecapa"
PROFILE_PATH = "voice_profiles/parvez_voice.pt"

TARGET_SAMPLE_RATE = 16000
THRESHOLD = 0.60


# ============================================================
# LOAD AND PREPARE AUDIO
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
    # Resample to 16 kHz
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

    return audio, sample_rate


# ============================================================
# LOAD SPEAKER RECOGNITION MODEL
# ============================================================

def load_model():

    print("\nLoading speaker recognition model...")

    # Import SpeechBrain AFTER audio/TorchCodec
    # has already been initialized.

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
# LOAD REGISTERED VOICE PROFILE
# ============================================================

def load_registered_profile():

    print("Loading registered voice profile...")

    registered_embedding = torch.load(
        PROFILE_PATH,
        map_location="cpu"
    )

    print("Registered voice profile loaded!")

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

        embedding = verification.encode_batch(
            audio
        )

    print(
        "Voice embedding generated successfully!"
    )

    return embedding


# ============================================================
# CALCULATE SIMILARITY
# ============================================================

def calculate_similarity(
    registered_embedding,
    new_embedding
):

    score = torch.nn.functional.cosine_similarity(
        registered_embedding.flatten(),
        new_embedding.flatten(),
        dim=0
    ).item()

    return score


# ============================================================
# DETERMINE CONFIDENCE
# ============================================================

def determine_confidence(score):

    if score >= 0.75:

        return "VERY HIGH"

    elif score >= 0.60:

        return "HIGH"

    elif score >= 0.40:

        return "LOW"

    else:

        return "VERY LOW"


# ============================================================
# AUTHENTICATE VOICE
# ============================================================

def authenticate(
    verification,
    registered_embedding,
    audio,
    voice_path
):

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # Generate embedding
    # --------------------------------------------------------

    new_embedding = generate_embedding(
        verification,
        audio
    )

    # --------------------------------------------------------
    # Compare voices
    # --------------------------------------------------------

    print(
        "\nComparing registered voice "
        "with new voice..."
    )

    score = calculate_similarity(
        registered_embedding,
        new_embedding
    )

    # --------------------------------------------------------
    # Authentication decision
    # --------------------------------------------------------

    if score >= THRESHOLD:

        authentication = "SUCCESS"
        same_speaker = True

    else:

        authentication = "FAILED"
        same_speaker = False

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence = determine_confidence(
        score
    )

    # --------------------------------------------------------
    # Processing time
    # --------------------------------------------------------

    processing_time = (
        time.perf_counter()
        - start_time
    )

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    # --------------------------------------------------------
    # Structured result
    # --------------------------------------------------------

    result = {

        "timestamp": timestamp,

        "voice_file": voice_path,

        "similarity_score": round(
            score,
            4
        ),

        "threshold": THRESHOLD,

        "confidence": confidence,

        "authentication": authentication,

        "same_speaker": same_speaker,

        "processing_time_seconds": round(
            processing_time,
            4
        )
    }

    return result


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_result(result):

    print("\n")
    print("----------------------------------------")
    print("          SECUREVOICE AI")
    print("       AUTHENTICATION ENGINE")
    print("----------------------------------------")

    print(
        f"Timestamp:             "
        f"{result['timestamp']}"
    )

    print(
        f"Voice file:            "
        f"{result['voice_file']}"
    )

    print(
        f"Similarity score:      "
        f"{result['similarity_score']:.4f}"
    )

    print(
        f"Threshold:             "
        f"{result['threshold']:.2f}"
    )

    print(
        f"Confidence:            "
        f"{result['confidence']}"
    )

    print(
        f"Authentication:        "
        f"{result['authentication']}"
    )

    print(
        f"Same speaker:          "
        f"{'YES' if result['same_speaker'] else 'NO'}"
    )

    print(
        f"Processing time:       "
        f"{result['processing_time_seconds']:.4f} seconds"
    )

    print("----------------------------------------")

    if result["same_speaker"]:

        print(
            "RESULT: Voice authentication successful."
        )

    else:

        print(
            "RESULT: Voice authentication failed."
        )

    print("----------------------------------------")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    # --------------------------------------------------------
    # Check command-line argument
    # --------------------------------------------------------

    if len(sys.argv) < 2:

        print("\nUsage:")

        print(
            "python authentication_engine.py "
            "<voice_file>"
        )

        print("\nExample:")

        print(
            "python authentication_engine.py "
            "Data/raw/voice1.wav"
        )

        sys.exit(1)

    voice_path = sys.argv[1]

    try:

        # ====================================================
        # IMPORTANT:
        # LOAD AUDIO BEFORE SPEECHBRAIN
        # ====================================================

        audio, sample_rate = prepare_audio(
            voice_path
        )

        # ----------------------------------------------------
        # Now load SpeechBrain
        # ----------------------------------------------------

        verification = load_model()

        # ----------------------------------------------------
        # Load registered profile
        # ----------------------------------------------------

        registered_embedding = (
            load_registered_profile()
        )

        # ----------------------------------------------------
        # Authenticate
        # ----------------------------------------------------

        result = authenticate(
            verification,
            registered_embedding,
            audio,
            voice_path
        )

        # ----------------------------------------------------
        # Display result
        # ----------------------------------------------------

        display_result(result)

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