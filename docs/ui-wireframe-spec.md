# UI Wireframe Spec

## Product

Local desktop app for one-click cleanup of AI-generated songs.

## Product Goal

The product is a fully local desktop application for end users who want to improve AI-generated songs with minimal technical setup. It focuses specifically on audible defects common in generated music, such as robotic vocals, metallic highs, dull top end, codec haze, unstable stereo image, and congested mixes.

The app should feel simple and guided:

1. Import a song
2. Analyze the file automatically
3. Accept the recommended repair preset or choose another
4. Run the cleanup locally
5. Compare before and after
6. Export the repaired version

## Core UX Principles

- Fully local
- One-click first
- Advanced controls hidden by default
- Restoration and finishing are separate
- Original audio is always preserved
- Before/after comparison is mandatory
- Plain-language explanations on the main path
- Strong defaults over technical freedom

## Primary User

Non-technical end user who wants to improve AI-generated songs with minimal setup.

## Supported Input and Output

### Input

- WAV
- FLAC
- MP3

### Output

- WAV
- FLAC
- Optional restored stems
- Optional repair report

## Main Flow

1. Import song
2. Analyze automatically
3. Accept recommended preset or change it
4. Run cleanup
5. Compare before/after
6. Export repaired result

## Navigation

Primary sections:

- Home
- Analysis
- Repair
- Compare
- Export
- Advanced

The navigation should be linear in the default flow, but users can go back without losing work.

## Global Layout Rules

### App Shell

- Left sidebar or top navigation with the current step highlighted
- Main content area centered and wide enough for waveform and analysis panels
- Persistent footer or status strip for hardware state, storage state, and model readiness

### Global Header

Should show:

- Project name
- Input file name
- Current processing status
- Back button when relevant
- Settings access

### Global Status Strip

Should show:

- Local mode enabled
- CPU or GPU mode
- Model status
- Available disk space warning if relevant

## Screen 1: Home

### Goal

Fast project start with minimal friction.

### Primary user question

How do I start cleaning up my song?

### Main layout blocks

1. Hero/import block
2. Recent projects block
3. System readiness block

### Layout detail

#### Hero/import block

Main visual focus of the screen.

Contains:

- Large drag-and-drop area
- Primary button: `Choose File`
- Helper text: `Drop a WAV, FLAC, or MP3 file to begin`
- Secondary text: `Everything stays on this device`

#### Recent projects block

List of previous sessions with:

- Project name
- Input file name
- Last modified date
- Status: analyzed, repaired, exported
- Quick action: `Open`

#### System readiness block

Contains small cards or badges for:

- `Local processing: ready`
- `GPU detected` or `CPU mode`
- `Models installed` or `Models need download`
- `Disk space ok`

### Primary actions

- `Choose File`
- Drop file into upload area
- `Open` recent project

### Secondary actions

- `Settings`
- `Manage Models`

### Recommended button labels

- `Choose File`
- `Open Project`
- `Manage Models`

### Empty state

- Clean landing page with import prompt
- No unnecessary technical text

### Error states

- Unsupported file type
- File unreadable
- File too short
- No storage space available

### Transition rules

- On valid import, automatically create project and move to `Analysis`
- If required models are missing, show download prompt before analysis starts

## Screen 2: Analysis

### Goal

Explain detected sound issues in plain language and recommend a repair path.

### Primary user question

What is wrong with my track, and what should I do?

### Main layout blocks

1. Song summary card
2. Issue cards section
3. Recommended preset panel
4. Runtime and hardware panel

### Layout detail

#### Song summary card

Contains:

- File name
- Duration
- Format
- Sample rate
- Bit depth if known
- Imported at time

#### Issue cards section

Show the most relevant detected problems as simple cards.

Possible cards:

- `Robotic vocals`
- `Metallic highs`
- `Dull top end`
- `Congested mix`
- `Stereo instability`
- `Heavy codec haze`

Each card should include:

- Issue name
- Short plain-language description
- Severity: low, medium, high
- Small `Learn more` link or disclosure

#### Recommended preset panel

Contains:

- Recommended preset name
- One-sentence reason
- Confidence level
- Primary button: `Use Recommended Repair`
- Secondary action: `Choose Another Preset`

#### Runtime and hardware panel

Contains:

- Expected runtime
- Processing mode: CPU or GPU
- Warnings like `This repair may be slow on CPU`

### Primary actions

- `Use Recommended Repair`
- `Choose Another Preset`

### Secondary actions

- `Back`
- `View Details`

### Recommended button labels

- `Use Recommended Repair`
- `Choose Another Preset`
- `View Details`

### Interaction rules

