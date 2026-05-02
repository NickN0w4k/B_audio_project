# PySide6 Desktop UI

This is a parallel desktop interface for `B Audio Project` built with `PySide6`.

Design goals:
- simpler and clearer surface
- flatter, tool-like layout
- minimal rounded styling
- modern without looking decorative

## Run

Create and use a local virtual environment:

```bash
py -3.12 -m venv .venv
```

Install Python dependencies:

```bash
.venv\Scripts\python.exe -m pip install -r engine/requirements.txt
```

Start the PySide6 app:

```bash
npm run desktop:pyside
```

or:

```bash
.venv\Scripts\python.exe apps/desktop-pyside/main.py
```

## Current Scope

The PySide6 UI supports:
- importing audio
- listing projects
- running analysis
- starting cleanup runs
- watching progress
- viewing detected issues and planned repair modules
- exporting WAV or FLAC

It reuses the existing local storage layout, SQLite database, and Python engine.

## Notes

- This is a replacement UI path in the repo, not a remote GitHub fork.
- The existing Tauri UI remains available during transition.
