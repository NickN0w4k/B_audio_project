# Product Interpretation

## Purpose

This document captures the interpreted product direction based on the Obsidian vault, the technical notes, and the chosen product decisions.

It answers three questions:

1. What product should be built first?
2. What should that product do well?
3. What should it intentionally not try to be in version 1?

## Core Interpretation

The vault does not describe a simple audio utility. It describes a modular restoration philosophy for AI-generated music built around a strict sequence:

1. separate
2. repair
3. rebuild
4. optionally finalize

The strongest recurring idea across the vault is that restoration must be separated from mastering. The system should not behave like a black-box one-click enhancer that blindly applies loudness, EQ, and limiting to a damaged stereo mix. Instead, it should treat AI-generated songs as raw source material that often contains stem-level defects and must be repaired before any final polish is applied.

## Product Definition

The best first product is:

- a fully local desktop application
- for one-click end users
- focused specifically on AI-generated song cleanup
- with simple guided workflows on the surface
- and modular restoration logic underneath

In other words, the product should feel simple, but not be simplistic.

## Why This Product Form Fits Best

### 1. The source material is complex

The vault is centered on defects that are not well handled by trivial stereo processing alone:

- robotic vocals
- metallic shimmer
- dull high end
- codec haze
- unstable stereo image
- congested dynamics

These issues often interact with each other, which is why the vault repeatedly argues for stem-aware repair instead of blind mix-bus processing.

### 2. The workflow needs trust

Users need:

- before/after comparison
- explicit progress during long jobs
- clear indication that files stay local
- preserved originals
- the ability to try a different repair path

That trust model fits a local desktop product much better than an abstract background service.

### 3. The audience is not primarily engineers

You selected:

- fully local
- one-click end users
- AI-generated song cleanup specifically

That means version 1 should not look like a research environment, a node graph system, or a DAW replacement. It should look like a focused consumer-facing repair tool with strong defaults.

## Product Positioning

This product should be positioned as:

- an AI song cleanup tool
- a local restoration workstation for generated music
- a guided quality-improvement app for damaged AI audio outputs

It should not be positioned first as:

- a full mastering suite
- a DAW
- a node-based experimental lab
- a generalized audio post-production environment

## Main User Promise

The user promise should be something close to:

`Import your AI-generated song, let the app detect the biggest problems, apply the best repair path locally, compare the result, and export a cleaner version.`

The promise is not perfection. The promise is controlled improvement.

## Main Product Goals

### 1. Make AI-generated songs sound cleaner and less synthetic

The product should reduce audible defects that commonly make generated songs feel artificial or amateurish.

### 2. Keep the workflow simple

The user should be able to reach a result in a short path:

1. import
2. analyze
3. choose or accept preset
4. run cleanup
5. compare
6. export

### 3. Keep all processing local

Privacy and local control are not side features. They are part of the core value proposition.

### 4. Preserve user trust

The app should always preserve the original file, explain what it is doing in plain language, and avoid pretending that uncertain repairs are guaranteed wins.

## Product Principles

### Guided, not overwhelming

The main experience should be preset-driven and recommendation-led.

### Modular internally, simple externally

Internally the system should be composed of separable modules. Externally the user should see a clean, curated flow.

### Restoration first, finishing second

Repair is the core product. Final polish is optional and should never be silently blended into the repair logic.

### Local and reversible

The user must feel safe using the app. The source file stays untouched, and the repaired version is always a separate output.

### Honest diagnostics

The app should detect probable artifact classes and recommend the most suitable repair path, but it should not overclaim certainty.

## What the Product Should Do Well in MVP

The MVP should be very good at a narrow set of real problems instead of mediocre at everything.

Primary targets:

- robotic or synthetic-sounding vocals
- metallic high-frequency harshness
- dull or cutoff high end
- codec-like haze
- generally congested AI-generated stereo mixes

The MVP does not need to solve every restoration scenario. It should solve the common AI-song-cleanup case reliably enough that users trust it.

## What the Product Should Not Try to Be in MVP

The MVP should explicitly avoid becoming:

- a full mastering environment
- a general-purpose DAW
- a forensic audio editor like RX
- a freeform node graph builder
- a platform for large-scale training or experimentation
- a cloud processing service

These may be adjacent spaces, but they are not the correct focus for version 1.

## Recommended User Flow

The intended default user flow is:

1. Open app
2. Drop in a song
3. Wait for automatic issue detection
4. Accept the recommended preset or choose another
5. Run the cleanup locally
6. Compare original and repaired versions
7. Export the cleaned file

This flow should remain the main path even if advanced controls are added later.

## Role of Artifact Detection

Artifact detection should be framed as:

- quality diagnostics
- artifact analysis
- repair routing
- restoration guidance

Its purpose is to identify audible error patterns that damage the sound image, so the system can choose more suitable correction steps.

It should not be framed as bypass logic.

## Product Layers

The product can be understood in three layers.

### Layer 1: Consumer path

The visible path for most users:

- import
- analyze
- repair
- compare
- export

### Layer 2: Guided control

The path for slightly more involved users:

- preset selection
- repair intensity
- optional finishing
- stem export

### Layer 3: Expert controls

The path for advanced users later:

- per-module controls
- per-stem intensity
- advanced diagnostics
- custom presets

The important point is that layer 3 must never damage layer 1.

## Recommended MVP Feature Set

- import WAV, FLAC, MP3
- normalize to internal working format
- artifact analysis
- recommended preset selection
- one-click repair run
- visible step-by-step progress
- before/after comparison
- WAV and FLAC export
- optional repair report
- original preservation

## Recommended MVP Repair Philosophy

The MVP should follow this sequence:

1. ingest and normalize
2. analyze probable defect classes
3. separate stems
4. repair vocals and music conservatively
5. rebuild mix
6. optionally apply light finishing
7. export

This preserves the vault's central logic without forcing the first release into an overcomplicated research-grade implementation.

## Key Risks in Product Interpretation

### Risk 1: Trying to be too powerful too early

If the first version tries to expose every model, every routing option, and every advanced audio concept, it will miss the one-click audience.

### Risk 2: Becoming a disguised mastering app

If the system quietly leans too much on loudness, EQ, and limiting, it will drift away from the restoration-first philosophy.

### Risk 3: Overpromising repair quality

Some source material will be too damaged for dramatic improvement. The product must stay honest.

### Risk 4: Heavy infrastructure too early

A cloud-heavy or service-heavy design would create unnecessary installation and operational complexity for the chosen audience.

## Strategic Conclusion

The correct first product is not a giant research platform and not a general audio workstation.

It is a narrow, trustworthy, local desktop tool for improving AI-generated songs through guided restoration.

Its defining qualities should be:

- local
- simple
- modular underneath
- restoration-first
- compare-before-export
- honest about outcomes

## Final Product Statement

The product should be built as a local desktop app that helps non-technical users clean up AI-generated songs through a guided process of artifact analysis, stem-aware repair, mix reconstruction, optional finishing, and before/after comparison, while preserving the original file and keeping the experience simple.
