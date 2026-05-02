from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np


ANALYSIS_REPORT_SCHEMA_VERSION = "1.0"


ISSUE_STRATEGIES: dict[str, dict[str, str]] = {
    "dull_top_end": {
        "title": "High-Frequency Rolloff",
        "detection": "Detected from missing top-band energy and a visible upper-band cutoff in the spectrogram.",
        "repair": "Use conservative brightness shaping now; later upgrade path is generative top-end reconstruction per stem.",
    },
    "metallic_highs": {
        "title": "Metallic Resonances",
        "detection": "Detected from excess energy in the 6-10 kHz harshness band.",
        "repair": "Use de-esser plus targeted upper-band reduction after separation, especially on vocals.",
    },
    "robotic_vocals": {
        "title": "Robotic Quantization",
        "detection": "Detected from overly uniform vocal-presence energy over time while upper vocal artifacts remain active.",
        "repair": "Use vocal humanization EQ now; later upgrade path is dedicated vocal naturalization and formant-aware restoration.",
    },
    "codec_haze": {
        "title": "Codec / Digital Haze",
        "detection": "Detected from low-mid clustering and reduced spectral clarity.",
        "repair": "Use low-mid cleanup and clarity compensation, ideally after stem separation to avoid damaging the full mix.",
    },
    "congested_mix": {
        "title": "Congested Dynamics",
        "detection": "Detected from dense RMS levels and reduced crest factor.",
        "repair": "Use gentle dynamic control after repair, keeping restoration separate from final mastering.",
    },
    "noise_floor": {
        "title": "Raised Noise Floor",
        "detection": "Detected from unusually elevated quiet passages relative to the program level.",
        "repair": "Use conditional vocal denoising only when the noise-floor flag is present.",
    },
    "room_smear": {
        "title": "Room Smear / Baked-In Reverb",
        "detection": "Detected from softened transient definition combined with persistent low-mid buildup.",
        "repair": "Use only light clarity compensation now; a real de-reverb path remains a later dedicated module.",
    },
    "general_cleanup": {
        "title": "General Cleanup",
        "detection": "No dominant artifact class was detected with high confidence.",
        "repair": "Keep the path conservative and avoid heavy restoration steps.",
    },
}


def emit(payload: dict) -> None:
    print(json.dumps(payload), flush=True)


def run_ffmpeg_normalize(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if input_path.resolve() == output_path.resolve():
        return

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ar",
        "48000",
        "-acodec",
        "pcm_f32le",
        str(output_path),
    ]

    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "FFmpeg normalization failed")


def load_audio_stereo(path: Path) -> tuple[np.ndarray, int]:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(path),
        "-f",
        "f32le",
        "-ac",
        "2",
        "-acodec",
        "pcm_f32le",
        "-ar",
        "48000",
        "-",
    ]

    completed = subprocess.run(command, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="ignore").strip() or "FFmpeg stereo decode failed")

    audio = np.frombuffer(completed.stdout, dtype=np.float32).copy()
    if audio.size == 0:
        raise RuntimeError("Decoded stereo audio is empty")

    return audio.reshape(-1, 2), 48000


def load_audio(path: Path, sample_rate: int, channels: int) -> np.ndarray:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(path),
        "-f",
        "f32le",
        "-ac",
        str(channels),
        "-acodec",
        "pcm_f32le",
        "-ar",
        str(sample_rate),
        "-",
    ]

    completed = subprocess.run(command, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="ignore").strip() or "FFmpeg audio decode failed")

    audio = np.frombuffer(completed.stdout, dtype=np.float32).copy()
    if audio.size == 0:
        raise RuntimeError("Decoded audio is empty")

    return audio.reshape(-1, channels)


def resample_audio_file(input_path: Path, output_path: Path, sample_rate: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ar",
        str(sample_rate),
        "-acodec",
        "pcm_f32le",
        str(output_path),
    ]

    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "FFmpeg resample failed")


def load_audio_for_analysis(path: Path) -> tuple[np.ndarray, int]:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(path),
        "-f",
        "s16le",
        "-ac",
        "1",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "48000",
        "-",
    ]

    completed = subprocess.run(command, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="ignore").strip() or "FFmpeg analysis decode failed")

    audio = np.frombuffer(completed.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return audio, 48000


def generate_spectrogram_image(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-lavfi",
        "showspectrumpic=s=1800x900:legend=1:scale=log",
        "-frames:v",
        "1",
        str(output_path),
    ]

    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "FFmpeg spectrogram generation failed")


