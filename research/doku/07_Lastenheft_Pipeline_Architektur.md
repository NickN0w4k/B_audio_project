---
title: "Lastenheft: Pipeline-Architektur"
tags: [doku, pipeline, architektur, lastenheft, modular]
created: 2026-04-29
---

# Lastenheft: Pipeline-Architektur

## Einleitung

Die Restaurierung KI-generierter Musik ist kein monolithischer Prozess, sondern eine hochgradig modulare DSP-Pipeline, die spezialisierte neuronale Netze und klassische Signalverarbeitung in einer definierten Abfolge kombiniert. Dieser Artikel beschreibt den architektonischen Blueprint für eine solche Pipeline — basierend auf dem Projektplan, dem technischen Implementierungskonzept und dem Lastenheft der NotebookLM-Quellen.

Das Kernparadigma lautet: KI-Generate sind kein Endprodukt, sondern rohes Ausgangsmaterial für einen professionellen, mehrstufigen Veredelungsprozess — analog zu einem „musikalischen Re-Amping", bei dem die Rohausgabe als technisch mangelhaftes Demo eines Session-Musikers behandelt wird.

## Die drei Phasen

### Phase 1: Multispektrale Quellentrennung (MSS)

Die Separation des Summensignals ist die Bedingung für jede chirurgische Korrektur. Ohne Quellentrennung führen Reparaturen in einem Frequenzband unweigerlich zu destruktiven Maskierungseffekten bei unbeteiligten Instrumenten. [[02_Quellentrennung_als_Fundament|Artikel 2]]

**Module:**
- **Demucs (htdemucs)**: Hybrid-Spektrogramm- und Wellenform-Trennung, 4-Stem-Output (Vocals, Drums, Bass, Other). SDR-Werte von 5–12 dB je nach Instrument.
- **BS-RoFormer**: Band-Split RoFormer, SOTA für Music Source Separation (ByteDance AI Labs). Attention-basierte Architektur mit getrennter Frequenzband-Verarbeitung.
- **bs-roformer-infer**: Inferenz-Wrapper für BS-RoFormer mit vortrainierten Checkpoints.

**Anforderungen:**
- Mindestens 4-Stem-Trennung (Vocals, Drums, Bass, Other)
- SDR ≥ 9 dB für Vocals als Qualitätsminimum
- Batch-Verarbeitung für ganze Alben
- GPU-Beschleunigung (CUDA) als Pflicht, CPU als Fallback

### Phase 2: Stemmweise Restaurierung

Nach der Separation wird jeder Stem isoliert durch eine spezialisierte Restaurierungskette geschickt. Die Module unterscheiden sich je nach Stem-Typ.

**Für Vocals:**
- **DeepFilterNet**: Niedriglatente Rauschunterdrückung im Zeitbereich, verstärkt periodische Signalkomponenten ohne metallische Artefakte [[03_Neuronale_Vocoder_und_Signalrestaurierung|Artikel 3]]
- **VoiceFixer**: Holistische Sprachrestaurierung für Clipping, Nachhall, niedrige Auflösung und Rauschen in einem Modell
- **Vocal Naturalizer** (ComfyUI_MusicTools): 5-Ebenen-Humanisierung gegen den Auto-Tune-Effekt — Pitch-Humanization, Formant-Dithering, Sibilant-Regeneration, Breathing Injection, Micro-Timing [[04_Modulare_Pipeline_ohne_Mastering|Artikel 4]]

**Für Instrumental-Stems:**
- **AudioSR**: Bandbreitenerweiterung (Super-Resolution) für Frequenzen oberhalb des Cutoffs (4–16 kHz → 48 kHz)
- **BigVGAN / HiFi-GAN**: Neuronale Vocoder für hochauflösende Synthese, falls der Stem stark degradiert ist
- **APNet2**: Amplitude-Phase-Netzwerk mit ConvNeXt v2 + MRD für effiziente, qualitativ hochwertige Vokoderung

**Für alle Stems:**
- **DisCoder**: High-Fidelity Music Vocoder mit DAC (Descript Audio Codec) für codec-verzerrte Restaurierung (ICASSP 2025)

**Anforderungen:**
- Konfigurierbare Modulkette pro Stem-Typ
- Jedes Module kann isoliert aktiviert/deaktiviert werden
- Qualitätsmetriken nach jedem Schritt (SI-SDR, PESQ, VISQOL)
- Echtzeit-Preview für manuelle Qualitätskontrolle

### Phase 3: Re-Mixing und referenzfreies Mastering

