# Technical Architecture

## Purpose

This document defines the technical architecture for the first buildable version of the local desktop app for one-click cleanup of AI-generated songs.

It translates the product direction and UI documents into an implementation-ready system design with:

- module boundaries
- runtime responsibilities
- data flow
- storage layout
- job execution model
- interface contracts
- MVP scope and upgrade path

Related documents:

- `docs/ui-wireframe-spec.md`
- `docs/ui-wireframes-ascii.md`

## Product Constraints

The architecture is shaped by these decisions:

- fully local only
- one-click end users first
- focused on AI-generated song cleanup specifically
- desktop-first experience
- offline-capable after installation and model download

This means the system should optimize for:

- simple installation
- reliable local processing
- minimal background infrastructure
- guided UX
- safe and reversible file handling

This means the system should avoid for MVP:

- distributed services
- cloud APIs as core dependencies
- remote job queues
- multi-user concepts
- overly flexible graph editors

## Architecture Overview

The application should use a local 3-layer architecture:

1. `Tauri UI`
2. `Rust App Core`
3. `Python Processing Engine`

### High-level diagram

```text
+---------------------------+
| Tauri Desktop UI          |
| React + TypeScript        |
+-------------+-------------+
              |
              | Tauri commands / events
              v
+---------------------------+
| Rust App Core             |
| App state, DB, jobs,      |
| file system, process mgmt |
+-------------+-------------+
              |
              | JSON job payloads / progress events
              v
+---------------------------+
| Python Processing Engine  |
| analysis, separation,     |
| repair, reconstruction,   |
| export                    |
+---------------------------+
```

## Technology Stack

### UI Layer

- `Tauri`
- `React`
- `TypeScript`
- `Zustand`
- `TanStack Query`
- `Wavesurfer.js`

### Desktop Core

- `Rust`
- `SQLite`
- Tauri command/event system

### Processing Engine

- `Python 3.11`
- `PyTorch`
- `torchaudio`
- `soundfile`
- `librosa`
- `NumPy`
- `SciPy`
- `FFmpeg`
- `Pedalboard`

### Initial Model Stack

MVP:

- `Demucs`
- `DeepFilterNet`
- custom DSP cleanup modules
- optional light `Pedalboard` finishing

Later:

- `BS-RoFormer`
- `AudioSR` or `Apollo`
- `VoiceFixer`
- `DisCoder`
- `APNet2`

## Core Design Principles

### 1. Local-first

All primary processing must work without remote services.

### 2. Guided complexity

The UI stays simple, but the internals remain modular.

### 3. Safe by default

The original source file is never modified or overwritten.

### 4. Reproducible runs

Each repair run should be represented by a structured configuration and stored outputs.

### 5. Replaceable modules

Model wrappers and DSP modules should be swappable without rewriting the whole app.

### 6. Honest output

If analysis confidence is low or a module cannot improve the file, the system should degrade gracefully and report this clearly.

## Runtime Responsibilities

## Tauri UI

The UI is responsible for:

- project creation flow
- file import and selection UX
- status display
- preset selection
- progress display
- before/after playback
- export flow
- advanced settings display

The UI must not:

- run heavy audio processing
- manage model execution directly
- own the source of truth for pipeline state

## Rust App Core

The Rust layer is the local orchestrator.

Responsibilities:

- application startup
- settings loading and persistence
- SQLite access
- project and asset indexing
- file-system-safe path creation
- spawning and supervising Python jobs
- progress event parsing
- cancellation handling
- local model registry state
- exposing commands to the UI

The Rust core should be treated as the stable shell around a more changeable Python engine.

## Python Processing Engine

The Python layer owns audio intelligence and heavy execution.

Responsibilities:

- ingest normalization
- analysis and issue detection
- stem separation
- repair chain execution
- reconstruction
- optional finishing
- export rendering
- metric generation
- structured reporting

It should not own:

- UI state
- project navigation
- persistent user-facing application logic beyond job execution

## Module Boundaries

The Python engine should be split into clear modules.

## 1. `io`

Responsibilities:

- load input files
- normalize format
- sample-rate conversion
- channel normalization
- safe output writing
- ffmpeg integration

Inputs:

- user source files

Outputs:

- normalized working file
- exported audio files

## 2. `analysis`

