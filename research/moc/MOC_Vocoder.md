---
title: "🗺️ MOC: Neuronale Vocoder"
tags: [moc, vocoder, neural-synthesis, audio-processing]
created: 2026-04-30
---

# 🗺️ Neuronale Vocoder & Signalrestaurierung

> **Kernthese:** Neuronale Vocoder rekonstruieren und verbessern KI-degradierte Audiosignale – sie sind das Herzstück der Signalrestaurierung nach der Quellentrennung.

---

## 📖 Synthese-Artikel

- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]] — AudioSR, VoiceFixer, BigVGAN, APNet2 & Co.

## 🔬 Quellen

### GAN-basierte Vocoder
- [[06_BigVGAN|BigVGAN]] — NVIDIA, Universal Vocoder mit großem Training
- [[12_HiFi-GAN|HiFi-GAN]] — Effiziente GAN-basierte Sprachsynthese, Grundlage vieler Folgemodelle

### AMP/Phase-basierte Vocoder
- [[08_APNet|APNet]] — All-Frame-Level Vocoder
- [[25_APNet2_paper|APNet2 Paper]] — Weiterentwicklung: höherer Wirkungsgrad

### Super-Resolution & Restaurierung
- [[09_AudioSR_versatile_audio_super_resolution|AudioSR]] — Vielseitige Audio-Super-Resolution
- [[24_AudioSR_paper|AudioSR Paper]] — ArXiv-Paper zu AudioSR
- [[04_DisCoder|DisCoder (ETH-DISCO)]] — High-Fidelity Music Vocoder via Neural Audio Codecs
- [[16_DisCoder_Chen-Julio|DisCoder (Chen-Julio)]] — Diskrepanz-Encoder für Audio-Restaurierung

### Speech-Restaurierung
- [[10_voicefixer_general_speech_restoration|VoiceFixer]] — General Speech Restoration
- [[07_DeepFilterNet|DeepFilterNet]] — Low-Complexity Speech Enhancement

## 🔗 Verwandte Konzepte

- [[02_Quellentrennung_als_Fundament|Quellentrennung]] — Vocoder greifen nach der Stem-Trennung
- [[01_KI_Audio_Artefakte_und_ihre_Ursachen|KI-Audio-Artefakte]] — Was Vocoder reparieren sollen
- [[04_Modulare_Pipeline_ohne_Mastering|Modulare Pipeline]] — Vocoder als Phase 2 der Pipeline

## 🏷️ Tags

`#vocoder` `#neural-synthesis` `#gan` `#super-resolution` `#audio-processing`