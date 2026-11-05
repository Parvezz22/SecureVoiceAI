import argparse
import csv
import io
import json
import time

from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import torch

from sklearn.metrics import roc_curve

from authentication_engine import (
    load_model,
    prepare_audio,
    generate_embedding,
    compare_embeddings,
    THRESHOLD
)


# ============================================================
# SECUREVOICE AI
# SPEAKER VERIFICATION PERFORMANCE EVALUATION
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent

TRIALS_FILE = (
    PROJECT_DIR
    / "Data"
    / "Evaluation"
    / "VoxCeleb1"
    / "trials"
    / "veri_test2.txt"
)

AUDIO_DIRECTORY = (
    PROJECT_DIR
    / "Data"
    / "Evaluation"
    / "VoxCeleb1"
    / "audio"
    / "wav"
)

RESULTS_DIRECTORY = (
    PROJECT_DIR
    / "Data"
    / "Evaluation"
    / "results"
)


# ============================================================
# LOAD TRIALS
# ============================================================

def load_trials(max_pairs=None):

    if not TRIALS_FILE.exists():
        raise FileNotFoundError(
            f"Trial list not found: {TRIALS_FILE}"
        )

    trials = []

    with open(TRIALS_FILE, "r", encoding="utf-8") as file:

        for line in file:

            parts = line.strip().split()

            if len(parts) != 3:
                continue

            label = int(parts[0])

            if label not in (0, 1):
                continue

            trials.append({
                "label": label,
                "file1": parts[1],
                "file2": parts[2]
            })

            if (
                max_pairs is not None
                and len(trials) >= max_pairs
            ):
                break

    if not trials:
        raise RuntimeError(
            "No valid evaluation trials found."
        )

    return trials


# ============================================================
# GENERATE AND CACHE EMBEDDINGS
# ============================================================

def get_embedding(
    relative_path,
    verification,
    embedding_cache
):

    if relative_path in embedding_cache:
        return embedding_cache[relative_path]

    audio_path = AUDIO_DIRECTORY / relative_path

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    # Suppress detailed audio-processing messages.
    with redirect_stdout(io.StringIO()):

        audio = prepare_audio(str(audio_path))

        embedding = generate_embedding(
            verification,
            audio
        )

    embedding = embedding.detach().cpu().flatten()

    embedding_cache[relative_path] = embedding

    return embedding


# ============================================================
# CALCULATE SIMILARITY SCORES
# ============================================================

def evaluate_trials(trials, verification):

    embedding_cache = {}

    labels = []
    scores = []

    total = len(trials)

    start_time = time.perf_counter()

    for index, trial in enumerate(trials, start=1):

        embedding1 = get_embedding(
            trial["file1"],
            verification,
            embedding_cache
        )

        embedding2 = get_embedding(
            trial["file2"],
            verification,
            embedding_cache
        )

        score = torch.nn.functional.cosine_similarity(
    embedding1.flatten(),
    embedding2.flatten(),
    dim=0
).item()

        labels.append(trial["label"])
        scores.append(score)

        if index % 100 == 0 or index == total:

            print(
                f"Processed {index}/{total} pairs | "
                f"Unique recordings: "
                f"{len(embedding_cache)}"
            )

    processing_time = (
        time.perf_counter() - start_time
    )

    return (
        np.array(labels),
        np.array(scores),
        processing_time,
        len(embedding_cache)
    )


# ============================================================
# CALCULATE METRICS AT A GIVEN THRESHOLD
# ============================================================

def calculate_metrics(labels, scores, threshold):

    genuine = labels == 1
    impostor = labels == 0

    accepted = scores >= threshold

    genuine_count = np.sum(genuine)
    impostor_count = np.sum(impostor)

    true_accepts = np.sum(accepted & genuine)
    false_rejects = np.sum(~accepted & genuine)

    false_accepts = np.sum(accepted & impostor)
    true_rejects = np.sum(~accepted & impostor)

    far = (
        false_accepts / impostor_count
        if impostor_count else 0
    )

    frr = (
        false_rejects / genuine_count
        if genuine_count else 0
    )

    accuracy = (
        (true_accepts + true_rejects) / len(labels)
    )

    return {
        "threshold": float(threshold),
        "FAR": float(far * 100),
        "FRR": float(frr * 100),
        "Accuracy": float(accuracy * 100),
        "True Accepts": int(true_accepts),
        "False Accepts": int(false_accepts),
        "True Rejects": int(true_rejects),
        "False Rejects": int(false_rejects)
    }


# ============================================================
# CALCULATE EQUAL ERROR RATE
# ============================================================

def calculate_eer(labels, scores):

    false_accept_rate, true_accept_rate, thresholds = (
        roc_curve(
            labels,
            scores,
            pos_label=1
        )
    )

    false_reject_rate = 1 - true_accept_rate

    differences = (
        false_accept_rate - false_reject_rate
    )

    crossing_indices = np.where(
        differences[:-1] * differences[1:] <= 0
    )[0]

    if len(crossing_indices) > 0:

        index = crossing_indices[0]

        x1 = differences[index]
        x2 = differences[index + 1]

        if x1 == x2:
            fraction = 0.5
        else:
            fraction = -x1 / (x2 - x1)

        eer = (
            false_accept_rate[index]
            + fraction * (
                false_accept_rate[index + 1]
                - false_accept_rate[index]
            )
        )

        threshold1 = thresholds[index]
        threshold2 = thresholds[index + 1]

        if np.isfinite(threshold1) and np.isfinite(threshold2):

            eer_threshold = (
                threshold1
                + fraction * (threshold2 - threshold1)
            )

        else:
            eer_threshold = threshold2

    else:

        index = np.argmin(
            np.abs(differences)
        )

        eer = (
            false_accept_rate[index]
            + false_reject_rate[index]
        ) / 2

        eer_threshold = thresholds[index]

    return float(eer * 100), float(eer_threshold)


