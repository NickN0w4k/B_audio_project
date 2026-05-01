# Development Backlog

## Purpose

This document turns the current product interpretation, UI definition, and technical architecture into an implementation backlog.

It is intended to answer:

1. What should be built first?
2. In what order should the work happen?
3. Which tasks are essential for MVP?
4. Which tasks can wait until later?

Related documents:

- `docs/product-interpretation.md`
- `docs/ui-wireframe-spec.md`
- `docs/ui-wireframes-ascii.md`
- `docs/technical-architecture.md`

## Delivery Strategy

The backlog follows a pragmatic build strategy:

1. establish the local app shell and storage model
2. create the Rust-to-Python execution bridge
3. implement the narrow MVP repair pipeline
4. connect the user flow from import to export
5. harden packaging, model handling, and error recovery

The MVP should optimize for:

- one-click usability
- reliable local processing
- clear progress reporting
- safe file handling
- narrow but useful repair quality

## Priority Levels

- `P0`: required for MVP to function
- `P1`: important for MVP usability and trust
- `P2`: valuable after core MVP works
- `P3`: later or optional

## Epic Overview

1. Foundation and Project Setup
2. Local Storage and Project Lifecycle
3. Rust-to-Python Job Runner
4. Audio Ingest and Normalization
5. Analysis and Preset Recommendation
6. Repair Pipeline MVP
7. Reconstruction and Export
8. UI Flow Implementation
9. Compare and Playback Experience
10. Error Handling and Recovery
11. Model Management and Local Runtime
12. Packaging and Windows Distribution
13. Post-MVP Enhancements

## Epic 1: Foundation and Project Setup

Goal:

Create a clean repository structure and baseline local application skeleton.

Priority: `P0`

### Tasks

1. Initialize desktop app structure with `Tauri + React + TypeScript`
2. Create Rust module layout for commands, jobs, db, settings, and events
3. Create Python engine layout for io, analysis, pipeline, models, dsp, reconstruction, metrics, and reports
4. Define shared JSON schema location and naming conventions
5. Configure formatting and linting for TypeScript, Rust, and Python
6. Add basic run scripts for desktop dev, engine dev, and local build
7. Add baseline README for developer setup

### Exit criteria

- app boots locally
- Rust and Python folders are in place
- developers can run the shell app and engine independently

## Epic 2: Local Storage and Project Lifecycle

Goal:

Implement the local project model and filesystem layout.

Priority: `P0`

### Tasks

1. Create app storage root strategy
2. Implement project directory creation
3. Implement source file registration flow
4. Add SQLite database initialization and migrations
5. Create tables for projects, source files, analysis reports, pipeline runs, run steps, assets, exports, and app settings
6. Implement project repository layer in Rust
7. Add recent projects query
8. Add project status tracking
9. Implement immutable original-file policy

### Exit criteria

- importing a file creates a project record
- metadata and file paths are persisted
- project reopening works

## Epic 3: Rust-to-Python Job Runner

Goal:

Create the local execution bridge for long-running repair jobs.

Priority: `P0`

### Tasks

1. Define JSON run payload schema
2. Implement Rust job launcher for Python subprocesses
3. Implement progress event parsing and forwarding
4. Implement run status persistence in SQLite
5. Add process cancellation support
6. Capture stdout and stderr into per-run logs
7. Implement final result event handling
8. Add timeout and abnormal-exit handling

### Exit criteria

- Rust can launch Python jobs
- progress reaches UI and storage
- cancellation works
- failed runs are recorded cleanly

## Epic 4: Audio Ingest and Normalization

Goal:

Convert imported files into the stable internal working format.

Priority: `P0`

### Tasks

1. Implement input validation for WAV, FLAC, MP3
2. Integrate FFmpeg or equivalent conversion path
3. Normalize input to `48 kHz`, `32-bit float`
4. Preserve source metadata where available
5. Write normalized working file into project storage
6. Add duration and channel extraction
7. Return ingest report to Rust

### Exit criteria

- valid input files become normalized working files
- invalid input fails with readable errors

## Epic 5: Analysis and Preset Recommendation

Goal:

