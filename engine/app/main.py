from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np


def emit(payload: dict) -> None:
    print(json.dumps(payload), flush=True)


def run_ffmpeg_normalize(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    issues: list[dict] = []

    if high_band < 0.045:
        issues.append(
            {
                "id": "dull_top_end",
                "label": "Dull top end",
                "severity": "high",
                "description": "High-frequency energy is low compared with the rest of the track.",
            }
        )

    if harsh_band > 0.32:
        issues.append(
            {
                "id": "metallic_highs",
                "label": "Metallic highs",
                "severity": "medium",
                "description": "The upper spectrum has a strong concentration in the metallic harshness band.",
            }
        )

    if rms > 0.18 and peak / max(rms, 1e-6) < 3.2:
        issues.append(
            {
                "id": "congested_mix",
                "label": "Congested mix",
                "severity": "medium",
                "description": "The track appears dense and dynamically constrained.",
            }
        )

    if centroid < 3200 and low_mid_band > 0.72:
        issues.append(
            {
                "id": "codec_haze",
                "label": "Codec haze",
                "severity": "medium",
                "description": "Energy is clustered in the low-mid range, which can sound hazy or smeared.",
            }
        )

    if not issues:
        issues.append(
            {
                "id": "general_cleanup",
                "label": "General cleanup",
                "severity": "low",
                "description": "No dominant defect class was detected, so a gentle cleanup path is recommended.",
            }
        )

    recommended_preset = "ai_song_cleanup"
    if any(issue["id"] == "metallic_highs" for issue in issues) and len(issues) == 1:
        recommended_preset = "reduce_metallic_harshness"
    elif any(issue["id"] == "dull_top_end" for issue in issues) and len(issues) == 1:
        recommended_preset = "restore_brightness"
    elif len(issues) == 1 and issues[0]["id"] == "general_cleanup":
        recommended_preset = "gentle_cleanup"

    return {
        "duration_sec": round(duration_sec, 2),
        "sample_rate": sample_rate,
        "peak": round(peak, 4),
        "rms": round(rms, 4),
        "spectral_centroid_hz": round(centroid, 2),
        "high_band_ratio": round(high_band, 4),
        "harsh_band_ratio": round(harsh_band, 4),
        "issues": issues,
        "recommended_preset": recommended_preset,
        "runtime_estimate_sec": 45,
    }


def write_analysis_report(analysis_path: Path, payload: dict, analysis: dict) -> None:
    analysis_report = {
        "project_id": payload["project_id"],
        "run_id": payload["run_id"],
        **analysis,
    }
    analysis_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_path.write_text(json.dumps(analysis_report, indent=2), encoding="utf-8")


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


def build_vocal_filter_chain(analysis: dict) -> str:
    issue_ids = {issue["id"] for issue in analysis["issues"]}
    filters = ["highpass=f=90"]

    if "dull_top_end" in issue_ids:
        filters.append("highshelf=f=7000:g=2")

    if "metallic_highs" in issue_ids:
        filters.append("equalizer=f=7600:t=q:w=1.5:g=-3")

    if "congested_mix" in issue_ids:
        filters.append("acompressor=threshold=0.18:ratio=1.5:attack=20:release=120")

    # No limiter here — this is an intermediate stem, not the final output.
    # The final mix gets limited during export.
    if not filters[1:]:  # only highpass, no conditional filters added
        return filters[0]
    return ",".join(filters)


def build_music_filter_chain(analysis: dict) -> str:
    issue_ids = {issue["id"] for issue in analysis["issues"]}
    filters: list[str] = []

    if "dull_top_end" in issue_ids:
        filters.append("highshelf=f=9500:g=2.5")

    if "codec_haze" in issue_ids:
        filters.append("equalizer=f=2600:t=q:w=1.2:g=-2")

    if "metallic_highs" in issue_ids:
        filters.append("equalizer=f=8200:t=q:w=1.4:g=-2")

    if "congested_mix" in issue_ids:
        filters.append("acompressor=threshold=0.12:ratio=1.8:attack=10:release=80")

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


def repair_vocals(
    vocals_path: Path,
    repaired_vocals_path: Path,
    analysis: dict,
) -> None:
    filter_chain = build_vocal_filter_chain(analysis)
    run_ffmpeg_filter(vocals_path, repaired_vocals_path, filter_chain)


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
        ("analyze", "Inspecting the track for common AI artifacts"),
        ("separate_stems", "Separating vocals and backing stems with Demucs"),
        ("repair_vocals", "Applying targeted cleanup to the vocal stem"),
        ("repair_music", "Applying targeted cleanup to the music stem"),
        ("reconstruct_mix", "Rebuilding the cleaned mix and exports"),
    ]

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
        elif step == "analyze":
            analysis = compute_analysis(normalized_path)
            write_analysis_report(analysis_path, payload, analysis)
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
            )
        elif step == "repair_music":
            if analysis is None:
                raise RuntimeError("Analysis must exist before music repair")

            run_ffmpeg_filter(music_path, repaired_music_path, build_music_filter_chain(analysis))
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
        raise RuntimeError("Analysis was not generated")

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


if __name__ == "__main__":
    if "--reexport" in sys.argv:
        preview, export_path, fmt = parse_reexport_argv()
        reexport(preview, export_path, fmt)
        raise SystemExit(0)

    raise SystemExit(main())