Responsibilities:

- inspect file properties
- detect probable artifact classes
- estimate severity
- recommend preset routing
- estimate runtime

Outputs:

- `AnalysisReport`

MVP artifact classes:

- robotic vocals
- metallic highs
- dull top end
- codec haze
- congested mix
- stereo instability

## 3. `pipeline`

Responsibilities:

- convert preset plus options into executable run plan
- validate required assets
- determine module order
- handle conditional branches
- record step execution state

Outputs:

- `PipelinePlan`

## 4. `models`

Responsibilities:

- wrap third-party ML models behind consistent interfaces
- manage model-specific input/output adaptation
- centralize model path lookup
- return stable error types

MVP wrappers:

- `DemucsRunner`
- `DeepFilterNetRunner`

Later wrappers:

- `BSRoFormerRunner`
- `AudioSRRunner`
- `VoiceFixerRunner`

## 5. `dsp`

Responsibilities:

- lightweight cleanup not requiring large ML models
- gain staging
- harshness reduction
- brightness shaping
- vocal smoothing
- simple phase-safe adjustments
- optional finishing chain

This module is important because not every quality improvement should require a large neural model.

## 6. `reconstruction`

Responsibilities:

- rebuild mix from repaired stems
- apply headroom strategy
- prevent clipping
- preserve reasonable balance
- produce preview and final output mix

## 7. `metrics`

Responsibilities:

- loudness metrics
- true peak
- spectral comparison metrics
- artifact score before and after
- run summary data for UI

## 8. `reports`

Responsibilities:

- write human-readable and machine-readable run reports
- summarize applied preset, steps, warnings, and outputs

Outputs:

- JSON report
- optional text or markdown summary later

## Job Execution Model

The app should use a local single-machine job runner managed by Rust.

### Why this model

- simpler install than local web services plus queue stack
- easier process supervision
- easier cancellation and recovery
- better fit for one-user desktop workflow

### Job lifecycle

1. UI requests a run
2. Rust validates project state and writes run record
3. Rust builds job payload
4. Rust launches Python engine subprocess
5. Python executes steps and emits progress
6. Rust persists progress and relays it to UI
7. Python writes outputs and final report
8. Rust marks run complete or failed

### Concurrency model

MVP:

- one active repair job at a time
- optional background processing while UI stays usable
- read-only browsing of old projects during active run

Rationale:

- easier GPU memory control
- simpler UX
- simpler error handling

Later:

- queued jobs
- batch processing
- limited concurrent CPU tasks

## Data Flow

### Main flow

```text
Import file
  -> normalize audio
  -> analyze audio
  -> generate recommended preset
  -> build pipeline plan
  -> execute repair modules
  -> reconstruct mix
  -> optional finishing
  -> export assets
  -> save report and metrics
```

### Detailed asset flow

```text
Source File
  -> Normalized Working File
  -> Stem Files
  -> Repaired Stem Files
  -> Rebuilt Mix Preview
  -> Final Repaired Mix
  -> Exported File(s)
  -> Report Files
```

## Storage Architecture

The app should use:

- `SQLite` for metadata
- local filesystem for media assets and reports

### Why SQLite

- zero external service dependency
- excellent fit for local desktop apps
- easy backup and migration path later

## Filesystem Layout

Recommended layout:

```text
storage/
  projects/
    <project-id>/
      source/
        original.ext
        normalized.wav
      analysis/
        analysis-report.json
      runs/
        <run-id>/
          plan.json
          progress.json
          logs/
          stems/
            vocals.wav
            drums.wav
            bass.wav
            other.wav
          repaired/
            vocals_repaired.wav
            drums_repaired.wav
            bass_repaired.wav
            other_repaired.wav
          previews/
            mix_preview.wav
          exports/
            song_cleaned.wav
            song_cleaned.flac
          reports/
            run-report.json
```

### Storage rules

- original file is immutable
- each run writes to its own directory
- previews and exports are versioned by run
- cleanup policies can remove old intermediates later, but never source files automatically without explicit user action

## Database Model

Recommended MVP tables:

## `projects`

- `id`
- `name`
- `created_at`
- `updated_at`
- `status`

## `source_files`

- `id`
- `project_id`
- `original_path`
- `normalized_path`
- `filename`
- `duration_sec`
- `sample_rate`
- `channels`
- `format`

