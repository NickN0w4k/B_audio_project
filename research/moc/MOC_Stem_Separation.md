---
title: "🗺️ MOC: Stem Separation / Quellentrennung"
tags: [moc, stem-separation, quellentrennung, mss]
created: 2026-04-30
---

# 🗺️ Stem Separation / Quellentrennung

> **Kernthese:** Quellentrennung (Music Source Separation, MSS) ist der erste und entscheidende Schritt in jeder KI-Audio-Restauration – bevor Vocoder oder Mastering greifen, müssen die Stems sauber getrennt sein.

---

## 📖 Synthese-Artikel

- [[02_Quellentrennung_als_Fundament|Quellentrennung als Fundament]] — Warum MSS der erste Schritt ist

## 🔬 Quellen

### Modelle & Frameworks
- [[05_demucs|Demucs (HTDemucs)]] — Facebooks Hybrid-Transformer-Modell, State-of-the-Art für MSS
- [[13_BS-RoFormer|BS-RoFormer]] — Band-Split RoFormer, alternative Architektur mit Band-Split-Aufmerksamkeit
- [[14_bs-roformer-infer|bs-roformer-infer]] — Inferenz-Wrapper für BS-RoFormer

### Studio-Outputs
- [[14_Music_Source_Separation_MSS|Music Source Separation (MSS)]] — Studio-Text-Note zum Thema

## 🔗 Verwandte Konzepte

- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder]] — Der nächste Schritt nach der Trennung
- [[04_Modulare_Pipeline_ohne_Mastering|Modulare Pipeline]] — Wie MSS in die Pipeline eingebettet wird
- [[07_Lastenheft_Pipeline_Architektur|Lastenheft Pipeline]] — Architektur-Blueprint mit MSS als Phase 1

## 🏷️ Tags

`#stem-separation` `#mss` `#quellentrennung` `#demucs` `#bs-roformer`