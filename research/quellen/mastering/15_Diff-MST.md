---
title: "Diff-MST: Differentiable Mastering Signal Transformer"
tags: [quelle, tool, mastering, differentiable, signal-processing]
created: 2026-04-29
---

# Diff-MST: Differentiable Mastering Signal Transformer

- **GitHub:** https://github.com/pratiky900/Diff-MST
- **Typ:** Differentielles Mastering-Modell

## Überblick
Diff-MST (Differentiable Mastering Signal Transformer) ist ein Framework für automatisiertes Audio-Mastering mittels differentieller DSP-Module. Anstatt reine Deep-Learning-End-to-End-Ansätze zu verwenden, kombiniert Diff-MST klassische DSP-Effektketten (EQ, Kompressor, Limiter) mit neuronalen Netzwerken, die die Parameter dieser Effekte lernen.

## Kernfeatures
- **Differentielle DSP-Kette:** EQ, Kompressor, Limiter als differentielle Module
- **Neural Parameter Prediction:** NN sagt DSP-Parameter voraus
- **Referenz-basiert:** Lernen von Mastering-Entscheidungen aus Referenz-Tracks
- **Interpretierbarkeit:** Da echte DSP-Module verwendet werden, sind die gelernten Parameter (EQ-Kurve, Kompressor-Settings etc.) direkt interpretierbar

## Architektur
1. Analysiere Target + Reference Audio
2. Neuronales Netz sagt DSP-Parameter voraus
3. Differentielle DSP-Kette wendet die Effekte an
4. Loss-Funktion vergleicht Output mit Referenz

## Relevanz
Verbindet die Welten von klassischem Audio-Mastering und Deep Learning — ein Ansatz, der Transparenz und Kontrolle bietet, die reinen NN-Ansätzen fehlen.
---
## 🔗 Verwandt
- [[MOC_Mastering|🗺️ MOC: Mastering]]
- [[06_Referenzfreies_Mastering_und_Alternativen|Referenzfreies Mastering und Alternativen]]
