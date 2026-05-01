---
title: "Neuronale Vocoder und Signalrestaurierung"
tags: [doku, tool, vocoder, restoration, audio-sr, neural-synthesis, bigvgan, hifi-gan]
created: 2026-04-29
---

# Neuronale Vocoder und Signalrestaurierung

## Einleitung

Subtraktive Methoden — Equalizer, spektrale Subtraktion, Wiener-Filter — können die strukturellen Defizite generativer Audiodaten nicht beheben, da sie keine verlorenen Informationen zurückgewinnen, sondern lediglich Amplituden manipulieren. Die moderne Audiorestaurierung basiert daher auf generativen Verfahren: Neuronale Netzwerke synthetisieren verlorene oder beschädigte Audioinformationen statistisch fundiert neu und „halluzinieren" das wahrscheinlichste hochauflösende Signal, das dem beschädigten Input zugrunde liegen könnte.

Dieser Artikel analysiert die wichtigsten Architekturen — von Latent-Diffusion über GAN-Vocoder bis hin zu Deep Filtering — und beleuchtet ihre jeweiligen Stärken, Grenzen und Einsatzgebiete innerhalb einer Restaurations-Pipeline.

## Hauptinhalt

### Diffusionsbasierte Super-Resolution: AudioSR

AudioSR (Versatile Audio Super-Resolution at Scale) ist ein generatives Modell basierend auf Latent Diffusion Models (LDM). Es kann Audio beliebiger Art mit einer Eingangsbandbreite zwischen 2 kHz und 16 kHz auf eine hochauflösende Ausgabe mit 24 kHz Bandbreite und 48 kHz Samplingrate hochskalieren.

**Mechanismus:** Das beschnittene Audiosignal wird in einen latenten Raum kodiert. Durch einen DDIM-Sampling-Prozess (50–100 Schritte) lernt das Netzwerk, Rauschen iterativ in kohärente, hochfrequente akustische Informationen zu überführen, die konditioniert auf die niederfrequenten Eigenschaften des Quellsignals generiert werden.

**Stärke:** Das Replacement-basierte Post-Processing — die originären niedrigen Frequenzen bleiben unangetastet, nur die halluzinierten Frequenzen oberhalb des Cutoffs werden phasengerecht addiert.

**Grenze:** AudioSR wurde primär auf Signale trainiert, die durch ideale Low-Pass-Filter beschnitten wurden. MP3-Kompression oder KI-Artefakte verursachen „Spektrogramm-Löcher" nahe der Grenzfrequenz, die den Diffusionsprozess verwirren können. Als Workaround empfiehlt sich ein sauberer Low-Pass-Filter bei ca. 14 kHz vor dem Upscaling. Zudem besteht Schwierigkeit, eine konsistente Phasenkohärenz und niederfrequente Stabilität aufrechtzuerhalten — die harmonische Modellierung im Bassbereich kann bei vollständigen Mischungen zu Ungleichgewichten führen.

### Band-Sequence Modeling: Apollo

Das Apollo-Modell (ICASSP 2025) überwindet die Schwächen spektrogrammbasierter Diffusion durch explizite Aufteilung des Frequenzspektrums. Ein Frequency Band Split Module modelliert die temporalen und spektralen Beziehungen zwischen verschiedenen Frequenzbändern separat. Dadurch wird vermieden, dass die Vorhersage hochfrequenter Obertöne die Integrität fundamentaler Bassfrequenzen stört. Apollo übertrifft bestehende SR-GAN-Architekturen signifikant und ist besonders effektiv, wenn mehrere Instrumente gleichzeitig verarbeitet werden müssen.

### GAN-basierte Vocoder: BigVGAN, HiFi-GAN und VoiceFixer

