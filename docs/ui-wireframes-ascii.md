# UI Wireframes ASCII

## Purpose

This document translates the screen-level UI specification into low-fidelity ASCII wireframes. The goal is to define layout, hierarchy, and interaction flow before visual design starts.

These wireframes are intentionally simple:

- no branding
- no final spacing system
- no final typography
- no color decisions
- focus on structure and user flow

## Global Shell

```text
+----------------------------------------------------------------------------------+
| APP NAME                          Project: Song_001            [Settings]        |
+----------------------+-----------------------------------------------------------+
| Home                 | Status: Local | GPU Ready | Models Ready | Disk OK        |
| Analysis             +-----------------------------------------------------------+
| Repair               |                                                           |
| Processing           |                 Main Screen Content Area                   |
| Compare              |                                                           |
| Export               |                                                           |
| Advanced             |                                                           |
|                      |                                                           |
+----------------------+-----------------------------------------------------------+
| Footer: Fully local processing | Original preserved | App version                |
+----------------------------------------------------------------------------------+
```

## Screen 1: Home

### Desktop layout

```text
+----------------------------------------------------------------------------------+
| APP NAME                          Home                            [Settings]      |
+----------------------+-----------------------------------------------------------+
| Home                 | Status: Local | GPU Ready | Models Ready | Disk OK        |
| Analysis             +-----------------------------------------------------------+
| Repair               |                                                           |
| Processing           |   +---------------------------------------------------+   |
| Compare              |   | Drop your song here                               |   |
| Export               |   |                                                   |   |
| Advanced             |   |        [ Choose File ]                            |   |
|                      |   |                                                   |   |
|                      |   | Drop a WAV, FLAC, or MP3 file to begin            |   |
|                      |   | Everything stays on this device                   |   |
|                      |   +---------------------------------------------------+   |
|                      |                                                           |
|                      |   +----------------------+  +------------------------+   |
|                      |   | Recent Projects      |  | System Readiness       |   |
|                      |   |----------------------|  |------------------------|   |
|                      |   | Song_A   [Open]      |  | Local: ready           |   |
|                      |   | Song_B   [Open]      |  | GPU: detected          |   |
|                      |   | Song_C   [Open]      |  | Models: installed      |   |
|                      |   |                      |  | Disk: OK               |   |
|                      |   +----------------------+  +------------------------+   |
+----------------------+-----------------------------------------------------------+
```

### Primary interaction focus

- import first
- recent projects second
- system readiness as reassurance, not as the main action

## Screen 2: Analysis

### Desktop layout

```text
+----------------------------------------------------------------------------------+
| APP NAME                      Analysis                          [Back] [Settings] |
+----------------------+-----------------------------------------------------------+
| Home                 | Status: Local | GPU Ready | Analysis Complete             |
| Analysis             +-----------------------------------------------------------+
| Repair               |  +-----------------------------------------------------+  |
| Processing           |  | Song Summary                                        |  |
| Compare              |  |-----------------------------------------------------|  |
| Export               |  | File: Song_001.mp3                                  |  |
| Advanced             |  | Length: 03:24    Format: MP3    Sample rate: 44.1k  |  |
|                      |  +-----------------------------------------------------+  |
|                      |                                                           |
|                      |  +-------------------+  +-------------------+            |
|                      |  | Robotic Vocals    |  | Metallic Highs    |            |
|                      |  | Severity: High    |  | Severity: Medium  |            |
|                      |  | [Learn More]      |  | [Learn More]      |            |
|                      |  +-------------------+  +-------------------+            |
|                      |                                                           |
|                      |  +-------------------+  +-------------------+            |
|                      |  | Dull Top End      |  | Congested Mix     |            |
|                      |  | Severity: High    |  | Severity: Medium  |            |
|                      |  | [Learn More]      |  | [Learn More]      |            |
|                      |  +-------------------+  +-------------------+            |
|                      |                                                           |
|                      |  +-----------------------------------------------------+  |
|                      |  | Recommended Repair                                  |  |
|                      |  |-----------------------------------------------------|  |
|                      |  | AI Song Cleanup                                     |  |
|                      |  | Best match for robotic vocals and dull top end      |  |
|                      |  | Confidence: High                                    |  |
|                      |  | ETA: 08 min on GPU                                  |  |
|                      |  | [ Use Recommended Repair ]  [ Choose Another ]      |  |
|                      |  +-----------------------------------------------------+  |
+----------------------+-----------------------------------------------------------+
```

### Notes

- issue cards should scan quickly
- recommendation panel should visually dominate the lower part of the page

## Screen 3: Repair Setup

### Desktop layout

