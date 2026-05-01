---
title: "Paper: AudioSR — Versatile Audio Super-resolution at Scale"
tags: [quelle, paper, super-resolution, vocoder]
created: 2026-04-29
---

# Paper: AudioSR — Versatile Audio Super-resolution at Scale

- **arXiv:** https://arxiv.org/abs/2309.07314
- **Autoren:** Haohe Liu, Ke Chen, Qiao Tian, Wenwu Wang, Mark D. Plumbley
- **Eingereicht:** 13. September 2023
- **Typ:** Diffusion-basiertes Audio-Super-Resolution-Modell

## Abstract
Audio Super-Resolution (ASR) ist die Aufgabe, hochfrequente Komponenten für niederauflösendes Audio vorherzusagen. Bisherige Methoden waren auf spezifische Audiotypen (nur Sprache, nur Musik) und feste Bandbreiten beschränkt.

AudioSR führt ein **diffusionsbasiertes generatives Modell** ein, das robuste Audio-Super-Resolution für vielfältige Audiotypen durchführt — Soundeffekte, Musik und Sprache. Es kann jedes Eingangssignal im Bandbreitenbereich 2kHz–16kHz auf 24kHz-Bandbreite (48kHz Sample-Rate) hochrechnen.

## Kernergebnisse
- Objektiv: Starke Ergebnisse auf verschiedenen ASR-Benchmarks
- Subjektiv: AudioSR verbessert die Generationsqualität einer breiten Palette von Audiogeneratoren (AudioLDM, FastSpeech2, MusicGen) als Plug-and-Play-Modul
- Demo: https://audioldm.github.io/audiosr

## Relevanz
Das zentrale Paper für Audio-Super-Resolution in der Pipeline. AudioSR ist gleichzeitig das Modell hinter dem GitHub-Repo haoheliu/versatile_audio_super_resolution (Quelle 9).

## Zitat
```bibtex
@article{liu2023audiosr,
  title={AudioSR: Versatile Audio Super-resolution at Scale},
  author={Liu, Haohe and Chen, Ke and Tian, Qiao and Wang, Wenwu and Plumbley, Mark D.},
  journal={arXiv preprint arXiv:2309.07314},
  year={2023}
}
```
---
## 🔗 Verwandt
- [[MOC_Vocoder|🗺️ MOC: Neuronale Vocoder]]
- [[09_AudioSR_versatile_audio_super_resolution|AudioSR]]