**HiFi-GAN** ist der etablierte Standard-Vocoder. Kern-Erkenntnis: Die Modellierung periodischer Muster des Audiosignals ist entscheidend für die Sample-Qualität. HiFi-GAN generiert 22,05 kHz Audio mit 167,9-facher Echtzeitgeschwindigkeit auf einer V100 GPU. Drei Generator-Varianten (V1, V2, V3) bieten Kompromisse zwischen Qualität und Geschwindigkeit.

**BigVGAN** (NVIDIA) erweitert HiFi-GAN um Anti-Aliased Activation mit benutzerdefinierten CUDA-Kerneln (1,5–3x schneller auf A100) und einen Multi-Scale Sub-Band CQT Discriminator. Es unterstützt 44 kHz mit bis zu 512x Upsampling-Ratio und bietet 122M Parameter für höchste Qualität.

**VoiceFixer** baut auf neuronalen Vocodern auf und ist darauf trainiert, Hintergrundrauschen, extremen Nachhall, niedrige Auflösungen (bis 2 kHz) und schweres Clipping in einem einzigen, vereinheitlichten Modell zu beheben. Es rekonstruiert die Stimme holistisch statt nur Störsignale zu filtern. In Mean-Opinion-Score-Metriken übertrifft VoiceFixer reine Entrauschungsmodelle deutlich.

**Grenze:** Das adversariale Training limitiert die Modelleffizienz. Ansätze wie FreeGAN versuchen, die Notwendigkeit des GAN-Trainings durch serielle Amplituden-Phasen-Vorhersage-Frameworks zu eliminieren.

### Amplituden-Phasen-prädiktion: APNet und APNet2

APNet (All-Frame-Level Neural Vocoder) verfolgt einen grundlegend anderen Ansatz: Statt autoregressiv oder iterativ zu generieren, sagt es Amplituden- und Phasenspektren direkt auf Frame-Ebene voraus. Ein Amplitude Spectrum Predictor (ASP) und ein Phase Spectrum Predictor (PSP) arbeiten parallel. Die Rekonstruktion erfolgt via ISTFT aus den kombinierten Spektren.

**Vorteil:** Ca. 8x schneller als HiFi-GAN v1 auf CPU bei vergleichbarer Qualität.

**Grenze:** Original-APNet ist auf 16 kHz Samplingrate beschränkt.

**APNet2** bringt ConvNeXt v2 als Backbone, Multi-Resolution Discriminator und 22,05 kHz / 256-Punkt Frame-Shift. Es übertrifft APNet und Vocos, ist vergleichbar mit HiFi-GAN, aber deutlich schneller in der Inferenz — ein konkurrenzfähiges Paradigma für Vocoder-Endstufen.

### Neural Audio Codecs: DisCoder

DisCoder (ETH DISCO Lab, ICASSP 2025) ist ein neuronaler Encoder-Decoder-Vocoder mit 430 Millionen Parametern, dediziert für polyphone Musik bei 44,1 kHz. Statt direkt Mel→Audio zu wandeln (wie HiFi-GAN), transformiert DisCoder das Mel-Spektrogramm zuerst in eine niederdimensionale Repräsentation, die am Descript Audio Codec (DAC)-Latent-Raum ausgerichtet ist. Ein feingetunter DAC-Decoder rekonstruiert das Audio.

**Stärke:** State-of-the-art Polyphonie-Klarheit, glättet formantschiebende „Chipmunk"-Artefakte und unsaubere Tonhöhen. Validierung via ViSQOL.

**Einsatzgebiet:** Chöre, mehrstimmiger Gesang, komplexe instrumentale Passagen, bei denen reine Sprach-Vocoder an ihre Grenzen stoßen.

### Deep Filtering im Zeitbereich: DeepFilterNet

DeepFilterNet verfolgt einen fundamental anderen Ansatz: Statt im Frequenzbereich (Spektrogramm) zu arbeiten, nutzt es tiefe Filterstrukturen im Zeitbereich, um periodische Komponenten zu verstärken. Die Entkopplung von Zeit- und Frequenzbereich reduziert die Komplexität drastisch.