```text
+----------------------------------------------------------------------------------+
| APP NAME                    Repair Setup                       [Back] [Settings] |
+----------------------+-----------------------------------------------------------+
| Home                 | Status: Local | GPU Ready | Ready to Start              |
| Analysis             +-----------------------------------------------------------+
| Repair               |  +-----------------------------------------------------+  |
| Processing           |  | Presets                                             |  |
| Compare              |  |-----------------------------------------------------|  |
| Export               |  | [AI Song Cleanup] [Gentle] [Fix Vocals] [Brightness]|  |
| Advanced             |  | [Metallic Harshness] [Deep Cleanup]                 |  |
|                      |  +-----------------------------------------------------+  |
|                      |                                                           |
|                      |  +----------------------+  +--------------------------+  |
|                      |  | Intensity            |  | Options                  |  |
|                      |  |----------------------|  |--------------------------|  |
|                      |  | ( ) Low              |  | [ ] Apply Light Finishing|  |
|                      |  | (x) Medium           |  | [ ] Export Restored Stems|  |
|                      |  | ( ) High             |  |                          |  |
|                      |  +----------------------+  +--------------------------+  |
|                      |                                                           |
|                      |  +-----------------------------------------------------+  |
|                      |  | Estimated Runtime: 08 min on GPU                    |  |
|                      |  | Medium repair strength recommended                  |  |
|                      |  +-----------------------------------------------------+  |
|                      |                                                           |
|                      |  [ Start Repair ]   [ Reset to Recommended ]            |
|                      |                                                           |
|                      |  [ Advanced Settings v ]                                |
+----------------------+-----------------------------------------------------------+
```

### Expanded advanced drawer

```text
+----------------------------------------------------------------------------------+
| Advanced Settings v                                                               |
|----------------------------------------------------------------------------------|
| Modules:                                                                         |
| [x] Vocal Cleanup    [x] Brightness Restore   [x] Metallic Reduction             |
| [ ] Light Finishing                                                               |
|                                                                                  |
| Per-Stem Controls:                                                               |
| Vocals:   [Low | Med | High]                                                     |
| Music:    [Low | Med | High]                                                     |
|                                                                                  |
| Experimental:                                                                    |
| [ ] Stronger Repair Mode  (slower, less predictable)                             |
+----------------------------------------------------------------------------------+
```

## Screen 4: Processing

### Desktop layout

```text
+----------------------------------------------------------------------------------+
| APP NAME                     Processing                         [Settings]       |
+----------------------+-----------------------------------------------------------+
| Home                 | Status: Running | GPU Active | ETA 06:42                 |
| Analysis             +-----------------------------------------------------------+
| Repair               |                                                           |
| Processing           |   +---------------------------------------------------+   |
| Compare              |   | Overall Progress                                  |   |
| Export               |   | [#####################-------------] 62%           |   |
| Advanced             |   | Current step: Repairing vocals                    |   |
|                      |   +---------------------------------------------------+   |
|                      |                                                           |
|                      |   +-----------------------------+  +------------------+   |
|                      |   | Pipeline Stages             |  | Activity Log     |   |
|                      |   |-----------------------------|  |------------------|   |
|                      |   | [x] Preparing audio         |  | Checking vocals  |   |
|                      |   | [x] Analyzing               |  | Reducing robotic |   |
|                      |   | [x] Separating stems        |  | artifacts        |   |
|                      |   | [>] Repairing vocals        |  |                  |   |
|                      |   | [ ] Repairing music         |  | Cleaning harsh   |   |
|                      |   | [ ] Rebuilding mix          |  | top-end shimmer  |   |
|                      |   | [ ] Saving results          |  |                  |   |
|                      |   +-----------------------------+  +------------------+   |
|                      |                                                           |
|                      |   [ Run in Background ]    [ Cancel Repair ]             |
|                      |                                                           |
|                      |   [ View Technical Log ]                                 |
+----------------------+-----------------------------------------------------------+
```

### Notes

- user should always know the current stage
- avoid visually noisy logs on the main screen

## Screen 5: Compare

### Desktop layout

```text
+----------------------------------------------------------------------------------+
| APP NAME                      Compare                           [Back] [Settings] |
+----------------------+-----------------------------------------------------------+
| Home                 | Status: Repair Complete | Ready for Review                |
| Analysis             +-----------------------------------------------------------+
| Repair               |  +-----------------------------------------------------+  |
| Processing           |  | A/B Playback                                         |  |
| Compare              |  |-----------------------------------------------------|  |
| Export               |  | [ Play Original ] [ Play Repaired ] [ A/B Toggle ]  |  |
| Advanced             |  | Loop: [ Set Start ] [ Set End ]                      |  |
|                      |  +-----------------------------------------------------+  |
|                      |                                                           |
|                      |  +-----------------------------------------------------+  |
|                      |  | Waveform Compare                                    |  |
|                      |  |-----------------------------------------------------|  |
|                      |  | Original waveform                                   |  |
|                      |  | Repaired waveform                                   |  |
|                      |  +-----------------------------------------------------+  |
|                      |                                                           |
|                      |  +---------------------------+  +----------------------+  |
|                      |  | Spectrogram Compare       |  | Repair Summary       |  |
|                      |  |---------------------------|  |----------------------|  |
|                      |  | Before / After panel      |  | Less robotic vocals  |  |
|                      |  |                           |  | Better top-end       |  |
|                      |  |                           |  | Reduced harshness    |  |
|                      |  +---------------------------+  | Stereo slightly      |  |
|                      |                                  | improved            |  |
|                      |                                  +----------------------+  |
|                      |                                                           |
|                      |  [ This Sounds Better ] [ No Real Change ]               |
|                      |  [ Try Another Repair ] [ Continue to Export ]           |
+----------------------+-----------------------------------------------------------+
```

