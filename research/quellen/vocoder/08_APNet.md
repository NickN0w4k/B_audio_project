---
title: "APNet: All-Frame-Level Neural Vocoder"
tags: [quelle, tool, vocoder, neural-synthesis, apnet]
created: 2026-04-29
---

# APNet: All-Frame-Level Neural Vocoder

- **GitHub:** https://github.com/YangAi520/APNet
- **Paper:** https://arxiv.org/abs/2305.07952
- **Autoren:** Yang Ai, Zhen-Hua Ling
- **Typ:** Neural Vocoder (Amplitude + Phase Spectrum Prediction)

## Überblick
APNet ist ein Neural Vocoder, der Sprache aus akustischen Features rekonstruiert, indem er Amplituden- und Phasenspektren direkt vorhersagt — statt das übliche iterative/autoregressive Vorgehen. Kernidee: Frame-Level-Operationen statt Sample-Level → ca. 8x schneller als HiFi-GAN v1 auf CPU bei vergleichbarer Qualität.

## Architektur
- **Amplitude Spectrum Predictor (ASP):** Residuales CNN, sagt Frame-Level Log-Amplitudenspektren aus akustischen Features voraus
- **Phase Spectrum Predictor (PSP):** Residuales CNN + zwei parallele lineare Conv-Layer → Phasenberechnungsformel
- **Rekonstruktion:** ISTFT aus kombinierten Amplituden + Phasen-Spektren

## Loss-Funktionen (Multi-Level)
1. Amplitude Mean Square Error
2. Phase Anti-Wrapping Error
3. Short-Time Spectral Inconsistency Error
4. Time Domain Reconstruction Error

## Ergebnisse
- **~8x schneller als HiFi-GAN v1** auf CPU (durch Frame-Level-Operationen)
- Vergleichbare Sprachqualität wie HiFi-GAN v1
- Bessere Qualität als gleich schnelle Modelle

## Einschränkung
- Aktuelle Version: nur 16kHz Sampling-Rate

## Zitat
```bibtex
@article{ai2023apnet,
  title={APNet: An All-Frame-Level Neural Vocoder...},
  author={Ai, Yang and Ling, Zhen-Hua},
  journal={IEEE/ACM TASLP},
  year={2023}
}
```
---
## 🔗 Verwandt
- [[MOC_Vocoder|🗺️ MOC: Neuronale Vocoder]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]]