# ============================================================
# SAVE EVALUATION RESULTS
# ============================================================

def save_results(
    labels,
    scores,
    fixed_metrics,
    eer,
    eer_threshold,
    processing_time,
    unique_recordings
):

    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save metrics as JSON
    # --------------------------------------------------------

    metrics = {
        "dataset": "VoxCeleb1 Test",
        "evaluation_pairs": int(len(labels)),
        "genuine_pairs": int(np.sum(labels == 1)),
        "impostor_pairs": int(np.sum(labels == 0)),
        "unique_recordings_processed": unique_recordings,
        "application_threshold": THRESHOLD,
        "application_threshold_metrics": fixed_metrics,
        "equal_error_rate_percent": eer,
        "eer_threshold": eer_threshold,
        "processing_time_seconds": round(
            processing_time,
            2
        )
    }

    json_path = (
        RESULTS_DIRECTORY / "evaluation_metrics.json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metrics,
            file,
            indent=4
        )

    # --------------------------------------------------------
    # Save threshold analysis as CSV
    # --------------------------------------------------------

    fpr, tpr, thresholds = roc_curve(
        labels,
        scores,
        pos_label=1
    )

    csv_path = (
        RESULTS_DIRECTORY / "threshold_analysis.csv"
    )

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Threshold",
            "FAR_Percent",
            "FRR_Percent",
            "Accuracy_Percent"
        ])

        for threshold in thresholds:

            if not np.isfinite(threshold):
                continue

            result = calculate_metrics(
                labels,
                scores,
                threshold
            )

            writer.writerow([
                result["threshold"],
                result["FAR"],
                result["FRR"],
                result["Accuracy"]
            ])

    print("\nResults saved successfully!")

    print(f"Metrics JSON: {json_path}")
    print(f"Threshold CSV: {csv_path}")


# ============================================================
# DISPLAY EVALUATION RESULTS
# ============================================================

def display_results(
    labels,
    scores,
    processing_time,
    unique_recordings
):

    metrics = calculate_metrics(
        labels,
        scores,
        THRESHOLD
    )

    eer, eer_threshold = calculate_eer(
        labels,
        scores
    )

    print("\n")
    print("=" * 55)
    print("       SECUREVOICE AI")
    print(" SPEAKER VERIFICATION PERFORMANCE")
    print("=" * 55)

    print(
        f"Evaluation pairs:       {len(labels)}"
    )

    print(
        f"Genuine pairs:          {np.sum(labels == 1)}"
    )

    print(
        f"Impostor pairs:         {np.sum(labels == 0)}"
    )

    print(
        f"Unique recordings:      {unique_recordings}"
    )

    print("-" * 55)

    print(
        f"Application threshold: {THRESHOLD:.4f}"
    )

    print(
        f"False Acceptance Rate:  "
        f"{metrics['FAR']:.4f}%"
    )

    print(
        f"False Rejection Rate:   "
        f"{metrics['FRR']:.4f}%"
    )

    print(
        f"Accuracy:               "
        f"{metrics['Accuracy']:.4f}%"
    )

    print("-" * 55)

    print(
        f"Equal Error Rate:       {eer:.4f}%"
    )

    print(
        f"EER Threshold:          {eer_threshold:.4f}"
    )

    print("-" * 55)

    print(
        f"Processing time:        "
        f"{processing_time:.2f} seconds"
    )

    print("=" * 55)

    save_results(
        labels,
        scores,
        metrics,
        eer,
        eer_threshold,
        processing_time,
        unique_recordings
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "SecureVoiceAI Speaker Verification Evaluation"
        )
    )

    parser.add_argument(
        "--max-pairs",
        type=int,
        default=None,
        help=(
            "Maximum number of trial pairs to evaluate. "
            "Omit to evaluate the complete trial list."
        )
    )

    args = parser.parse_args()

    if (
        args.max_pairs is not None
        and args.max_pairs < 1
    ):
        parser.error("--max-pairs must be greater than zero")

    print("\nSECUREVOICE AI EVALUATION ENGINE")
    print("-" * 45)

    print("Loading VoxCeleb1 trial list...")

    trials = load_trials(args.max_pairs)

    print(
        f"Loaded {len(trials)} evaluation pairs."
    )

    print("\nLoading ECAPA speaker recognition model...")

    verification = load_model()

    print("\nStarting speaker verification evaluation...")

    (
        labels,
        scores,
        processing_time,
        unique_recordings
    ) = evaluate_trials(
        trials,
        verification
    )

    if not np.any(labels == 1) or not np.any(labels == 0):

        raise RuntimeError(
            "Evaluation requires both genuine "
            "and impostor pairs."
        )

    display_results(
        labels,
        scores,
        processing_time,
        unique_recordings
    )


if __name__ == "__main__":

    main()