# Frontend UI Direction Plan

## Purpose

This document defines the frontend direction for the next product phase.

It is intended to answer:

1. What UI direction are we choosing?
2. What kind of product experience are we trying to build?
3. What will we keep, what will we stop, and what will we rebuild?
4. In what order should the frontend work happen?

This is a plan document.

It is not a brainstorming note and not a temporary comparison of options.

## Decision

The product UI will move forward on:

- `Tauri + React + TypeScript + Vite`

The current `PySide6` UI path will not continue as the main product direction.

`PySide6` may remain in the repository temporarily as a reference during migration, but it is no longer the primary UI strategy.

We are also not adopting:

- `Electron`
- `Next.js`
- `Svelte`

for the main desktop application at this stage.

## Why This Direction

This decision is based on product fit, implementation fit, and long-term maintainability.

### Product fit

The app needs a UI that is:

- modern
- minimal
- clear under load
- visually more refined than the current PySide path
- easier to shape into a desktop tool instead of a generic admin-style interface

### Implementation fit

The repository already contains a working and relevant base for this direction:

- `apps/desktop-ui`
- `src-tauri`
- existing Rust commands and events
- existing Python engine integration

This makes `Tauri + React` the lowest-risk way to move toward a better UI without replacing the actual backend architecture.

### Architecture fit

The app already has the right execution model for a responsive UI:

- `React` for interface and interaction
- `Rust` for orchestration, persistence, jobs, and desktop integration
- `Python` for heavy audio analysis and repair

The UI should stay responsive not because the framework is magical, but because heavy work remains outside the UI thread.

## Strategic Goal

We want the product to feel like a focused desktop audio tool.

We do not want it to feel like:

- a dashboard
- a web admin panel
- a developer utility
- a form-heavy setup screen

We want it to feel like:

- a guided cleanup tool
- a local desktop product
- a focused compare-and-decide workspace
- a calm, modern, minimal tool

## Product Experience Goal

The frontend should support this user journey cleanly:

1. Import a song
2. Let the app analyze it automatically
3. Show the main issues clearly
4. Recommend a repair path
5. Run cleanup locally without freezing the interface
6. Compare original and repaired output with confidence
7. Export the final result

The main product promise should be visible in the UI:

- local
- guided
- understandable
- trustworthy

## Core Principles

### 1. Desktop tool, not web app

The new React UI must be designed like a desktop application, not like a typical browser dashboard.

That means:

- fewer simultaneous panels
- stronger visual hierarchy
- more stable work areas
- less card-grid clutter
- clearer primary actions

### 2. One primary task per screen

Each screen should answer one main user question.

Examples:

- `Home`: how do I start or reopen work?
- `Analysis`: what is wrong with this song?
- `Repair`: what repair should I run?
- `Compare`: does the repaired version actually sound better?
- `Export`: how do I save the final result?

### 3. Compare is the trust center

The product is only convincing if the compare experience is convincing.

That means the compare screen is not secondary. It is one of the most important parts of the entire product.

It must make it easy to:

- hear the difference
- inspect the difference
- decide whether the repair helped
- move to export or go back for another pass

### 4. Heavy work stays out of the UI

The frontend must never become the place where expensive processing happens.

The execution model stays:

- UI in `React`
- orchestration in `Rust`
- repair and analysis in `Python`

This is how we keep the interface responsive during longer jobs.

### 5. Advanced controls stay secondary

The product remains guided.

Advanced controls should exist only where they add real value, and they should not dominate the main flow.

### 6. Final output must be visually and conceptually separate from preview output

The product must clearly distinguish:

- working assets
- preview assets
- final cleaned export

This matters in compare, reporting, and export confidence.

## Technology Plan

## Primary stack

The frontend stack will be:

- `React 19`
- `TypeScript`
- `Vite`
- `Tauri 2`

## Supporting libraries

The recommended supporting stack is:

