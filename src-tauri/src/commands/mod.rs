use crate::db::{ImportProjectResult, NewProjectInput, ProjectDetail, ProjectSummary, RunDetail};
use crate::jobs::{run_engine, RunLaunchResult, RunOptions, RunPayload};
use crate::settings::AppSettingsSnapshot;
use crate::AppState;
use serde::Serialize;
use std::path::PathBuf;
use std::process::Command;
use std::thread;
use tauri::Emitter;
use tauri::Manager;
use tauri::State;
use tauri_plugin_dialog::DialogExt;

#[derive(Debug, Serialize)]
pub struct InitResponse {
    pub ok: bool,
    pub message: String,
}

#[derive(Debug, Serialize)]
pub struct AppStatus {
    pub app_name: String,
    pub storage_dir: String,
    pub database_path: String,
    pub engine_entry: String,
    pub python_command: String,
    pub cuda_available: bool,
    pub gpu_name: Option<String>,
    pub active_run_id: Option<String>,
}

#[derive(Debug, serde::Deserialize)]
struct PythonRuntimeStatus {
    cuda_available: bool,
    gpu_name: Option<String>,
}

fn detect_python_runtime(python_command: &str) -> PythonRuntimeStatus {
    let probe = Command::new(python_command)
        .args([
            "-c",
            "import json; import torch; print(json.dumps({'cuda_available': bool(torch.cuda.is_available()), 'gpu_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))",
        ])
        .output();

    let Ok(output) = probe else {
        return PythonRuntimeStatus {
            cuda_available: false,
            gpu_name: None,
        };
    };

    if !output.status.success() {
        return PythonRuntimeStatus {
            cuda_available: false,
            gpu_name: None,
        };
    }

    serde_json::from_slice(&output.stdout).unwrap_or(PythonRuntimeStatus {
        cuda_available: false,
        gpu_name: None,
    })
}

#[derive(Debug, Serialize)]
pub struct ProjectListResponse {
    pub projects: Vec<ProjectSummary>,
}

#[derive(Debug, Serialize)]
pub struct FileDialogResponse {
    pub path: Option<String>,
}

#[derive(Debug, serde::Deserialize)]
pub struct StartRunRequest {
    pub project_id: String,
    pub preset: String,
    pub intensity: String,
    pub apply_light_finishing: bool,
    pub export_stems: bool,
    pub gpu_enabled: bool,
}

#[derive(Debug, serde::Deserialize)]
pub struct AnalyzeProjectRequest {
    pub project_id: String,
}

