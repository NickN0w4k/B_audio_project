use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProgressEvent {
    pub run_id: String,
    pub step: String,
    pub status: String,
    pub progress: f32,
    pub message: String,
}
