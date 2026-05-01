---
title: "DisCoder"
tags: [quelle, tool, vocoder, neural-synthesis, audio-restoration]
created: 2026-04-29
---

# DisCoder

- **GitHub:** https://github.com/Chen-Julio/DisCoder
- **Typ:** Diskrepanz-Encoder für Audio-Restaurierung

## Überblick
DisCoder ist ein Framework, das die Diskrepanz zwischen einem verlustbehafteten und einem Referenz-Audiosignal lernt. Anstatt das vollständige Audiosignal zu rekonstruieren, kodiert DisCoder nur den Unterschied (die Diskrepanz) zwischen Eingabe und Ziel — ein effizienterer Ansatz für Audio-Restaurierung.

## Kernfeatures
- **Diskrepanz-basiertes Lernen:** Lernt nur den Unterschied zwischen verlustbehaftetem und Target-Audio
- **Effiziente Repräsentation:** Weniger Parameter nötig, da nur Delta kodiert wird
- **Anwendbar auf:** Audio-Super-Resolution, Denoising, Restaurierung
- **Modularer Ansatz:** Kann mit bestehenden Vocoder-Modellen kombiniert werden

## Architektur
- Encoder extrahiert Diskrepanz-Features
- Decoder rekonstruiert das Delta-Signal
- Addition mit Eingabe → restauriertes Audio

## Relevanz für AI Audio Restoration
Interessanter komplementärer Ansatz zu Modellen wie AudioSR oder VoiceFixer: statt das gesamte Signal zu generieren, wird nur die "fehlende" Information ergänzt. Potenziell effizienter und artefaktfreier.
---
## 🔗 Verwandt
- [[MOC_Vocoder|🗺️ MOC: Neuronale Vocoder]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]]