### Notes

- this is the emotional center of the product
- playback controls must feel immediate

## Screen 6: Export

### Desktop layout

```text
+----------------------------------------------------------------------------------+
| APP NAME                       Export                           [Back] [Settings] |
+----------------------+-----------------------------------------------------------+
| Home                 | Status: Ready to Export                                 |
| Analysis             +-----------------------------------------------------------+
| Repair               |  +-----------------------------------------------------+  |
| Processing           |  | Export Settings                                     |  |
| Compare              |  |-----------------------------------------------------|  |
| Export               |  | Format:      (o) WAV   ( ) FLAC                     |  |
| Advanced             |  | File name:   [ Song_001_cleaned__________ ]         |  |
|                      |  | Save to:     [ C:\Exports\.............. ] [Browse]|  |
|                      |  +-----------------------------------------------------+  |
|                      |                                                           |
|                      |  +---------------------------+  +----------------------+  |
|                      |  | Optional Outputs          |  | Export Summary       |  |
|                      |  |---------------------------|  |----------------------|  |
|                      |  | [ ] Export restored stems |  | Preset: AI Cleanup   |  |
|                      |  | [ ] Export repair report  |  | Format: WAV          |  |
|                      |  |                           |  | Est. size: 38 MB     |  |
|                      |  +---------------------------+  | Local export only    |  |
|                      |                                  +----------------------+  |
|                      |                                                           |
|                      |  [ Export Cleaned File ]                                  |
|                      |  [ Open Output Folder ]                                   |
+----------------------+-----------------------------------------------------------+
```

### Success state variation

```text
+----------------------------------------------------------------------------------+
| Export Complete                                                                   |
|----------------------------------------------------------------------------------|
| Your cleaned file was saved successfully.                                         |
|                                                                                  |
| Path: C:\Exports\Song_001_cleaned.wav                                           |
|                                                                                  |
| [ Open Output Folder ]   [ Back to Home ]   [ Stay in Project ]                  |
+----------------------------------------------------------------------------------+
```

## Screen 7: Advanced

### Desktop layout

```text
+----------------------------------------------------------------------------------+
| APP NAME                     Advanced Settings                 [Back] [Settings] |
+----------------------+-----------------------------------------------------------+
| Home                 | Status: Advanced Mode                                   |
| Analysis             +-----------------------------------------------------------+
| Repair               |  +---------------------------+  +----------------------+  |
| Processing           |  | Analysis Details          |  | Warning Flags        |  |
| Compare              |  |---------------------------|  |----------------------|  |
| Export               |  | Robotic vocal: 0.87       |  | Low bitrate input    |  |
| Advanced             |  | Metallic highs: 0.66      |  | Heavy compression    |  |
|                      |  | Dull top end: 0.91        |  | CPU mode may be slow |  |
|                      |  +---------------------------+  +----------------------+  |
|                      |                                                           |
|                      |  +-----------------------------------------------------+  |
|                      |  | Module Controls                                     |  |
|                      |  |-----------------------------------------------------|  |
|                      |  | Vocal Cleanup            [Off | Low | Med | High]   |  |
|                      |  | Brightness Restoration  [Off | Low | Med | High]   |  |
|                      |  | Metallic Reduction      [Off | Low | Med | High]   |  |
|                      |  | Light Finishing         [Off | Low | Med | High]   |  |
|                      |  +-----------------------------------------------------+  |
|                      |                                                           |
|                      |  +-----------------------------------------------------+  |
|                      |  | Per-Stem Controls                                   |  |
|                      |  |-----------------------------------------------------|  |
|                      |  | Vocals: [Low | Med | High]                          |  |
|                      |  | Music:  [Low | Med | High]                          |  |
|                      |  +-----------------------------------------------------+  |
|                      |                                                           |
|                      |  [ Apply Advanced Settings ] [ Save as Custom Preset ]  |
|                      |  [ Reset to Recommended Settings ]                      |
+----------------------+-----------------------------------------------------------+
```

## Mobile/Small Window Behavior Notes

These screens are desktop-first, but the app should still remain usable in smaller windows.

### Rules

- sidebar can collapse into top step navigation
- two-column panels stack vertically
- waveform and spectrogram panels become tabbed if space is limited
- primary actions stay pinned near the bottom edge

## Interaction Flow Summary

```text
Home -> Analysis -> Repair Setup -> Processing -> Compare -> Export
                        ^                 |            |
                        |                 |            v
                        +----- Try Another Repair <----+

Advanced is entered from Repair Setup and returns there.
```

## Design Notes for Next Phase

- keep the visual tone closer to a premium media utility than a DAW
- the compare screen deserves the richest interaction design
- progress clarity is critical because local AI processing can take time
- the app should always make the user feel safe: local, reversible, original preserved