- `React Router`
- `TanStack Query`
- `Zustand`
- `Tailwind CSS`
- `Radix UI`
- `clsx`
- `tailwind-merge`

Optional and only where justified:

- `framer-motion`
- `wavesurfer.js`
- `Web Workers`

## Why these choices

### React Router

We need clean screen-level structure for a linear desktop workflow.

### TanStack Query

We need a disciplined way to load and refresh:

- app status
- projects
- project detail
- run detail
- export state

without reintroducing tangled manual state flows.

### Zustand

We need lightweight local UI state for things like:

- compare mode
- loop ranges
- selected playback target
- local panel visibility

### Tailwind CSS and Radix UI

We need a styling foundation that is:

- fast to iterate
- highly controllable
- modern
- consistent

without locking us into a generic component look.

## Visual Direction

## Overall feel

The interface should feel:

- dark
- calm
- modern
- precise
- minimal
- studio-like

It should not feel:

- glossy
- playful
- loud
- over-decorated
- like a SaaS admin panel

## Layout direction

The main shell should use:

- a narrow left navigation area
- a compact top bar
- a central work surface
- a bottom status strip

An optional right-side detail area is acceptable only when it clearly improves focus.

## Design rules

- one main accent color
- restrained status colors
- one main type family
- few surface levels
- consistent spacing rhythm
- consistent radius system
- limited use of shadows
- minimal badge noise

## Screen Plan

## 1. Home

### Goal

Start a project or reopen an existing one with minimal friction.

### Must contain

- large import area
- recent projects list
- compact readiness indicators

### Must avoid

- too many actions at once
- dense technical information
- dashboard clutter

## 2. Analysis

### Goal

Explain the detected problems and recommend the next step.

### Must contain

- song summary
- a short list of the most important issues
- recommended repair preset
- runtime expectation
- one clear action to continue

### Must avoid

- flooding the user with raw technical detail
- too many parallel cards of equal weight
- large blocks of text in the main path

## 3. Repair

### Goal

Let the user start cleanup confidently with minimal decision overload.

### Must contain

- preset choice
- intensity choice
- short explanation of the recommendation
- start action
- optional advanced area

### Must avoid

- large form layouts
- too many checkboxes in the default view
- exposing low-level internals in the main flow

## 4. Compare

### Goal

Provide a clear, trustworthy before/after judgment surface.

### Must contain

- original versus final comparison
- A/B switching with position preservation
- loop controls
- spectrogram comparison
- repair summary
- quick verdict
- direct path to export

### Must avoid

- mixing preview and final concepts
- too many side panels
- burying the playback controls
- reducing compare to a simple file player

## 5. Export

### Goal

Save the repaired result cleanly and confidently.

### Must contain

- format selection
- final output summary
- optional additional outputs
- clear confirmation

### Must avoid

- re-explaining analysis
- duplicating compare functionality
- unnecessary complexity at the end of the flow

## Application Structure Plan

The existing monolithic React surface must be broken into feature-driven parts.

## Target structure

```text
apps/desktop-ui/src/
  app/
    App.tsx
    router.tsx
    providers.tsx
  components/
    layout/
    ui/
  features/
    projects/
    analysis/
    repair/
    compare/
    export/
    runtime/
  lib/
    tauri/
    audio/
    format/
    utils/
  stores/
  styles/
```

## Structural rules

- no more major screen logic concentrated in a single `App.tsx`
- feature-specific UI and logic live together
- backend data handling is separated from local UI state
- reusable layout pieces are centralized
- compare-specific state stays isolated from unrelated screens

## State Management Plan

## Backend-driven data

Use `TanStack Query` for:

- app status
- projects list
- project detail
- run detail
- exports
- readiness state

## Local UI state

Use `Zustand` for:

- compare target
- loop positions
- selected transport state
- temporary panel open or closed state
- temporary screen-level UI choices

## Rule

Do not duplicate backend state across multiple manual React states unless there is a strong reason.

## Performance Plan

The UI must remain responsive during analysis, cleanup, and export.

