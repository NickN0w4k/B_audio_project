---
title: "master_me"
tags: [quelle, tool, mastering, referenzfrei, livestream, open-source]
created: 2026-04-29
---

# master_me

- **GitHub:** https://github.com/trummerschlunk/master_me
- **Lizenz:** GPL3
- **Typ:** Automatisches Live-Mastering Plugin
- **Formate:** CLAP, VST, VST3, AU, LV2, JACK Standalone

## Überblick
master_me ist ein kostenloses Open-Source-Audio-Plugin für automatisches Mastering in Live-Streaming-Situationen. Entwickelt von Berliner Mastering-Engineer Klaus Scheuermann (2020, während Covid-Lockdowns). 2022 gefördert vom Prototype Fund (BMBF).

**Wichtig:** Nicht für Offline-Musik-Mastering gedacht — "Your art deserves closer, offline attention."

## Signalfluss
1. **Pre-processing:** Gain, Mono, Phase, Stereo-Correct
2. **Gate:** Noise Gate (Threshold, Attack, Release)
3. **EQ:** Highpass, Tilt-EQ, Side-EQ (Stereo-Width)
4. **Leveler:** Automatische Lautstärkeanpassung an Target-Loudness (LUFS)
5. **Knee Compressor:** Mid-Side Kompressor (analog: Manley Variable MU, Vertigo VSC-2)
6. **Multiband Mid/Side Compressor:** 8 Frequenzbänder, interpolierte Parameter
7. **Limiter:** Sound-Shaping Limiter (analog: Chandler TG-1, UREI 1178)
8. **Brickwall:** Protection Limiter, kein Overshoot über Ceiling

## Kernfeatures
- **Zero Latency:** Echtzeit-fähig
- **Easy + Expert Mode:** Zwei GUI-Tiefen
- **Target Loudness:** -18 LUFS (Video), -14 LUFS (Podcast), -23 LUFS (EBU Broadcast)
- **Stereo-Correct:** Custom Modul für CCC VOC — erkennt Phasenprobleme und korrigiert
- **DSP in Faust** geschrieben, GUI/Plugin via DPF (DISTRHO Plugin Framework)

## Relevanz
Einziges Tool in der Sammlung, das explizit für Live-Szenarien designed ist. Kein ML, reines algorithmisches DSP — komplementär zu NN-basierten Ansätzen.
---
## 🔗 Verwandt
- [[MOC_Mastering|🗺️ MOC: Mastering]]
- [[06_Referenzfreies_Mastering_und_Alternativen|Referenzfreies Mastering und Alternativen]]
