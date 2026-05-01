---
title: "Demucs: Music Source Separation"
tags: [quelle, tool, mss, stem-separation, quellentrennung, audio-processing]
created: 2026-04-29
---

# Demucs: Music Source Separation

- **GitHub:** https://github.com/facebookresearch/demucs
- **Paper v4:** Hybrid Transformer Demucs (HTDemucs)
- **Autor:** Alexandre Défossez (Meta AI, inzwischen nicht mehr bei Meta)
- **Lizenz:** MIT
- **Typ:** Music Source Separation (Drums, Bass, Vocals, Other)
- **Status:** Nicht mehr aktiv gewartet (Fork: adefossez/demucs)

## Überblick
Demucs ist ein SOTA-Modell für musikalische Quelltrennung. Die v4-Version (Hybrid Transformer Demucs) nutzt eine duale U-Net-Architektur mit Cross-Domain Transformer zwischen Encoder und Decoder. Erreicht 9.00 dB SDR auf MUSDB HQ (9.20 dB mit Sparse Attention + Fine-Tuning).

## Architektur (HTDemucs v4)
- **Dual U-Net:** Waveform-Zweig + Spektrogramm-Zweig
- **Cross-Domain Transformer:** Self-Attention innerhalb jeder Domäne + Cross-Attention zwischen Domänen
- **Quellen:** Drums, Bass, Vocals, Other (4-Stem)
- **Experimentell:** 6-Stem-Modell mit Guitar + Piano (Piano-Quality noch schwach)

## Modellvarianten
| Modell | Beschreibung |
|--------|-------------|
| htdemucs | Hybrid Transformer (v4 Default) |
| htdemucs_ft | Fine-Tuned Version (9.00 SDR) |
| hdemucs_mmi | Retrained Hybrid v3 Baseline |
| demucs | Classic v2 (Waveform-only) |

## Quick Start
```bash
pip install demucs
demucs song.mp3  # → separated/htdemucs/song/{drums,bass,vocals,other}.wav
demucs -n htdemucs_ft song.mp3  # Fine-tuned Modell
```

## Vergleich (SDR auf MUSDB HQ)
- Wave-U-Net: 3.2 dB
- Spleeter: 5.9 dB (25k Songs Training)
- Hybrid Demucs v3: 7.7 dB
- **HTDemucs ft (v4): 9.0 dB** ← SOTA ohne Extra-Data
- Band-Split RNN: 9.0 dB (1.7k Extra-Mixes)

## Integrationen
- UVR5 Desktop App, Hugging Face Spaces, Colab, Neutone VST/AU
- Docker: xserrat/docker-facebook-demucs
- torchaudio hat integrierte HDemucs-Unterstützung

## Relevanz
Quelltrennung ist oft der erste Schritt in Audio-Restaurierungs-Pipelines: Vocals isolieren, bevor Restaurierung/Enhancement stattfindet. Demucs ist der Goldstandard dafür.
---
## 🔗 Verwandt
- [[MOC_Stem_Separation|🗺️ MOC: Stem Separation]]
- [[02_Quellentrennung_als_Fundament|Quellentrennung als Fundament]]
