use anyhow::{anyhow, Result};
use chrono::Utc;
use rusqlite::{params, Connection, OptionalExtension};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize)]
pub struct ProjectSummary {
    pub id: String,
    pub name: String,
    pub status: String,
    pub created_at: String,
    pub updated_at: String,
    pub source_filename: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct SourceFileRecord {
    pub id: String,
    pub project_id: String,
    pub original_path: String,
    pub normalized_path: Option<String>,
    pub filename: String,
    pub duration_sec: Option<f64>,
    pub sample_rate: Option<i64>,
    pub channels: Option<i64>,
    pub format: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct RunSummary {
    pub id: String,
    pub project_id: String,
    pub preset: String,
    pub intensity: String,
    pub status: String,
    pub started_at: Option<String>,
    pub finished_at: Option<String>,
    pub report_path: Option<String>,
    pub failure_message: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct AnalysisIssue {
    pub id: String,
    pub label: String,
    pub severity: String,
    pub confidence: Option<f64>,
    pub description: String,
    pub artifact_title: Option<String>,
    pub detection: Option<String>,
    pub repair: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct AnalysisReportRecord {
    pub id: String,
    pub project_id: String,
    pub report_path: String,
    pub schema_version: Option<String>,
    pub compatibility_notice: Option<String>,
    pub recommended_preset: Option<String>,
    pub suggested_intensity: Option<String>,
    pub planned_repair_modules: Vec<String>,
    pub runtime_estimate_sec: Option<i64>,
    pub overall_confidence: Option<f64>,
    pub estimated_cutoff_hz: Option<f64>,
    pub spectrogram_path: Option<String>,
    pub summary_json: Option<String>,
    pub created_at: String,
    pub issues: Vec<AnalysisIssue>,
}

#[derive(Debug, Clone, Serialize)]
pub struct RunStepSummary {
    pub id: String,
    pub run_id: String,
    pub step_name: String,
    pub status: String,
    pub started_at: Option<String>,
    pub finished_at: Option<String>,
    pub metrics_json: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct AssetRecord {
    pub id: String,
    pub project_id: String,
    pub run_id: Option<String>,
    pub kind: String,
    pub path: String,
    pub metadata_json: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ExportRecord {
    pub id: String,
    pub run_id: String,
    pub format: String,
    pub path: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct RunDetail {
    pub run: RunSummary,
    pub steps: Vec<RunStepSummary>,
    pub assets: Vec<AssetRecord>,
    pub exports: Vec<ExportRecord>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ProjectDetail {
    pub project: ProjectSummary,
    pub source_file: SourceFileRecord,
    pub analysis_report: Option<AnalysisReportRecord>,
    pub latest_run: Option<RunSummary>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ImportProjectResult {
    pub project: ProjectDetail,
}

#[derive(Debug, Clone, Deserialize)]
pub struct NewProjectInput {
    pub source_path: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct NewRunResult {
    pub run: RunSummary,
    pub payload_path: String,
}

#[derive(Clone)]
pub struct Database {
    path: PathBuf,
}

#[derive(Clone, Copy)]
struct IssueStrategy {
    title: &'static str,
    detection: &'static str,
    repair: &'static str,
}

const GENERAL_CLEANUP_REPAIR: &str = "Gentle cleanup: keep the repair path conservative";

impl Database {
    pub fn new(path: impl AsRef<Path>) -> Result<Self> {
        Ok(Self {
            path: path.as_ref().to_path_buf(),
        })
    }

    fn connection(&self) -> Result<Connection> {
        Ok(Connection::open(&self.path)?)
    }

    pub fn initialize(&self) -> Result<()> {
        if let Some(parent) = self.path.parent() {
            fs::create_dir_all(parent)?;
        }

        let connection = self.connection()?;

        connection.execute_batch(
            r#"
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

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL
            );
            "#,
        )?;

        let columns = connection
            .prepare("PRAGMA table_info(pipeline_runs)")?
            .query_map([], |row| row.get::<_, String>(1))?
            .collect::<std::result::Result<Vec<_>, _>>()?;

        if !columns.iter().any(|column| column == "failure_message") {
            connection.execute("ALTER TABLE pipeline_runs ADD COLUMN failure_message TEXT", [])?;
        }

        Ok(())
    }

    pub fn import_project(
        &self,
        input: NewProjectInput,
        storage_dir: &Path,
    ) -> Result<ImportProjectResult> {
        let source_path = PathBuf::from(&input.source_path);
        if !source_path.exists() {
            return Err(anyhow!("Source file does not exist"));
        }

        let filename = source_path
            .file_name()
            .and_then(|value| value.to_str())
            .ok_or_else(|| anyhow!("Source file name is invalid"))?
            .to_string();

        let project_id = Uuid::new_v4().to_string();
        let source_id = Uuid::new_v4().to_string();
        let now = Utc::now().to_rfc3339();

        let project_dir = storage_dir.join("projects").join(&project_id);
        let source_dir = project_dir.join("source");
        fs::create_dir_all(&source_dir)?;

        let copied_original_path = source_dir.join(format!("original_{}", &filename));
        fs::copy(&source_path, &copied_original_path)?;

        let project_name = source_path
            .file_stem()
            .and_then(|value| value.to_str())
            .unwrap_or("Imported Project")
            .to_string();

        let format = source_path
            .extension()
            .and_then(|value| value.to_str())
            .map(|value| value.to_lowercase());

        let connection = self.connection()?;
        connection.execute(
            "INSERT INTO projects (id, name, status, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![project_id, project_name, "imported", now, now],
        )?;

        connection.execute(
            "INSERT INTO source_files (id, project_id, original_path, normalized_path, filename, duration_sec, sample_rate, channels, format) VALUES (?1, ?2, ?3, NULL, ?4, NULL, NULL, NULL, ?5)",
            params![source_id, project_id, copied_original_path.display().to_string(), filename, format],
        )?;

        let detail = self.get_project_detail(&project_id)?;
        Ok(ImportProjectResult { project: detail })
    }

    pub fn list_projects(&self) -> Result<Vec<ProjectSummary>> {
        let connection = self.connection()?;
        let mut statement = connection.prepare(
            r#"
            SELECT p.id, p.name, p.status, p.created_at, p.updated_at,
                   (SELECT filename FROM source_files sf WHERE sf.project_id = p.id ORDER BY rowid DESC LIMIT 1) AS source_filename
            FROM projects p
            ORDER BY p.updated_at DESC
            "#,
        )?;

        let rows = statement.query_map([], |row| {
            Ok(ProjectSummary {
                id: row.get(0)?,
                name: row.get(1)?,
                status: row.get(2)?,
                created_at: row.get(3)?,
                updated_at: row.get(4)?,
                source_filename: row.get(5)?,
            })
        })?;

        rows.collect::<Result<Vec<_>, _>>().map_err(Into::into)
    }

    pub fn get_project_detail(&self, project_id: &str) -> Result<ProjectDetail> {
        let connection = self.connection()?;

        let project = connection
            .query_row(
                r#"
                SELECT p.id, p.name, p.status, p.created_at, p.updated_at,
                       (SELECT filename FROM source_files sf WHERE sf.project_id = p.id ORDER BY rowid DESC LIMIT 1) AS source_filename
                FROM projects p
                WHERE p.id = ?1
                "#,
                params![project_id],
                |row| {
                    Ok(ProjectSummary {
                        id: row.get(0)?,
                        name: row.get(1)?,
                        status: row.get(2)?,
                        created_at: row.get(3)?,
                        updated_at: row.get(4)?,
                        source_filename: row.get(5)?,
                    })
                },
            )
            .optional()?
            .ok_or_else(|| anyhow!("Project not found"))?;

        let source_file = connection
            .query_row(
                r#"
                SELECT id, project_id, original_path, normalized_path, filename, duration_sec, sample_rate, channels, format
                FROM source_files
                WHERE project_id = ?1
                ORDER BY rowid DESC
                LIMIT 1
                "#,
                params![project_id],
                |row| {
                    Ok(SourceFileRecord {
                        id: row.get(0)?,
                        project_id: row.get(1)?,
                        original_path: row.get(2)?,
                        normalized_path: row.get(3)?,
                        filename: row.get(4)?,
                        duration_sec: row.get(5)?,
                        sample_rate: row.get(6)?,
                        channels: row.get(7)?,
                        format: row.get(8)?,
                    })
                },
            )
            .optional()?
            .ok_or_else(|| anyhow!("Project source file not found"))?;

        let latest_run = connection
            .query_row(
                r#"
                SELECT id, project_id, preset, intensity, status, started_at, finished_at, report_path, failure_message
                FROM pipeline_runs
                WHERE project_id = ?1
                ORDER BY rowid DESC
                LIMIT 1
                "#,
                params![project_id],
                |row| {
                    Ok(RunSummary {
                        id: row.get(0)?,
                        project_id: row.get(1)?,
                        preset: row.get(2)?,
                        intensity: row.get(3)?,
                        status: row.get(4)?,
                        started_at: row.get(5)?,
                        finished_at: row.get(6)?,
                        report_path: row.get(7)?,
                        failure_message: row.get(8)?,
                    })
                },
            )
            .optional()?;

        let analysis_report = connection
            .query_row(
                r#"
                SELECT id, project_id, report_path, recommended_preset, runtime_estimate_sec, summary_json, created_at
                FROM analysis_reports
                WHERE project_id = ?1
                ORDER BY rowid DESC
                LIMIT 1
                "#,
                params![project_id],
                |row| {
                    let summary_json: Option<String> = row.get(5)?;
                    let schema_version = summary_json
                        .as_deref()
                        .and_then(parse_schema_version_from_summary);
                    let legacy_report = schema_version.is_none();
                    let issues = summary_json
                        .as_deref()
                        .and_then(parse_issues_from_summary)
                        .unwrap_or_default();
                    let suggested_intensity = summary_json
                        .as_deref()
                        .and_then(parse_suggested_intensity_from_summary)
                        .or_else(|| derive_suggested_intensity(&issues));
                    let planned_repair_modules = summary_json
                        .as_deref()
                        .and_then(parse_planned_repair_modules_from_summary)
                        .unwrap_or_else(|| derive_planned_repair_modules(&issues));

                    Ok(AnalysisReportRecord {
                        id: row.get(0)?,
                        project_id: row.get(1)?,
                        report_path: row.get(2)?,
                        schema_version,
                        compatibility_notice: legacy_report.then_some(
                            "Legacy analysis report detected. Some guidance fields were reconstructed during load."
                                .to_string(),
                        ),
                        recommended_preset: row.get(3)?,
                        suggested_intensity,
                        planned_repair_modules,
                        runtime_estimate_sec: row.get(4)?,
                        overall_confidence: summary_json
                            .as_deref()
                            .and_then(parse_overall_confidence_from_summary),
                        estimated_cutoff_hz: summary_json
                            .as_deref()
                            .and_then(parse_estimated_cutoff_from_summary),
                        spectrogram_path: summary_json
                            .as_deref()
                            .and_then(parse_spectrogram_path_from_summary),
                        summary_json,
                        created_at: row.get(6)?,
                        issues,
                    })
                },
            )
            .optional()?;

        Ok(ProjectDetail {
            project,
            source_file,
            analysis_report,
            latest_run,
        })
    }

    pub fn create_run(
        &self,
        project_id: &str,
        preset: &str,
        intensity: &str,
        storage_dir: &Path,
    ) -> Result<NewRunResult> {
        let now = Utc::now().to_rfc3339();
        let run_id = Uuid::new_v4().to_string();
        let run_dir = storage_dir.join("projects").join(project_id).join("runs").join(&run_id);
        fs::create_dir_all(&run_dir)?;

        let payload_path = run_dir.join("run-payload.json");

        let connection = self.connection()?;
        connection.execute(
            "INSERT INTO pipeline_runs (id, project_id, preset, intensity, status, started_at, finished_at, plan_path, report_path) VALUES (?1, ?2, ?3, ?4, ?5, ?6, NULL, NULL, NULL)",
            params![run_id, project_id, preset, intensity, "queued", now],
        )?;

        connection.execute(
            "UPDATE projects SET status = ?1, updated_at = ?2 WHERE id = ?3",
            params!["processing", now, project_id],
        )?;

        let run = self
            .get_latest_run(project_id)?
            .ok_or_else(|| anyhow!("Failed to create run"))?;

        Ok(NewRunResult {
            run,
            payload_path: payload_path.display().to_string(),
        })
    }

    pub fn store_analysis_report(
        &self,
        project_id: &str,
        analysis_report_path: &str,
        normalized_path: &str,
    ) -> Result<()> {
        let connection = self.connection()?;
        let now = Utc::now().to_rfc3339();

        let analysis_json = std::fs::read_to_string(analysis_report_path)?;
        let analysis_value = serde_json::from_str::<serde_json::Value>(&analysis_json)?;
        let recommended_preset = analysis_value
            .get("recommended_preset")
            .and_then(serde_json::Value::as_str)
            .unwrap_or("ai_song_cleanup");
        let runtime_estimate_sec = analysis_value
            .get("runtime_estimate_sec")
            .and_then(serde_json::Value::as_i64)
            .unwrap_or(45);

        connection.execute(
            "UPDATE source_files SET normalized_path = ?1 WHERE project_id = ?2",
            params![normalized_path, project_id],
        )?;

        connection.execute(
            "DELETE FROM analysis_reports WHERE project_id = ?1",
            params![project_id],
        )?;

        connection.execute(
            "INSERT INTO analysis_reports (id, project_id, report_path, recommended_preset, runtime_estimate_sec, summary_json, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            params![
                Uuid::new_v4().to_string(),
                project_id,
                analysis_report_path,
                recommended_preset,
                runtime_estimate_sec,
                analysis_json,
                now,
            ],
        )?;

        connection.execute(
            "DELETE FROM assets WHERE project_id = ?1 AND run_id IS NULL AND kind = 'normalized_audio'",
            params![project_id],
        )?;

        connection.execute(
            "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?1, ?2, NULL, ?3, ?4, NULL)",
            params![Uuid::new_v4().to_string(), project_id, "normalized_audio", normalized_path],
        )?;

        connection.execute(
            "UPDATE projects SET status = ?1, updated_at = ?2 WHERE id = ?3",
            params!["analyzed", now, project_id],
        )?;

        Ok(())
    }

    pub fn get_latest_run(&self, project_id: &str) -> Result<Option<RunSummary>> {
        let connection = self.connection()?;
        connection
            .query_row(
                r#"
                SELECT id, project_id, preset, intensity, status, started_at, finished_at, report_path, failure_message
                FROM pipeline_runs
                WHERE project_id = ?1
                ORDER BY rowid DESC
                LIMIT 1
                "#,
                params![project_id],
                |row| {
                    Ok(RunSummary {
                        id: row.get(0)?,
                        project_id: row.get(1)?,
                        preset: row.get(2)?,
                        intensity: row.get(3)?,
                        status: row.get(4)?,
                        started_at: row.get(5)?,
                        finished_at: row.get(6)?,
                        report_path: row.get(7)?,
                        failure_message: row.get(8)?,
                    })
                },
            )
            .optional()
            .map_err(Into::into)
    }

    pub fn update_run_progress(&self, run_id: &str, status: &str) -> Result<()> {
        let connection = self.connection()?;
        connection.execute(
            "UPDATE pipeline_runs SET status = ?1 WHERE id = ?2",
            params![status, run_id],
        )?;
        Ok(())
    }

    pub fn upsert_run_step(
        &self,
        run_id: &str,
        step_name: &str,
        status: &str,
        metrics_json: Option<&str>,
    ) -> Result<()> {
        let connection = self.connection()?;
        let existing_id: Option<String> = connection
            .query_row(
                "SELECT id FROM run_steps WHERE run_id = ?1 AND step_name = ?2 LIMIT 1",
                params![run_id, step_name],
                |row| row.get(0),
            )
            .optional()?;

        let now = Utc::now().to_rfc3339();

        match existing_id {
            Some(step_id) => {
                let finished_at = if status == "completed" || status == "failed" {
                    Some(now.clone())
                } else {
                    None
                };

                connection.execute(
                    "UPDATE run_steps SET status = ?1, finished_at = COALESCE(?2, finished_at), metrics_json = COALESCE(?3, metrics_json) WHERE id = ?4",
                    params![status, finished_at, metrics_json, step_id],
                )?;
            }
            None => {
                let step_id = Uuid::new_v4().to_string();
                let finished_at = if status == "completed" || status == "failed" {
                    Some(now.clone())
                } else {
                    None
                };

                connection.execute(
                    "INSERT INTO run_steps (id, run_id, step_name, status, started_at, finished_at, metrics_json) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                    params![step_id, run_id, step_name, status, now, finished_at, metrics_json],
                )?;
            }
        }

        Ok(())
    }

    pub fn get_run_detail(&self, run_id: &str) -> Result<RunDetail> {
        let connection = self.connection()?;

        let run = connection
            .query_row(
                r#"
                SELECT id, project_id, preset, intensity, status, started_at, finished_at, report_path, failure_message
                FROM pipeline_runs
                WHERE id = ?1
                "#,
                params![run_id],
                |row| {
                    Ok(RunSummary {
                        id: row.get(0)?,
                        project_id: row.get(1)?,
                        preset: row.get(2)?,
                        intensity: row.get(3)?,
                        status: row.get(4)?,
                        started_at: row.get(5)?,
                        finished_at: row.get(6)?,
                        report_path: row.get(7)?,
                        failure_message: row.get(8)?,
                    })
                },
            )
            .optional()?
            .ok_or_else(|| anyhow!("Run not found"))?;

        let mut statement = connection.prepare(
            r#"
            SELECT id, run_id, step_name, status, started_at, finished_at, metrics_json
            FROM run_steps
            WHERE run_id = ?1
            ORDER BY rowid ASC
            "#,
        )?;

        let rows = statement.query_map(params![run_id], |row| {
            Ok(RunStepSummary {
                id: row.get(0)?,
                run_id: row.get(1)?,
                step_name: row.get(2)?,
                status: row.get(3)?,
                started_at: row.get(4)?,
                finished_at: row.get(5)?,
                metrics_json: row.get(6)?,
            })
        })?;

        let steps = rows.collect::<Result<Vec<_>, _>>().map_err(anyhow::Error::from)?;

        let mut asset_statement = connection.prepare(
            r#"
            SELECT id, project_id, run_id, kind, path, metadata_json
            FROM assets
            WHERE run_id = ?1
            ORDER BY rowid ASC
            "#,
        )?;

        let asset_rows = asset_statement.query_map(params![run_id], |row| {
            Ok(AssetRecord {
                id: row.get(0)?,
                project_id: row.get(1)?,
                run_id: row.get(2)?,
                kind: row.get(3)?,
                path: row.get(4)?,
                metadata_json: row.get(5)?,
            })
        })?;

        let assets = asset_rows
            .collect::<Result<Vec<_>, _>>()
            .map_err(anyhow::Error::from)?;

        let mut export_statement = connection.prepare(
            r#"
            SELECT id, run_id, format, path, created_at
            FROM exports
            WHERE run_id = ?1
            ORDER BY rowid ASC
            "#,
        )?;

        let export_rows = export_statement.query_map(params![run_id], |row| {
            Ok(ExportRecord {
                id: row.get(0)?,
                run_id: row.get(1)?,
                format: row.get(2)?,
                path: row.get(3)?,
                created_at: row.get(4)?,
            })
        })?;

        let exports = export_rows
            .collect::<Result<Vec<_>, _>>()
            .map_err(anyhow::Error::from)?;

        Ok(RunDetail {
            run,
            steps,
            assets,
            exports,
        })
    }

    pub fn complete_run(&self, run_id: &str, report_path: Option<&str>) -> Result<()> {
        let connection = self.connection()?;
        let now = Utc::now().to_rfc3339();

        let project_id: String = connection.query_row(
            "SELECT project_id FROM pipeline_runs WHERE id = ?1",
            params![run_id],
            |row| row.get(0),
        )?;

        connection.execute(
            "UPDATE pipeline_runs SET status = ?1, finished_at = ?2, report_path = COALESCE(?3, report_path) WHERE id = ?4",
            params!["completed", now, report_path, run_id],
        )?;

        connection.execute(
            "UPDATE pipeline_runs SET failure_message = NULL WHERE id = ?1",
            params![run_id],
        )?;

        connection.execute(
            "UPDATE projects SET status = ?1, updated_at = ?2 WHERE id = ?3",
            params!["ready", now, project_id],
        )?;

        if let Some(report_path) = report_path {
            let report_json = std::fs::read_to_string(report_path).unwrap_or_default();
            if let Ok(value) = serde_json::from_str::<serde_json::Value>(&report_json) {
                if let Some(normalized_path) = value.get("normalized_path").and_then(serde_json::Value::as_str) {
                    connection.execute(
                        "UPDATE source_files SET normalized_path = ?1 WHERE project_id = ?2",
                        params![normalized_path, project_id],
                    )?;

                    connection.execute(
                        "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?1, ?2, ?3, ?4, ?5, NULL)",
                        params![Uuid::new_v4().to_string(), project_id, run_id, "normalized_audio", normalized_path],
                    )?;
                }

                if let Some(analysis_report_path) = value
                    .get("analysis_report_path")
                    .and_then(serde_json::Value::as_str)
                {
                    let analysis_json = std::fs::read_to_string(analysis_report_path).unwrap_or_default();
                    if let Ok(analysis_value) = serde_json::from_str::<serde_json::Value>(&analysis_json) {
                        let recommended_preset = analysis_value
                            .get("recommended_preset")
                            .and_then(serde_json::Value::as_str)
                            .unwrap_or("ai_song_cleanup");
                        let runtime_estimate_sec = analysis_value
                            .get("runtime_estimate_sec")
                            .and_then(serde_json::Value::as_i64)
                            .unwrap_or(45);

                        connection.execute(
                            "INSERT INTO analysis_reports (id, project_id, report_path, recommended_preset, runtime_estimate_sec, summary_json, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                            params![
                                Uuid::new_v4().to_string(),
                                project_id,
                                analysis_report_path,
                                recommended_preset,
                                runtime_estimate_sec,
                                analysis_json,
                                now,
                            ],
                        )?;
                    }
                }

                if let Some(preview_path) = value.get("preview_path").and_then(serde_json::Value::as_str) {
                    connection.execute(
                        "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?1, ?2, ?3, ?4, ?5, NULL)",
                        params![Uuid::new_v4().to_string(), project_id, run_id, "mix_preview", preview_path],
                    )?;
                }

                for (report_key, kind) in [
                    ("vocals_path", "stem_vocals"),
                    ("music_path", "stem_music"),
                    ("repaired_vocals_path", "repaired_vocals"),
                    ("repaired_music_path", "repaired_music"),
                ] {
                    if let Some(asset_path) = value.get(report_key).and_then(serde_json::Value::as_str) {
                        connection.execute(
                            "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?1, ?2, ?3, ?4, ?5, NULL)",
                            params![Uuid::new_v4().to_string(), project_id, run_id, kind, asset_path],
                        )?;
                    }
                }

                if let Some(export_path) = value.get("export_path").and_then(serde_json::Value::as_str) {
                    connection.execute(
                        "INSERT INTO exports (id, run_id, format, path, created_at) VALUES (?1, ?2, ?3, ?4, ?5)",
                        params![Uuid::new_v4().to_string(), run_id, "wav", export_path, now],
                    )?;

                    connection.execute(
                        "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?1, ?2, ?3, ?4, ?5, NULL)",
                        params![Uuid::new_v4().to_string(), project_id, run_id, "cleaned_export", export_path],
                    )?;
                }
            }
        }

        Ok(())
    }

    pub fn fail_run(&self, run_id: &str, failure_message: Option<&str>) -> Result<()> {
        let connection = self.connection()?;
        let now = Utc::now().to_rfc3339();

        let project_id: String = connection.query_row(
            "SELECT project_id FROM pipeline_runs WHERE id = ?1",
            params![run_id],
            |row| row.get(0),
        )?;

        connection.execute(
            "UPDATE pipeline_runs SET status = ?1, finished_at = ?2, failure_message = ?3 WHERE id = ?4",
            params!["failed", now, failure_message, run_id],
        )?;

        connection.execute(
            "UPDATE projects SET status = ?1, updated_at = ?2 WHERE id = ?3",
            params!["error", now, project_id],
        )?;

        Ok(())
    }

    pub fn add_export(
        &self,
        run_id: &str,
        project_id: &str,
        format: &str,
        path: &str,
    ) -> Result<String> {
        let connection = self.connection()?;
        let id = Uuid::new_v4().to_string();
        let now = Utc::now().to_rfc3339();

        connection.execute(
            "INSERT INTO exports (id, run_id, format, path, created_at) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![id, run_id, format, path, now],
        )?;

        connection.execute(
            "INSERT INTO assets (id, project_id, run_id, kind, path, metadata_json) VALUES (?1, ?2, ?3, ?4, ?5, NULL)",
            params![Uuid::new_v4().to_string(), project_id, run_id, "cleaned_export", path],
        )?;

        Ok(id)
    }

    pub fn get_export_path_for_run(&self, run_id: &str, format: &str) -> Result<Option<String>> {
        let connection = self.connection()?;
        connection
            .query_row(
                "SELECT path FROM exports WHERE run_id = ?1 AND format = ?2 ORDER BY rowid DESC LIMIT 1",
                params![run_id, format],
                |row: &rusqlite::Row<'_>| row.get(0),
            )
            .optional()
            .map_err(Into::into)
    }
}

fn parse_issues_from_summary(summary_json: &str) -> Option<Vec<AnalysisIssue>> {
    let value = serde_json::from_str::<serde_json::Value>(summary_json).ok()?;
    let issues = value.get("issues")?.as_array()?;

    Some(
        issues
            .iter()
            .filter_map(|issue| {
                let issue_id = issue.get("id")?.as_str()?.to_string();
                let strategy = issue_strategy(&issue_id);
                Some(AnalysisIssue {
                    id: issue_id,
                    label: issue.get("label")?.as_str()?.to_string(),
                    severity: issue.get("severity")?.as_str()?.to_string(),
                    confidence: issue.get("confidence").and_then(serde_json::Value::as_f64),
                    description: issue.get("description")?.as_str()?.to_string(),
                    artifact_title: issue
                        .get("artifact_title")
                        .and_then(serde_json::Value::as_str)
                        .map(ToString::to_string)
                        .or_else(|| strategy.map(|value| value.title.to_string())),
                    detection: issue
                        .get("detection")
                        .and_then(serde_json::Value::as_str)
                        .map(ToString::to_string)
                        .or_else(|| strategy.map(|value| value.detection.to_string())),
                    repair: issue
                        .get("repair")
                        .and_then(serde_json::Value::as_str)
                        .map(ToString::to_string)
                        .or_else(|| strategy.map(|value| value.repair.to_string())),
                })
            })
            .collect(),
    )
}

fn parse_overall_confidence_from_summary(summary_json: &str) -> Option<f64> {
    let value = serde_json::from_str::<serde_json::Value>(summary_json).ok()?;
    value.get("overall_confidence")?.as_f64()
}

fn parse_estimated_cutoff_from_summary(summary_json: &str) -> Option<f64> {
    let value = serde_json::from_str::<serde_json::Value>(summary_json).ok()?;
    value.get("estimated_cutoff_hz")?.as_f64()
}

fn parse_spectrogram_path_from_summary(summary_json: &str) -> Option<String> {
    let value = serde_json::from_str::<serde_json::Value>(summary_json).ok()?;
    value.get("spectrogram_path")?.as_str().map(ToString::to_string)
}

fn parse_suggested_intensity_from_summary(summary_json: &str) -> Option<String> {
    let value = serde_json::from_str::<serde_json::Value>(summary_json).ok()?;
    value
        .get("suggested_intensity")?
        .as_str()
        .map(ToString::to_string)
}

fn parse_schema_version_from_summary(summary_json: &str) -> Option<String> {
    let value = serde_json::from_str::<serde_json::Value>(summary_json).ok()?;
    value
        .get("schema_version")?
        .as_str()
        .map(ToString::to_string)
}

fn parse_planned_repair_modules_from_summary(summary_json: &str) -> Option<Vec<String>> {
    let value = serde_json::from_str::<serde_json::Value>(summary_json).ok()?;
    let modules = value.get("planned_repair_modules")?.as_array()?;

    Some(
        modules
            .iter()
            .filter_map(|module| module.as_str().map(ToString::to_string))
            .collect(),
    )
}

fn derive_suggested_intensity(issues: &[AnalysisIssue]) -> Option<String> {
    if issues.is_empty() {
        return Some("medium".to_string());
    }

    let high_count = issues.iter().filter(|issue| issue.severity == "high").count();
    let medium_count = issues.iter().filter(|issue| issue.severity == "medium").count();
    let has_robotic_vocals = issues.iter().any(|issue| issue.id == "robotic_vocals");

    let suggested = if high_count >= 2 || (high_count >= 1 && medium_count >= 2) {
        "strong"
    } else if has_robotic_vocals || high_count >= 1 || medium_count >= 2 {
        "medium"
    } else {
        "light"
    };

    Some(suggested.to_string())
}

fn derive_planned_repair_modules(issues: &[AnalysisIssue]) -> Vec<String> {
    let mut modules: Vec<String> = issues.iter().filter_map(|issue| issue.repair.clone()).collect();
    modules.dedup();

    if modules.is_empty() {
        modules.push(GENERAL_CLEANUP_REPAIR.to_string());
    }

    modules
}

fn issue_strategy(issue_id: &str) -> Option<IssueStrategy> {
    match issue_id {
        "dull_top_end" => Some(IssueStrategy {
            title: "High-Frequency Rolloff",
            detection: "Detected from missing top-band energy and a visible upper-band cutoff in the spectrogram.",
            repair: "Use conservative brightness shaping now; later upgrade path is generative top-end reconstruction per stem.",
        }),
        "metallic_highs" => Some(IssueStrategy {
            title: "Metallic Resonances",
            detection: "Detected from excess energy in the 6-10 kHz harshness band.",
            repair: "Use de-esser plus targeted upper-band reduction after separation, especially on vocals.",
        }),
        "robotic_vocals" => Some(IssueStrategy {
            title: "Robotic Quantization",
            detection: "Detected from overly uniform vocal-presence energy over time while upper vocal artifacts remain active.",
            repair: "Use vocal humanization EQ now; later upgrade path is dedicated vocal naturalization and formant-aware restoration.",
        }),
        "codec_haze" => Some(IssueStrategy {
            title: "Codec / Digital Haze",
            detection: "Detected from low-mid clustering and reduced spectral clarity.",
            repair: "Use low-mid cleanup and clarity compensation, ideally after stem separation to avoid damaging the full mix.",
        }),
        "congested_mix" => Some(IssueStrategy {
            title: "Congested Dynamics",
            detection: "Detected from dense RMS levels and reduced crest factor.",
            repair: "Use gentle dynamic control after repair, keeping restoration separate from final mastering.",
        }),
        "noise_floor" => Some(IssueStrategy {
            title: "Raised Noise Floor",
            detection: "Detected from unusually elevated quiet passages relative to the program level.",
            repair: "Use conditional vocal denoising only when the noise-floor flag is present.",
        }),
        "room_smear" => Some(IssueStrategy {
            title: "Room Smear / Baked-In Reverb",
            detection: "Detected from softened transient definition combined with persistent low-mid buildup.",
            repair: "Use only light clarity compensation now; a real de-reverb path remains a later dedicated module.",
        }),
        "general_cleanup" => Some(IssueStrategy {
            title: "General Cleanup",
            detection: "No dominant artifact class was detected with high confidence.",
            repair: "Keep the path conservative and avoid heavy restoration steps.",
        }),
        _ => None,
    }
}