## `analysis_reports`

- `id`
- `project_id`
- `report_path`
- `recommended_preset`
- `runtime_estimate_sec`
- `summary_json`
- `created_at`

## `pipeline_runs`

- `id`
- `project_id`
- `preset`
- `intensity`
- `status`
- `started_at`
- `finished_at`
- `plan_path`
- `report_path`

## `run_steps`

- `id`
- `run_id`
- `step_name`
- `status`
- `started_at`
- `finished_at`
- `metrics_json`

## `assets`

- `id`
- `project_id`
- `run_id`
- `kind`
- `path`
- `metadata_json`

## `exports`

- `id`
- `run_id`
- `format`
- `path`
- `created_at`

## `app_settings`

- `key`
- `value_json`

## Interface Contracts

The key internal contract between Rust and Python should be file-based JSON plus structured process output.

### Run request payload

```json
{
  "project_id": "uuid",
  "run_id": "uuid",
  "input_path": "C:/Users/Nick/Desktop/B_audio_project/storage/projects/123/source/normalized.wav",
  "preset": "ai_song_cleanup",
  "options": {
    "intensity": "medium",
    "apply_light_finishing": false,
    "export_stems": false,
    "gpu_enabled": true
  }
}
```

### Progress event

```json
{
  "run_id": "uuid",
  "step": "repair_vocals",
  "status": "running",
  "progress": 0.62,
  "message": "Reducing robotic vocal artifacts"
}
```

### Step completion event

```json
{
  "run_id": "uuid",
  "step": "reconstruct_mix",
  "status": "completed",
  "outputs": [
    "C:/.../mix_preview.wav"
  ],
  "metrics": {
    "lufs": -15.1,
    "true_peak_db": -1.2,
    "artifact_score_before": 0.71,
    "artifact_score_after": 0.39
  }
}
```

### Final result event

```json
{
  "run_id": "uuid",
  "status": "completed",
  "report_path": "C:/.../run-report.json",
  "exports": [
    "C:/.../song_cleaned.wav"
  ]
}
```

## Preset System

Presets are a product feature and a technical contract.

The preset system should map user-friendly names to executable configurations.

### MVP presets

- `ai_song_cleanup`
- `gentle_cleanup`
- `fix_robotic_vocals`
- `restore_brightness`
- `reduce_metallic_harshness`
- `deep_cleanup`

### Preset responsibilities

- define which modules are active
- define default strengths
- define optional branches
- define user-visible copy

### Example internal preset structure

```json
{
  "id": "ai_song_cleanup",
  "display_name": "AI Song Cleanup",
  "steps": [
    "normalize",
    "analyze",
    "separate_stems",
    "repair_vocals",
    "repair_music",
    "reconstruct_mix"
  ],
  "defaults": {
    "intensity": "medium",
    "apply_light_finishing": false
  }
}
```

## Analysis Architecture

The analysis module should not try to be perfect. It should be useful and robust.

### MVP analysis strategy

Blend:

- file metadata inspection
- simple spectral heuristics
- stem-aware quick probes where needed
- rule-based preset recommendation

### Analysis outputs

- issue classes
- confidence scores
- recommended preset
- estimated runtime
- warnings

### Example warning flags

- very low bitrate input
- strong clipping detected
- CPU fallback active
- extreme distortion may limit improvement

## Processing Pipeline

## MVP pipeline

```text
ingest
  -> normalize
  -> analyze
  -> stem separation (Demucs)
  -> vocal cleanup (DeepFilterNet + DSP)
  -> music cleanup (DSP)
  -> reconstruct mix
  -> optional light finishing
  -> export
```

### Why this pipeline

- technically achievable
- stable enough for early users
- aligned with the vault's separation-first philosophy
- avoids depending on the heaviest models too early

## Example step definitions

### `normalize`

- convert input to `48 kHz`, `32-bit float`
- preserve original channels where possible
- write normalized working WAV

### `separate_stems`

- run Demucs
- write `vocals`, `drums`, `bass`, `other`
- register stem assets

### `repair_vocals`

- denoise with DeepFilterNet when indicated
- apply vocal smoothing / harshness control where indicated
- produce repaired vocal stem

### `repair_music`