def estimate_lower_cutoff_knee_hz(freqs: np.ndarray, spectrum: np.ndarray) -> float | None:
    if freqs.size == 0 or spectrum.size == 0:
        return None

    high_band_mask = freqs >= 12000
    high_freqs = freqs[high_band_mask]
    high_spectrum = spectrum[high_band_mask]
    if high_freqs.size == 0:
        return None

    smoothed = np.convolve(high_spectrum, np.ones(41, dtype=np.float32) / 41.0, mode="same")
    peak_level = float(np.max(smoothed))
    if peak_level <= 0:
        return None

    normalized = smoothed / (peak_level + 1e-12)

    best_freq: float | None = None
    best_score = 0.0

    # For this use case we only want the high cutoff knee near the top of the
    # spectrum, not earlier dips around 15-17 kHz that can still contain a lot
    # of energy. Search only in the top band.
    for index in range(16, high_freqs.size - 16):
        freq = float(high_freqs[index])
        if freq < 17500:
            continue

        before_level = float(np.mean(normalized[index - 16 : index]))
        after_level = float(np.mean(normalized[index + 1 : index + 17]))
        if before_level <= 0.03:
            continue

        drop_ratio = after_level / (before_level + 1e-12)
        drop_strength = before_level - after_level
        freq_bias = max(0.0, min((freq - 17500.0) / 5000.0, 1.0))
        score = drop_strength * (0.75 + freq_bias)

        if drop_ratio < 0.92 and score > best_score:
            best_score = score
            best_freq = freq

    if best_freq is not None:
        return best_freq

    active = np.where((high_freqs >= 17500) & (normalized >= 0.03))[0]
    if active.size:
        return float(high_freqs[active[-1]])

    return None


def estimate_spectrogram_cutoff_hz(audio: np.ndarray, sample_rate: int) -> float | None:
    if audio.size < 4096:
        return None

    n_fft = 4096
    hop = 1024
    if audio.shape[0] < n_fft:
        return None

    frame_count = 1 + (audio.shape[0] - n_fft) // hop
    if frame_count <= 0:
        return None

    window = np.hanning(n_fft).astype(np.float32)
    spectrogram = np.empty((n_fft // 2 + 1, frame_count), dtype=np.float32)

    for frame_index in range(frame_count):
        start = frame_index * hop
        frame = audio[start : start + n_fft] * window
        spectrogram[:, frame_index] = np.abs(np.fft.rfft(frame)).astype(np.float32)

    freqs = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)
    high_mask = freqs >= 12000
    high_freqs = freqs[high_mask]
    high_spec = spectrogram[high_mask]
    if high_freqs.size == 0 or high_spec.size == 0:
        return None

    # Collapse time conservatively: keep bins that are consistently present,
    # which matches the visible horizontal cutoff line better than a single FFT.
    time_profile = np.percentile(high_spec, 75, axis=1)
    time_profile = np.convolve(time_profile, np.ones(9, dtype=np.float32) / 9.0, mode="same")
    peak = float(np.max(time_profile))
    if peak <= 0:
        return None

    normalized = time_profile / (peak + 1e-12)

    best_freq: float | None = None
    best_score = 0.0

    for index in range(12, high_freqs.size - 12):
        freq = float(high_freqs[index])
        if freq < 17000:
            continue

        below = float(np.mean(normalized[index - 10 : index]))
        above = float(np.mean(normalized[index + 1 : index + 11]))
        if below <= 0.015:
            continue

        drop = below - above
        ratio = above / (below + 1e-12)
        score = drop * (0.5 + min((freq - 17000.0) / 7000.0, 1.0))

        if ratio < 0.82 and score > best_score:
            best_score = score
            best_freq = freq

    if best_freq is not None:
        return best_freq

    active = np.where((high_freqs >= 17000) & (normalized >= 0.015))[0]
    if active.size:
        return float(high_freqs[active[-1]])

    return None


def compute_spectral_variation(audio: np.ndarray, sample_rate: int, low_hz: float, high_hz: float) -> float | None:
    if audio.size < 4096:
        return None

    n_fft = 2048
    hop = 512
    if audio.shape[0] < n_fft:
        return None

    frame_count = 1 + (audio.shape[0] - n_fft) // hop
    if frame_count <= 1:
        return None

    window = np.hanning(n_fft).astype(np.float32)
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)
    band_mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(band_mask):
        return None

    band_energies = np.empty(frame_count, dtype=np.float32)
    for frame_index in range(frame_count):
        start = frame_index * hop
        frame = audio[start : start + n_fft] * window
        spectrum = np.abs(np.fft.rfft(frame)).astype(np.float32)
        band_energies[frame_index] = float(np.mean(spectrum[band_mask]))

    mean_energy = float(np.mean(band_energies))
    if mean_energy <= 1e-9:
        return None

    return float(np.std(band_energies) / mean_energy)


