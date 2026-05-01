---
title: "Paper: APNet2 — High-quality and High-efficiency Neural Vocoder"
tags: [quelle, paper, vocoder, apnet, neural-synthesis]
created: 2026-04-29
---

# Paper: APNet2 — High-quality and High-efficiency Neural Vocoder

- **arXiv:** https://arxiv.org/abs/2311.11545
- **Autoren:** Hui-Peng Du, Ye-Xin Lu, Yang Ai, Zhen-Hua Ling
- **Eingereicht:** 20. November 2023
- **Typ:** Neural Vocoder (Amplitude + Phase Spectrum Prediction)

## Abstract
Nachfolgearbeit von APNet (Quelle 8). Das Original-APNet konnte Sprache mit HiFi-GAN-vergleichbarer Qualität generieren, war aber auf 16kHz und 5ms Frame-Shift beschränkt.

**APNet2** bringt folgende Verbesserungen:
- **ConvNeXt v2** als Backbone für Amplituden- und Phasenprädiktion (statt einfaches CNN)
- **Multi-Resolution Discriminator (MRD)** in GAN-Losses
- **Konfiguration:** 22.05kHz Sample-Rate, 256-Punkt Frame-Shift (~11.6ms)

## Ergebnisse
- Übertrifft APNet und Vocos in Sprachqualität
- Vergleichbar mit HiFi-GAN und iSTFTNet bei deutlich höherer Inferenzgeschwindigkeit
- Frame-Level-Operationen bleiben → schneller als autoregressive Vocoder

## Relevanz
Wichtige Evolution des APNet-Ansatzes. Zeigt, dass direkte Amplituden-/Phasenprädiktion ein konkurrenzfähiges Paradigma für Vocoder ist — relevant als Endstufe in Restaurierungs-Pipelines.

## Zitat
```bibtex
@article{du2023apnet2,
  title={APNet2: High-quality and High-efficiency Neural Vocoder...},
  author={Du, Hui-Peng and Lu, Ye-Xin and Ai, Yang and Ling, Zhen-Hua},
  journal={arXiv preprint arXiv:2311.11545},
  year={2023}
}
```
---
## 🔗 Verwandt
- [[MOC_Vocoder|🗺️ MOC: Neuronale Vocoder]]
- [[08_APNet|APNet]]