Detect likely artifact classes and recommend a repair path.

Priority: `P0`

### Tasks

1. Define `AnalysisReport` schema
2. Implement file-level metadata inspection
3. Implement spectral heuristics for dull top end and harsh metallic highs
4. Implement simple detection heuristics for codec haze and congested mix
5. Implement initial vocal artifact probe logic
6. Implement severity scoring and confidence output
7. Map analysis outputs to recommended presets
8. Estimate runtime based on device mode and preset
9. Persist analysis report to project storage and DB

### Exit criteria

- user gets a stable recommended preset
- analysis screen can render real issue data

## Epic 6: Repair Pipeline MVP

Goal:

Build the first useful end-to-end repair chain.

Priority: `P0`

### Tasks

1. Implement pipeline plan builder from preset plus options
2. Integrate `Demucs` stem separation
3. Register generated stems as assets
4. Integrate `DeepFilterNet` for vocal cleanup
5. Implement DSP-based vocal smoothing and harshness reduction
6. Implement conservative music cleanup DSP path
7. Implement optional light finishing path with `Pedalboard`
8. Implement step-level metrics collection hooks
9. Write per-step outputs and progress events

### Exit criteria

- AI Song Cleanup preset completes end-to-end
- output assets exist for compare and export

## Epic 7: Reconstruction and Export

Goal:

Turn repaired stems into a usable final mix and export result.

Priority: `P0`

### Tasks

1. Implement mix reconstruction from repaired stems
2. Add headroom and clipping protection strategy
3. Create preview mix output for compare screen
4. Implement final export rendering for WAV
5. Implement final export rendering for FLAC
6. Implement optional stems export
7. Generate machine-readable run report
8. Register exported assets in DB

### Exit criteria

- repaired mix can be previewed and exported
- output files are reliably written to disk

## Epic 8: UI Flow Implementation

Goal:

Implement the guided one-click interface from Home to Export.

Priority: `P0`

### Tasks

1. Build app shell with navigation and status strip
2. Implement Home screen with file import and recent projects
3. Implement Analysis screen with issue cards and recommended preset panel
4. Implement Repair Setup screen with presets, intensity, and options
5. Implement Processing screen with global progress and stage list
6. Implement Export screen with format and output selection
7. Wire navigation transitions between screens
8. Connect screens to real Rust commands and persisted state

### Exit criteria

- user can complete the full guided flow visually and functionally

## Epic 9: Compare and Playback Experience

Goal:

Make before/after evaluation fast and trustworthy.

Priority: `P1`

### Tasks

1. Integrate waveform playback component
2. Load original and repaired preview assets
3. Implement fast A/B toggle
4. Implement loop region controls
5. Add simple spectrogram comparison panel
6. Show repair summary and metrics deltas
7. Add `Try Another Repair` return path
8. Add quick user feedback buttons

### Exit criteria

- compare screen makes outcome judgement easy
- rerun flow is possible without rebuilding project state manually

## Epic 10: Error Handling and Recovery

Goal:

Make failure states understandable and non-destructive.

Priority: `P1`

### Tasks

1. Define internal structured error type
2. Map engine errors to user-readable messages
3. Add unsupported-file errors
4. Add missing-model errors
5. Add insufficient-disk-space errors
6. Add Python-process-failure handling
7. Add export-failure handling
8. Preserve partial outputs on failure
9. Mark runs as failed or cancelled correctly

### Exit criteria

- major failure cases are readable and recoverable
- originals and finished outputs are never lost

## Epic 11: Model Management and Local Runtime

Goal:

Manage local dependencies cleanly enough for end users.

Priority: `P1`

### Tasks

1. Define model registry manifest format
2. Detect presence of required models
3. Add model status to app state and UI
4. Implement missing-model prompt flow
5. Add version tracking for installed models
6. Validate model paths before job launch
7. Add CPU/GPU capability detection
8. Add warning copy for CPU fallback mode

### Exit criteria

- app can explain whether it is ready to run
- missing model state is not a hidden failure

## Epic 12: Packaging and Windows Distribution

Goal:

Ship a usable local Windows build.

Priority: `P1`

### Tasks