def compute_transient_flatness(audio: np.ndarray, sample_rate: int) -> float | None:
    if audio.size < 4096:
        return None

    n_fft = 2048
    hop = 512
    if audio.shape[0] < n_fft:
        return None

    frame_count = 1 + (audio.shape[0] - n_fft) // hop
    if frame_count <= 1:
        return None

    window = np.hanning(n_fft).astype(np.float32)
    freqs = np.fft.rfftfreq(n_fft, 1.0 / sample_rate)
    band_mask = (freqs >= 1000.0) & (freqs <= 6000.0)
    if not np.any(band_mask):
        return None

    energies = np.empty(frame_count, dtype=np.float32)
    for frame_index in range(frame_count):
        start = frame_index * hop
        frame = audio[start : start + n_fft] * window
        spectrum = np.abs(np.fft.rfft(frame)).astype(np.float32)
        energies[frame_index] = float(np.mean(spectrum[band_mask]))

    mean_energy = float(np.mean(energies))
    if mean_energy <= 1e-9:
        return None

    return float(np.percentile(energies, 95) / mean_energy)


def write_audio_stereo(path: Path, audio: np.ndarray) -> None:
    write_audio_stereo_with_rate(path, audio, 48000)


def write_audio_stereo_with_rate(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim != 2 or audio.shape[1] != 2:
        raise RuntimeError("Stereo audio write requires a two-channel array")

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "f32le",
        "-ar",
        str(sample_rate),
        "-ac",
        "2",
        "-i",
        "-",
        "-acodec",
        "pcm_f32le",
        str(path),
    ]

    completed = subprocess.run(command, input=audio.tobytes(), capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="ignore").strip() or "FFmpeg stereo write failed")


