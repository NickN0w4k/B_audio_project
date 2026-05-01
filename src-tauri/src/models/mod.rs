#[derive(Debug, Clone)]
pub struct ModelRegistryStatus {
    pub models_ready: bool,
}

impl Default for ModelRegistryStatus {
    fn default() -> Self {
        Self { models_ready: false }
    }
}