#[derive(Debug, Serialize)]
pub struct AnalyzeProjectResult {
    pub analysis_report_path: String,
    pub normalized_path: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct RunProgressPayload {
    pub run_id: String,
    pub status: String,
    pub message: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct StepProgressPayload {
    pub run_id: String,
    pub status: String,
    pub step_name: String,
    pub message: String,
    pub progress: f32,
}

#[tauri::command]
pub fn init_app() -> InitResponse {
    InitResponse {
        ok: true,
        message: "Application initialized".to_string(),
    }
}

#[tauri::command]
pub fn get_app_status(state: State<'_, AppState>) -> Result<AppStatus, String> {
    let settings = state
        .settings
        .lock()
        .map_err(|_| "Failed to lock settings state".to_string())?;
    let jobs = state
        .jobs
        .lock()
        .map_err(|_| "Failed to lock jobs state".to_string())?;

    let snapshot: AppSettingsSnapshot = settings.snapshot();
    let runtime = detect_python_runtime(&snapshot.python_command);

    Ok(AppStatus {
        app_name: "B Audio Project".to_string(),
        storage_dir: snapshot.storage_dir,
        database_path: snapshot.database_path,
        engine_entry: snapshot.engine_entry,
        python_command: snapshot.python_command,
        cuda_available: runtime.cuda_available,
        gpu_name: runtime.gpu_name,
        active_run_id: jobs.active_run_id().map(ToString::to_string),
    })
}

#[tauri::command]
pub fn import_project(
    input: NewProjectInput,
    state: State<'_, AppState>,
) -> Result<ImportProjectResult, String> {
    let settings = state
        .settings
        .lock()
        .map_err(|_| "Failed to lock settings state".to_string())?;
    let database = state
        .database
        .lock()
        .map_err(|_| "Failed to lock database state".to_string())?;

    database
        .import_project(input, &settings.storage_dir)
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn list_projects(state: State<'_, AppState>) -> Result<ProjectListResponse, String> {
    let database = state
        .database
        .lock()
        .map_err(|_| "Failed to lock database state".to_string())?;

    database
        .list_projects()
        .map(|projects| ProjectListResponse { projects })
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn get_project(project_id: String, state: State<'_, AppState>) -> Result<ProjectDetail, String> {
    let database = state
        .database
        .lock()
        .map_err(|_| "Failed to lock database state".to_string())?;

    database
        .get_project_detail(&project_id)
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn get_run(run_id: String, state: State<'_, AppState>) -> Result<RunDetail, String> {
    let database = state
        .database
        .lock()
        .map_err(|_| "Failed to lock database state".to_string())?;

    database.get_run_detail(&run_id).map_err(|error| error.to_string())
}

#[tauri::command]
pub async fn open_source_file_dialog(app: tauri::AppHandle) -> Result<FileDialogResponse, String> {
    let file_path = app
        .dialog()
        .file()
        .add_filter("Audio", &["wav", "flac", "mp3"])
        .blocking_pick_file();

    let path = file_path.map(|value| value.to_string());
    Ok(FileDialogResponse { path })
}

#[tauri::command]
pub fn analyze_project(
    request: AnalyzeProjectRequest,
    state: State<'_, AppState>,
) -> Result<AnalyzeProjectResult, String> {
    let settings = state
        .settings
        .lock()
        .map_err(|_| "Failed to lock settings state".to_string())?
        .clone();

    let database = state
        .database
        .lock()
        .map_err(|_| "Failed to lock database state".to_string())?
        .clone();

    let project = database
        .get_project_detail(&request.project_id)
        .map_err(|error| error.to_string())?;

    let project_dir = settings.storage_dir.join("projects").join(&request.project_id);
    let normalized_path = project_dir.join("source").join("normalized.wav");
    let analysis_report_path = project_dir.join("analysis").join("analysis-report.json");

    let output = Command::new(&settings.python_command)
        .arg(&settings.engine_entry)
        .arg("--analyze-input")
        .arg(&project.source_file.original_path)
        .arg("--normalized-output")
        .arg(&normalized_path)
        .arg("--analysis-report")
        .arg(&analysis_report_path)
        .arg("--project-id")
        .arg(&request.project_id)
        .output()
        .map_err(|error| format!("Failed to run analysis: {}", error))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Analysis failed: {}", stderr.trim()));
    }

    let analysis_report_path_str = analysis_report_path.display().to_string();
    let normalized_path_str = normalized_path.display().to_string();

    database
        .store_analysis_report(
            &request.project_id,
            &analysis_report_path_str,
            &normalized_path_str,
        )
        .map_err(|error| error.to_string())?;

    Ok(AnalyzeProjectResult {
        analysis_report_path: analysis_report_path_str,
        normalized_path: normalized_path_str,
    })
}

#[tauri::command]
pub fn start_project_run(
    request: StartRunRequest,
    app: tauri::AppHandle,
    state: State<'_, AppState>,
) -> Result<RunLaunchResult, String> {
    {
        let jobs = state
            .jobs
            .lock()
            .map_err(|_| "Failed to lock jobs state".to_string())?;

        if jobs.active_run_id().is_some() {
            return Err("Another run is already active".to_string());
        }
    }

    let settings = state
        .settings
        .lock()
        .map_err(|_| "Failed to lock settings state".to_string())?
        .clone();

    let database = state
        .database
        .lock()
        .map_err(|_| "Failed to lock database state".to_string())?
        .clone();

    let created_run = database
        .create_run(
            &request.project_id,
            &request.preset,
            &request.intensity,
            &settings.storage_dir,
        )
        .map_err(|error| error.to_string())?;

    let project = database
        .get_project_detail(&request.project_id)
        .map_err(|error| error.to_string())?;

    let analysis_report_path = project
        .analysis_report
        .as_ref()
        .map(|report| report.report_path.clone())
        .ok_or_else(|| "Run analysis first before starting cleanup.".to_string())?;

    let input_path = project.source_file.original_path;

    let payload = RunPayload {
        project_id: request.project_id,
        run_id: created_run.run.id.clone(),
        input_path,
        analysis_report_path: Some(analysis_report_path),
        preset: request.preset,
        options: RunOptions {
            intensity: request.intensity,
            apply_light_finishing: request.apply_light_finishing,
            export_stems: request.export_stems,
            gpu_enabled: request.gpu_enabled,
        },
    };

    {
        let mut jobs = state
            .jobs
            .lock()
            .map_err(|_| "Failed to lock jobs state".to_string())?;
        jobs.set_active_run(Some(created_run.run.id.clone()));
    }

    let run_id = created_run.run.id.clone();
    let app_handle = app.clone();

    thread::spawn(move || {
        let _ = app_handle.emit(
            "run-status",
            RunProgressPayload {
                run_id: run_id.clone(),
                status: "running".to_string(),
                message: None,
            },
        );

        let progress_app_handle = app_handle.clone();
        let result = run_engine(&settings, &database, payload, move |progress| {
            let _ = progress_app_handle.emit(
                "run-step",
                StepProgressPayload {
                    run_id: progress.run_id.clone(),
                    status: progress.status.clone(),
                    step_name: progress.step.clone(),
                    message: progress.message.clone(),
                    progress: progress.progress,
                },
            );
        });

        let final_status = if result.is_ok() { "completed" } else { "failed" };
        let final_message = result.as_ref().err().map(|error| error.to_string());

        if let Some(state) = app_handle.try_state::<AppState>() {
            if let Ok(mut jobs) = state.jobs.lock() {
                jobs.clear_if_matches(&run_id);
            }
        }

        let _ = app_handle.emit(
            "run-status",
            RunProgressPayload {
                run_id: run_id.clone(),
                status: final_status.to_string(),
                message: final_message,
            },
        );
    });

    Ok(RunLaunchResult {
        run_id: created_run.run.id,
        status: "running".to_string(),
    })
}

#[derive(Debug, serde::Deserialize)]
pub struct ExportRequest {
    pub run_id: String,
    pub project_id: String,
    pub format: String,
}

#[derive(Debug, Serialize)]
pub struct ExportResult {
    pub export_id: String,
    pub path: String,
    pub format: String,
}

#[tauri::command]
pub fn export_audio(request: ExportRequest, state: State<'_, AppState>) -> Result<ExportResult, String> {
    let format = request.format.to_lowercase();
    if format != "wav" && format != "flac" {
        return Err("Format must be wav or flac".to_string());
    }

    let database = state
        .database
        .lock()
        .map_err(|_| "Failed to lock database state".to_string())?;

    let run_detail = database
        .get_run_detail(&request.run_id)
        .map_err(|e| e.to_string())?;

    let preview_asset = run_detail
        .assets
        .iter()
        .find(|a| a.kind == "mix_preview")
        .ok_or_else(|| "No preview mix found for this run".to_string())?;

    let existing_export = database
        .get_export_path_for_run(&request.run_id, &format)
        .ok()
        .flatten();

    if let Some(existing_path) = existing_export {
        let path = PathBuf::from(&existing_path);
        if path.exists() {
            return Ok(ExportResult {
                export_id: String::new(),
                path: existing_path,
                format,
            });
        }
    }

    let settings = state
        .settings
        .lock()
        .map_err(|_| "Failed to lock settings state".to_string())?;

    let storage_dir = PathBuf::from(&settings.snapshot().storage_dir);
    let export_dir = storage_dir
        .join("projects")
        .join(&request.project_id)
        .join("runs")
        .join(&request.run_id)
        .join("exports");

    let extension = if format == "flac" { "flac" } else { "wav" };
    let export_path = export_dir.join(format!("song_cleaned.{}", extension));

    let preview_path = PathBuf::from(&preview_asset.path);
    let engine_entry = PathBuf::from(&settings.snapshot().engine_entry);

    let output = Command::new(&settings.python_command)
        .arg(&engine_entry)
        .arg("--reexport")
        .arg("--preview")
        .arg(&preview_path)
        .arg("--export-path")
        .arg(&export_path)
        .arg("--format")
        .arg(&format)
        .output()
        .map_err(|e| format!("Failed to run reexport: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("Reexport failed: {}", stderr.trim()));
    }

    let export_path_str = export_path.display().to_string();
    let export_id = database
        .add_export(&request.run_id, &request.project_id, &format, &export_path_str)
        .map_err(|e| e.to_string())?;

    Ok(ExportResult {
        export_id,
        path: export_path_str,
        format,
    })
}