def normalize_peak(audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    peak = float(np.max(np.abs(audio)) + 1e-12)
    if peak > target_peak:
        audio = audio * (target_peak / peak)

    return np.clip(audio, -1.0, 1.0).astype(np.float32)


def compute_analysis(normalized_path: Path) -> dict:
    audio, sample_rate = load_audio_for_analysis(normalized_path)
    if audio.size == 0:
        raise RuntimeError("Normalized audio is empty")

    duration_sec = float(audio.shape[0] / sample_rate)
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio)) + 1e-12))
    abs_audio = np.abs(audio)

    # Use a manageable analysis window for fast heuristics.
    window_size = min(audio.shape[0], sample_rate * 10)
    window = audio[:window_size]
    spectrum = np.abs(np.fft.rfft(window * np.hanning(window.shape[0])))
    freqs = np.fft.rfftfreq(window.shape[0], 1.0 / sample_rate)

    total_energy = float(np.sum(spectrum) + 1e-12)
    high_band = float(np.sum(spectrum[freqs >= 12000]) / total_energy)
    harsh_band = float(np.sum(spectrum[(freqs >= 6000) & (freqs <= 10000)]) / total_energy)
    low_mid_band = float(np.sum(spectrum[(freqs >= 200) & (freqs <= 4000)]) / total_energy)
    centroid = float(np.sum(freqs * spectrum) / total_energy)
    lower_cutoff_knee_hz = estimate_spectrogram_cutoff_hz(audio, sample_rate)
    if lower_cutoff_knee_hz is None:
        lower_cutoff_knee_hz = estimate_lower_cutoff_knee_hz(freqs, spectrum)
    transient_peak = float(np.percentile(abs_audio, 95))
    noise_floor = float(np.percentile(abs_audio, 10))
    noise_floor_ratio = noise_floor / max(rms, 1e-6)
    crest_factor = peak / max(rms, 1e-6)
    vocal_presence_variation = compute_spectral_variation(audio, sample_rate, 2000.0, 6000.0)
    vocal_artifact_variation = compute_spectral_variation(audio, sample_rate, 6000.0, 10000.0)
    transient_flatness = compute_transient_flatness(audio, sample_rate)

    issues: list[dict] = []

    def add_issue(issue_id: str, label: str, severity: str, description: str, confidence: float) -> None:
        strategy = ISSUE_STRATEGIES.get(issue_id, ISSUE_STRATEGIES["general_cleanup"])
        issues.append(
            {
                "id": issue_id,
                "label": label,
                "severity": severity,
                "confidence": round(max(0.0, min(confidence, 0.99)), 2),
                "description": description,
                "artifact_title": strategy["title"],
                "detection": strategy["detection"],
                "repair": strategy["repair"],
            }
        )

    if high_band < 0.045:
        add_issue(
            "dull_top_end",
            "Dull top end",
            "high",
            "High-frequency energy is low compared with the rest of the track.",
            0.6 + min(0.35, (0.045 - high_band) * 8.0),
        )

    if harsh_band > 0.32:
        add_issue(
            "metallic_highs",
            "Metallic highs",
            "medium",
            "The upper spectrum has a strong concentration in the metallic harshness band.",
            0.58 + min(0.32, (harsh_band - 0.32) * 2.8),
        )

    if vocal_presence_variation is not None and vocal_artifact_variation is not None:
        if vocal_presence_variation < 0.28 and vocal_artifact_variation > 0.22:
            add_issue(
                "robotic_vocals",
                "Robotic vocals",
                "medium",
                "The vocal-presence region is unusually uniform over time while upper vocal artifacts remain active, which can sound synthetic or auto-tuned.",
                0.5
                + min(0.2, (0.28 - vocal_presence_variation) * 1.5)
                + min(0.2, max(0.0, vocal_artifact_variation - 0.22) * 1.5),
            )

    if rms > 0.18 and crest_factor < 3.2:
        add_issue(
            "congested_mix",
            "Congested mix",
            "medium",
            "The track appears dense and dynamically constrained.",
            0.55 + min(0.25, (3.2 - crest_factor) * 0.2),
        )

    if centroid < 3200 and low_mid_band > 0.72:
        add_issue(
            "codec_haze",
            "Codec haze",
            "medium",
            "Energy is clustered in the low-mid range, which can sound hazy or smeared.",
            0.52 + min(0.28, (low_mid_band - 0.72) * 1.8),
        )

    if transient_flatness is not None and low_mid_band > 0.68 and transient_flatness < 1.85:
        add_issue(
            "room_smear",
            "Room smear",
            "low",
            "Transient definition looks softened while low-mid energy stays elevated, which can indicate baked-in reverb or smeared ambience.",
            0.46
            + min(0.2, (1.85 - transient_flatness) * 0.35)
            + min(0.15, max(0.0, low_mid_band - 0.68) * 1.2),
        )

    if noise_floor_ratio > 0.22 and transient_peak < 0.45:
        add_issue(
            "noise_floor",
            "Raised noise floor",
            "low",
            "The quieter parts of the track sit unusually high, which may indicate broadband noise or persistent background residue.",
            0.5 + min(0.25, (noise_floor_ratio - 0.22) * 1.5),
        )

    if not issues:
        add_issue(
            "general_cleanup",
            "General cleanup",
            "low",
            "No dominant defect class was detected, so a gentle cleanup path is recommended.",
            0.4,
        )

    recommended_preset = "ai_song_cleanup"
    if any(issue["id"] == "metallic_highs" for issue in issues) and len(issues) == 1:
        recommended_preset = "reduce_metallic_harshness"
    elif any(issue["id"] == "dull_top_end" for issue in issues) and len(issues) == 1:
        recommended_preset = "restore_brightness"
    elif len(issues) == 1 and issues[0]["id"] == "general_cleanup":
        recommended_preset = "gentle_cleanup"

    high_count = sum(1 for issue in issues if issue["severity"] == "high")
    medium_count = sum(1 for issue in issues if issue["severity"] == "medium")
    has_robotic_vocals = any(issue["id"] == "robotic_vocals" for issue in issues)

    suggested_intensity = "light"
    if high_count >= 2 or (high_count >= 1 and medium_count >= 2):
        suggested_intensity = "strong"
    elif has_robotic_vocals or high_count >= 1 or medium_count >= 2:
        suggested_intensity = "medium"

    planned_repair_modules = list(dict.fromkeys(issue["repair"] for issue in issues if issue.get("repair")))
    if not planned_repair_modules:
        planned_repair_modules = ["Gentle cleanup: keep the repair path conservative"]

    return {
        "duration_sec": round(duration_sec, 2),
        "sample_rate": sample_rate,
        "peak": round(peak, 4),
        "rms": round(rms, 4),
        "crest_factor": round(crest_factor, 3),
        "spectral_centroid_hz": round(centroid, 2),
        "estimated_cutoff_hz": round(lower_cutoff_knee_hz, 2) if lower_cutoff_knee_hz is not None else None,
        "high_band_ratio": round(high_band, 4),
        "harsh_band_ratio": round(harsh_band, 4),
        "noise_floor": round(noise_floor, 4),
        "noise_floor_ratio": round(noise_floor_ratio, 4),
        "transient_peak": round(transient_peak, 4),
        "vocal_presence_variation": round(vocal_presence_variation, 4) if vocal_presence_variation is not None else None,
        "vocal_artifact_variation": round(vocal_artifact_variation, 4) if vocal_artifact_variation is not None else None,
        "transient_flatness": round(transient_flatness, 4) if transient_flatness is not None else None,
        "overall_confidence": round(float(np.mean([issue["confidence"] for issue in issues])), 2),
        "issues": issues,
        "suggested_intensity": suggested_intensity,
        "planned_repair_modules": planned_repair_modules,
        "recommended_preset": recommended_preset,
        "runtime_estimate_sec": 45,
    }