- Analysis results should avoid raw model names by default
- Technical evidence can exist behind `View Details`
- If confidence is low, say so clearly

### Loading state

- Show progress steps such as:
- `Reading audio`
- `Checking vocals`
- `Inspecting high frequencies`
- `Building repair recommendation`

### Error states

- Analysis failed
- File corrupted
- Runtime dependency missing

### Transition rules

- `Use Recommended Repair` goes to `Repair Setup` with preset preselected
- `Choose Another Preset` also goes to `Repair Setup`, but opens preset choice focus

## Screen 3: Repair Setup

### Goal

Let the user confirm a repair strategy without overwhelming them.

### Primary user question

What repair should I run?

### Main layout blocks

1. Preset selector
2. Intensity selector
3. Optional export and finishing options
4. Advanced settings disclosure

### Layout detail

#### Preset selector

Preset cards should include:

- Preset name
- Short description
- Best for label
- Speed estimate

Recommended presets:

- `AI Song Cleanup`
- `Gentle Cleanup`
- `Fix Robotic Vocals`
- `Restore Brightness`
- `Reduce Metallic Harshness`
- `Deep Cleanup`

#### Intensity selector

Radio buttons or segmented control:

- `Low`
- `Medium`
- `High`

Description text under each selection:

- Low: smaller changes, safer
- Medium: balanced default
- High: stronger cleanup, more processing

#### Optional export and finishing options

Contains toggles:

- `Apply Light Finishing`
- `Export Restored Stems`

Light finishing must be described as optional final polish, not core repair.

#### Advanced settings disclosure

Collapsed by default.

Contains:

- Module toggles
- Per-stem options
- Experimental features warning

### Primary actions

- `Start Repair`

### Secondary actions

- `Back`
- `Reset to Recommended`
- `Open Advanced Settings`

### Recommended defaults

- Preset: `AI Song Cleanup`
- Intensity: `Medium`
- Light finishing: `Off`
- Export stems: `Off`

### Interaction rules

- Do not expose raw model settings on the default path
- If the user changes preset, update expected runtime immediately
- If `High` intensity is chosen, show a short note about longer runtime

### Error and warning states

- GPU unavailable, CPU fallback active
- Low disk space for stems export
- Deep cleanup may take a long time

### Transition rules

- `Start Repair` moves to `Processing`

## Screen 4: Processing

### Goal

Build user trust during long-running local processing.

### Primary user question

Is the app working, and how long will it take?

### Main layout blocks

1. Global progress section
2. Stage-by-stage progress list
3. Plain-language activity log
4. Background and cancel controls

### Layout detail

#### Global progress section

Contains:

- Large progress bar
- Percent complete
- Estimated time remaining
- Current stage name

#### Stage-by-stage progress list

Show steps like:

- `Preparing audio`
- `Analyzing`
- `Separating stems`
- `Repairing vocals`
- `Repairing music`
- `Rebuilding mix`
- `Applying light finishing`
- `Saving results`

Each stage has one of:

- pending
- active
- completed
- failed

#### Plain-language activity log

Examples:

- `Checking the vocal track for robotic artifacts`
- `Cleaning harsh high-frequency shimmer`
- `Rebuilding the repaired mix`

Avoid terminal-like output in the main panel.

#### Background and cancel controls

Contains:

- `Run in Background`
- `Cancel Repair`

### Primary actions

- `Run in Background`
- `Cancel Repair`

### Secondary actions

- `View Technical Log`

### Interaction rules

- If the app is minimized, processing should continue if possible
- If canceled, keep all finished intermediate outputs for debugging or resume options later

### States

- active processing
- paused if supported later
- canceled
- completed
- failed

### Error states

- Processing dependency failed
- Model file missing
- Out of memory
- Export path unavailable

### Transition rules

- Successful completion moves to `Compare`
- Failure moves to recoverable error panel with retry options

## Screen 5: Compare

### Goal

Let the user quickly decide whether the repaired result sounds better.

### Primary user question

Did the cleanup improve the track?

### Main layout blocks

1. A/B playback controls
2. Waveform comparison panel
3. Spectrogram comparison panel
4. Repair summary panel
5. Feedback and rerun actions

### Layout detail

#### A/B playback controls

Contains:

- `Play Original`
- `Play Repaired`
- `A/B Toggle`
- Loop region controls
- Timeline scrubber

Playback switching should be fast and level-matched if possible.

#### Waveform comparison panel

Shows:

- original waveform
- repaired waveform
- synced cursor

#### Spectrogram comparison panel

Simple, readable, not overly scientific.

Should highlight:

- restored high-frequency detail
- reduced harshness bands
- reduced noise haze if visible

#### Repair summary panel

Contains before/after summary such as:

