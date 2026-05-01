---
title: "Paper: A Fourier Explanation of AI-music Artifacts"
tags: [quelle, paper, artefakt, fourier, detektion]
created: 2026-04-29
---

# Paper: A Fourier Explanation of AI-music Artifacts

- **arXiv:** https://arxiv.org/abs/2506.19108
- **Autoren:** Darius Afchar, Gabriel Meseguer-Brocal, Kamil Akesbi, Romain Hennequin
- **Eingereicht:** 23. Juni 2025
- **Akzeptiert:** ISMIR 2025
- **Lizenz:** CC BY-NC-SA 4.0
- **Typ:** Theoretische Analyse + KI-Musik-Detektion

## Abstract
Dieses Paper ist der theoretische Unterbau für die Erkennung von KI-generierter Musik. Es analysiert Deconvolution-Module (die in fast allen generativen Modellen verwendet werden) und beweist mathematisch, dass deren Ausgaben **systematische Frequenzartefakte** erzeugen — kleine, aber charakteristische Spektral-Peaks.

## Kernergebnisse
1. **Checkerboard-Artefakte sind architektur-bedingt**, nicht trainings-bedingt. Die Deconvolution-Operation erzeugt sie zwangsläufig.
2. **Einfaches, interpretierbares Detektionskriterium:** Die Autoren schlagen eine Fourier-basierte Methode vor, die >99% Genauigkeit bei der Erkennung KI-generierter Musik erreicht.
3. **Validierung:** Getestet auf Open-Source-Modelle UND kommerzielle Generatoren (Suno, Udio).
4. **Parallele zu Bildern:** Analog zum bekannten Checkerboard-Artefakt in Bildgeneratoren, aber hier auf Audio-Spektrogramme angewendet.

## Relevanz für die Pipeline
Dieses Paper ist fundamental: es erklärt **warum** KI-Musik überhaupt erkennbare Artefakte hat und liefert die theoretische Grundlage für Detektion. Gleichzeitig zeigt es, dass diese Artefakte potenziell durch geschicktere Architektur-Designs vermieden werden könnten.

## Bezug zu anderen Quellen
- Verwandt mit Quelle 1 (sangarshanan: AI music detection with checkerboard artifacts)
- Erklärt die Artefakte, die AudioSR/VoiceFixer etc. restaurieren sollen

## Zitat
```bibtex
@article{afchar2025fourier,
  title={A Fourier Explanation of AI-music Artifacts},
  author={Afchar, Darius and Meseguer-Brocal, Gabriel and Akesbi, Kamil and Hennequin, Romain},
  journal={arXiv preprint arXiv:2506.19108},
  year={2025},
  note={Accepted at ISMIR 2025}
}
```
---
## 🔗 Verwandt
- [[MOC_Artefakte|🗺️ MOC: KI-Audio-Artefakte]]
- [[05_Checkerboard_und_Fourier_Artefakte|Checkerboard und Fourier-Artefakte]]