def write_analysis_report(
    analysis_path: Path,
    project_id: str,
    analysis: dict,
    run_id: str | None = None,
) -> None:
    analysis_report = {
        "schema_version": ANALYSIS_REPORT_SCHEMA_VERSION,
        "project_id": project_id,
        "run_id": run_id,
        **analysis,
    }
    analysis_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_path.write_text(json.dumps(analysis_report, indent=2), encoding="utf-8")


def load_analysis_report(analysis_path: Path) -> dict:
    return json.loads(analysis_path.read_text(encoding="utf-8"))


def analyze_project(input_path: Path, normalized_path: Path, analysis_path: Path, project_id: str) -> int:
    run_ffmpeg_normalize(input_path, normalized_path)
    analysis = compute_analysis(normalized_path)
    spectrogram_path = analysis_path.parent / "analysis-spectrogram.png"
    generate_spectrogram_image(normalized_path, spectrogram_path)
    analysis["spectrogram_path"] = str(spectrogram_path)
    write_analysis_report(analysis_path, project_id, analysis)
    return 0


def build_filter_chain(analysis: dict) -> str:
    issue_ids = {issue["id"] for issue in analysis["issues"]}
    filters: list[str] = []

    if "dull_top_end" in issue_ids:
        filters.append("highshelf=f=9000:g=3")

    if "metallic_highs" in issue_ids:
        filters.append("equalizer=f=8200:t=q:w=1.4:g=-3")

    if "codec_haze" in issue_ids:
        filters.append("equalizer=f=2600:t=q:w=1.0:g=-1.5")

    if "congested_mix" in issue_ids:
        filters.append("alimiter=limit=0.93")

    if not filters:
        filters.append("volume=1.0")

    return ",".join(filters)


def intensity_scale(intensity: str) -> float:
    return {
        "light": 0.75,
        "medium": 1.0,
        "strong": 1.35,
    }.get(intensity, 1.0)


def build_vocal_filter_chain(analysis: dict, intensity: str) -> str:
    issue_ids = {issue["id"] for issue in analysis["issues"]}
    scale = intensity_scale(intensity)
    filters = ["highpass=f=90"]

    if "robotic_vocals" in issue_ids:
        # Conservative vocal humanization: soften static presence buildup and
        # gently smooth the upper vocal band without introducing synthetic pitch
        # processing or modulation artifacts.
        filters.append(f"equalizer=f=3200:t=q:w=1.2:g={-1.5 * scale:.2f}")
        filters.append(f"equalizer=f=6800:t=q:w=1.6:g={-1.5 * scale:.2f}")

    if "dull_top_end" in issue_ids:
        filters.append(f"highshelf=f=7000:g={2.0 * scale:.2f}")

    if "room_smear" in issue_ids:
        filters.append(f"equalizer=f=2400:t=q:w=1.0:g={-0.8 * scale:.2f}")
        filters.append(f"highshelf=f=8200:g={0.8 * scale:.2f}")

    if "metallic_highs" in issue_ids:
        threshold = 0.10 / scale
        amount = 0.35 * scale
        filters.append(
            f"deesser=i={amount:.2f}:m=0.5:f=0.5:s=o:threshold={threshold:.3f}:t=0"
        )
        filters.append(f"equalizer=f=7600:t=q:w=1.5:g={-3.0 * scale:.2f}")

    if "congested_mix" in issue_ids:
        ratio = 1.0 + (0.5 * scale)
        filters.append(f"acompressor=threshold=0.18:ratio={ratio:.2f}:attack=20:release=120")

    # No limiter here — this is an intermediate stem, not the final output.
    # The final mix gets limited during export.
    if not filters[1:]:  # only highpass, no conditional filters added
        return filters[0]
    return ",".join(filters)