- `Vocals sound less robotic`
- `High-end harshness reduced`
- `Top-end clarity improved`
- `Stereo image slightly stabilized`

If no meaningful gain was found, say so honestly.

#### Feedback and rerun actions

Contains:

- `This Sounds Better`
- `No Real Change`
- `Try Another Repair`
- `Continue to Export`

### Primary actions

- `Continue to Export`
- `Try Another Repair`

### Secondary actions

- `This Sounds Better`
- `No Real Change`
- `Back`

### Interaction rules

- Comparison must be immediate and easy
- Keep the user anchored to audible outcomes, not just visuals
- If the user selects `Try Another Repair`, return to `Repair Setup` with previous settings loaded

### Transition rules

- `Continue to Export` goes to `Export`
- `Try Another Repair` goes back to `Repair Setup`

## Screen 6: Export

### Goal

Deliver the repaired result cleanly and safely.

### Primary user question

How do I save the repaired version?

### Main layout blocks

1. Export format and file settings
2. Optional output selections
3. Export summary

### Layout detail

#### Export format and file settings

Contains:

- Format selector: `WAV`, `FLAC`
- File name field
- Output location picker

#### Optional output selections

Contains checkboxes:

- `Export restored stems`
- `Export repair report`

#### Export summary

Contains:

- Chosen format
- Estimated file size
- Output path
- Short summary of selected repair preset

### Primary actions

- `Export Cleaned File`

### Secondary actions

- `Open Output Folder`
- `Back to Compare`

### Recommended button labels

- `Export Cleaned File`
- `Open Output Folder`

### Success state

- Confirmation message
- Path shown clearly
- Shortcut to open folder

### Error states

- Export failed
- Output path unavailable
- Not enough space

### Transition rules

- After successful export, offer return to `Home` or stay in project

## Screen 7: Advanced

### Goal

Expose deeper control without damaging the one-click experience.

### Primary user question

Can I fine-tune how the app repairs the song?

### Access pattern

This screen should not be in the main path for casual users. It should be opened explicitly through `Advanced Settings`.

### Main layout blocks

1. Analysis detail panel
2. Module controls
3. Per-stem controls
4. Experimental features section
5. Custom preset actions

### Layout detail

#### Analysis detail panel

Contains:

- detected issue classes
- confidence scores
- warning flags
- technical notes for power users

#### Module controls

Examples:

- vocal cleanup on or off
- brightness restoration on or off
- metallic harshness reduction on or off
- light finishing on or off

Each module should expose only a few controls such as:

- disabled
- low
- medium
- high

#### Per-stem controls

Later-capable section for:

- vocals
- drums
- bass
- other

Should stay simple even here.

#### Experimental features section

Must include warnings like:

- slower processing
- less predictable output
- may not improve all songs

#### Custom preset actions

Contains:

- `Save as Custom Preset`
- `Reset to Recommended Settings`

### Primary actions

- `Apply Advanced Settings`
- `Save as Custom Preset`

### Secondary actions

- `Reset to Recommended Settings`
- `Back`

### Interaction rules

- Do not turn Advanced into a node editor
- Keep control count intentionally low
- Make reset easy and obvious

## Reusable UI Components

- `FileDropZone`
- `IssueCard`
- `PresetCard`
- `ProgressStageList`
- `WaveformComparePlayer`
- `SpectrogramPanel`
- `ExportOptionsPanel`
- `HardwareStatusBadge`
- `ModelDownloadStatus`
- `AnalysisSummaryCard`
- `RepairSummaryPanel`

## Global States

### Empty state

No project loaded.

### Loading state

Analysis or repair in progress.

### Success state

Repair finished and compare/export available.

### Error state

Readable explanation plus retry path.

## Common Error Cases

- Unsupported file
- Missing local model
- Not enough disk space
- GPU unavailable
- Processing failed
- Export failed
- File permissions problem

## Voice and Copy Guidelines

- Use plain language first
- Prefer `repair` and `cleanup` over technical jargon
- Do not mention model names in the default path
- Be honest when confidence is low or improvement is uncertain
- Emphasize privacy and local processing where useful

## MVP Interaction Rules

- Never overwrite original
- Always recommend one preset automatically
- Keep advanced controls hidden
- Keep finishing optional
- Always offer A/B comparison before export
- Preserve project history locally

## Suggested First Clickable Prototype

1. Home
2. Analysis
3. Repair Setup
4. Processing
5. Compare
6. Export

## Notes for Design Phase

- The design should feel closer to a focused media utility than a complex DAW
- Trust and clarity matter more than maximum visual density
- The compare screen is the emotional center of the product and should receive extra attention
- The product should communicate that it improves the sound while preserving user control and the original file
