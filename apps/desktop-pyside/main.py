from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
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
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "B Audio Project"
DEFAULT_PRESET = "ai_song_cleanup"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
                SELECT id, project_id, preset, intensity, status, started_at, finished_at, report_path, failure_message
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
                    "compatibility_notice": None if summary.get("schema_version") else "Legacy analysis report detected. Some guidance fields were reconstructed during load.",
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
                SELECT id, project_id, preset, intensity, status, started_at, finished_at, report_path, failure_message
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
            return {"run": dict(run), "steps": steps, "assets": assets, "exports": exports}

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
                (source_id, project_id, str(copied_original_path), filename, source.suffix.lower().lstrip(".")),
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

    def run(self) -> None:
        try:
            project = self.db.get_project_detail(self.project_id)
            analysis_report = project.get("analysis_report")
            if not analysis_report:
                raise RuntimeError("Run analysis first before starting cleanup.")

            run_id, payload_path = self.db.create_run(self.project_id, self.preset, self.intensity)
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
            self.db.update_run_progress(run_id, "running")
            assert process.stdout is not None
            for raw_line in process.stdout:
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
            if return_code != 0:
                failure_message = stderr_output.strip() or "Engine process failed"
                self.db.fail_run(run_id, failure_message)
                raise RuntimeError(failure_message)

            self.finished_ok.emit(run_id)
        except Exception as error:  # noqa: BLE001
            self.failed.emit(str(error))


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