def build_music_filter_chain(analysis: dict, intensity: str) -> str:
    issue_ids = {issue["id"] for issue in analysis["issues"]}
    scale = intensity_scale(intensity)
    filters: list[str] = []

    if "dull_top_end" in issue_ids:
        filters.append(f"highshelf=f=9500:g={2.5 * scale:.2f}")

    if "room_smear" in issue_ids:
        filters.append(f"equalizer=f=2300:t=q:w=1.0:g={-1.0 * scale:.2f}")
        filters.append(f"highshelf=f=9000:g={0.9 * scale:.2f}")

    if "codec_haze" in issue_ids:
        filters.append(f"equalizer=f=2600:t=q:w=1.2:g={-2.0 * scale:.2f}")

    if "metallic_highs" in issue_ids:
        filters.append(f"equalizer=f=8200:t=q:w=1.4:g={-2.0 * scale:.2f}")

    if "congested_mix" in issue_ids:
        ratio = 1.0 + (0.8 * scale)
        filters.append(f"acompressor=threshold=0.12:ratio={ratio:.2f}:attack=10:release=80")

    filters.append("alimiter=limit=0.93")
    return ",".join(filters)


def split_stems(normalized_path: Path, vocals_path: Path, music_path: Path, gpu_enabled: bool) -> None:
    if importlib.util.find_spec("demucs") is None:
        raise RuntimeError(
            "Demucs is not installed. Install engine dependencies with `python -m pip install -r engine/requirements.txt`."
        )

    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model

    model = get_model("htdemucs")
    device = "cuda" if gpu_enabled and torch.cuda.is_available() else "cpu"
    audio = load_audio(normalized_path, model.samplerate, model.audio_channels)
    mix = torch.from_numpy(audio.T).float()

    ref = mix.mean(0)
    mix = mix - ref.mean()
    mix = mix / ref.std().clamp_min(1e-8)

    with torch.no_grad():
        sources = apply_model(
            model,
            mix[None],
            device=device,
            shifts=1,
            split=True,
            overlap=0.25,
            progress=False,
            num_workers=0,
        )[0]

    sources = (sources * ref.std().clamp_min(1e-8)) + ref.mean()
    source_names = list(model.sources)

    if "vocals" not in source_names:
        raise RuntimeError("Demucs model did not expose a vocals stem")

    vocals_index = source_names.index("vocals")
    vocals = sources[vocals_index].detach().cpu().numpy().T
    music = torch.sum(torch.cat([sources[:vocals_index], sources[vocals_index + 1 :]], dim=0), dim=0).detach().cpu().numpy().T

    write_audio_stereo_with_rate(vocals_path, normalize_peak(vocals), model.samplerate)
    write_audio_stereo_with_rate(music_path, normalize_peak(music), model.samplerate)


def denoise_vocals_with_deepfilternet(
    vocals_path: Path,
    output_path: Path,
    gpu_enabled: bool,
) -> None:
    if importlib.util.find_spec("df") is None:
        raise RuntimeError(
            "DeepFilterNet is not installed. Install engine dependencies with `python -m pip install -r engine/requirements.txt`."
        )

    import torch

    from df.enhance import enhance as df_enhance
    from df.enhance import init_df

    model, df_state, _suffix = init_df()
    df_sample_rate = df_state.sr()
    prepared_vocals_path = vocals_path

    if df_sample_rate != 44100:
        prepared_vocals_path = output_path.parent / "vocals_for_df.wav"
        resample_audio_file(vocals_path, prepared_vocals_path, df_sample_rate)

    audio = load_audio(prepared_vocals_path, df_sample_rate, 2)
    waveform = torch.from_numpy(audio.T.copy()).float()
    enhanced = df_enhance(
        model,
        df_state,
        waveform,
        pad=True,
        atten_lim_db=6.0,
    )
    enhanced_audio = enhanced.detach().cpu().numpy().T
    enhanced_path = output_path

    if df_sample_rate != 44100:
        enhanced_path = output_path.parent / "vocals_denoised_df_48k.wav"

    write_audio_stereo_with_rate(enhanced_path, enhanced_audio, df_sample_rate)

    if enhanced_path != output_path:
        resample_audio_file(enhanced_path, output_path, 44100)


