from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
import time
from pathlib import Path

from PySide6.QtCore import QThread, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "B Audio Project"
DEFAULT_PRESET = "ai_song_cleanup"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def asset_label(kind: str) -> str:
    labels = {
        "normalized_audio": "Normalized Working File",
        "mix_preview": "Preview Mix",
        "cleaned_export": "Cleaned Export",
        "stem_vocals": "Stem: Vocals",
        "stem_music": "Stem: Music",
        "repaired_vocals": "Repaired Vocals",
        "repaired_music": "Repaired Music",
    }
    return labels.get(kind, kind)


def intensity_description(intensity: str) -> str:
    descriptions = {
        "light": "Uses gentler EQ and compression moves. Best when the track already sounds close and you want to avoid over-processing.",
        "medium": "Balanced default. Applies enough correction to fix common AI artifacts without pushing the sound too far.",
        "strong": "Uses deeper EQ cuts, boosts, and stronger dynamic control. Best for obvious artifacts, but more likely to change the original tone.",
    }
    return descriptions.get(intensity, "")


def preset_description(preset: str) -> str:
    descriptions = {
        "ai_song_cleanup": "Best overall repair path for mixed AI-song defects like robotic vocals, harsh highs, haze, and smeared reconstruction.",
        "restore_brightness": "Best when the main issue is missing air and top-end detail rather than strong vocal or mix defects.",
        "reduce_metallic_harshness": "Best when the track sounds brittle, metallic, or overly sharp in the upper bands.",
        "gentle_cleanup": "Best when the song already sounds close and you only want a light repair pass with lower risk.",
    }
    return descriptions.get(preset, "Balanced restoration path for common AI-generated song defects.")


def runtime_hint(report: dict | None, preset: str, intensity: str, gpu_enabled: bool) -> str:
    base_runtime = int((report or {}).get("runtime_estimate_sec") or 45)
    preset_multiplier = {
        "ai_song_cleanup": 1.0,
        "restore_brightness": 0.85,
        "reduce_metallic_harshness": 0.9,
        "gentle_cleanup": 0.75,
    }.get(preset, 1.0)
    intensity_multiplier = {
        "light": 0.85,
        "medium": 1.0,
        "strong": 1.2,
    }.get(intensity, 1.0)
    device_multiplier = 1.0 if gpu_enabled else 2.2
    estimate = max(20, int(base_runtime * preset_multiplier * intensity_multiplier * device_multiplier))
    mode = "GPU" if gpu_enabled else "CPU"
    return f"Estimated runtime: about {estimate} sec on {mode}."


def format_cutoff_text(report: dict | None) -> str:
    if not report:
        return "Detected cutoff: unavailable"
    cutoff = report.get("estimated_cutoff_hz")
    if cutoff is None:
        return "Detected cutoff: not detected in this analysis report"
    return f"Detected cutoff: {cutoff} Hz"


def pipeline_steps(report: dict | None) -> list[dict]:
    if not report:
        return []
    pipeline_plan = report.get("pipeline_plan") or {}
    steps = pipeline_plan.get("steps")
    return steps if isinstance(steps, list) else []


def pipeline_step_label(step: dict) -> str:
    return step.get("label") or step.get("id") or "Pipeline Step"


def pipeline_module_lines(step: dict) -> list[str]:
    modules = step.get("modules")
    if not isinstance(modules, list):
        return []

    lines: list[str] = []
    for module in modules:
        if not isinstance(module, dict):
            continue
        label = module.get("label") or module.get("id") or "Module"
        reason = module.get("reason")
        if reason:
            lines.append(f"{label} - {reason}")
        else:
            lines.append(label)
    return lines


def pipeline_stage_lines(report: dict | None) -> list[str]:
    lines: list[str] = []
    for step in pipeline_steps(report):
        module_lines = pipeline_module_lines(step)
        if not module_lines:
            lines.append(pipeline_step_label(step))
            continue
        for module_line in module_lines:
            lines.append(f"{pipeline_step_label(step)}: {module_line}")
    return lines


def pipeline_step_lookup(report: dict | None) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for step in pipeline_steps(report):
        step_id = step.get("id")
        if isinstance(step_id, str) and step_id:
            lookup[step_id] = step
    return lookup


def compare_summary_lines(analysis_report: dict | None, run_report: dict | None) -> list[str]:
    if not analysis_report:
        return ["Run analysis to generate a repair summary."]

    issues = analysis_report.get("issues", [])
    if not issues:
        return ["No dominant artifact class was detected, so the repair path stays conservative."]

    lines: list[str] = []
    for issue in issues[:4]:
        title = issue.get("artifact_title") or issue.get("label") or issue.get("id") or "Issue"
        repair = issue.get("repair")
        if repair:
            lines.append(f"{title}: {repair}")
        else:
            lines.append(f"{title}: addressed by the selected cleanup path.")

    pipeline_lines = pipeline_stage_lines(run_report)
    if pipeline_lines:
        lines.append(f"Pipeline: {len(pipeline_steps(run_report))} stages prepared for this run.")

    metrics = (run_report or {}).get("metrics") or {}
    delta = metrics.get("delta") or {}
    metric_lines: list[str] = []
    harsh_delta = delta.get("harsh_band_ratio")
    if isinstance(harsh_delta, (int, float)) and harsh_delta < -0.002:
        metric_lines.append(f"Harsh high-band energy reduced ({harsh_delta:.4f}).")
    high_band_delta = delta.get("high_band_ratio")
    if isinstance(high_band_delta, (int, float)) and high_band_delta > 0.002:
        metric_lines.append(f"Top-end energy increased ({high_band_delta:+.4f}).")
    crest_delta = delta.get("crest_factor")
    if isinstance(crest_delta, (int, float)) and crest_delta > 0.08:
        metric_lines.append(f"Transient contrast improved ({crest_delta:+.3f} crest factor).")
    stereo_delta = delta.get("stereo_correlation")
    if isinstance(stereo_delta, (int, float)) and stereo_delta > 0.015:
        metric_lines.append(f"Stereo image became more stable ({stereo_delta:+.4f} correlation).")
    lines.extend(metric_lines[:3])

    return lines


def format_milliseconds(value: int) -> str:
    total_seconds = max(0, value // 1000)
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


@dataclass
class AppPaths:
    workspace_dir: Path
    storage_dir: Path
    database_path: Path
    engine_entry: Path
    python_command: str = "python"

    @classmethod
    def discover(cls) -> "AppPaths":
        workspace_dir = Path(__file__).resolve().parents[2]
        storage_dir = workspace_dir / "storage"
        database_path = storage_dir / "app.db"
        engine_entry = workspace_dir / "engine" / "app" / "main.py"
        venv_python = workspace_dir / ".venv" / "Scripts" / "python.exe"
        storage_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            workspace_dir=workspace_dir,
            storage_dir=storage_dir,
            database_path=database_path,
            engine_entry=engine_entry,
            python_command=str(venv_python if venv_python.exists() else Path(sys.executable)),
        )


def probe_runtime(paths: AppPaths) -> dict:
    output = subprocess.run(
        [
            paths.python_command,
            "-c",
            "import json; import torch; print(json.dumps({'cuda_available': bool(torch.cuda.is_available()), 'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))",
        ],
        capture_output=True,
        text=True,
    )
    runtime = {"cuda_available": False, "gpu_name": None}
    if output.returncode == 0:
        try:
            runtime = json.loads(output.stdout)
        except json.JSONDecodeError:
            runtime = {"cuda_available": False, "gpu_name": None}
    return {
        "app_name": APP_NAME,
        "storage_dir": str(paths.storage_dir),
        "database_path": str(paths.database_path),
        "engine_entry": str(paths.engine_entry),
        "python_command": paths.python_command,
        **runtime,
    }