## Performance rules

- no heavy audio processing in the React renderer
- no long synchronous transformations in screen components
- no unnecessary polling when events can be used
- prefer cached assets and precomputed outputs
- isolate re-renders to the components that actually need updates

## If needed later

If visual processing becomes expensive, we can add:

- `Web Workers` for UI-side preprocessing
- canvas-based rendering for larger visual surfaces
- list virtualization for larger histories or logs

## Migration Plan

The move back to `Tauri + React` should happen in clear phases.

## Phase 1: Lock the direction

Goal:

Make `Tauri + React` the official main frontend direction.

Tasks:

1. Document the decision
2. Stop expanding PySide as the main product path
3. Align future UI work to the React/Tauri direction

## Phase 2: Rebuild the frontend foundation

Goal:

Create a clean React structure that can support the redesigned UI.

Tasks:

1. Break apart the current monolithic `App.tsx`
2. Introduce screen routing structure
3. Introduce provider structure
4. Add feature folders
5. Add the chosen state and styling foundation

## Phase 3: Build the new app shell

Goal:

Make the product feel like a real desktop tool immediately.

Tasks:

1. Build sidebar
2. Build top bar
3. Build bottom status strip
4. Define shell spacing and surface rules

## Phase 4: Rebuild Home and Compare first

Goal:

Improve first impression and core trust surface early.

Tasks:

1. Redesign Home around import clarity
2. Redesign recent projects presentation
3. Rebuild Compare as a strong A/B workspace
4. Carry over loop and summary ideas from the PySide line

## Phase 5: Rebuild Analysis and Repair

Goal:

Make the guided path simple and convincing.

Tasks:

1. Simplify analysis presentation
2. Strengthen recommendation display
3. Reduce repair setup complexity
4. Move advanced controls out of the default path

## Phase 6: Rebuild Export and finishing UX

Goal:

Make the end of the workflow as clear as the beginning.

Tasks:

1. Simplify export selection
2. Improve final output summary
3. Add optional report and extra outputs cleanly

## Phase 7: Polish processing and recovery UX

Goal:

Make long jobs and failure states feel controlled and understandable.

Tasks:

1. Improve progress language
2. Separate user-facing progress from technical logs
3. Improve cancel behavior presentation
4. Improve background-run handling
5. Improve failure and recovery messaging

## What We Keep

We keep the existing architectural separation:

- `Tauri`
- `Rust` orchestration
- `Python` engine
- background process execution
- local storage model
- structured run reporting

We also keep the product flow:

- Home
- Analysis
- Repair
- Compare
- Export

## What We Stop Doing

We stop treating `PySide6` as the main frontend direction.

We also stop building the React UI in a way that feels like a generic web dashboard.

That means we avoid:

- overgrown card grids
- too many equal-priority panels
- monolithic screen logic
- mixing technical detail into the main flow
- UI structures that look like admin software

## What We Bring Forward From PySide

We keep the good ideas that emerged during the PySide phase and re-express them in the React UI.

These include:

- stronger compare focus
- A/B switching with position preservation
- loop-based comparison
- repair summary
- quick verdict
- background run support
- clearer processing stages
- stronger guided repair setup

These are product improvements, not reasons to keep the PySide UI itself.

## Success Criteria

This plan is successful when:

- `Tauri + React` is again the clear frontend mainline
- the UI looks and behaves like a focused desktop tool
- the product is more minimal and modern than the current PySide line
- the interface stays responsive during long runs
- the guided flow is easier to understand than the previous React version
- compare is clearly the strongest and most trustworthy part of the UI
- the codebase is easier to extend than the previous monolithic React surface

## Immediate Next Steps

1. Treat this plan as the frontend direction of record
2. Start restructuring `apps/desktop-ui`
3. Re-establish the Tauri/React path as the active primary UI
4. Build the new shell and the new Home screen
5. Build the new Compare screen early
6. Migrate the remaining screens in sequence
