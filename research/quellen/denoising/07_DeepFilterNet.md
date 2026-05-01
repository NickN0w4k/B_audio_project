---
title: "DeepFilterNet: Low Complexity Speech Enhancement for Full-Band Audio"
tags: [quelle, tool, denoising, speech-enhancement, deep-learning]
created: 2026-04-29
---

# DeepFilterNet: Low Complexity Speech Enhancement for Full-Band Audio

- **GitHub:** https://github.com/Rikorose/DeepFilterNet
- **Paper v1:** https://arxiv.org/abs/2110.05588
- **Paper v2:** https://arxiv.org/abs/2205.05474
- **Paper v3:** https://arxiv.org/abs/2305.08227
- **Autor:** Hendrik Schröter et al.
- **Lizenz:** MIT
- **Typ:** Speech Enhancement / Noise Suppression (48kHz Full-Band)

## Überblick
DeepFilterNet ist ein Framework für Echtzeit-Sprachverbesserung bei 48kHz Full-Band-Audio. Kerninnovation: "Deep Filtering" — eine günstige, erlernbare Filter-Operation im Zeit-Frequenz-Bereich, die als Ersatz für teure Masking-Operationen dient.

## Architektur
- **Encoder:** Extrahiert Features aus dem Noisy-Signal
- **Deep Filtering:** Ersetzt traditionelle Masking durch erlernbare Filter-Kernel im STFT-Bereich
- **Decoder:** Rekonstruiert sauberes Signal

## Kernfeatures
- **48kHz Full-Band:** Keine Abstriche bei der Sample-Rate
- **Low Complexity:** Für Embedded-Geräte und Echtzeit
- **Rust-Binary:** `deep-filter` als standalone CLI (keine Python-Dependencies)
- **LADSPA Plugin:** Integration in PipeWire für systemweites Real-Time Noise Suppression
- **Post-Filter:** Optionales Oversubtraction für sehr laute Störgeräusche
- **Versionen:** DeepFilterNet v1, v2 (Echtzeit auf Embedded), v3 (Perceptually Motivated)

## Quick Start
```bash
# Pre-compiled binary (kein Python nötig)
deep-filter noisy_audio.wav -o out/

# Python
from df import enhance, init_df
model, df_state, _ = init_df()
enhanced_audio = enhance(model, df_state, noisy_audio)
```

## Training
- Rust-basierte Data-Augmentation (libDF)
- HDF5-Datasets für Speech, Noise, RIR
- Unterstützt Multi-Dataset-Training mit Sampling-Faktoren

## Relevanz
Eines der wenigen Modelle, die 48kHz Full-Band in Echtzeit unterstützen — entscheidend für produktive Audio-Restaurierung. Deep Filtering als Architektur-Paradigma ist ein interessanter Gegenentwurf zu reinen Masking- oder Mapping-Ansätzen.
---
## 🔗 Verwandt
- [[MOC_Denoising|🗺️ MOC: Denoising & Restaurierung]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]]