class MainWindow(QMainWindow):
    def __init__(self, db: Database, paths: AppPaths) -> None:
        super().__init__()
        self.db = db
        self.paths = paths
        self.current_project_id: str | None = None
        self.current_run_id: str | None = None
        self.analyze_worker: AnalyzeWorker | None = None
        self.run_worker: RunWorker | None = None
        self.export_worker: ExportWorker | None = None

        self.setWindowTitle(f"{APP_NAME} · PySide6")
        self.resize(1440, 920)
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
        subtitle = QLabel("Tool-first desktop surface. Flat, clear, and direct.")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(subtitle)
        layout.addLayout(header)

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
        left_layout.addWidget(projects_box)
        splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        summary_box = QGroupBox("Overview")
        summary_layout = QGridLayout(summary_box)
        summary_layout.setHorizontalSpacing(12)
        summary_layout.setVerticalSpacing(8)
        self.project_name_value = QLabel("No project selected")
        self.status_value = QLabel("-")
        self.schema_value = QLabel("-")
        self.preset_value = QLabel("-")
        self.intensity_value = QLabel("-")
        self.cutoff_value = QLabel("-")
        summary_layout.addWidget(QLabel("Project"), 0, 0)
        summary_layout.addWidget(self.project_name_value, 0, 1)
        summary_layout.addWidget(QLabel("Status"), 0, 2)
        summary_layout.addWidget(self.status_value, 0, 3)
        summary_layout.addWidget(QLabel("Schema"), 1, 0)
        summary_layout.addWidget(self.schema_value, 1, 1)
        summary_layout.addWidget(QLabel("Preset"), 1, 2)
        summary_layout.addWidget(self.preset_value, 1, 3)
        summary_layout.addWidget(QLabel("Suggested Intensity"), 2, 0)
        summary_layout.addWidget(self.intensity_value, 2, 1)
        summary_layout.addWidget(QLabel("Detected Cutoff"), 2, 2)
        summary_layout.addWidget(self.cutoff_value, 2, 3)
        right_layout.addWidget(summary_box)

        actions_box = QGroupBox("Actions")
        actions_layout = QGridLayout(actions_box)
        self.analyze_button = QPushButton("Run Analysis")
        self.analyze_button.clicked.connect(self.run_analysis)
        self.cleanup_button = QPushButton("Start Cleanup")
        self.cleanup_button.clicked.connect(self.start_cleanup)
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_audio)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([DEFAULT_PRESET, "restore_brightness", "reduce_metallic_harshness", "gentle_cleanup"])
        self.intensity_combo = QComboBox()
        self.intensity_combo.addItems(["light", "medium", "strong"])
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["wav", "flac"])
        self.gpu_checkbox = QCheckBox("Use GPU when available")
        self.gpu_checkbox.setChecked(True)
        self.finishing_checkbox = QCheckBox("Apply light finishing")
        self.export_stems_checkbox = QCheckBox("Export stems")
        actions_layout.addWidget(QLabel("Preset"), 0, 0)
        actions_layout.addWidget(self.preset_combo, 0, 1)
        actions_layout.addWidget(QLabel("Intensity"), 0, 2)
        actions_layout.addWidget(self.intensity_combo, 0, 3)
        actions_layout.addWidget(self.gpu_checkbox, 1, 0, 1, 2)
        actions_layout.addWidget(self.finishing_checkbox, 1, 2, 1, 2)
        actions_layout.addWidget(self.export_stems_checkbox, 2, 0, 1, 2)
        actions_layout.addWidget(QLabel("Export Format"), 2, 2)
        actions_layout.addWidget(self.export_format_combo, 2, 3)
        actions_layout.addWidget(self.analyze_button, 3, 0)
        actions_layout.addWidget(self.cleanup_button, 3, 1)
        actions_layout.addWidget(self.export_button, 3, 2)
        right_layout.addWidget(actions_box)

        progress_box = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_box)
        self.progress_label = QLabel("Idle")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        right_layout.addWidget(progress_box)

        details_split = QSplitter(Qt.Orientation.Horizontal)
        details_split.setChildrenCollapsible(False)

        issues_box = QGroupBox("Detected Issues")
        issues_layout = QVBoxLayout(issues_box)
        self.issue_list = QListWidget()
        issues_layout.addWidget(self.issue_list)
        details_split.addWidget(issues_box)

        modules_box = QGroupBox("Repair Plan")
        modules_layout = QVBoxLayout(modules_box)
        self.module_list = QListWidget()
        modules_layout.addWidget(self.module_list)
        details_split.addWidget(modules_box)

        right_layout.addWidget(details_split, 1)

        log_box = QGroupBox("Activity")
        log_layout = QVBoxLayout(log_box)
        self.activity_log = QPlainTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        log_layout.addWidget(self.activity_log)
        right_layout.addWidget(log_box, 1)

        splitter.addWidget(right_panel)
        splitter.setSizes([320, 1020])

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
            QGroupBox {
                background: #171a1f;
                border: 1px solid #2a3039;
                margin-top: 12px;
                padding: 12px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QListWidget, QPlainTextEdit, QComboBox {
                background: #0e1014;
                border: 1px solid #2a3039;
                selection-background-color: #2b4f75;
                outline: none;
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

    def set_busy(self, busy: bool) -> None:
        self.analyze_button.setDisabled(busy or self.current_project_id is None)
        self.cleanup_button.setDisabled(busy or self.current_project_id is None)
        self.export_button.setDisabled(busy or self.current_run_id is None)

    def refresh_projects(self) -> None:
        selected_id = self.current_project_id
        self.project_list.clear()
        for project in self.db.list_projects():
            text = f"{project['name']}\n{project['status']}"
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
        self.project_name_value.setText("No project selected")
        self.status_value.setText("-")
        self.schema_value.setText("-")
        self.preset_value.setText("-")
        self.intensity_value.setText("-")
        self.cutoff_value.setText("-")
        self.issue_list.clear()
        self.module_list.clear()
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
        project = detail["project"]
        analysis_report = detail["analysis_report"]
        latest_run = detail["latest_run"]
        self.current_run_id = latest_run["id"] if latest_run else None

        self.project_name_value.setText(project["name"])
        self.status_value.setText(project["status"])
        self.schema_value.setText((analysis_report or {}).get("schema_version") or "legacy / unknown")
        self.preset_value.setText((analysis_report or {}).get("recommended_preset") or "-")
        self.intensity_value.setText((analysis_report or {}).get("suggested_intensity") or "-")
        cutoff = (analysis_report or {}).get("estimated_cutoff_hz")
        self.cutoff_value.setText(f"{cutoff} Hz" if cutoff is not None else "-")

        self.issue_list.clear()
        if analysis_report:
            if analysis_report.get("compatibility_notice"):
                self.issue_list.addItem(f"NOTICE: {analysis_report['compatibility_notice']}")
            for issue in analysis_report.get("issues", []):
                title = issue.get("artifact_title") or issue.get("label") or issue.get("id")
                confidence = issue.get("confidence")
                summary = f"{title} [{issue.get('severity', '-')}]"
                if confidence is not None:
                    summary += f" · conf {confidence}"
                item = QListWidgetItem(summary)
                item.setToolTip(
                    "\n".join(
                        part
                        for part in [
                            issue.get("description"),
                            f"Detection: {issue.get('detection')}" if issue.get("detection") else None,
                            f"Repair: {issue.get('repair')}" if issue.get("repair") else None,
                        ]
                        if part
                    )
                )
                self.issue_list.addItem(item)

        self.module_list.clear()
        for module in (analysis_report or {}).get("planned_repair_modules", []):
            self.module_list.addItem(module)

        if latest_run:
            run_detail = self.db.get_run_detail(latest_run["id"])
            if run_detail["steps"]:
                last_step = run_detail["steps"][-1]
                self.progress_label.setText(f"{last_step['step_name']}: {last_step['status']}")
            else:
                self.progress_label.setText(latest_run["status"])
        else:
            self.progress_label.setText("Idle")
            self.progress_bar.setValue(0)

        self.set_busy(False)

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
            self.refresh_projects()
            self._select_project(project_id)
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
        self.log(f"Analysis completed for {project_id}")
        self.set_busy(False)
        self.load_project(project_id)

    def start_cleanup(self) -> None:
        if not self.current_project_id:
            return
        self.set_busy(True)
        self.progress_label.setText("Starting cleanup")
        self.progress_bar.setValue(0)
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
        self.run_worker.failed.connect(self._worker_failed)
        self.run_worker.start()

    def _run_progress(self, step: str, status: str, message: str, progress: float) -> None:
        self.progress_label.setText(f"{step} · {status} · {message}")
        self.progress_bar.setValue(int(progress * 100))
        self.log(f"{step}: {message}")

    def _run_finished(self, run_id: str) -> None:
        self.current_run_id = run_id
        self.progress_label.setText("Cleanup completed")
        self.progress_bar.setValue(100)
        self.log(f"Cleanup completed for run {run_id}")
        self.set_busy(False)
        if self.current_project_id:
            self.load_project(self.current_project_id)

    def export_audio(self) -> None:
        if not self.current_project_id or not self.current_run_id:
            return
        self.set_busy(True)
        fmt = self.export_format_combo.currentText()
        self.progress_label.setText(f"Exporting {fmt}")
        self.log(f"Exporting run {self.current_run_id} as {fmt}")
        self.export_worker = ExportWorker(self.db, self.paths, self.current_project_id, self.current_run_id, fmt)
        self.export_worker.finished_ok.connect(self._export_finished)
        self.export_worker.failed.connect(self._worker_failed)
        self.export_worker.start()

    def _export_finished(self, path: str) -> None:
        self.progress_label.setText("Export completed")
        self.progress_bar.setValue(100)
        self.log(f"Export completed: {path}")
        self.set_busy(False)
        if self.current_project_id:
            self.load_project(self.current_project_id)

    def _worker_failed(self, message: str) -> None:
        self.progress_label.setText("Operation failed")
        self.progress_bar.setValue(0)
        self.log(f"ERROR: {message}")
        self.set_busy(False)
        self.show_error(message)
        if self.current_project_id:
            self.load_project(self.current_project_id)

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
