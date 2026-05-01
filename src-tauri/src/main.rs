mod commands;
mod db;
mod events;
mod jobs;
mod models;
mod settings;

use commands::{
    analyze_project, export_audio, get_app_status, get_project, get_run, import_project, init_app,
    list_projects, open_source_file_dialog, start_project_run,
};
use db::Database;
use jobs::JobManager;
use settings::AppSettings;
use std::sync::Mutex;
use tauri::Manager;

pub struct AppState {
    pub database: Mutex<Database>,
    pub settings: Mutex<AppSettings>,
    pub jobs: Mutex<JobManager>,
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let handle = app.handle();
            let settings = AppSettings::load(&handle)?;
            let database = Database::new(&settings.database_path)?;
            database.initialize()?;

            app.manage(AppState {
                database: Mutex::new(database),
                settings: Mutex::new(settings),
                jobs: Mutex::new(JobManager::default()),
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            init_app,
            get_app_status,
            import_project,
            list_projects,
            get_project,
            get_run,
            open_source_file_dialog,
            analyze_project,
            start_project_run,
            export_audio
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application")
}