1. Define Windows-first packaging approach
2. Bundle or provision Python runtime strategy
3. Define FFmpeg bundling strategy
4. Verify storage path permissions
5. Test installer and first-run behavior
6. Validate GPU fallback behavior on non-GPU systems
7. Add first-run dependency checks
8. Add release checklist for desktop packaging

### Exit criteria

- new user can install and run the app on Windows without manual engineering steps

## Epic 13: Post-MVP Enhancements

Goal:

Extend quality, flexibility, and throughput after MVP is stable.

Priority: `P2` and `P3`

### Candidate tasks

1. Add batch processing
2. Add queued runs
3. Add cached stem reuse
4. Add stronger artifact scoring
5. Add `BS-RoFormer` integration
6. Add `AudioSR` or `Apollo`
7. Add `VoiceFixer` path for stronger vocal recovery
8. Add custom preset library
9. Add resumable runs
10. Add advanced per-stem controls

## Milestones

## Milestone 1: Shell and Storage

Includes:

- Epic 1
- Epic 2
- basic parts of Epic 8 for app boot and Home screen

Expected outcome:

- user can import files into a real local project structure

## Milestone 2: Engine Bridge and Ingest

Includes:

- Epic 3
- Epic 4

Expected outcome:

- local engine can be launched from the app and normalize real audio files

## Milestone 3: Real Analysis and Recommendation

Includes:

- Epic 5
- Analysis UI from Epic 8

Expected outcome:

- user gets a real analysis screen with recommended preset

## Milestone 4: End-to-End Cleanup MVP

Includes:

- Epic 6
- Epic 7
- Repair and Processing UI from Epic 8

Expected outcome:

- user can complete a full repair run and produce a cleaned file

## Milestone 5: Compare, Recovery, and Packaging

Includes:

- Epic 9
- Epic 10
- Epic 11
- Epic 12

Expected outcome:

- app becomes credible for external testing by non-technical users

## Suggested Build Order by Task Group

### Group A: App skeleton

1. initialize Tauri app
2. create Rust modules
3. create Python engine skeleton
4. create SQLite bootstrap

### Group B: Local file flow

1. import file
2. create project folder
3. persist metadata
4. normalize source audio

### Group C: Local execution bridge

1. define run payload
2. spawn Python process
3. parse progress
4. persist run state

### Group D: User-facing intelligence

1. analysis report schema
2. heuristic detectors
3. preset recommendation mapping
4. runtime estimate

### Group E: First useful repair

1. Demucs integration
2. DeepFilterNet integration
3. DSP cleanup path
4. reconstruction
5. export

### Group F: UX completion

1. Home
2. Analysis
3. Repair Setup
4. Processing
5. Compare
6. Export

### Group G: Hardening

1. error mapping
2. model management
3. packaging
4. installer validation

## Recommended MVP Cut Line

Must-have for first external MVP:

- app shell
- local project storage
- Rust-to-Python runner
- input normalization
- analysis report
- recommended preset
- Demucs-based separation
- DeepFilterNet vocal cleanup
- conservative DSP music cleanup
- reconstruction
- WAV export
- compare screen with A/B playback
- readable failure handling

Can wait until shortly after MVP:

- FLAC export
- stems export
- spectrogram comparison
- custom presets
- stronger model stack

## Risks and Mitigations

### Risk: packaging consumes more time than expected

Mitigation:

- treat packaging as an early milestone concern
- test on clean Windows environments early

### Risk: repair quality is inconsistent

Mitigation:

- keep preset set narrow
- prefer conservative defaults
- use compare flow as a product safety net

### Risk: model dependencies are brittle

Mitigation:

- wrap all models behind stable runner interfaces
- centralize model path resolution

### Risk: UI outruns engine reality

Mitigation:

- connect screens to real data early
- avoid over-polishing mock flows before the repair pipeline works

## Recommended Next Execution Step

If implementation starts immediately, the best next action is:

1. scaffold the repository structure
2. initialize the Tauri app shell
3. create the Rust storage and job modules
4. create the Python engine entry point and run payload contract

That sequence produces the minimum real foundation on which the rest of the backlog can be built.
