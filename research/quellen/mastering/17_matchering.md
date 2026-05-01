---
title: "Matchering 2.0"
tags: [quelle, tool, mastering, referenzbasiert, spectral-matching]
created: 2026-04-29
---

# Matchering 2.0

- **GitHub:** https://github.com/sergree/matchering
- **PyPI:** https://pypi.org/project/matchering
- **Lizenz:** MIT
- **Typ:** Audio Matching & Mastering (Reference-basiert)

## Überblick
Matchering 2.0 ist eine Containerized Web App, Python-Library und ComfyUI-Node für referenzbasiertes Audio-Matching und Mastering. Kernidee: zwei Audiodateien (Target + Reference) rein → Matchering gleicht RMS, Frequenzgang, Peak-Amplitude und Stereo-Width an.

## Kernfeatures
- **Referenz-basiertes Mastering:** Target klingt wie Reference
- **Multi-Interface:** Desktop App (UVR5), Docker, Python-Library, ComfyUI-Node
- **Eigener Hyrax Brickwall Limiter:** Open-Source-Implementierung
- **Benn Jordan Review:** Rank 3 hinter 2 professionellen Mastering-Engineers (Studie mit 472 Einträgen)
- **Integration in UVR5 Desktop App** und Songmastr/MVSEP/Moises

## Signalverarbeitung
1. RMS-Matching (Root Mean Square Loudness)
2. Frequenzgang-Matching (Frequency Response)
3. Peak-Amplitude-Matching
4. Stereo-Width-Matching
5. Hyrax Brickwall Limiter

## Quick Start (Python)
```python
import matchering as mg
mg.process(
    target="my_song.wav",
    reference="reference_song.wav",
    results=[mg.pcm16("my_song_master_16bit.wav")],
)
```

## Besonderheit
Kein Machine Learning! Rein algorithmischer Ansatz — das macht Matchering interpretierbar und kontrollierbar, im Gegensatz zu NN-basierten Mastering-Tools.

## Zitat
- Habr-Artikel: https://habr.com/ru/post/709120/
---
## 🔗 Verwandt
- [[MOC_Mastering|🗺️ MOC: Mastering]]
- [[06_Referenzfreies_Mastering_und_Alternativen|Referenzfreies Mastering und Alternativen]]