def repair_vocals(
    vocals_path: Path,
    repaired_vocals_path: Path,
    analysis: dict,
    intensity: str,
    gpu_enabled: bool,
) -> None:
    issue_ids = {issue["id"] for issue in analysis["issues"]}
    filtered_input_path = vocals_path

    if "noise_floor" in issue_ids:
        denoised_vocals_path = repaired_vocals_path.parent / "vocals_denoised.wav"
        denoise_vocals_with_deepfilternet(vocals_path, denoised_vocals_path, gpu_enabled)
        filtered_input_path = denoised_vocals_path

    filter_chain = build_vocal_filter_chain(analysis, intensity)
    run_ffmpeg_filter(filtered_input_path, repaired_vocals_path, filter_chain)


def reconstruct_mix(vocals_path: Path, music_path: Path, preview_path: Path) -> None:
    vocals, _sample_rate = load_audio_stereo(vocals_path)
    music, _sample_rate = load_audio_stereo(music_path)

    frame_count = max(vocals.shape[0], music.shape[0])

    def pad(audio: np.ndarray) -> np.ndarray:
        if audio.shape[0] == frame_count:
            return audio

        padded = np.zeros((frame_count, 2), dtype=np.float32)
        padded[: audio.shape[0]] = audio
        return padded

    mix = pad(vocals) + pad(music)
    write_audio_stereo(preview_path, normalize_peak(mix))


def run_ffmpeg_filter(input_path: Path, output_path: Path, filter_chain: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-af",
        filter_chain,
        "-ar",
        "48000",
        "-acodec",
        "pcm_f32le",
        str(output_path),
    ]

    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "FFmpeg repair filter chain failed")


def export_cleaned_mix(preview_path: Path, export_path: Path) -> None:
    export_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(preview_path),
        "-af",
        "alimiter=limit=0.95:level_in=1:level_out=1:attack=5:release=50",
        "-ar",
        "48000",
        "-acodec",
        "pcm_s16le",
        str(export_path),
    ]

    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "FFmpeg export failed")


def export_cleaned_mix_flac(preview_path: Path, export_path: Path) -> None:
    export_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(preview_path),
        "-af",
        "alimiter=limit=0.95:level_in=1:level_out=1:attack=5:release=50",
        "-ar",
        "48000",
        "-acodec",
        "flac",
        str(export_path),
    ]

    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "FFmpeg FLAC export failed")