class Database:
    def __init__(self, paths: AppPaths) -> None:
        self.paths = paths
        self.paths.storage_dir.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.paths.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS source_files (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    original_path TEXT NOT NULL,
                    normalized_path TEXT,
                    filename TEXT NOT NULL,
                    duration_sec REAL,
                    sample_rate INTEGER,
                    channels INTEGER,
                    format TEXT,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );

                CREATE TABLE IF NOT EXISTS analysis_reports (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    report_path TEXT NOT NULL,
                    recommended_preset TEXT,
                    runtime_estimate_sec INTEGER,
                    summary_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );

                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    preset TEXT NOT NULL,
                    intensity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    plan_path TEXT,
                    report_path TEXT,
                    failure_message TEXT,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                );

                CREATE TABLE IF NOT EXISTS run_steps (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    metrics_json TEXT,
                    FOREIGN KEY(run_id) REFERENCES pipeline_runs(id)
                );

                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    run_id TEXT,
                    kind TEXT NOT NULL,
                    path TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY(project_id) REFERENCES projects(id),
                    FOREIGN KEY(run_id) REFERENCES pipeline_runs(id)
                );

                CREATE TABLE IF NOT EXISTS exports (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    format TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES pipeline_runs(id)
                );
                """
            )

            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(pipeline_runs)").fetchall()
            }
            if "failure_message" not in columns:
                connection.execute("ALTER TABLE pipeline_runs ADD COLUMN failure_message TEXT")
            if "user_feedback" not in columns:
                connection.execute("ALTER TABLE pipeline_runs ADD COLUMN user_feedback TEXT")

    def list_projects(self) -> list[sqlite3.Row]:
        with self.connection() as connection:
            return connection.execute(
                """
                SELECT p.id, p.name, p.status, p.created_at, p.updated_at,
                       (SELECT filename FROM source_files sf WHERE sf.project_id = p.id ORDER BY rowid DESC LIMIT 1) AS source_filename
                FROM projects p
                ORDER BY p.updated_at DESC
                """
            ).fetchall()

    def get_project_detail(self, project_id: str) -> dict:
        with self.connection() as connection:
            project = connection.execute(
                """
                SELECT p.id, p.name, p.status, p.created_at, p.updated_at,
                       (SELECT filename FROM source_files sf WHERE sf.project_id = p.id ORDER BY rowid DESC LIMIT 1) AS source_filename
                FROM projects p
                WHERE p.id = ?
                """,
                (project_id,),
            ).fetchone()
            if project is None:
                raise RuntimeError("Project not found")

            source_file = connection.execute(
                """
                SELECT id, project_id, original_path, normalized_path, filename, duration_sec, sample_rate, channels, format
                FROM source_files
                WHERE project_id = ?
                ORDER BY rowid DESC
                LIMIT 1
                """,
                (project_id,),
            ).fetchone()
            if source_file is None:
                raise RuntimeError("Project source file not found")

            latest_run = connection.execute(
                """
                SELECT id, project_id, preset, intensity, status, started_at, finished_at, report_path, failure_message, user_feedback
                FROM pipeline_runs
                WHERE project_id = ?
                ORDER BY rowid DESC
                LIMIT 1
                """,
                (project_id,),
            ).fetchone()

            analysis_row = connection.execute(
                """
                SELECT id, project_id, report_path, recommended_preset, runtime_estimate_sec, summary_json, created_at
                FROM analysis_reports
                WHERE project_id = ?
                ORDER BY rowid DESC
                LIMIT 1
                """,
                (project_id,),
            ).fetchone()

            analysis_report = None
            if analysis_row is not None:
                summary_json = analysis_row["summary_json"]
                summary = json.loads(summary_json) if summary_json else {}
                analysis_report = {
                    "id": analysis_row["id"],
                    "project_id": analysis_row["project_id"],
                    "report_path": analysis_row["report_path"],
                    "schema_version": summary.get("schema_version"),
                    "compatibility_notice": None
                    if summary.get("schema_version")
                    else "Legacy analysis report detected. Some guidance fields were reconstructed during load.",
                    "recommended_preset": analysis_row["recommended_preset"],
                    "suggested_intensity": summary.get("suggested_intensity", "medium"),
                    "planned_repair_modules": summary.get("planned_repair_modules", []),
                    "runtime_estimate_sec": analysis_row["runtime_estimate_sec"],
                    "overall_confidence": summary.get("overall_confidence"),
                    "estimated_cutoff_hz": summary.get("estimated_cutoff_hz"),
                    "spectrogram_path": summary.get("spectrogram_path"),
                    "created_at": analysis_row["created_at"],
                    "issues": summary.get("issues", []),
                }

            return {
                "project": dict(project),
                "source_file": dict(source_file),
                "analysis_report": analysis_report,
                "latest_run": dict(latest_run) if latest_run is not None else None,
            }

    def get_run_detail(self, run_id: str) -> dict:
        with self.connection() as connection:
            run = connection.execute(
                """
                SELECT id, project_id, preset, intensity, status, started_at, finished_at, report_path, failure_message, user_feedback
                FROM pipeline_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
            if run is None:
                raise RuntimeError("Run not found")

            steps = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT id, run_id, step_name, status, started_at, finished_at, metrics_json
                    FROM run_steps
                    WHERE run_id = ?
                    ORDER BY rowid ASC
                    """,
                    (run_id,),
                ).fetchall()
            ]
            assets = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT id, project_id, run_id, kind, path, metadata_json
                    FROM assets
                    WHERE run_id = ?
                    ORDER BY rowid ASC
                    """,
                    (run_id,),
                ).fetchall()
            ]
            exports = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT id, run_id, format, path, created_at
                    FROM exports
                    WHERE run_id = ?
                    ORDER BY rowid ASC
                    """,
                    (run_id,),
                ).fetchall()
            ]
            run_dict = dict(run)
            run_report = None
            report_path = run_dict.get("report_path")
            if report_path:
                report_file = Path(report_path)
                if report_file.exists():
                    run_report = json.loads(report_file.read_text(encoding="utf-8"))

            return {
                "run": run_dict,
                "report": run_report,
                "steps": steps,
                "assets": assets,
                "exports": exports,
            }

    def import_project(self, source_path: str) -> str:
        source = Path(source_path)
        if not source.exists():
            raise RuntimeError("Source file does not exist")

        project_id = str(uuid.uuid4())
        source_id = str(uuid.uuid4())
        now = utc_now()
        filename = source.name
        project_name = source.stem or "Imported Project"
        project_dir = self.paths.storage_dir / "projects" / project_id
        source_dir = project_dir / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        copied_original_path = source_dir / f"original_{filename}"
        shutil.copy2(source, copied_original_path)

        with self.connection() as connection:
            connection.execute(
                "INSERT INTO projects (id, name, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (project_id, project_name, "imported", now, now),
            )
            connection.execute(
                "INSERT INTO source_files (id, project_id, original_path, normalized_path, filename, duration_sec, sample_rate, channels, format) VALUES (?, ?, ?, NULL, ?, NULL, NULL, NULL, ?)",
                (
                    source_id,
                    project_id,
                    str(copied_original_path),
                    filename,
                    source.suffix.lower().lstrip("."),
                ),
            )
        return project_id

    def store_analysis_report(self, project_id: str, analysis_report_path: Path, normalized_path: Path) -> None:
        now = utc_now()
        analysis_json = analysis_report_path.read_text(encoding="utf-8")
        analysis_value = json.loads(analysis_json)
        recommended_preset = analysis_value.get("recommended_preset", DEFAULT_PRESET)
        runtime_estimate_sec = analysis_value.get("runtime_estimate_sec", 45)

        with self.connection() as connection:
            connection.execute(
                "UPDATE source_files SET normalized_path = ? WHERE project_id = ?",
                (str(normalized_path), project_id),
            )
            connection.execute("DELETE FROM analysis_reports WHERE project_id = ?", (project_id,))
            connection.execute(
                "INSERT INTO analysis_reports (id, project_id, report_path, recommended_preset, runtime_estimate_sec, summary_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    project_id,
                    str(analysis_report_path),
                    recommended_preset,
                    runtime_estimate_sec,
                    analysis_json,
                    now,
                ),
            )
            connection.execute(
                "DELETE FROM assets WHERE project_id = ? AND run_id IS NULL AND kind = 'normalized_audio'",
                (project_id,),
            )
            connection.execute(
                "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?, ?, NULL, ?, ?, NULL)",
                (str(uuid.uuid4()), project_id, "normalized_audio", str(normalized_path)),
            )
            connection.execute(
                "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
                ("analyzed", now, project_id),
            )

    def create_run(self, project_id: str, preset: str, intensity: str) -> tuple[str, Path]:
        now = utc_now()
        run_id = str(uuid.uuid4())
        run_dir = self.paths.storage_dir / "projects" / project_id / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        payload_path = run_dir / "run-payload.json"

        with self.connection() as connection:
            connection.execute(
                "INSERT INTO pipeline_runs (id, project_id, preset, intensity, status, started_at, finished_at, plan_path, report_path, failure_message) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL)",
                (run_id, project_id, preset, intensity, "queued", now),
            )
            connection.execute(
                "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
                ("processing", now, project_id),
            )
        return run_id, payload_path

    def update_run_progress(self, run_id: str, status: str) -> None:
        with self.connection() as connection:
            connection.execute("UPDATE pipeline_runs SET status = ? WHERE id = ?", (status, run_id))

    def upsert_run_step(self, run_id: str, step_name: str, status: str) -> None:
        now = utc_now()
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT id, finished_at FROM run_steps WHERE run_id = ? AND step_name = ? LIMIT 1",
                (run_id, step_name),
            ).fetchone()
            finished_at = now if status in {"completed", "failed"} else None
            if existing is None:
                connection.execute(
                    "INSERT INTO run_steps (id, run_id, step_name, status, started_at, finished_at, metrics_json) VALUES (?, ?, ?, ?, ?, ?, NULL)",
                    (str(uuid.uuid4()), run_id, step_name, status, now, finished_at),
                )
            else:
                connection.execute(
                    "UPDATE run_steps SET status = ?, finished_at = COALESCE(?, finished_at) WHERE id = ?",
                    (status, finished_at, existing["id"]),
                )

    def complete_run(self, run_id: str, report_path: str) -> None:
        now = utc_now()
        report_json = Path(report_path).read_text(encoding="utf-8")
        value = json.loads(report_json)

        with self.connection() as connection:
            project_id = connection.execute(
                "SELECT project_id FROM pipeline_runs WHERE id = ?",
                (run_id,),
            ).fetchone()[0]
            connection.execute(
                "UPDATE pipeline_runs SET status = ?, finished_at = ?, report_path = ?, failure_message = NULL WHERE id = ?",
                ("completed", now, report_path, run_id),
            )
            connection.execute(
                "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
                ("ready", now, project_id),
            )

            normalized_path = value.get("normalized_path")
            if normalized_path:
                connection.execute(
                    "UPDATE source_files SET normalized_path = ? WHERE project_id = ?",
                    (normalized_path, project_id),
                )
                connection.execute(
                    "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?, ?, ?, ?, ?, NULL)",
                    (str(uuid.uuid4()), project_id, run_id, "normalized_audio", normalized_path),
                )

            analysis_report_path = value.get("analysis_report_path")
            if analysis_report_path:
                analysis_json = Path(analysis_report_path).read_text(encoding="utf-8")
                analysis_value = json.loads(analysis_json)
                connection.execute(
                    "INSERT INTO analysis_reports (id, project_id, report_path, recommended_preset, runtime_estimate_sec, summary_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        project_id,
                        analysis_report_path,
                        analysis_value.get("recommended_preset", DEFAULT_PRESET),
                        analysis_value.get("runtime_estimate_sec", 45),
                        analysis_json,
                        now,
                    ),
                )

            preview_path = value.get("preview_path")
            if preview_path:
                connection.execute(
                    "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?, ?, ?, ?, ?, NULL)",
                    (str(uuid.uuid4()), project_id, run_id, "mix_preview", preview_path),
                )

            repaired_spectrogram_path = value.get("repaired_spectrogram_path")
            if repaired_spectrogram_path:
                connection.execute(
                    "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?, ?, ?, ?, ?, NULL)",
                    (str(uuid.uuid4()), project_id, run_id, "repaired_spectrogram", repaired_spectrogram_path),
                )

            for report_key, kind in (
                ("vocals_path", "stem_vocals"),
                ("music_path", "stem_music"),
                ("repaired_vocals_path", "repaired_vocals"),
                ("repaired_music_path", "repaired_music"),
            ):
                asset_path = value.get(report_key)
                if asset_path:
                    connection.execute(
                        "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?, ?, ?, ?, ?, NULL)",
                        (str(uuid.uuid4()), project_id, run_id, kind, asset_path),
                    )

            export_path = value.get("export_path")
            if export_path:
                connection.execute(
                    "INSERT INTO exports (id, run_id, format, path, created_at) VALUES (?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), run_id, "wav", export_path, now),
                )
                connection.execute(
                    "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?, ?, ?, ?, ?, NULL)",
                    (str(uuid.uuid4()), project_id, run_id, "cleaned_export", export_path),
                )

    def fail_run(self, run_id: str, message: str | None) -> None:
        now = utc_now()
        with self.connection() as connection:
            project_id = connection.execute(
                "SELECT project_id FROM pipeline_runs WHERE id = ?",
                (run_id,),
            ).fetchone()[0]
            connection.execute(
                "UPDATE pipeline_runs SET status = ?, finished_at = ?, failure_message = ? WHERE id = ?",
                ("failed", now, message, run_id),
            )
            connection.execute(
                "UPDATE projects SET status = ?, updated_at = ? WHERE id = ?",
                ("failed", now, project_id),
            )

    def add_export(self, run_id: str, project_id: str, fmt: str, path: str) -> None:
        now = utc_now()
        with self.connection() as connection:
            connection.execute(
                "INSERT INTO exports (id, run_id, format, path, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), run_id, fmt, path, now),
            )
            connection.execute(
                "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?, ?, ?, ?, ?, NULL)",
                (str(uuid.uuid4()), project_id, run_id, "cleaned_export", path),
            )

    def set_run_feedback(self, run_id: str, feedback: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE pipeline_runs SET user_feedback = ? WHERE id = ?",
                (feedback, run_id),
            )


class AnalyzeWorker(QThread):
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, db: Database, paths: AppPaths, project_id: str) -> None:
        super().__init__()
        self.db = db
        self.paths = paths
        self.project_id = project_id

    def run(self) -> None:
        try:
            project = self.db.get_project_detail(self.project_id)
            project_dir = self.paths.storage_dir / "projects" / self.project_id
            normalized_path = project_dir / "source" / "normalized.wav"
            analysis_report_path = project_dir / "analysis" / "analysis-report.json"
            output = subprocess.run(
                [
                    self.paths.python_command,
                    str(self.paths.engine_entry),
                    "--analyze-input",
                    project["source_file"]["original_path"],
                    "--normalized-output",
                    str(normalized_path),
                    "--analysis-report",
                    str(analysis_report_path),
                    "--project-id",
                    self.project_id,
                ],
                capture_output=True,
                text=True,
            )
            if output.returncode != 0:
                raise RuntimeError(output.stderr.strip() or "Analysis failed")
            self.db.store_analysis_report(self.project_id, analysis_report_path, normalized_path)
            self.finished_ok.emit(self.project_id)
        except Exception as error:  # noqa: BLE001
            self.failed.emit(str(error))


class RunWorker(QThread):
    progress = Signal(str, str, str, float)
    finished_ok = Signal(str)
    failed = Signal(str)
    cancelled = Signal(str)

    def __init__(
        self,
        db: Database,
        paths: AppPaths,
        project_id: str,
        preset: str,
        intensity: str,
        export_stems: bool,
        apply_finishing: bool,
        gpu_enabled: bool,
    ) -> None:
        super().__init__()
        self.db = db
        self.paths = paths
        self.project_id = project_id
        self.preset = preset
        self.intensity = intensity
        self.export_stems = export_stems
        self.apply_finishing = apply_finishing
        self.gpu_enabled = gpu_enabled
        self.process: subprocess.Popen[str] | None = None
        self.run_id: str | None = None
        self._cancel_requested = False

    def run(self) -> None:
        try:
            project = self.db.get_project_detail(self.project_id)
            analysis_report = project.get("analysis_report")
            if not analysis_report:
                raise RuntimeError("Run analysis first before starting cleanup.")

            run_id, payload_path = self.db.create_run(self.project_id, self.preset, self.intensity)
            self.run_id = run_id
            payload = {
                "project_id": self.project_id,
                "run_id": run_id,
                "input_path": project["source_file"]["original_path"],
                "analysis_report_path": analysis_report["report_path"],
                "preset": self.preset,
                "options": {
                    "intensity": self.intensity,
                    "apply_light_finishing": self.apply_finishing,
                    "export_stems": self.export_stems,
                    "gpu_enabled": self.gpu_enabled,
                },
            }
            payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            process = subprocess.Popen(
                [self.paths.python_command, str(self.paths.engine_entry), "--run-payload", str(payload_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.process = process
            self.db.update_run_progress(run_id, "running")
            assert process.stdout is not None
            for raw_line in process.stdout:
                if self._cancel_requested:
                    break
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue

                step = value.get("step")
                if step:
                    status = value.get("status", "running")
                    message = value.get("message", "")
                    progress = float(value.get("progress", 0.0))
                    self.db.upsert_run_step(run_id, step, status)
                    self.progress.emit(step, status, message, progress)
                    continue

                if value.get("status") == "completed" and value.get("report_path"):
                    self.db.complete_run(run_id, value["report_path"])

            stderr_output = process.stderr.read() if process.stderr is not None else ""
            return_code = process.wait()
            self.process = None
            if self._cancel_requested:
                self.db.fail_run(run_id, "Run cancelled by user")
                self.cancelled.emit(run_id)
                return
            if return_code != 0:
                failure_message = stderr_output.strip() or "Engine process failed"
                self.db.fail_run(run_id, failure_message)
                raise RuntimeError(failure_message)

            self.finished_ok.emit(run_id)
        except Exception as error:  # noqa: BLE001
            self.failed.emit(str(error))

    def cancel(self) -> None:
        self._cancel_requested = True
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()


class ExportWorker(QThread):
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, db: Database, paths: AppPaths, project_id: str, run_id: str, fmt: str) -> None:
        super().__init__()
        self.db = db
        self.paths = paths
        self.project_id = project_id
        self.run_id = run_id
        self.fmt = fmt.lower()

    def run(self) -> None:
        try:
            run_detail = self.db.get_run_detail(self.run_id)
            preview_asset = next(
                (asset for asset in run_detail["assets"] if asset["kind"] == "mix_preview"),
                None,
            )
            if preview_asset is None:
                raise RuntimeError("No preview mix found for this run")

            export_dir = self.paths.storage_dir / "projects" / self.project_id / "runs" / self.run_id / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            extension = "flac" if self.fmt == "flac" else "wav"
            export_path = export_dir / f"song_cleaned.{extension}"

            output = subprocess.run(
                [
                    self.paths.python_command,
                    str(self.paths.engine_entry),
                    "--reexport",
                    "--preview",
                    preview_asset["path"],
                    "--export-path",
                    str(export_path),
                    "--format",
                    self.fmt,
                ],
                capture_output=True,
                text=True,
            )
            if output.returncode != 0:
                raise RuntimeError(output.stderr.strip() or "Reexport failed")

            self.db.add_export(self.run_id, self.project_id, self.fmt, str(export_path))
            self.finished_ok.emit(str(export_path))
        except Exception as error:  # noqa: BLE001
            self.failed.emit(str(error))


class AudioCard(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("audioCard")
        self.audio_output = QAudioOutput(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        self.status_badge = QLabel("No Source")
        self.status_badge.setObjectName("audioBadge")
        title_row.addWidget(self.title_label)
        title_row.addStretch(1)
        title_row.addWidget(self.status_badge)

        self.path_label = QLabel("Not available yet.")
        self.path_label.setObjectName("audioMeta")
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        time_row = QHBoxLayout()
        self.elapsed_label = QLabel("00:00")
        self.elapsed_label.setObjectName("audioMeta")
        self.duration_label = QLabel("00:00")
        self.duration_label.setObjectName("audioMeta")
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self._seek)
        time_row.addWidget(self.elapsed_label)
        time_row.addWidget(self.position_slider, 1)
        time_row.addWidget(self.duration_label)

        button_row = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.setObjectName("transportPrimary")
        self.play_button.clicked.connect(self.toggle_playback)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("transportGhost")
        self.stop_button.clicked.connect(self.stop)
        button_row.addWidget(self.play_button)
        button_row.addWidget(self.stop_button)
        button_row.addStretch(1)

        layout.addLayout(title_row)
        layout.addWidget(self.path_label)
        layout.addLayout(time_row)
        layout.addLayout(button_row)

        self.player.playbackStateChanged.connect(self._sync_buttons)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.source_path: str | None = None
        self.duration_ms = 0
        self._sync_buttons()

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_source(self, path: str | None) -> None:
        self.source_path = path if path and Path(path).exists() else None
        self.path_label.setText(path or "Not available yet.")
        if self.source_path:
            self.player.setSource(QUrl.fromLocalFile(self.source_path))
        else:
            self.player.setSource(QUrl())
        self.duration_ms = 0
        self.position_slider.setRange(0, 0)
        self.elapsed_label.setText("00:00")
        self.duration_label.setText("00:00")
        self.stop()
        self._sync_buttons()

    def toggle_playback(self) -> None:
        if not self.source_path:
            return
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop(self) -> None:
        self.player.stop()

    def current_position(self) -> int:
        return self.player.position()

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def _seek(self, position: int) -> None:
        if self.source_path:
            self.player.setPosition(position)

    def _on_position_changed(self, position: int) -> None:
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)
        self.elapsed_label.setText(format_milliseconds(position))

    def _on_duration_changed(self, duration: int) -> None:
        self.duration_ms = duration
        self.position_slider.setRange(0, duration)
        self.duration_label.setText(format_milliseconds(duration))

    def _sync_buttons(self) -> None:
        enabled = self.source_path is not None
        self.play_button.setEnabled(enabled)
        self.stop_button.setEnabled(enabled)
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("Pause")
            self.status_badge.setText("Playing")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.play_button.setText("Play")
            self.status_badge.setText("Paused")
        else:
            self.play_button.setText("Play")
            self.status_badge.setText("Ready" if enabled else "No Source")


class ABCompareDeck(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("audioCard")
        self.audio_output_a = QAudioOutput(self)
        self.audio_output_b = QAudioOutput(self)
        self.player_a = QMediaPlayer(self)
        self.player_b = QMediaPlayer(self)
        self.player_a.setAudioOutput(self.audio_output_a)
        self.player_b.setAudioOutput(self.audio_output_b)
        self.audio_output_a.setVolume(0.8)
        self.audio_output_b.setVolume(0.8)
        self.active_key = "a"
        self.source_a: str | None = None
        self.source_b: str | None = None
        self.loop_start_ms: int | None = None
        self.loop_end_ms: int | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        self.title_label = QLabel("A/B Compare")
        self.title_label.setObjectName("sectionTitle")
        self.active_badge = QLabel("Active A")
        self.active_badge.setObjectName("audioBadge")
        self.summary_label = QLabel("Original vs repaired playback with seamless switching.")
        self.summary_label.setObjectName("audioMeta")
        self.summary_label.setWordWrap(True)
        title_row.addWidget(self.title_label)
        title_row.addStretch(1)
        title_row.addWidget(self.active_badge)
        layout.addLayout(title_row)
        layout.addWidget(self.summary_label)

        source_row = QHBoxLayout()
        self.source_a_label = QLabel("A: Original")
        self.source_a_label.setObjectName("abBadge")
        self.source_b_label = QLabel("B: Repaired")
        self.source_b_label.setObjectName("abBadge")
        self.active_label = QLabel("Switch between sources while keeping the same playback position.")
        self.active_label.setObjectName("audioMeta")
        source_row.addWidget(self.source_a_label)
        source_row.addWidget(self.source_b_label)
        source_row.addStretch(1)
        source_row.addWidget(self.active_label)
        layout.addLayout(source_row)

        path_row = QHBoxLayout()
        self.path_a_label = QLabel("-")
        self.path_b_label = QLabel("-")
        self.path_a_label.setObjectName("audioMeta")
        self.path_b_label.setObjectName("audioMeta")
        self.path_a_label.setWordWrap(True)
        self.path_b_label.setWordWrap(True)
        self.path_a_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.path_b_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path_row.addWidget(self.path_a_label, 1)
        path_row.addWidget(self.path_b_label, 1)
        layout.addLayout(path_row)

        timeline_row = QHBoxLayout()
        self.elapsed_label = QLabel("00:00")
        self.elapsed_label.setObjectName("audioMeta")
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self._seek)
        self.duration_label = QLabel("00:00")
        self.duration_label.setObjectName("audioMeta")
        timeline_row.addWidget(self.elapsed_label)
        timeline_row.addWidget(self.position_slider, 1)
        timeline_row.addWidget(self.duration_label)
        layout.addLayout(timeline_row)

        loop_row = QHBoxLayout()
        self.loop_set_start_button = QPushButton("Set Loop In")
        self.loop_set_start_button.setObjectName("transportGhost")
        self.loop_set_start_button.clicked.connect(self.set_loop_start)
        self.loop_set_end_button = QPushButton("Set Loop Out")
        self.loop_set_end_button.setObjectName("transportGhost")
        self.loop_set_end_button.clicked.connect(self.set_loop_end)
        self.loop_clear_button = QPushButton("Clear Loop")
        self.loop_clear_button.setObjectName("transportGhost")
        self.loop_clear_button.clicked.connect(self.clear_loop)
        self.loop_label = QLabel("Loop: off")
        self.loop_label.setObjectName("audioMeta")
        loop_row.addWidget(self.loop_set_start_button)
        loop_row.addWidget(self.loop_set_end_button)
        loop_row.addWidget(self.loop_clear_button)
        loop_row.addWidget(self.loop_label)
        loop_row.addStretch(1)
        layout.addLayout(loop_row)

        controls_row = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.setObjectName("transportPrimary")
        self.play_button.clicked.connect(self.toggle_playback)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("transportGhost")
        self.stop_button.clicked.connect(self.stop)
        self.switch_button = QPushButton("Switch A/B")
        self.switch_button.setObjectName("transportGhost")
        self.switch_button.clicked.connect(self.switch_ab)
        controls_row.addWidget(self.play_button)
        controls_row.addWidget(self.stop_button)
        controls_row.addWidget(self.switch_button)
        controls_row.addStretch(1)
        layout.addLayout(controls_row)

        self.player_a.playbackStateChanged.connect(self._sync_buttons)
        self.player_b.playbackStateChanged.connect(self._sync_buttons)
        self.player_a.positionChanged.connect(self._on_position_changed)
        self.player_b.positionChanged.connect(self._on_position_changed)
        self.player_a.durationChanged.connect(self._on_duration_changed)
        self.player_b.durationChanged.connect(self._on_duration_changed)
        self._sync_buttons()

    def set_a_source(self, label: str, path: str | None) -> None:
        self.source_a = path if path and Path(path).exists() else None
        self.source_a_label.setText(f"A: {label}")
        self.path_a_label.setText(path or "-")
        self.player_a.setSource(QUrl.fromLocalFile(self.source_a) if self.source_a else QUrl())
        if self.active_key == "a":
            self.stop()
        self._sync_buttons()

    def set_b_source(self, label: str, path: str | None) -> None:
        self.source_b = path if path and Path(path).exists() else None
        self.source_b_label.setText(f"B: {label}")
        self.path_b_label.setText(path or "-")
        self.player_b.setSource(QUrl.fromLocalFile(self.source_b) if self.source_b else QUrl())
        if self.active_key == "b":
            self.stop()
        self._sync_buttons()

    def toggle_playback(self) -> None:
        player = self._active_player()
        if player is None:
            return
        if player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            player.pause()
        else:
            player.play()

    def stop(self) -> None:
        self.player_a.stop()
        self.player_b.stop()

    def set_loop_start(self) -> None:
        player = self._active_player()
        if player is None:
            return
        self.loop_start_ms = player.position()
        if self.loop_end_ms is not None and self.loop_end_ms <= self.loop_start_ms:
            self.loop_end_ms = None
        self._sync_loop_label()

    def set_loop_end(self) -> None:
        player = self._active_player()
        if player is None:
            return
        position = player.position()
        if self.loop_start_ms is not None and position <= self.loop_start_ms:
            self.loop_end_ms = None
        else:
            self.loop_end_ms = position
        self._sync_loop_label()

    def clear_loop(self) -> None:
        self.loop_start_ms = None
        self.loop_end_ms = None
        self._sync_loop_label()

    def switch_ab(self) -> None:
        current = self._active_player()
        next_key = "b" if self.active_key == "a" else "a"
        next_player = self.player_b if next_key == "b" else self.player_a
        next_source = self.source_b if next_key == "b" else self.source_a
        if next_source is None:
            return

        position = current.position() if current is not None else 0
        was_playing = current is not None and current.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        if current is not None:
            current.pause()

        self.active_key = next_key
        next_player.setPosition(position)
        if was_playing:
            next_player.play()
        self._sync_buttons()
        self._sync_timeline_from_active()

    def _active_player(self) -> QMediaPlayer | None:
        if self.active_key == "a":
            return self.player_a if self.source_a else None
        return self.player_b if self.source_b else None

    def _seek(self, position: int) -> None:
        player = self._active_player()
        if player is not None:
            player.setPosition(position)

    def _on_position_changed(self, _position: int) -> None:
        player = self._active_player()
        if (
            player is not None
            and self.loop_start_ms is not None
            and self.loop_end_ms is not None
            and player.position() >= self.loop_end_ms
        ):
            player.setPosition(self.loop_start_ms)
        self._sync_timeline_from_active()

    def _on_duration_changed(self, _duration: int) -> None:
        self._sync_timeline_from_active()

    def _sync_timeline_from_active(self) -> None:
        player = self._active_player()
        if player is None:
            self.position_slider.setRange(0, 0)
            self.position_slider.setValue(0)
            self.elapsed_label.setText("00:00")
            self.duration_label.setText("00:00")
            return
        position = player.position()
        duration = player.duration()
        self.position_slider.blockSignals(True)
        self.position_slider.setRange(0, max(duration, 0))
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)
        self.elapsed_label.setText(format_milliseconds(position))
        self.duration_label.setText(format_milliseconds(duration))

    def _sync_buttons(self) -> None:
        player = self._active_player()
        has_any_source = self.source_a is not None or self.source_b is not None
        self.play_button.setEnabled(player is not None)
        self.stop_button.setEnabled(has_any_source)
        self.switch_button.setEnabled(self.source_a is not None and self.source_b is not None)
        self.loop_set_start_button.setEnabled(player is not None)
        self.loop_set_end_button.setEnabled(player is not None)
        self.loop_clear_button.setEnabled(self.loop_start_ms is not None or self.loop_end_ms is not None)
        active_source = "A" if self.active_key == "a" else "B"
        self.active_badge.setText(f"Active {active_source}")
        self.active_label.setText(
            "Original selected" if self.active_key == "a" else "Repaired selected"
        )
        self.switch_button.setText("Switch to B" if self.active_key == "a" else "Switch to A")
        if player is not None and player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("Pause")
        else:
            self.play_button.setText("Play")
        self._sync_loop_label()

    def _sync_loop_label(self) -> None:
        if self.loop_start_ms is None and self.loop_end_ms is None:
            self.loop_label.setText("Loop: off")
            return
        start_text = format_milliseconds(self.loop_start_ms or 0)
        end_text = format_milliseconds(self.loop_end_ms or 0)
        if self.loop_start_ms is not None and self.loop_end_ms is not None:
            self.loop_label.setText(f"Loop: {start_text} -> {end_text}")
        elif self.loop_start_ms is not None:
            self.loop_label.setText(f"Loop in: {start_text} · set loop out")
        else:
            self.loop_label.setText(f"Loop out: {end_text} · set loop in")


class SpectrogramView(QScrollArea):
    zoom_changed = Signal(float)
    horizontal_changed = Signal(int)
    vertical_changed = Signal(int)

    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("spectrogramScroll")
        self.setWidgetResizable(True)
        self.base_pixmap = QPixmap()
        self.zoom_factor = 1.0
        self._syncing = False

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        self.path_label = QLabel("No spectrogram available")
        self.path_label.setObjectName("audioMeta")
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.image_label = QLabel("No spectrogram available")
        self.image_label.setObjectName("spectrogramCompareLabel")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(260)

        controls = QHBoxLayout()
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.setObjectName("transportGhost")
        self.zoom_out_button.clicked.connect(lambda: self.set_zoom(self.zoom_factor / 1.25))
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setObjectName("transportGhost")
        self.zoom_in_button.clicked.connect(lambda: self.set_zoom(self.zoom_factor * 1.25))
        self.zoom_reset_button = QPushButton("Reset")
        self.zoom_reset_button.setObjectName("transportGhost")
        self.zoom_reset_button.clicked.connect(lambda: self.set_zoom(1.0))
        self.zoom_value_label = QLabel("100%")
        self.zoom_value_label.setObjectName("audioMeta")
        controls.addWidget(self.zoom_out_button)
        controls.addWidget(self.zoom_in_button)
        controls.addWidget(self.zoom_reset_button)
        controls.addWidget(self.zoom_value_label)
        controls.addStretch(1)

        layout.addWidget(self.title_label)
        layout.addWidget(self.path_label)
        layout.addLayout(controls)
        layout.addWidget(self.image_label)
        self.setWidget(container)

        self.horizontalScrollBar().valueChanged.connect(self._emit_horizontal)
        self.verticalScrollBar().valueChanged.connect(self._emit_vertical)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_image(self, path: str | None) -> None:
        self.path_label.setText(path or "No spectrogram available")
        if path and Path(path).exists():
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.base_pixmap = pixmap
                self.set_zoom(self.zoom_factor, emit_signal=False)
                return
        self.base_pixmap = QPixmap()
        self.image_label.setPixmap(QPixmap())
        self.image_label.setText("No spectrogram available")

    def set_zoom(self, zoom_factor: float, emit_signal: bool = True) -> None:
        self.zoom_factor = max(0.5, min(6.0, zoom_factor))
        self.zoom_value_label.setText(f"{int(self.zoom_factor * 100)}%")
        if self.base_pixmap.isNull():
            return
        scaled = self.base_pixmap.scaled(
            max(1, int(self.base_pixmap.width() * self.zoom_factor)),
            max(1, int(self.base_pixmap.height() * self.zoom_factor)),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self.image_label.setText("")
        self.image_label.adjustSize()
        if emit_signal:
            self.zoom_changed.emit(self.zoom_factor)

    def sync_zoom(self, zoom_factor: float) -> None:
        self.set_zoom(zoom_factor, emit_signal=False)

    def sync_horizontal(self, value: int) -> None:
        self._syncing = True
        self.horizontalScrollBar().setValue(value)
        self._syncing = False

    def sync_vertical(self, value: int) -> None:
        self._syncing = True
        self.verticalScrollBar().setValue(value)
        self._syncing = False

    def _emit_horizontal(self, value: int) -> None:
        if not self._syncing:
            self.horizontal_changed.emit(value)

    def _emit_vertical(self, value: int) -> None:
        if not self._syncing:
            self.vertical_changed.emit(value)


class SpectrogramComparePanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("audioCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel("Spectrogram Compare")
        title.setObjectName("sectionTitle")
        subtitle = QLabel("Inspect the same song visually before and after repair. Zoom and scroll stay linked.")
        subtitle.setObjectName("audioMeta")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        self.before_view = SpectrogramView("Original Spectrogram")
        self.after_view = SpectrogramView("Repaired Spectrogram")
        split.addWidget(self.before_view)
        split.addWidget(self.after_view)
        split.setSizes([560, 560])
        layout.addWidget(split, 1)

        self.before_view.zoom_changed.connect(self.after_view.sync_zoom)
        self.after_view.zoom_changed.connect(self.before_view.sync_zoom)
        self.before_view.horizontal_changed.connect(self.after_view.sync_horizontal)
        self.after_view.horizontal_changed.connect(self.before_view.sync_horizontal)
        self.before_view.vertical_changed.connect(self.after_view.sync_vertical)
        self.after_view.vertical_changed.connect(self.before_view.sync_vertical)

    def set_images(self, before_path: str | None, after_path: str | None) -> None:
        self.before_view.set_image(before_path)
        self.after_view.set_image(after_path)

class MainWindow(QMainWindow):
    def __init__(self, db: Database, paths: AppPaths) -> None:
        super().__init__()
        self.db = db
        self.paths = paths
        self.runtime = probe_runtime(paths)
        self.current_project_id: str | None = None
        self.current_run_id: str | None = None
        self.current_project_detail: dict | None = None
        self.current_run_detail: dict | None = None
        self.analyze_worker: AnalyzeWorker | None = None
        self.run_worker: RunWorker | None = None
        self.export_worker: ExportWorker | None = None
        self.active_run_started_at: float | None = None
        self.active_run_backgrounded = False

        self.setWindowTitle(f"{APP_NAME} · PySide6")
        self.resize(1440, 900)
        self._build_ui()
        self.refresh_projects()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        import_action = QAction("Import Audio", self)
        import_action.triggered.connect(self.import_audio)
        toolbar.addAction(import_action)
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_projects)
        toolbar.addAction(refresh_action)

        header = QHBoxLayout()
        title = QLabel("AI Song Cleanup")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Local restoration tool. Flat, clear, and direct.")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(subtitle)
        layout.addLayout(header)

        self.message_label = QLabel("")
        self.message_label.setObjectName("messageBanner")
        self.message_label.setVisible(False)
        self.error_label = QLabel("")
        self.error_label.setObjectName("errorBanner")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        layout.addWidget(self.message_label)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(
            [DEFAULT_PRESET, "restore_brightness", "reduce_metallic_harshness", "gentle_cleanup"]
        )
        self.intensity_combo = QComboBox()
        self.intensity_combo.addItems(["light", "medium", "strong"])
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["wav", "flac"])
        self.gpu_checkbox = QCheckBox("GPU acceleration")
        self.gpu_checkbox.setChecked(True)
        self.finishing_checkbox = QCheckBox("Apply light finishing pass (optional polish)")
        self.export_stems_checkbox = QCheckBox("Export individual stems")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter, 1)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        projects_box = QGroupBox("Projects")
        projects_layout = QVBoxLayout(projects_box)
        self.project_list = QListWidget()
        self.project_list.currentItemChanged.connect(self._on_project_changed)
        projects_layout.addWidget(self.project_list)
        left_layout.addWidget(projects_box, 1)

        quick_box = QGroupBox("Quick Actions")
        quick_layout = QVBoxLayout(quick_box)
        self.quick_analyze_button = QPushButton("Analyze Selected")
        self.quick_analyze_button.clicked.connect(self.run_analysis)
        self.quick_cleanup_button = QPushButton("Start Cleanup")
        self.quick_cleanup_button.clicked.connect(self.start_cleanup)
        self.quick_export_button = QPushButton("Export Latest")
        self.quick_export_button.clicked.connect(self.export_audio)
        quick_layout.addWidget(self.quick_analyze_button)
        quick_layout.addWidget(self.quick_cleanup_button)
        quick_layout.addWidget(self.quick_export_button)
        quick_layout.addStretch(1)
        left_layout.addWidget(quick_box)

        splitter.addWidget(left_panel)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right_panel = QWidget()
        right_scroll.setWidget(right_panel)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        overview_box = QGroupBox("Overview")
        overview_layout = QGridLayout(overview_box)
        overview_layout.setContentsMargins(10, 8, 10, 8)
        overview_layout.setHorizontalSpacing(12)
        overview_layout.setVerticalSpacing(4)
        self.project_name_value = QLabel("No project selected")
        self.project_name_value.setWordWrap(True)
        self.project_name_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.status_value = QLabel("-")
        self.schema_value = QLabel("-")
        self.preset_value = QLabel("-")
        self.intensity_value = QLabel("-")
        self.cutoff_value = QLabel("-")
        self.runtime_value = QLabel("-")
        self.runtime_detail_value = QLabel("-")
        overview_layout.setColumnStretch(1, 2)
        overview_layout.setColumnStretch(3, 1)
        overview_layout.setColumnStretch(5, 1)
        overview_layout.addWidget(QLabel("Project"), 0, 0)
        overview_layout.addWidget(self.project_name_value, 0, 1)
        overview_layout.addWidget(QLabel("Status"), 0, 2)
        overview_layout.addWidget(self.status_value, 0, 3)
        overview_layout.addWidget(QLabel("Preset"), 0, 4)
        overview_layout.addWidget(self.preset_value, 0, 5)
        overview_layout.addWidget(QLabel("Intensity"), 1, 0)
        overview_layout.addWidget(self.intensity_value, 1, 1)
        overview_layout.addWidget(QLabel("Cutoff"), 1, 2)
        overview_layout.addWidget(self.cutoff_value, 1, 3)
        overview_layout.addWidget(QLabel("Device"), 1, 4)
        overview_layout.addWidget(self.runtime_value, 1, 5)
        right_layout.addWidget(overview_box)

        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs, 1)
        self._build_home_tab()
        self._build_analysis_tab()
        self._build_repair_tab()
        self._build_compare_tab()
        self._build_export_tab()
        self._build_advanced_tab()

        bottom_split = QSplitter(Qt.Orientation.Horizontal)
        bottom_split.setChildrenCollapsible(False)

        progress_box = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_box)
        self.progress_label = QLabel("Idle")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.run_steps_list = QListWidget()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_action_row = QHBoxLayout()
        self.background_button = QPushButton("Run in Background")
        self.background_button.clicked.connect(self.run_in_background)
        self.cancel_run_button = QPushButton("Cancel Repair")
        self.cancel_run_button.clicked.connect(self.cancel_active_run)
        progress_action_row.addWidget(self.background_button)
        progress_action_row.addWidget(self.cancel_run_button)
        progress_action_row.addStretch(1)
        progress_layout.addLayout(progress_action_row)
        progress_layout.addWidget(self.run_steps_list)
        bottom_split.addWidget(progress_box)

        log_box = QGroupBox("Activity")
        log_layout = QVBoxLayout(log_box)
        self.activity_log = QPlainTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        log_layout.addWidget(self.activity_log)
        bottom_split.addWidget(log_box)
        bottom_split.setSizes([600, 600])

        right_layout.addWidget(bottom_split, 1)

        splitter.addWidget(right_scroll)
        splitter.setSizes([320, 1200])

        self.preset_combo.currentTextChanged.connect(self._sync_preset_text)
        self.intensity_combo.currentTextChanged.connect(self._sync_intensity_text)
        self.gpu_checkbox.toggled.connect(lambda _checked: self._sync_repair_runtime_hint())
        self.issue_list.currentItemChanged.connect(self._show_issue_detail)
        self.stems_list.currentItemChanged.connect(self._show_stem_preview)

        self._apply_styles()
        self._sync_runtime_summary()
        self._sync_preset_text(self.preset_combo.currentText())
        self._sync_intensity_text(self.intensity_combo.currentText())

    def _build_home_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        system_box = QGroupBox("System Readiness")
        form = QFormLayout(system_box)
        self.system_storage_value = QLabel("-")
        self.system_db_value = QLabel("-")
        self.system_python_value = QLabel("-")
        self.system_engine_value = QLabel("-")
        self.system_storage_value.setWordWrap(True)
        self.system_db_value.setWordWrap(True)
        self.system_python_value.setWordWrap(True)
        self.system_engine_value.setWordWrap(True)
        form.addRow("Storage", self.system_storage_value)
        form.addRow("Database", self.system_db_value)
        form.addRow("Python", self.system_python_value)
        form.addRow("Engine", self.system_engine_value)
        layout.addWidget(system_box)

        selected_box = QGroupBox("Selected Project")
        selected_form = QFormLayout(selected_box)
        self.home_filename_value = QLabel("-")
        self.home_original_value = QLabel("-")
        self.home_normalized_value = QLabel("-")
        self.home_latest_run_value = QLabel("-")
        for widget in (
            self.home_filename_value,
            self.home_original_value,
            self.home_normalized_value,
            self.home_latest_run_value,
        ):
            widget.setWordWrap(True)
            widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        selected_form.addRow("File", self.home_filename_value)
        selected_form.addRow("Original", self.home_original_value)
        selected_form.addRow("Normalized", self.home_normalized_value)
        selected_form.addRow("Latest Run", self.home_latest_run_value)
        layout.addWidget(selected_box)
        layout.addStretch(1)

        self.tabs.addTab(tab, "Home")

    def _build_analysis_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.analysis_rerun_button = QPushButton("Re-run Analysis")
        self.analysis_rerun_button.clicked.connect(self.run_analysis)
        self.analysis_continue_button = QPushButton("Continue to Repair Setup")
        self.analysis_continue_button.clicked.connect(lambda: self.tabs.setCurrentWidget(self.repair_tab))
        action_row.addWidget(self.analysis_rerun_button)
        action_row.addWidget(self.analysis_continue_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.analysis_notice_label = QLabel("")
        self.analysis_notice_label.setObjectName("noticeLabel")
        self.analysis_notice_label.setWordWrap(True)
        self.analysis_notice_label.setVisible(False)
        layout.addWidget(self.analysis_notice_label)

        self.analysis_upgrade_button = QPushButton("Re-run Analysis with Current Schema")
        self.analysis_upgrade_button.clicked.connect(self.run_analysis)
        self.analysis_upgrade_button.setVisible(False)
        layout.addWidget(self.analysis_upgrade_button)

        summary_box = QGroupBox("Analysis Summary")
        summary_grid = QGridLayout(summary_box)
        self.analysis_runtime_value = QLabel("-")
        self.analysis_confidence_value = QLabel("-")
        self.analysis_report_schema_value = QLabel("-")
        self.analysis_suggested_intensity_value = QLabel("-")
        summary_grid.addWidget(QLabel("Recommended"), 0, 0)
        summary_grid.addWidget(QLabel("Est. Runtime"), 0, 2)
        summary_grid.addWidget(QLabel("Confidence"), 1, 0)
        summary_grid.addWidget(QLabel("Suggested Intensity"), 1, 2)
        summary_grid.addWidget(QLabel("Schema"), 2, 0)
        self.analysis_recommended_value = QLabel("-")
        summary_grid.addWidget(self.analysis_recommended_value, 0, 1)
        summary_grid.addWidget(self.analysis_runtime_value, 0, 3)
        summary_grid.addWidget(self.analysis_confidence_value, 1, 1)
        summary_grid.addWidget(self.analysis_suggested_intensity_value, 1, 3)
        summary_grid.addWidget(self.analysis_report_schema_value, 2, 1)
        layout.addWidget(summary_box)

        spectrogram_box = QGroupBox("Spectrogram")
        spectrogram_layout = QVBoxLayout(spectrogram_box)
        self.spectrogram_text_label = QLabel(
            "Use the frequency scale on the image to spot sharp high-frequency cutoffs and check whether any air remains above the cutoff region."
        )
        self.spectrogram_text_label.setWordWrap(True)
        self.spectrogram_cutoff_label = QLabel("-")
        self.spectrogram_label = QLabel("No spectrogram available")
        self.spectrogram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spectrogram_label.setMinimumHeight(220)
        self.spectrogram_label.setObjectName("spectrogramLabel")
        spectrogram_layout.addWidget(self.spectrogram_text_label)
        spectrogram_layout.addWidget(self.spectrogram_cutoff_label)
        spectrogram_layout.addWidget(self.spectrogram_label)
        layout.addWidget(spectrogram_box)

        detail_split = QSplitter(Qt.Orientation.Horizontal)
        detail_split.setChildrenCollapsible(False)

        issue_box = QGroupBox("Detected Issues")
        issue_layout = QVBoxLayout(issue_box)
        self.issue_list = QListWidget()
        issue_layout.addWidget(self.issue_list)
        detail_split.addWidget(issue_box)

        issue_detail_box = QGroupBox("Issue Detail")
        issue_detail_layout = QVBoxLayout(issue_detail_box)
        self.issue_detail_title = QLabel("Select an issue")
        self.issue_detail_title.setObjectName("sectionTitle")
        self.issue_detail_body = QLabel("-")
        self.issue_detail_body.setWordWrap(True)
        self.issue_detail_body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        issue_detail_layout.addWidget(self.issue_detail_title)
        issue_detail_layout.addWidget(self.issue_detail_body)
        issue_detail_layout.addStretch(1)
        detail_split.addWidget(issue_detail_box)

        modules_box = QGroupBox("Planned Repair Modules")
        modules_layout = QVBoxLayout(modules_box)
        self.analysis_module_list = QListWidget()
        modules_layout.addWidget(self.analysis_module_list)
        detail_split.addWidget(modules_box)
        detail_split.setSizes([360, 430, 280])

        layout.addWidget(detail_split, 1)

        self.analysis_tab = tab
        self.tabs.addTab(tab, "Analysis")

    def _build_repair_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        self.start_cleanup_button = QPushButton("Start AI Song Cleanup")
        self.start_cleanup_button.clicked.connect(self.start_cleanup)
        self.reset_recommended_button = QPushButton("Reset to Recommended")
        self.reset_recommended_button.clicked.connect(self.reset_to_recommended)
        top_row.addWidget(self.start_cleanup_button)
        top_row.addWidget(self.reset_recommended_button)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        settings_split = QSplitter(Qt.Orientation.Horizontal)
        settings_split.setChildrenCollapsible(False)

        preset_box = QGroupBox("Repair Path")
        preset_layout = QVBoxLayout(preset_box)
        self.repair_preset_title = QLabel("AI Song Cleanup")
        self.repair_preset_title.setObjectName("sectionTitle")
        self.repair_preset_description = QLabel("")
        self.repair_preset_description.setWordWrap(True)
        self.repair_runtime_hint = QLabel("Estimated runtime: -")
        self.repair_runtime_hint.setObjectName("audioMeta")
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addWidget(self.repair_preset_title)
        preset_layout.addWidget(self.repair_preset_description)
        preset_layout.addWidget(self.repair_runtime_hint)
        preset_layout.addStretch(1)
        settings_split.addWidget(preset_box)

        project_box = QGroupBox("Project")
        project_form = QFormLayout(project_box)
        self.repair_project_name = QLabel("-")
        self.repair_source_path = QLabel("-")
        self.repair_source_path.setWordWrap(True)
        self.repair_source_path.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        project_form.addRow("Name", self.repair_project_name)
        project_form.addRow("Source", self.repair_source_path)
        settings_split.addWidget(project_box)

        intensity_box = QGroupBox("Intensity")
        intensity_layout = QVBoxLayout(intensity_box)
        self.repair_suggested_label = QLabel("Suggested by analysis: -")
        self.repair_intensity_description = QLabel("")
        self.repair_intensity_description.setWordWrap(True)
        intensity_layout.addWidget(self.repair_suggested_label)
        intensity_layout.addWidget(self.intensity_combo)
        intensity_layout.addWidget(self.repair_intensity_description)
        intensity_layout.addStretch(1)
        settings_split.addWidget(intensity_box)

        options_box = QGroupBox("Options")
        options_layout = QVBoxLayout(options_box)
        options_layout.addWidget(self.gpu_checkbox)
        options_layout.addWidget(self.export_stems_checkbox)
        options_layout.addWidget(self.finishing_checkbox)
        options_layout.addStretch(1)
        settings_split.addWidget(options_box)
        settings_split.setSizes([340, 280, 320, 280])

        layout.addWidget(settings_split)

        detail_split = QSplitter(Qt.Orientation.Horizontal)
        detail_split.setChildrenCollapsible(False)

        repair_issues_box = QGroupBox("Detected Issues")
        repair_issues_layout = QVBoxLayout(repair_issues_box)
        self.repair_issue_list = QListWidget()
        repair_issues_layout.addWidget(self.repair_issue_list)
        detail_split.addWidget(repair_issues_box)

        repair_modules_box = QGroupBox("Active Repair Modules")
        repair_modules_layout = QVBoxLayout(repair_modules_box)
        self.repair_module_list = QListWidget()
        repair_modules_layout.addWidget(self.repair_module_list)
        detail_split.addWidget(repair_modules_box)

        layout.addWidget(detail_split, 1)

        self.repair_tab = tab
        self.tabs.addTab(tab, "Repair")

    def _build_compare_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        compare_header = QHBoxLayout()
        self.compare_continue_button = QPushButton("Continue to Export")
        self.compare_continue_button.clicked.connect(lambda: self.tabs.setCurrentWidget(self.export_tab))
        self.compare_retry_button = QPushButton("Run Again with Different Settings")
        self.compare_retry_button.clicked.connect(self.try_another_repair)
        compare_header.addWidget(self.compare_continue_button)
        compare_header.addWidget(self.compare_retry_button)
        compare_header.addStretch(1)
        layout.addLayout(compare_header)

        self.ab_compare_deck = ABCompareDeck()
        layout.addWidget(self.ab_compare_deck)

        compare_summary_split = QSplitter(Qt.Orientation.Horizontal)
        compare_summary_split.setChildrenCollapsible(False)

        summary_box = QGroupBox("Repair Summary")
        summary_layout = QVBoxLayout(summary_box)
        self.compare_summary_label = QLabel("Run a cleanup to see a plain-language summary of what changed.")
        self.compare_summary_label.setWordWrap(True)
        self.compare_summary_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        summary_layout.addWidget(self.compare_summary_label)
        compare_summary_split.addWidget(summary_box)

        verdict_box = QGroupBox("Quick Verdict")
        verdict_layout = QVBoxLayout(verdict_box)
        self.compare_feedback_label = QLabel("Listen to the same section on A and B, then record your verdict.")
        self.compare_feedback_label.setWordWrap(True)
        verdict_layout.addWidget(self.compare_feedback_label)
        verdict_row = QHBoxLayout()
        self.compare_better_button = QPushButton("This Sounds Better")
        self.compare_better_button.clicked.connect(lambda: self._record_compare_feedback("This sounds better"))
        self.compare_no_change_button = QPushButton("No Real Change")
        self.compare_no_change_button.clicked.connect(lambda: self._record_compare_feedback("No real change"))
        verdict_row.addWidget(self.compare_better_button)
        verdict_row.addWidget(self.compare_no_change_button)
        verdict_layout.addLayout(verdict_row)
        compare_summary_split.addWidget(verdict_box)
        compare_summary_split.setSizes([760, 340])
        layout.addWidget(compare_summary_split)

        self.spectrogram_compare_panel = SpectrogramComparePanel()
        layout.addWidget(self.spectrogram_compare_panel)

        compare_focus_split = QSplitter(Qt.Orientation.Horizontal)
        compare_focus_split.setChildrenCollapsible(False)
        self.original_audio_card = AudioCard("Original")
        self.compare_audio_card = AudioCard("Preview Mix")
        compare_focus_split.addWidget(self.original_audio_card)
        compare_focus_split.addWidget(self.compare_audio_card)
        compare_focus_split.setSizes([520, 520])
        layout.addWidget(compare_focus_split)

        stems_split = QSplitter(Qt.Orientation.Horizontal)
        stems_split.setChildrenCollapsible(False)

        stems_box = QGroupBox("All Stems")
        stems_layout = QVBoxLayout(stems_box)
        self.stems_list = QListWidget()
        stems_layout.addWidget(self.stems_list)
        self.normalized_path_label = QLabel("-")
        self.normalized_path_label.setWordWrap(True)
        self.normalized_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        stems_layout.addWidget(self.normalized_path_label)
        stems_split.addWidget(stems_box)

        self.stem_preview_card = AudioCard("Stem Preview")
        stems_split.addWidget(self.stem_preview_card)
        stems_split.setSizes([300, 660])
        layout.addWidget(stems_split, 1)

        self.compare_tab = tab
        self.tabs.addTab(tab, "Compare")

    def _build_export_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        export_action_row = QHBoxLayout()
        export_action_row.addWidget(QLabel("Output Format"))
        export_action_row.addWidget(self.export_format_combo)
        self.export_confirm_button = QPushButton("Confirm Export")
        self.export_confirm_button.clicked.connect(self.export_audio)
        export_action_row.addWidget(self.export_confirm_button)
        export_action_row.addStretch(1)
        layout.addLayout(export_action_row)

        export_split = QSplitter(Qt.Orientation.Horizontal)
        export_split.setChildrenCollapsible(False)

        self.export_audio_card = AudioCard("Current Export")
        export_split.addWidget(self.export_audio_card)

        exports_box = QGroupBox("Available Exports")
        exports_layout = QVBoxLayout(exports_box)
        self.exports_list = QListWidget()
        exports_layout.addWidget(self.exports_list)
        export_split.addWidget(exports_box)
        export_split.setSizes([700, 320])
        layout.addWidget(export_split)

        stem_box = QGroupBox("Stem Export Paths")
        stem_layout = QVBoxLayout(stem_box)
        self.export_stem_paths = QListWidget()
        stem_layout.addWidget(self.export_stem_paths)
        layout.addWidget(stem_box, 1)

        self.export_tab = tab
        self.tabs.addTab(tab, "Export")

    def _build_advanced_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        placeholder_box = QGroupBox("Advanced")
        placeholder_layout = QVBoxLayout(placeholder_box)
        placeholder = QLabel(
            "This area is reserved for future expert controls such as stereo diagnostics, per-stem controls, module toggles, and deeper analysis details. The main path stays simple by default."
        )
        placeholder.setWordWrap(True)
        placeholder_layout.addWidget(placeholder)
        self.advanced_features_list = QListWidget()
        for item in [
            "Stereo instability diagnostics",
            "Per-stem repair strength",
            "Advanced module routing",
            "Model management and readiness",
            "Detailed analysis metrics",
        ]:
            self.advanced_features_list.addItem(item)
        placeholder_layout.addWidget(self.advanced_features_list)
        layout.addWidget(placeholder_box)
        layout.addStretch(1)

        self.advanced_tab = tab
        self.tabs.addTab(tab, "Advanced")

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background: #111317;
                color: #e6e8eb;
                font-family: Segoe UI;
                font-size: 13px;
            }
            QMainWindow {
                background: #111317;
            }
            QToolBar {
                background: #171a1f;
                border: 1px solid #232830;
                spacing: 8px;
                padding: 6px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QGroupBox {
                background: #171a1f;
                border: 1px solid #2a3039;
                margin-top: 12px;
                padding: 10px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QListWidget, QPlainTextEdit, QComboBox, QTabWidget::pane {
                background: #0e1014;
                border: 1px solid #2a3039;
                selection-background-color: #2b4f75;
                outline: none;
            }
            QSlider::groove:horizontal {
                background: #1f242c;
                height: 6px;
                border: 1px solid #2a3039;
            }
            QSlider::handle:horizontal {
                background: #6ea7d8;
                width: 14px;
                margin: -5px 0;
                border: 1px solid #8fbde4;
            }
            QTabBar::tab {
                background: #171a1f;
                border: 1px solid #2a3039;
                padding: 10px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #223140;
                color: #f2f6fa;
            }
            QPushButton {
                background: #1e242c;
                border: 1px solid #39424f;
                padding: 8px 12px;
                min-height: 18px;
            }
            QPushButton:hover {
                background: #25303a;
            }
            QPushButton:disabled {
                color: #7d8691;
                background: #161a20;
            }
            QLabel#titleLabel {
                font-size: 26px;
                font-weight: 700;
            }
            QLabel#subtitleLabel {
                color: #98a2ad;
            }
            QLabel#sectionTitle {
                font-size: 16px;
                font-weight: 700;
            }
            QLabel {
                line-height: 1.3;
            }
            QLabel#messageBanner, QLabel#errorBanner, QLabel#noticeLabel {
                border: 1px solid #2a3039;
                padding: 8px 10px;
                background: #171a1f;
            }
            QLabel#messageBanner {
                border-color: #2f6b3c;
                color: #b8efc4;
            }
            QLabel#errorBanner {
                border-color: #7a3a3a;
                color: #ffb6b6;
            }
            QLabel#noticeLabel {
                border-color: #6c5c2f;
                color: #f2e1a3;
            }
            QLabel#spectrogramLabel {
                background: #0e1014;
                border: 1px solid #2a3039;
            }
            QScrollArea#spectrogramScroll {
                background: #0e1014;
                border: 1px solid #2a3039;
            }
            QLabel#spectrogramCompareLabel {
                background: #0e1014;
                border: 1px solid #2a3039;
                padding: 8px;
            }
            QWidget#audioCard {
                background: #141920;
                border: 1px solid #2d3642;
                border-radius: 10px;
            }
            QLabel#audioMeta {
                color: #9da7b3;
            }
            QLabel#audioBadge {
                background: #223140;
                border: 1px solid #39536d;
                border-radius: 10px;
                color: #dcecff;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#abBadge {
                background: #1a222c;
                border: 1px solid #324153;
                border-radius: 10px;
                color: #b8c7d9;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton#transportPrimary {
                background: #2b5c8c;
                border: 1px solid #4d7fb2;
                color: #f3f8fd;
                font-weight: 700;
                min-width: 84px;
            }
            QPushButton#transportPrimary:hover {
                background: #356a9f;
            }
            QPushButton#transportGhost {
                background: #171d24;
                border: 1px solid #3a4553;
                color: #d9dee5;
                min-width: 84px;
            }
            QPushButton#transportGhost:hover {
                background: #202933;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #1a1f26;
            }
            QListWidget::item:selected {
                background: #27415e;
            }
            QProgressBar {
                background: #0e1014;
                border: 1px solid #2a3039;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #3a6ea5;
            }
            """
        )

    def log(self, text: str) -> None:
        self.activity_log.appendPlainText(text)

    def set_message(self, text: str | None) -> None:
        self.message_label.setVisible(bool(text))
        self.message_label.setText(text or "")

    def set_error(self, text: str | None) -> None:
        self.error_label.setVisible(bool(text))
        self.error_label.setText(text or "")

    def set_busy(self, busy: bool) -> None:
        has_project = self.current_project_id is not None
        has_run = self.current_run_id is not None
        self.quick_analyze_button.setDisabled(busy or not has_project)
        self.quick_cleanup_button.setDisabled(busy or not has_project)
        self.quick_export_button.setDisabled(busy or not has_run)
        self.analysis_rerun_button.setDisabled(busy or not has_project)
        self.analysis_upgrade_button.setDisabled(busy or not has_project)
        self.start_cleanup_button.setDisabled(busy or not has_project)
        self.export_confirm_button.setDisabled(busy or not has_run)
        self.background_button.setDisabled(not busy or self.run_worker is None)
        self.cancel_run_button.setDisabled(not busy or self.run_worker is None)

    def _sync_runtime_summary(self) -> None:
        runtime_label = "GPU Ready" if self.runtime["cuda_available"] else "CPU Only"
        runtime_detail = self.runtime["gpu_name"] or "CUDA not available"
        self.runtime_value.setText(runtime_label)
        self.runtime_detail_value.setText(runtime_detail)
        self.system_storage_value.setText(self.runtime["storage_dir"])
        self.system_db_value.setText(self.runtime["database_path"])
        self.system_python_value.setText(self.runtime["python_command"])
        self.system_engine_value.setText(self.runtime["engine_entry"])

    def _sync_intensity_text(self, intensity: str) -> None:
        self.repair_intensity_description.setText(intensity_description(intensity))
        self._sync_repair_runtime_hint()

    def _sync_preset_text(self, preset: str) -> None:
        self.repair_preset_title.setText(preset.replace("_", " ").title())
        self.repair_preset_description.setText(preset_description(preset))
        self._sync_repair_runtime_hint()

    def _sync_repair_runtime_hint(self) -> None:
        report = (self.current_project_detail or {}).get("analysis_report") if self.current_project_detail else None
        self.repair_runtime_hint.setText(
            runtime_hint(report, self.preset_combo.currentText(), self.intensity_combo.currentText(), self.gpu_checkbox.isChecked())
        )

    def reset_to_recommended(self) -> None:
        report = (self.current_project_detail or {}).get("analysis_report") if self.current_project_detail else None
        if not report:
            self.show_error("Run analysis first before resetting to the recommended repair.")
            return
        recommended_preset = report.get("recommended_preset") or DEFAULT_PRESET
        suggested_intensity = report.get("suggested_intensity") or "medium"
        if self.preset_combo.findText(recommended_preset) >= 0:
            self.preset_combo.setCurrentText(recommended_preset)
        if self.intensity_combo.findText(suggested_intensity) >= 0:
            self.intensity_combo.setCurrentText(suggested_intensity)
        self.finishing_checkbox.setChecked(False)
        self.export_stems_checkbox.setChecked(False)
        self.set_message("Repair settings reset to the current recommendation.")

    def refresh_projects(self) -> None:
        selected_id = self.current_project_id
        self.project_list.clear()
        for project in self.db.list_projects():
            text = f"{project['name']}\n{project['source_filename'] or 'No source file'} · {project['status']}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, project["id"])
            self.project_list.addItem(item)
            if project["id"] == selected_id:
                self.project_list.setCurrentItem(item)
        if self.project_list.count() and self.project_list.currentItem() is None:
            self.project_list.setCurrentRow(0)
        elif self.project_list.count() == 0:
            self._render_empty_state()

    def _render_empty_state(self) -> None:
        self.current_project_id = None
        self.current_run_id = None
        self.current_project_detail = None
        self.current_run_detail = None
        self.project_name_value.setText("No project selected")
        self.status_value.setText("-")
        self.schema_value.setText("-")
        self.preset_value.setText("-")
        self.intensity_value.setText("-")
        self.cutoff_value.setText("-")
        self.home_filename_value.setText("-")
        self.home_original_value.setText("-")
        self.home_normalized_value.setText("-")
        self.home_latest_run_value.setText("-")
        self.analysis_recommended_value.setText("-")
        self.analysis_runtime_value.setText("-")
        self.analysis_confidence_value.setText("-")
        self.analysis_suggested_intensity_value.setText("-")
        self.analysis_report_schema_value.setText("-")
        self.analysis_notice_label.setVisible(False)
        self.analysis_upgrade_button.setVisible(False)
        self.spectrogram_cutoff_label.setText("-")
        self.spectrogram_label.setPixmap(QPixmap())
        self.spectrogram_label.setText("No spectrogram available")
        self.repair_project_name.setText("-")
        self.repair_source_path.setText("-")
        self.repair_suggested_label.setText("Suggested by analysis: -")
        self.issue_list.clear()
        self.analysis_module_list.clear()
        self.repair_issue_list.clear()
        self.repair_module_list.clear()
        self.exports_list.clear()
        self.export_stem_paths.clear()
        self.stems_list.clear()
        self.run_steps_list.clear()
        self.issue_detail_title.setText("Select an issue")
        self.issue_detail_body.setText("-")
        self.ab_compare_deck.set_a_source("Original", None)
        self.ab_compare_deck.set_b_source("Repaired", None)
        self.original_audio_card.set_source(None)
        self.compare_audio_card.set_source(None)
        self.stem_preview_card.set_source(None)
        self.export_audio_card.set_source(None)
        self.set_message(None)
        self.set_error(None)
        self.progress_label.setText("Idle")
        self.progress_bar.setValue(0)
        self.set_busy(False)

    def _on_project_changed(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            self._render_empty_state()
            return
        project_id = current.data(Qt.ItemDataRole.UserRole)
        self.current_project_id = project_id
        self.load_project(project_id)

    def load_project(self, project_id: str) -> None:
        detail = self.db.get_project_detail(project_id)
        self.current_project_detail = detail
        project = detail["project"]
        source_file = detail["source_file"]
        analysis_report = detail["analysis_report"]
        latest_run = detail["latest_run"]
        self.current_run_id = latest_run["id"] if latest_run else None
        self.current_run_detail = self.db.get_run_detail(self.current_run_id) if self.current_run_id else None

        self.project_name_value.setText(project["name"])
        self.status_value.setText(project["status"])
        self.schema_value.setText((analysis_report or {}).get("schema_version") or "legacy / unknown")
        self.preset_value.setText((analysis_report or {}).get("recommended_preset") or "-")
        self.intensity_value.setText((analysis_report or {}).get("suggested_intensity") or "-")
        cutoff = (analysis_report or {}).get("estimated_cutoff_hz")
        self.cutoff_value.setText(f"{cutoff} Hz" if cutoff is not None else "-")

        self.home_filename_value.setText(source_file.get("filename") or "-")
        self.home_original_value.setText(source_file.get("original_path") or "-")
        self.home_normalized_value.setText(source_file.get("normalized_path") or "-")
        self.home_latest_run_value.setText(
            f"{latest_run['status']} · {latest_run['id']}" if latest_run else "No run yet"
        )

        self._render_analysis(detail)
        self._render_repair(detail)
        self._render_compare(detail)
        self._render_export(detail)
        self._render_progress()
        self.set_busy(False)

    def _render_analysis(self, detail: dict) -> None:
        source_file = detail["source_file"]
        report = detail["analysis_report"]
        self.analysis_continue_button.setEnabled(bool(report))
        if not report:
            self.analysis_recommended_value.setText("No analysis report yet")
            self.analysis_runtime_value.setText("-")
            self.analysis_confidence_value.setText("-")
            self.analysis_suggested_intensity_value.setText("-")
            self.analysis_report_schema_value.setText("-")
            self.analysis_notice_label.setVisible(False)
            self.analysis_upgrade_button.setVisible(False)
            self.spectrogram_cutoff_label.setText("-")
            self.spectrogram_label.setPixmap(QPixmap())
            self.spectrogram_label.setText("No spectrogram available")
            self.issue_list.clear()
            self.analysis_module_list.clear()
            self.issue_detail_title.setText("Select an issue")
            self.issue_detail_body.setText("Run analysis first.")
            return

        self.analysis_recommended_value.setText(report.get("recommended_preset") or "Pending")
        self.analysis_runtime_value.setText(f"{report.get('runtime_estimate_sec', '—')} sec")
        self.analysis_confidence_value.setText(str(report.get("overall_confidence", "—")))
        self.analysis_suggested_intensity_value.setText(report.get("suggested_intensity") or "medium")
        self.analysis_report_schema_value.setText(report.get("schema_version") or "unknown")

        notice = report.get("compatibility_notice")
        self.analysis_notice_label.setVisible(bool(notice))
        self.analysis_notice_label.setText(notice or "")
        self.analysis_upgrade_button.setVisible(bool(notice))

        self.spectrogram_cutoff_label.setText(format_cutoff_text(report))
        spectrogram_path = report.get("spectrogram_path")
        if spectrogram_path and Path(spectrogram_path).exists():
            pixmap = QPixmap(spectrogram_path)
            if not pixmap.isNull():
                self.spectrogram_label.setPixmap(
                    pixmap.scaledToWidth(760, Qt.TransformationMode.SmoothTransformation)
                )
                self.spectrogram_label.setText("")
            else:
                self.spectrogram_label.setPixmap(QPixmap())
                self.spectrogram_label.setText("Failed to load spectrogram image")
        else:
            self.spectrogram_label.setPixmap(QPixmap())
            self.spectrogram_label.setText("No spectrogram available")

        self.issue_list.clear()
        for issue in report.get("issues", []):
            title = issue.get("artifact_title") or issue.get("label") or issue.get("id")
            confidence = issue.get("confidence")
            text = f"{title} [{issue.get('severity', '-')}]"
            if confidence is not None:
                text += f" · confidence {confidence}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, issue)
            self.issue_list.addItem(item)
        if self.issue_list.count():
            self.issue_list.setCurrentRow(0)
        else:
            self.issue_detail_title.setText("No issues")
            self.issue_detail_body.setText("The analysis report did not include any issue entries.")

        self.analysis_module_list.clear()
        analysis_module_lines = pipeline_stage_lines(self.current_run_detail.get("report") if self.current_run_detail else None)
        if analysis_module_lines:
            for line in analysis_module_lines:
                self.analysis_module_list.addItem(line)
        else:
            for module in report.get("planned_repair_modules", []):
                self.analysis_module_list.addItem(module)

        self.log(f"Loaded analysis report for {source_file.get('filename')}")

    def _show_issue_detail(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            self.issue_detail_title.setText("Select an issue")
            self.issue_detail_body.setText("-")
            return
        issue = current.data(Qt.ItemDataRole.UserRole) or {}
        title = issue.get("artifact_title") or issue.get("label") or issue.get("id") or "Issue"
        self.issue_detail_title.setText(title)
        parts = [
            f"Severity: {issue.get('severity', '-')}",
            f"Confidence: {issue.get('confidence', '—')}",
            issue.get("description"),
            f"Detection: {issue.get('detection')}" if issue.get("detection") else None,
            f"Repair: {issue.get('repair')}" if issue.get("repair") else None,
        ]
        self.issue_detail_body.setText("\n\n".join(part for part in parts if part))

    def _render_repair(self, detail: dict) -> None:
        project = detail["project"]
        source_file = detail["source_file"]
        report = detail["analysis_report"]

        self.repair_project_name.setText(project["name"])
        self.repair_source_path.setText(source_file.get("original_path") or "-")
        suggested = (report or {}).get("suggested_intensity") or "medium"
        self.repair_suggested_label.setText(f"Suggested by analysis: {suggested}")
        self.repair_issue_list.clear()
        self.repair_module_list.clear()

        if report:
            recommended_preset = report.get("recommended_preset") or DEFAULT_PRESET
            if self.preset_combo.findText(recommended_preset) >= 0:
                self.preset_combo.setCurrentText(recommended_preset)
            if self.intensity_combo.findText(suggested) >= 0:
                self.intensity_combo.setCurrentText(suggested)
            for issue in report.get("issues", []):
                title = issue.get("artifact_title") or issue.get("label") or issue.get("id")
                self.repair_issue_list.addItem(f"{issue.get('severity', '-')} · {title}")
            repair_report = self.current_run_detail.get("report") if self.current_run_detail else None
            repair_module_lines = pipeline_stage_lines(repair_report)
            if repair_module_lines:
                for line in repair_module_lines:
                    self.repair_module_list.addItem(line)
            else:
                for module in report.get("planned_repair_modules", []):
                    self.repair_module_list.addItem(module)
        else:
            self.repair_issue_list.addItem("Run analysis first to unlock cleanup settings.")
        self._sync_preset_text(self.preset_combo.currentText())

    def _render_compare(self, detail: dict) -> None:
        source_file = detail["source_file"]
        analysis_report = detail["analysis_report"]
        run_detail = self.current_run_detail
        self.original_audio_card.set_title("Original")
        self.original_audio_card.set_source(source_file.get("original_path"))
        self.stems_list.clear()
        self.normalized_path_label.setText(
            f"Normalized working file: {source_file.get('normalized_path') or 'Unavailable'}"
        )
        self.compare_summary_label.setText(
            "\n\n".join(compare_summary_lines(analysis_report, run_detail.get("report") if run_detail else None))
        )
        saved_feedback = run_detail.get("run", {}).get("user_feedback") if run_detail else None
        self.compare_feedback_label.setText(
            f"Verdict recorded: {saved_feedback}" if saved_feedback else "Set a loop around the same phrase, switch between A and B, then record your verdict."
        )
        original_spectrogram = (analysis_report or {}).get("spectrogram_path")
        repaired_spectrogram = None
        if run_detail:
            repaired_asset = next(
                (asset for asset in run_detail["assets"] if asset["kind"] == "repaired_spectrogram"),
                None,
            )
            repaired_spectrogram = repaired_asset["path"] if repaired_asset else run_detail.get("report", {}).get("repaired_spectrogram_path")
        self.spectrogram_compare_panel.set_images(original_spectrogram, repaired_spectrogram)

        if not run_detail:
            self.ab_compare_deck.set_a_source("Original", source_file.get("original_path"))
            self.ab_compare_deck.set_b_source("Repaired", None)
            self.compare_audio_card.set_title("Preview Mix")
            self.compare_audio_card.set_source(None)
            self.stem_preview_card.set_title("Stem Preview")
            self.stem_preview_card.set_source(None)
            return

        extra_assets = [
            asset
            for asset in run_detail["assets"]
            if asset["kind"] not in {"mix_preview", "normalized_audio", "cleaned_export"}
        ]
        for asset in extra_assets:
            item = QListWidgetItem(asset_label(asset["kind"]))
            item.setData(Qt.ItemDataRole.UserRole, asset)
            self.stems_list.addItem(item)
        if self.stems_list.count():
            self.stems_list.setCurrentRow(0)
        else:
            self.stem_preview_card.set_title("Stem Preview")
            self.stem_preview_card.set_source(None)

        preview_asset = next(
            (asset for asset in run_detail["assets"] if asset["kind"] == "mix_preview"),
            None,
        )
        export_asset = run_detail["exports"][0]["path"] if run_detail["exports"] else None

        self.ab_compare_deck.set_a_source("Original", source_file.get("original_path"))
        self.ab_compare_deck.set_b_source("Repaired", export_asset or (preview_asset["path"] if preview_asset else None))
        self.compare_audio_card.set_title("Preview Mix")
        self.compare_audio_card.set_source(preview_asset["path"] if preview_asset else None)

    def _record_compare_feedback(self, verdict: str) -> None:
        if self.current_run_id:
            self.db.set_run_feedback(self.current_run_id, verdict)
        self.compare_feedback_label.setText(f"Verdict recorded: {verdict}")
        self.log(f"Compare verdict: {verdict}")
        if self.current_project_id:
            self.load_project(self.current_project_id)

    def _show_stem_preview(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            self.stem_preview_card.set_title("Stem Preview")
            self.stem_preview_card.set_source(None)
            return
        asset = current.data(Qt.ItemDataRole.UserRole) or {}
        self.stem_preview_card.set_title(asset_label(asset.get("kind", "Stem Preview")))
        self.stem_preview_card.set_source(asset.get("path"))

    def _render_export(self, detail: dict) -> None:
        run_detail = self.current_run_detail
        self.exports_list.clear()
        self.export_stem_paths.clear()
        if not run_detail:
            self.export_audio_card.set_title("Current Export")
            self.export_audio_card.set_source(None)
            return

        current_export = run_detail["exports"][0] if run_detail["exports"] else None
        self.export_audio_card.set_title("Current Export")
        self.export_audio_card.set_source(current_export["path"] if current_export else None)

        for export in run_detail["exports"]:
            self.exports_list.addItem(f"{export['format'].upper()} · {export['path']}")

        stem_assets = [
            asset
            for asset in run_detail["assets"]
            if asset["kind"] in {"stem_vocals", "stem_music", "repaired_vocals", "repaired_music"}
        ]
        for asset in stem_assets:
            self.export_stem_paths.addItem(f"{asset_label(asset['kind'])}: {asset['path']}")

    def _render_progress(self) -> None:
        self.run_steps_list.clear()
        if not self.current_run_detail:
            self.progress_label.setText("Idle")
            self.progress_bar.setValue(0)
            return

        run = self.current_run_detail["run"]
        steps = self.current_run_detail["steps"]
        pipeline_lookup = pipeline_step_lookup(self.current_run_detail.get("report"))
        if steps:
            last_step = steps[-1]
            progress_title = pipeline_step_label(pipeline_lookup.get(last_step["step_name"], {}))
            progress = int((len([step for step in steps if step['status'] == 'completed']) / max(len(steps), 1)) * 100)
            self.progress_bar.setValue(progress)
            eta_suffix = ""
            if self.active_run_started_at and progress > 0 and progress < 100:
                elapsed = max(0.0, time.time() - self.active_run_started_at)
                eta_seconds = int((elapsed / max(progress, 1)) * (100 - progress))
                eta_suffix = f" · ETA {format_milliseconds(eta_seconds * 1000)}"
            self.progress_label.setText(f"{progress_title} · {last_step['status']}{eta_suffix}")
        else:
            self.progress_label.setText(run["status"])
            self.progress_bar.setValue(0)

        for step in steps:
            planned_step = pipeline_lookup.get(step["step_name"], {})
            state_icon = {
                "completed": "[x]",
                "running": "[>]",
                "failed": "[!]",
            }.get(step["status"], "[ ]")
            line = f"{state_icon} {pipeline_step_label(planned_step) if planned_step else step['step_name']} · {step['status']}"
            self.run_steps_list.addItem(line)
            for module_line in pipeline_module_lines(planned_step):
                self.run_steps_list.addItem(f"  {module_line}")
        if run.get("failure_message"):
            self.run_steps_list.addItem(f"FAILED: {run['failure_message']}")

    def import_audio(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Audio",
            str(self.paths.workspace_dir),
            "Audio Files (*.wav *.flac *.mp3)",
        )
        if not path:
            return
        try:
            project_id = self.db.import_project(path)
            self.log(f"Imported project from {path}")
            self.set_error(None)
            self.set_message(f"Imported: {Path(path).stem}")
            self.refresh_projects()
            self._select_project(project_id)
            self.tabs.setCurrentWidget(self.analysis_tab)
            self.run_analysis()
        except Exception as error:  # noqa: BLE001
            self.show_error(str(error))

    def _select_project(self, project_id: str) -> None:
        for index in range(self.project_list.count()):
            item = self.project_list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == project_id:
                self.project_list.setCurrentItem(item)
                break

    def run_analysis(self) -> None:
        if not self.current_project_id:
            return
        self.set_busy(True)
        self.set_error(None)
        self.set_message("Running analysis...")
        self.progress_label.setText("Running analysis")
        self.progress_bar.setValue(10)
        self.log(f"Analyzing project {self.current_project_id}")
        self.analyze_worker = AnalyzeWorker(self.db, self.paths, self.current_project_id)
        self.analyze_worker.finished_ok.connect(self._analysis_finished)
        self.analyze_worker.failed.connect(self._worker_failed)
        self.analyze_worker.start()

    def _analysis_finished(self, project_id: str) -> None:
        self.progress_label.setText("Analysis completed")
        self.progress_bar.setValue(100)
        self.set_message("Analysis complete.")
        self.log(f"Analysis completed for {project_id}")
        self.set_busy(False)
        self.load_project(project_id)
        self.tabs.setCurrentWidget(self.analysis_tab)

    def start_cleanup(self) -> None:
        if not self.current_project_id:
            return
        if not self.current_project_detail or not self.current_project_detail.get("analysis_report"):
            self.show_error("Run analysis first before starting cleanup.")
            return
        self.set_busy(True)
        self.set_error(None)
        self.set_message("Starting cleanup run...")
        self.progress_label.setText("Starting cleanup")
        self.progress_bar.setValue(0)
        self.active_run_started_at = time.time()
        self.active_run_backgrounded = False
        self.log(f"Starting cleanup for {self.current_project_id}")
        self.run_worker = RunWorker(
            self.db,
            self.paths,
            self.current_project_id,
            self.preset_combo.currentText(),
            self.intensity_combo.currentText(),
            self.export_stems_checkbox.isChecked(),
            self.finishing_checkbox.isChecked(),
            self.gpu_checkbox.isChecked(),
        )
        self.run_worker.progress.connect(self._run_progress)
        self.run_worker.finished_ok.connect(self._run_finished)
        self.run_worker.cancelled.connect(self._run_cancelled)
        self.run_worker.failed.connect(self._worker_failed)
        self.run_worker.start()

    def _run_progress(self, step: str, status: str, message: str, progress: float) -> None:
        plain_labels = {
            "normalize": "Preparing audio",
            "separate_stems": "Separating stems",
            "repair_vocals": "Repairing vocals",
            "repair_music": "Repairing music",
            "reconstruct_mix": "Rebuilding mix",
        }
        title = plain_labels.get(step, step)
        eta_suffix = ""
        percent = int(progress * 100)
        if self.active_run_started_at and percent > 0 and percent < 100:
            elapsed = max(0.0, time.time() - self.active_run_started_at)
            eta_seconds = int((elapsed / max(percent, 1)) * (100 - percent))
            eta_suffix = f" · ETA {format_milliseconds(eta_seconds * 1000)}"
        self.progress_label.setText(f"{title} · {status}{eta_suffix}")
        self.progress_bar.setValue(int(progress * 100))
        self.log(f"{step}: {message}")
        self.set_message(message)

    def _run_finished(self, run_id: str) -> None:
        self.current_run_id = run_id
        self.active_run_started_at = None
        self.active_run_backgrounded = False
        self.progress_label.setText("Cleanup completed")
        self.progress_bar.setValue(100)
        self.set_message(f"Run {run_id} completed.")
        self.log(f"Cleanup completed for run {run_id}")
        self.set_busy(False)
        if self.current_project_id:
            self.load_project(self.current_project_id)
        self.tabs.setCurrentWidget(self.compare_tab)

    def _run_cancelled(self, run_id: str) -> None:
        self.current_run_id = run_id
        self.active_run_started_at = None
        self.active_run_backgrounded = False
        self.progress_label.setText("Cleanup cancelled")
        self.progress_bar.setValue(0)
        self.set_message(None)
        self.set_error("Cleanup cancelled by user.")
        self.log(f"Cleanup cancelled for run {run_id}")
        self.set_busy(False)
        if self.current_project_id:
            self.load_project(self.current_project_id)

    def try_another_repair(self) -> None:
        if not self.current_project_detail or not self.current_project_detail.get("analysis_report"):
            self.show_error("Run analysis first before trying another repair.")
            return
        self.set_error(None)
        self.set_message("Adjust the repair settings, then start another cleanup run.")
        self.tabs.setCurrentWidget(self.repair_tab)

    def export_audio(self) -> None:
        if not self.current_project_id or not self.current_run_id:
            return
        self.set_busy(True)
        self.set_error(None)
        fmt = self.export_format_combo.currentText()
        self.set_message(f"Exporting {fmt}...")
        self.progress_label.setText(f"Exporting {fmt}")
        self.log(f"Exporting run {self.current_run_id} as {fmt}")
        self.export_worker = ExportWorker(
            self.db,
            self.paths,
            self.current_project_id,
            self.current_run_id,
            fmt,
        )
        self.export_worker.finished_ok.connect(self._export_finished)
        self.export_worker.failed.connect(self._worker_failed)
        self.export_worker.start()

    def _export_finished(self, path: str) -> None:
        self.progress_label.setText("Export completed")
        self.progress_bar.setValue(100)
        self.set_message(f"Export saved: {path}")
        self.log(f"Export completed: {path}")
        self.set_busy(False)
        if self.current_project_id:
            self.load_project(self.current_project_id)
        self.tabs.setCurrentWidget(self.export_tab)

    def _worker_failed(self, message: str) -> None:
        self.active_run_started_at = None
        self.active_run_backgrounded = False
        self.progress_label.setText("Operation failed")
        self.progress_bar.setValue(0)
        self.set_message(None)
        self.set_error(message)
        self.log(f"ERROR: {message}")
        self.set_busy(False)
        self.show_error(message)
        if self.current_project_id:
            self.load_project(self.current_project_id)

    def run_in_background(self) -> None:
        if self.run_worker is None or not self.run_worker.isRunning():
            return
        self.active_run_backgrounded = True
        self.set_message("Cleanup continues in the background while you review other screens.")
        self.log("Cleanup moved to background")
        self.tabs.setCurrentWidget(self.home_tab)

    def cancel_active_run(self) -> None:
        if self.run_worker is None or not self.run_worker.isRunning():
            return
        self.set_message("Cancelling cleanup run...")
        self.log("Cancelling active cleanup run")
        self.run_worker.cancel()

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, APP_NAME, message)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    paths = AppPaths.discover()
    db = Database(paths)
    window = MainWindow(db, paths)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
