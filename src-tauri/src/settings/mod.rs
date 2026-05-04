use anyhow::Result;
use serde::Serialize;
use std::path::PathBuf;
use tauri::AppHandle;
use tauri::Manager;

#[derive(Debug, Clone)]
pub struct AppSettings {
    pub storage_dir: PathBuf,
    pub database_path: PathBuf,
    pub engine_entry: PathBuf,
    pub python_command: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct AppSettingsSnapshot {
    pub storage_dir: String,
    pub database_path: String,
    pub engine_entry: String,
    pub python_command: String,
}

impl AppSettings {
    pub fn load(app: &AppHandle) -> Result<Self> {
        let app_data_dir = app
            .path()
            .app_data_dir()
            .unwrap_or(std::env::current_dir()?.join("storage"));

        let storage_dir = app_data_dir.join("storage");
        let database_path = storage_dir.join("app.db");
        let workspace_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .ok_or_else(|| anyhow::anyhow!("Failed to resolve workspace directory"))?
            .to_path_buf();
        let engine_entry = workspace_dir.join("engine").join("app").join("main.py");

        std::fs::create_dir_all(&storage_dir)?;

        let python_command = resolve_python_command(&workspace_dir);

        Ok(Self {
            storage_dir,
            database_path,
            engine_entry,
            python_command,
        })
    }

    pub fn snapshot(&self) -> AppSettingsSnapshot {
        AppSettingsSnapshot {
            storage_dir: self.storage_dir.display().to_string(),
            database_path: self.database_path.display().to_string(),
            engine_entry: self.engine_entry.display().to_string(),
            python_command: self.python_command.clone(),
        }
    }
}

fn resolve_python_command(workspace_dir: &PathBuf) -> String {
    let venv_python = if cfg!(windows) {
        workspace_dir.join(".venv").join("Scripts").join("python.exe")
    } else {
        workspace_dir.join(".venv").join("bin").join("python")
    };

    if venv_python.is_file() {
        return venv_python.display().to_string();
    }

    "python".to_string()
}