def write_report(
    report_path: Path,
    payload: dict,
    normalized_path: Path,
    analysis_path: Path,
    analysis: dict,
    vocals_path: Path,
    music_path: Path,
    repaired_vocals_path: Path,
    repaired_music_path: Path,
    preview_path: Path,
    export_path: Path,
) -> None:
    report = {
        "project_id": payload["project_id"],
        "run_id": payload["run_id"],
        "preset": payload["preset"],
        "normalized_path": str(normalized_path),
        "analysis_report_path": str(analysis_path),
        "recommended_preset": analysis["recommended_preset"],
        "vocals_path": str(vocals_path),
        "music_path": str(music_path),
        "repaired_vocals_path": str(repaired_vocals_path),
        "repaired_music_path": str(repaired_music_path),
        "preview_path": str(preview_path),
        "export_path": str(export_path),
        "status": "completed",
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def run(payload_path: Path) -> int:
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    run_id = payload["run_id"]
    input_path = Path(payload["input_path"])
    analysis_report_path = payload.get("analysis_report_path")
    intensity = str(payload.get("options", {}).get("intensity", "medium"))
    gpu_enabled = bool(payload.get("options", {}).get("gpu_enabled", True))
    run_dir = payload_path.parent
    project_dir = run_dir.parent.parent
    normalized_path = project_dir / "source" / "normalized.wav"
    analysis_path = project_dir / "analysis" / "analysis-report.json"
    stems_dir = run_dir / "stems"
    vocals_path = stems_dir / "vocals.wav"
    music_path = stems_dir / "music.wav"
    repaired_vocals_path = stems_dir / "vocals_repaired.wav"
    repaired_music_path = stems_dir / "music_repaired.wav"
    preview_path = run_dir / "previews" / "mix_preview.wav"
    export_path = run_dir / "exports" / "song_cleaned.wav"
    report_path = run_dir / "run-report.json"
    analysis: dict | None = None

    steps = [
        ("normalize", "Preparing and normalizing audio"),
        ("separate_stems", "Separating vocals and backing stems with Demucs"),
        ("repair_vocals", "Applying targeted cleanup to the vocal stem"),
        ("repair_music", "Applying targeted cleanup to the music stem"),
        ("reconstruct_mix", "Rebuilding the cleaned mix and exports"),
    ]

    if analysis_report_path:
        analysis = load_analysis_report(Path(analysis_report_path))
    elif analysis_path.exists():
        analysis = load_analysis_report(analysis_path)

    for index, (step, message) in enumerate(steps, start=1):
        emit(
            {
                "run_id": run_id,
                "step": step,
                "status": "running",
                "progress": round(index / len(steps), 2),
                "message": message,
            }
        )

        if step == "normalize":
            run_ffmpeg_normalize(input_path, normalized_path)
        elif step == "separate_stems":
            split_stems(
                normalized_path,
                vocals_path,
                music_path,
                bool(payload.get("options", {}).get("gpu_enabled", True)),
            )
        elif step == "repair_vocals":
            if analysis is None:
                raise RuntimeError("Analysis must exist before vocal repair")

            repair_vocals(
                vocals_path,
                repaired_vocals_path,
                analysis,
                intensity,
                gpu_enabled,
            )
        elif step == "repair_music":
            if analysis is None:
                raise RuntimeError("Analysis must exist before music repair")

            run_ffmpeg_filter(music_path, repaired_music_path, build_music_filter_chain(analysis, intensity))
        elif step == "reconstruct_mix":
            reconstruct_mix(repaired_vocals_path, repaired_music_path, preview_path)
            export_cleaned_mix(preview_path, export_path)

        emit(
            {
                "run_id": run_id,
                "step": step,
                "status": "completed",
                "progress": round(index / len(steps), 2),
                "message": f"{message} completed",
            }
        )

        time.sleep(0.05)

    if analysis is None:
        raise RuntimeError("Analysis is required before cleanup. Run project analysis first.")

    write_report(
        report_path,
        payload,
        normalized_path,
        analysis_path,
        analysis,
        vocals_path,
        music_path,
        repaired_vocals_path,
        repaired_music_path,
        preview_path,
        export_path,
    )

    emit(
        {
            "run_id": run_id,
            "status": "completed",
            "report_path": str(report_path),
            "exports": [str(export_path)],
        }
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="B Audio Project engine entry point")
    parser.add_argument("--run-payload", type=Path, help="Path to a run payload JSON file")
    args = parser.parse_args()

    if args.run_payload is None:
        print("No run payload provided", file=sys.stderr)
        return 1

    try:
        return run(args.run_payload)
    except Exception as error:  # noqa: BLE001
        print(str(error), file=sys.stderr)
        return 1


def reexport(preview_path: Path, export_path: Path, fmt: str) -> None:
    fmt = fmt.lower().strip()
    if fmt == "flac":
        export_cleaned_mix_flac(preview_path, export_path)
    else:
        export_cleaned_mix(preview_path, export_path)


def parse_reexport_argv() -> tuple[Path, Path, str]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--export-path", type=Path, required=True)
    parser.add_argument("--format", type=str, default="wav")
    args = parser.parse_args()
    return args.preview, args.export_path, args.format


def parse_analyze_argv() -> tuple[Path, Path, Path, str]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyze-input", type=Path, required=True)
    parser.add_argument("--normalized-output", type=Path, required=True)
    parser.add_argument("--analysis-report", type=Path, required=True)
    parser.add_argument("--project-id", type=str, required=True)
    args = parser.parse_args()
    return args.analyze_input, args.normalized_output, args.analysis_report, args.project_id


if __name__ == "__main__":
    if "--analyze-input" in sys.argv:
        input_path, normalized_path, analysis_path, project_id = parse_analyze_argv()
        raise SystemExit(analyze_project(input_path, normalized_path, analysis_path, project_id))

    if "--reexport" in sys.argv:
        preview, export_path, fmt = parse_reexport_argv()
        reexport(preview, export_path, fmt)
        raise SystemExit(0)

    raise SystemExit(main())
