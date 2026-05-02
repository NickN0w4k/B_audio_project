# Analyse & Techstack-Konzept: B_audio_project

**Stand:** 01. Mai 2026
**Fokus:** Lokale Windows-Desktop-App zur KI-Song-Restauration

## 1. Projektübersicht
Das Ziel ist eine vollständig lokal laufende (Windows-first) Desktop-Anwendung zur Bereinigung und Restauration von KI-generierter Musik (z. B. Suno, Udio). Die App trennt strikt zwischen der Audio-Analyse, der Signal-Reparatur auf Basis isolierter Spuren (Stems) und einem optionalen Mastering/Export. 

## 2. Techstack & Architektur
Die Anwendung folgt einem modularen Aufbau, der Frontend, Backend und eine lokale Engine trennt:
* **Frontend (UI):** React, TypeScript (`App.tsx`), Tauri für die Desktop-Integration.
* **Backend:** Rust (Command-Handling, SQLite-Datenbankanbindung, Job-Supervision).
* **Engine (Audio Processing):** Python (`main.py`).
    * **Abhängigkeiten:** `numpy`, `demucs` (für Stem-Separation), `deepfilternet` (für Denoising), `ffmpeg` (für Filter, EQ, Limiter, Normalisierung und Spektrogramm-Generierung).
* **Datenhaltung:** SQLite-Persistenz für Projekte, Assets und Report-Verwaltung (`src-tauri/src/db/mod.rs`).

## 3. Aktueller Entwicklungsstand & Implementierte Features
Die Pipeline wurde erfolgreich von einem ad-hoc-Ansatz auf eine strukturierte, dokumentationsbasierte Artefakt-Strategie umgestellt. Alle Compiler-Checks (`cargo check`, `npx tsc --noEmit`) sind erfolgreich durchgelaufen.

### 3.1 Audio-Analyse & Artefakt-Erkennung
* Die Analyse läuft nun als eigenständiger Prozess vor der eigentlichen Bereinigung.
* **Erkannte Artefakte:** Die App identifiziert gezielt Probleme wie *Dull top end* (High-Frequency Rolloff), *Metallic highs* (metallische Resonanzen), *Robotic vocals* (starre Quantisierung), *Codec haze*, *Congested mix*, *Raised noise floor* und *Room smear* (eingebackener Hall).
* Die Engine berechnet zudem Confidence-Scores für die erkannten Fehler.

### 3.2 Modulare DSP-Reparatur
* **Bedingtes Denoising:** `DeepFilterNet` wird nicht mehr pauschal, sondern **nur noch bedingt** auf der isolierten Gesangsspur angewendet, wenn ein erhöhter Rauschteppich (`noise_floor`) erkannt wurde.
* **De-Esser:** Ein separater De-Esser-Schritt (über FFmpeg) wurde hinzugefügt, der bei Erkennung von `metallic_highs` dynamisch eingreift.
* **Clarity Compensation:** Für das Problem `room_smear` wurde eine konservative EQ-Korrektur (leichte Reduktion im Low-Mid-Bereich) implementiert, um den Sound aufzuklaren. Dies ersetzt vorerst einen echten, ressourcenintensiven De-Reverb-Prozess.
* **Intensitäts-Skalierung:** Die Analyse schlägt eine Reparatur-Intensität vor (`light`, `medium`, `strong`), welche die EQ- und Kompressionsparameter in der Engine direkt skaliert.

## 4. Datenstruktur & Schema-Versionierung
* **Zentralisierung:** Die Zuordnung von Artefakten zu Lösungsstrategien (`ISSUE_STRATEGIES`) wurde aus dem Frontend entfernt und in die Python-Engine sowie das Rust-Backend verschoben. 
* **Analyse-Reports:** Der Report (`summary_json`) enthält nun Metadaten wie `artifact_title`, `detection`-Erklärungen, `repair`-Strategien, `suggested_intensity` und `planned_repair_modules`. Das Frontend fungiert primär als Renderer für diese Backend-Daten.
* **Schema-Versionierung & Abwärtskompatibilität:**
    * Neue Reports erhalten die Version `schema_version = "1.0"`.
    * Fehlt diese Version beim Laden eines alten Reports, erkennt Rust diesen als "Legacy" und rekonstruiert fehlende Felder automatisch aus einer Fallback-Logik.
    * Das UI zeigt für Legacy-Reports eine Warnung an und bietet einen 1-Klick-Button ("Re-run Analysis with Current Schema") zur Neugenerierung des Reports an.

## 5. Nächste geplante Schritte
* Die Schema- und Kompatibilitätsdetails sollen in exportierte Report-Dateien sowie in die Compare/Export-Screens übernommen werden, um durchgängige Nachvollziehbarkeit zu gewährleisten.
* Die Erkennung von "Stereo Instability" (Phasenprobleme) soll in die Analyse aufgenommen werden.
* Ein dezidiertes De-Reverb-Modul ist als späteres Upgrade für die `room_smear`-Korrektur angedacht.