- apply conservative brightness and harshness repair
- avoid heavy hallucination in MVP unless explicitly enabled later

### `reconstruct_mix`

- combine repaired stems
- maintain headroom
- produce preview mix

### `light_finishing`

- optional only
- low-risk loudness-safe polish
- must remain separate from core restoration logic

## Error Handling Strategy

The app must convert technical failures into user-readable outcomes.

### Error layers

1. input errors
2. dependency errors
3. model execution errors
4. storage errors
5. export errors

### User-facing behavior

- explain what failed
- preserve successful intermediate assets where possible
- allow retry from a sensible step later
- never delete the original file because of a failed run

### Internal error format

Errors should include:

- code
- message
- step
- technical details
- suggested user action if available

## Cancellation and Recovery

### Cancellation

Rust should own the cancellation signal and propagate it to the Python process.

Behavior:

- current step stops as safely as possible
- already written outputs remain
- run marked `cancelled`

### Recovery

For MVP, recovery can be conservative:

- failed or cancelled runs can be restarted from the beginning
- assets from previous runs remain inspectable

Later:

- resume from selected step
- cached stem reuse

## Logging and Observability

MVP logging should support user trust and developer debugging.

### User-visible logging

- plain-language progress updates
- clear current step
- final summary

### Developer logging

- per-run log files
- subprocess stdout/stderr capture
- timing data per step

## Model Management

The app should treat models as managed local assets.

### Responsibilities

- detect whether required models exist
- show download state
- validate model paths
- prevent launching runs when required models are missing

### MVP behavior

- download or install models separately from run execution
- maintain a local registry in settings or a manifest file
- mark models by version

## Security and Privacy

Because the product is fully local, privacy is a core feature.

Requirements:

- no mandatory cloud upload
- no silent external processing
- clear indication when everything remains on-device
- local file access should be limited to chosen files and app storage paths

## Packaging and Deployment

### MVP target

- Windows-first desktop build

### Packaging responsibilities

- package Tauri app
- bundle or install Python runtime cleanly
- provide FFmpeg dependency strategy
- support local model storage path

### Packaging challenge

The hardest part of the MVP is not UI or DSP logic. It is packaging the local runtime cleanly:

- Python environment
- model dependencies
- FFmpeg
- GPU compatibility expectations

This should be treated as a first-class engineering task, not as a final polish item.

## Recommended Repository Structure

```text
apps/
  desktop-ui/
src-tauri/
  src/
    commands/
    db/
    jobs/
    models/
    settings/
    events/
engine/
  app/
    main.py
    io/
    analysis/
    pipeline/
    models/
    dsp/
    reconstruction/
    metrics/
    reports/
shared/
  schemas/
docs/
storage/
```

## MVP Scope

Included:

- single local desktop workflow
- project import
- analysis report
- preset routing
- one active run at a time
- Demucs separation
- DeepFilterNet vocal cleanup
- conservative DSP-based music cleanup
- reconstruction
- compare workflow
- WAV and FLAC export
- SQLite metadata
- local reports and logs

Excluded for MVP:

- remote workers
- cloud sync
- team collaboration
- full graph editor
- heavy batch queue
- advanced super-resolution stack as default path

## V2 Evolution Path

The architecture should allow these upgrades without redesigning the whole app:

- queue multiple runs
- batch processing
- cache and reuse stems
- stronger artifact scoring
- `BS-RoFormer` instead of or beside Demucs
- `AudioSR` or `Apollo` integration
- `VoiceFixer` for heavier vocal rescue
- resumable runs
- custom preset library

## Build Order Recommendation

1. local project and storage layer
2. Rust-to-Python job runner
3. ingest and normalize
4. analysis report contract
5. Demucs integration
6. DeepFilterNet integration
7. reconstruction and export
8. compare-ready asset wiring
9. preset refinement
10. packaging and installer hardening

## Final Recommendation

The right MVP architecture for this product is a local desktop app with:

- `React + Tauri` for the UX
- `Rust` as the orchestration shell
- `Python` as the audio processing engine
- `SQLite + filesystem` for persistence
- `Demucs + DeepFilterNet + DSP` as the first reliable repair stack

This architecture is the best fit for the product constraints because it keeps the user experience simple while keeping the internals modular, replaceable, and realistic to build.