Nach der Stemm-Restauration werden die Stems wieder zu einem kohärenten Mix zusammengeführt und abschließend gemastert — ohne Referenz-Track. [[06_Referenzfreies_Mastering_und_Alternativen|Artikel 6]]

**Module:**
- **Diff-MST**: Differentiable Mixing Style Transfer für Re-Mixing der restaurierten Stems
- **BABE-2**: Generative Equalization für blinde spektrale Balance
- **Pedalboard**: Regelbasierte Dynamikkette (Kompressor, EQ, Limiter)
- **master_me**: Alternatives Automastering mit konfigurierbarer Modulkette

**Anforderungen:**
- Ziel-LUFS konfigurierbar (Default: -14 LUFS für Streaming)
- Brickwall-Limiter als finales Sicherheitsmodul
- Kein Referenz-Track erforderlich
- True-Peak-Limiting ≤ -1 dBTP

## Architektur-Prinzipien

### Modularität

Jedes Modul ist ein isolierter Block mit definiertem Input/Output (WAV/FLAC, 44.1/48 kHz). Module können ausgetauscht, deaktiviert oder ersetzt werden, ohne die Pipeline zu brechen. Die Konfiguration erfolgt über eine zentrale YAML/JSON-Datei.

### Entkopplung von Reparatur und Mastering

Die strikte Trennung zwischen Phase 2 (Restaurierung) und Phase 3 (Mastering) ist kein Design-Compromise, sondern physikalische Notwendigkeit. Mastering-Algorithmen mit Dynamikkompression und Limiting verstärken verbliebene Artefakte. [[04_Modulare_Pipeline_ohne_Mastering|Artikel 4]]

### Idempotenz

Jeder Pipeline-Durchlauf muss reproduzierbare Ergebnisse liefern. Deterministische Modelle (GANs, Filter) bevorzugen, stochastische Modelle (Diffusion) mit festem Seed.

### Fallback-Strategie

Wenn ein Restaurierungsmodul keine Verbesserung liefert (SI-SDR sinkt), wird das Original-Signal durchgereicht. Keine Verschlechterung als Default.

## Qualitätsmetriken

| Metrik | Phase | Schwellenwert |
|--------|-------|---------------|
| SDR | MSS | ≥ 9 dB (Vocals) |
| SI-SDR | Restaurierung | Verbesserung ≥ 1 dB |
| PESQ | Restaurierung | ≥ 3.0 |
| LUFS | Mastering | -16 bis -12 LUFS |
| True Peak | Mastering | ≤ -1 dBTP |
| Spectral Similarity | Gesamt | SSIM ≥ 0.85 |

## Technische Anforderungen

- **Runtime**: Python 3.10+, PyTorch 2.x mit CUDA 12+
- **GPU**: Mindestens 8 GB VRAM (empfohlen: 24 GB für Batch-Verarbeitung)
- **RAM**: Mindestens 16 GB (empfohlen: 32 GB)
- **Storage**: SSD für temporäre Zwischendateien
- **API**: REST-API mit Endpunkten für Upload, Status, Download
- **Formate**: Input: WAV/MP3/FLAC, Output: WAV 48kHz/24bit + FLAC 48kHz

## Fazit

Die Architektur der KI-Audio-Restauration folgt einem zwingenden logischen Fluss: Zerlegung → Reparatur → Wiederaufbau. Jede Phase baut auf der vorherigen auf, und keine Phase kann übersprungen werden. Die Modularität sichert die Austauschbarkeit einzelner Komponenten, während die Entkopplung von Reparatur und Mastering die physikalische Notwendigkeit respektiert, dass Dynamikbearbeitung erst nach vollständiger Signalreparatur erfolgen darf. Die Pipeline ist als vollautomatischer Prozess konzipiert, der aber an jedem Punkt manuelle Eingriffe erlaubt.

## Querverweise

- [[01_KI_Audio_Artefakte_und_ihre_Ursachen|Artikel 1: KI-Audio-Artefakte und ihre Ursachen]]
- [[02_Quellentrennung_als_Fundament|Artikel 2: Quellentrennung als Fundament]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Artikel 3: Neuronale Vocoder und Signalrestaurierung]]
- [[04_Modulare_Pipeline_ohne_Mastering|Artikel 4: Modulare Pipeline ohne Mastering]]
- [[06_Referenzfreies_Mastering_und_Alternativen|Artikel 6: Referenzfreies Mastering und Alternativen]]
---
## 🔗 Verwandt
- [[MOC_Pipeline|🗺️ MOC: Pipeline & Architektur]]
- [[00_HOME|🏠 Home]]
