# B Audio Project

Local desktop app for one-click cleanup of AI-generated songs.

## Repository Layout

- `apps/desktop-ui`: React frontend used by the Tauri shell
- `src-tauri`: Rust desktop core, storage bootstrap, and job orchestration
- `engine/app`: Python processing engine entry point and module skeleton
- `docs`: product, UI, architecture, and backlog documents
- `shared/schemas`: shared payload examples and interface references

## Current Status

The repository now contains a working local desktop MVP with:

- React + Tauri desktop shell
- SQLite-backed project, run, asset, and export persistence
- local file import and project storage bootstrap
- Rust-to-Python background run execution with progress events
- analysis, preview, compare, and retry flow in the desktop UI
- Python cleanup pipeline with normalize, analyze, stem separation, repair, reconstruct, and WAV export stages

## Next Implementation Steps

1. Install and validate the real ML audio dependencies locally
2. Validate the `Demucs` plus `DeepFilterNet` repair chain on longer real songs
3. Add optional FLAC export and light finishing path
4. Evaluate `AudioSR` or `Apollo` as an optional later restoration stage

## Development Notes

### Frontend

From the repository root:

```bash
npm install
npm run dev
```

### Python Engine

The engine entry point is:

- `engine/app/main.py`

It accepts a `--run-payload` JSON file and emits structured progress events to stdout.

Install engine dependencies before running the cleanup pipeline:

```bash
python -m pip install -r engine/requirements.txt
```

The current pipeline expects `ffmpeg` on `PATH`, uses `Demucs` for stem separation, and uses `DeepFilterNet` for vocal cleanup.

Current runtime note: the `deepfilternet` package is not fully compatible with the installed modern `torchaudio` API, so the engine uses the DeepFilterNet core model with local FFmpeg-based audio I/O instead of the package's default file loading helpers.

### Storage

The app uses local storage and initializes an SQLite database on startup.