**Stärke:** 48 kHz Full-Band-Audio, Echtzeitfähigkeit, extrem niedrige Latenz. Erweitert mit Rust-Binary, LADSPA-Plugin für PipeWire-Integration und Post-Filter für Oversubtraction. Verfügt über Versionen v1, v2 (Echtzeit auf Embedded-Geräten) und v3 (Perceptually Motivated).

**Einsatzgebiet:** Gezielte Rauschunterdrückung bei Sprachsignalen ohne spektrale Artefakte — die isolierte Stimme nimmt den gefürchteten metallischen Roboterklang nicht an. Ideal als Vorstufe vor nachgeschalteter Resynthese.

### Vergleich der Architekturen

| Architektur | Primärer Arbeitsbereich | Kernmechanismus | Stärke | Grenze |
|-------------|------------------------|-----------------|--------|--------|
| AudioSR | Mel-Spektrogramm | Latent Diffusion (DDIM) | Universelles Upscaling 2–48 kHz | Phasenkohärenz bei Mischungen |
| Apollo | Frequenzband-Split | Band-Sequence Modeling | Phasenkohärente MusiksR | Neueres Modell, weniger Community |
| HiFi-GAN | Zeit-/Frequenzbereich | GAN (periodic patterns) | Geschwindigkeit, Etabliertheit | Upsampling-Aliasing |
| BigVGAN | Zeit-/Frequenzbereich | GAN + Anti-Aliased Activation | 44 kHz, CUDA-optimiert | Ressourcenbedarf (122M Params) |
| VoiceFixer | Zeit-/Frequenzbereich | Neuronaler Vocoder (holistisch) | Multi-Degradation in einem Modell | Sprachfokus, weniger Musik |
| APNet2 | Amplituden + Phasen | Frame-Level Prediction | 8x schneller als HiFi-GAN | Sprachfokus |
| DisCoder | Codec-Latent | GAN + DAC-Decoder | Polyphone Musik, 430M Params | Hoher Ressourcenbedarf |
| DeepFilterNet | Zeitbereich | Deep Filtering | Echtzeit, 48 kHz, keine metallischen Artefakte | Nur Entrauschung, keine Resynthese |

## Fazit

Die Landschaft neuronaler Vocoder und Restaurierungsmodelle bietet für jeden Artefakt-Typ ein spezialisiertes Werkzeug: AudioSR und Apollo für die Bandbreitenerweiterung, BigVGAN und HiFi-GAN für hochauflösende Synthese, VoiceFixer für holistische Sprachrestaurierung, APNet2 für effiziente Amplituden-Phasen-Prediction, DisCoder für polyphone Musik und DeepFilterNet für latenzarmes Echtzeit-Denoising. Die Kunst der Pipeline-Orchestrierung besteht darin, das richtige Modell für den richtigen Artefakt-Typ auf dem richtigen Stem einzusetzen — denn kein einzelnes Modell löst alle Probleme.

## Querverweise

- [[01_KI_Audio_Artefakte_und_ihre_Ursachen|Artikel 1: KI-Audio-Artefakte und ihre Ursachen]] — Die Artefakte, die diese Modelle adressieren
- [[02_Quellentrennung_als_Fundament|Artikel 2: Quellentrennung als Fundament]] — Die Isolierung der Stems vor der Restaurierung
- [[04_Modulare_Pipeline_ohne_Mastering|Artikel 4: Modulare Pipeline ohne Mastering]] — Wie diese Modelle in ComfyUI_MusicTools orchestriert werden
- [[05_Checkerboard_und_Fourier_Artefakte|Artikel 5: Checkerboard und Fourier-Artefakte]] — Die architektur-bedingten Artefakte, die Vocoder erzeugen oder vermeiden
---
## 🔗 Verwandt
- [[MOC_Pipeline|🗺️ MOC: Pipeline & Architektur]]
- [[00_HOME|🏠 Home]]
- [[MOC_Vocoder|🗺️ MOC: Vocoder]]
