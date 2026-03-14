from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import wave

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = ROOT / "data" / "derived" / "audio"
FEATURES_DIR = OUTPUTS_DIR / "features_1s"
MANIFEST_PATH = OUTPUTS_DIR / "blinded_audio_manifest.csv"
SUMMARY_PATH = ROOT / "results" / "blinded" / "tables" / "blinded_session_summary.csv"
INTERVALS_DIR = ROOT / "data" / "derived" / "behavior" / "cleaned_intervals"

SAMPLE_RATE = 16_000
CHANNELS = 1
BYTES_PER_SAMPLE = 2
BIN_S = 1.0

FFMPEG_CANDIDATES = [
    Path(r"C:\Users\plattlab\BORIS\Lib\site-packages\boris\misc\ffmpeg.exe"),
    Path(r"C:\Users\plattlab\BORIS\Lib\site-packages\boris\misc\ffprobe.exe"),
]


def resolve_ffmpeg() -> Path:
    candidates = [
        Path(r"C:\Users\plattlab\BORIS\Lib\site-packages\boris\misc\ffmpeg.exe"),
        Path(r"C:\Users\plattlab\miniforge3\envs\dlc22\Library\bin\ffmpeg.exe"),
        Path(r"C:\Users\plattlab\miniforge3\pkgs\ffmpeg-8.0.1-gpl_h02474b5_509\Library\bin\ffmpeg.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Could not locate ffmpeg.exe")


def build_behavior_index(timeline: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    starts = timeline["start_s"].to_numpy(dtype=float)
    ends = timeline["end_s"].to_numpy(dtype=float)
    return starts, ends, timeline.reset_index(drop=True)


def behavior_row_for_time(starts: np.ndarray, ends: np.ndarray, timeline: pd.DataFrame, time_s: float) -> pd.Series | None:
    idx = np.searchsorted(starts, time_s, side="right") - 1
    if idx < 0 or idx >= len(timeline):
        return None
    if starts[idx] <= time_s < ends[idx]:
        return timeline.iloc[idx]
    return None


def extract_session_features(
    ffmpeg_path: Path,
    session_id: str,
    audio_path: Path,
    session_start_s: float,
    session_end_s: float,
    timeline: pd.DataFrame,
) -> pd.DataFrame:
    duration_s = session_end_s - session_start_s
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        temp_wav = Path(tmp.name)
    cmd = [
        str(ffmpeg_path),
        "-hide_banner",
        "-loglevel",
        "error",
        "-fflags",
        "+genpts",
        "-ss",
        f"{session_start_s:.3f}",
        "-t",
        f"{duration_s:.3f}",
        "-i",
        str(audio_path),
        "-vn",
        "-map",
        "0:a:0",
        "-ac",
        str(CHANNELS),
        "-ar",
        str(SAMPLE_RATE),
        "-af",
        "asetpts=N/SR/TB",
        "-f",
        "wav",
        "-y",
        str(temp_wav),
    ]

    starts, ends, timeline_idx = build_behavior_index(timeline)
    rows = []
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed for session {session_id}: {result.stderr.strip()}")

        with wave.open(str(temp_wav), "rb") as wav_handle:
            if wav_handle.getframerate() != SAMPLE_RATE:
                raise RuntimeError(f"Unexpected sample rate for session {session_id}: {wav_handle.getframerate()}")
            if wav_handle.getnchannels() != CHANNELS:
                raise RuntimeError(f"Unexpected channel count for session {session_id}: {wav_handle.getnchannels()}")

            bin_start = session_start_s
            while bin_start < session_end_s - 1e-9:
                bin_end = min(bin_start + BIN_S, session_end_s)
                bin_duration = bin_end - bin_start
                samples_needed = int(round(bin_duration * SAMPLE_RATE))
                raw = wav_handle.readframes(samples_needed)
                if not raw:
                    break

                samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                if samples.size == 0:
                    break

                norm = samples / 32768.0
                rms = float(np.sqrt(np.mean(np.square(norm))))
                peak_abs = float(np.max(np.abs(norm)))
                rms_dbfs = float(20 * np.log10(max(rms, 1e-12)))
                peak_dbfs = float(20 * np.log10(max(peak_abs, 1e-12)))
                midpoint = (bin_start + bin_end) / 2.0
                behavior_row = behavior_row_for_time(starts, ends, timeline_idx, midpoint)

                rows.append(
                    {
                        "session_id": session_id,
                        "audio_file": audio_path.name,
                        "bin_start_s": bin_start,
                        "bin_end_s": bin_end,
                        "bin_mid_s": midpoint,
                        "elapsed_start_s": bin_start - session_start_s,
                        "elapsed_mid_s": midpoint - session_start_s,
                        "elapsed_mid_min": (midpoint - session_start_s) / 60.0,
                        "bin_duration_s": bin_end - bin_start,
                        "n_samples": int(samples.size),
                        "rms": rms,
                        "peak_abs": peak_abs,
                        "rms_dbfs": rms_dbfs,
                        "peak_dbfs": peak_dbfs,
                        "social_state": None if behavior_row is None else behavior_row["social_state"],
                        "activity_state": None if behavior_row is None else behavior_row["activity_state"],
                        "attention_state": None if behavior_row is None else behavior_row["attention_state"],
                        "atypical_state": None if behavior_row is None else behavior_row["atypical_state"],
                        "social_engaged": False if behavior_row is None else bool(behavior_row["social_engaged"]),
                        "physical_contact_implied": False if behavior_row is None else bool(behavior_row["physical_contact_implied"]),
                        "proximity_implied": False if behavior_row is None else bool(behavior_row["proximity_implied"]),
                    }
                )
                bin_start = bin_end
    finally:
        if temp_wav.exists():
            temp_wav.unlink(missing_ok=True)

    features = pd.DataFrame(rows)
    if features.empty:
        return features

    rms90 = float(features["rms_dbfs"].quantile(0.90))
    rms95 = float(features["rms_dbfs"].quantile(0.95))
    peak90 = float(features["peak_dbfs"].quantile(0.90))
    features["is_loud_rms_p90"] = features["rms_dbfs"] >= rms90
    features["is_very_loud_rms_p95"] = features["rms_dbfs"] >= rms95
    features["is_loud_peak_p90"] = features["peak_dbfs"] >= peak90
    features["session_rms_dbfs_p90"] = rms90
    features["session_rms_dbfs_p95"] = rms95
    features["session_peak_dbfs_p90"] = peak90
    return features


def summarize_audio(features: pd.DataFrame) -> dict[str, object]:
    return {
        "session_id": features["session_id"].iloc[0],
        "audio_file": features["audio_file"].iloc[0],
        "audio_selection_note": features["audio_selection_note"].iloc[0],
        "n_bins": int(len(features)),
        "mean_rms_dbfs": float(features["rms_dbfs"].mean()),
        "median_rms_dbfs": float(features["rms_dbfs"].median()),
        "rms_dbfs_p90": float(features["rms_dbfs"].quantile(0.90)),
        "rms_dbfs_p95": float(features["rms_dbfs"].quantile(0.95)),
        "peak_dbfs_p90": float(features["peak_dbfs"].quantile(0.90)),
        "frac_loud_rms_p90": float(features["is_loud_rms_p90"].mean()),
        "frac_very_loud_rms_p95": float(features["is_very_loud_rms_p95"].mean()),
        "frac_loud_peak_p90": float(features["is_loud_peak_p90"].mean()),
        "mean_rms_dbfs_attention_outside": mean_for_mask(features, features["attention_state"] == "Attention to outside agents", "rms_dbfs"),
        "mean_rms_dbfs_social": mean_for_mask(features, features["social_engaged"], "rms_dbfs"),
        "mean_rms_dbfs_nonsocial": mean_for_mask(features, ~features["social_engaged"], "rms_dbfs"),
    }


def mean_for_mask(df: pd.DataFrame, mask: pd.Series, col: str) -> float | None:
    if not mask.any():
        return None
    return float(df.loc[mask, col].mean())


def is_effectively_silent(features: pd.DataFrame) -> bool:
    if features.empty:
        return True
    return bool(
        (features["peak_dbfs"] <= -200).all()
        or (features["rms_dbfs"].median() <= -200 and features["peak_dbfs"].median() <= -200)
    )


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    ffmpeg_path = resolve_ffmpeg()
    manifest = pd.read_csv(MANIFEST_PATH)
    session_summary = pd.read_csv(SUMMARY_PATH)

    all_features = []
    audio_summaries = []

    for row in manifest.itertuples(index=False):
        if pd.isna(row.selected_audio_path):
            continue
        session_id = str(row.session_id)
        summary_row = session_summary.loc[session_summary["session_id"].astype(str) == session_id].iloc[0]
        timeline = pd.read_csv(INTERVALS_DIR / f"{session_id}_layered_timeline.csv")
        features = extract_session_features(
            ffmpeg_path=ffmpeg_path,
            session_id=session_id,
            audio_path=Path(row.selected_audio_path),
            session_start_s=float(summary_row["session_start_s"]),
            session_end_s=float(summary_row["session_end_s"]),
            timeline=timeline,
        )
        selection_note = "manifest_selected"
        if is_effectively_silent(features) and not pd.isna(row.second_path):
            fallback_features = extract_session_features(
                ffmpeg_path=ffmpeg_path,
                session_id=session_id,
                audio_path=Path(row.second_path),
                session_start_s=float(summary_row["session_start_s"]),
                session_end_s=float(summary_row["session_end_s"]),
                timeline=timeline,
            )
            if not is_effectively_silent(fallback_features):
                features = fallback_features
                selection_note = "fallback_second_due_to_silent_longest"
            else:
                selection_note = "selected_audio_silent"
        features["audio_selection_note"] = selection_note
        features.to_csv(FEATURES_DIR / f"{session_id}_audio_features_1s.csv", index=False)
        all_features.append(features)
        audio_summaries.append(summarize_audio(features))

    pd.concat(all_features, ignore_index=True).to_csv(OUTPUTS_DIR / "blinded_audio_features_1s.csv", index=False)
    pd.DataFrame(audio_summaries).sort_values("session_id").to_csv(OUTPUTS_DIR / "blinded_audio_summary.csv", index=False)


if __name__ == "__main__":
    main()
