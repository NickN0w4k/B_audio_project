use crate::db::Database;
use crate::events::ProgressEvent;
use crate::settings::AppSettings;
use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::io::{BufRead, BufReader, Read};
use std::path::PathBuf;
use std::process::{Command, Stdio};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunOptions {
    pub intensity: String,
    pub apply_light_finishing: bool,
    pub export_stems: bool,
    pub gpu_enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunPayload {
    pub project_id: String,
    pub run_id: String,
    pub input_path: String,
    pub preset: String,
    pub options: RunOptions,
}

#[derive(Debug, Clone, Serialize)]
pub struct RunLaunchResult {
    pub run_id: String,
    pub status: String,
}

#[derive(Default)]
pub struct JobManager {
    active_run_id: Option<String>,
}

impl JobManager {
    pub fn active_run_id(&self) -> Option<&str> {
        self.active_run_id.as_deref()
    }

    pub fn set_active_run(&mut self, run_id: Option<String>) {
        self.active_run_id = run_id;
    }

    pub fn clear_if_matches(&mut self, run_id: &str) {
        if self.active_run_id.as_deref() == Some(run_id) {
            self.active_run_id = None;
        }
    }
}

pub fn write_payload(payload_path: PathBuf, payload: &RunPayload) -> Result<()> {
    let serialized = serde_json::to_string_pretty(payload)?;
    std::fs::write(payload_path, serialized)?;
    Ok(())
}

pub fn run_engine<F>(
    settings: &AppSettings,
    database: &Database,
    payload: RunPayload,
    mut on_progress: F,
) -> Result<RunLaunchResult>
where
    F: FnMut(&ProgressEvent),
{
    let payload_path = settings
        .storage_dir
        .join("projects")
        .join(&payload.project_id)
        .join("runs")
        .join(&payload.run_id)
        .join("run-payload.json");

    write_payload(payload_path.clone(), &payload)?;

    let mut child = Command::new(&settings.python_command)
        .arg(&settings.engine_entry)
        .arg("--run-payload")
        .arg(&payload_path)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;

    database.update_run_progress(&payload.run_id, "running")?;

    let stdout = child
        .stdout
        .take()
        .ok_or_else(|| anyhow!("Failed to capture engine stdout"))?;
    let mut stderr = child
        .stderr
        .take()
        .ok_or_else(|| anyhow!("Failed to capture engine stderr"))?;
    let reader = BufReader::new(stdout);

    for line in reader.lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }

        let value: Value = match serde_json::from_str(&line) {
            Ok(v) => v,
            Err(_) => continue, // non-JSON lines (e.g. DF logger output) are ignored
        };

        if value.get("step").is_some() {
            let progress: ProgressEvent = serde_json::from_value(value)?;
            database.update_run_progress(&progress.run_id, "running")?;
            database.upsert_run_step(&progress.run_id, &progress.step, &progress.status, None)?;
            on_progress(&progress);
            continue;
        }

        if value.get("status").and_then(Value::as_str) == Some("completed") {
            let report_path = value.get("report_path").and_then(Value::as_str);
            database.complete_run(&payload.run_id, report_path)?;
        }
    }

    let status = child.wait()?;
    let mut stderr_output = String::new();
    stderr.read_to_string(&mut stderr_output)?;

    if !status.success() {
        let failure_message = stderr_output.trim().to_string();
        database.fail_run(
            &payload.run_id,
            if failure_message.is_empty() {
                None
            } else {
                Some(failure_message.as_str())
            },
        )?;
        return Err(anyhow!(
            "Engine process failed: {}",
            failure_message
        ));
    }

    Ok(RunLaunchResult {
        run_id: payload.run_id,
        status: "completed".to_string(),
    })
}
