---
title: "Tab 1"
tags: [quelle, notebooklm, projektplan, pipeline, architektur]
created: 2026-04-29
---

Tab 1
Projektplan: KI-Musik-Restauration – Architektur & Pipeline-Design
1. Einführung und Zielsetzung
Das Ziel dieses Projekts ist die Implementierung einer hochgradig modularen DSP-Pipeline zur Überwindung des „Uncanny Valley“ von KI-generiertem Audio. Der technologische Ansatz basiert auf dem Paradigma des „Musikalischen Re-Ampings“: Wir betrachten die Rohausgabe generativer Modelle (wie Suno oder Udio) nicht als finales Produkt, sondern als technisch mangelhaftes Demo eines „Session-Musikers“. Diese Perspektive ist entscheidend, da KI-Signale systematische Degradationen enthalten, die durch herkömmliches Mastering – insbesondere durch Summendynamikbearbeitung – drastisch verstärkt würden.
Zwingende Voraussetzung für professionelle High-Fidelity-Resultate ist die Entkopplung der Restaurationsschritte vom Mastering. Erst wenn die spektralen und zeitlichen Artefakte auf Stem-Ebene isoliert und behoben wurden, darf das Signal in eine finale Dynamikkette überführt werden.
2. Analyse der KI-Artefakte (Ätiologie)
Die folgende Tabelle klassifiziert die physikalischen Ursachen der Signaldegradation, basierend auf aktuellen Analysen der Fourier-Eigenschaften generativer Architekturen:
Artefakt-Typ
	
Signaltheoretische Ursache
	
Akustische Manifestation


High-Frequency Rolloff
	
Drastische Bitraten-Reduktion; interner Tiefpassfilter (oft bei 16 kHz) zur Senkung der Inferenzlast.
	
Dumpfes, lebloses Klangbild; Fehlen der psychoakustischen „Air“-Frequenzen; mangelnde Transparenz.


Checkerboard-Muster (Spectral Peaks)
	
Stride-Kernel-Mismatch in Transposed Convolutions; asymmetrische Überlappungen beim Upsampling im Decoder.
	
Systematische spektrale Spitzen; hochfrequenter digitaler Schleier („Digital Haze“) über dem Gesamtsignal.


Metallische Resonanzen (Phase Distortion)
	
Inkohärente Phasenlage durch fehlerhafte Magnitude-zu-Phase-Schätzung (Griffin-Lim) oder Phase Wrapping.
	
„Unterwasser“-Klang; metallisches Gurgeln („Swoosh“-Effekte) bei Becken, Hi-Hats und perkussiven Transienten.


Robotische Quantisierung
	
Mangelnde mikrodynamische Varianz; Average-Value Approximation der Trainingsdaten in neuronalen Vocodern.
	
Unnatürlicher Auto-Tune-Effekt; starre Formanten; emotionale Sterilität der vokalen Darbietung.


Mangelnde Mix-Dynamik
	
End-to-End-Generierung im latenten Raum führt zu „totkomprimierten“ Signalen ohne Makrodynamik.
	
Flaches Hörerlebnis; Fehlen der 3 kHz Präsenzanhebung; verstopftes („congested“) Klangbild in dichten Passagen.
3. Die Restaurations-Pipeline: Schritt-für-Schritt-Blueprint
3.1 Phase 1: Multispektrale Quellentrennung (MSS) Die Separation des Summensignals ist die Bedingung für jede chirurgische Korrektur. Ohne Quellentrennung führen Reparaturen in einem Frequenzband unweigerlich zu destruktiven Maskierungseffekten bei unbeteiligten Instrumenten.
Modellauswahl: Implementieren Sie den BS-RoFormer (Band-Split RoPE Transformer) oder UVR5 (mit Demucs v4 oder MDX-Net).
Strategie (MSR Challenge 2025): Orientierung am CP-JKU-Team-Ansatz mittels Curriculum-Learning:
Warm-Start: Initialisierung auf sauberen Stems.
Degradation-Lernen: Training auf künstlich verzerrten Signalen zur Artefakt-Resilienz.
Head-Expansion: Erweiterung der Extraktion auf bis zu 8 Stems (Vocals, Drums, Bass, Piano, Guitar, Other).
3.2 Phase 2: Spektrale Reinigung und Denoising
Zeitbereich-Filterung: Einsatz von DeepFilterNet zur Entfernung von Hiss und instationärem Rauschen. Dies vermeidet die bei spektraler Subtraktion üblichen „Musical Noise“-Artefakte.
Neuronale Rekonstruktion: Anwendung von Wave-U-Net zur Eliminierung des Digital Haze. Die Skip-Connections der Architektur bewahren dabei hochfrequente Phaseninformationen.
Dereverberation: Nutzung von Diffusionsmodellen (z. B. BUDDy) oder DeEcho-Algorithmen, um den „eingebackenen“ KI-Hall zu entfernen und trockene Signale für das Re-Amping zu gewinnen.
3.3 Phase 3: Bandbreitenerweiterung (Super-Resolution) KI-Modelle kappen Obertöne oft hart bei 16 kHz. Diese müssen generativ „halluziniert“ werden.
Pre-Processing: Implementieren Sie zwingend einen sauberen Low-Pass-Filter bei ca. 14 kHz vor dem Upscaling, um DDIM-Sampling-Konfusionen durch Artefakte nahe der Grenzfrequenz zu vermeiden.
Modelle: Einsatz von AudioSR (Latent Diffusion) oder dem Apollo-Modell (Band-Sequence Modeling). Für High-End-Anwendungen (44.1/48 kHz) ist der Einsatz von A2SB (Audio-to-Audio Schrödinger Bridges) oder LatentFlowSR vorgeschrieben.
Post-Processing: Nutzen Sie das Replacement-Verfahren: Behalten Sie das originale Low-End bei und addieren Sie nur die neu generierten Frequenzen oberhalb des Cutoffs.
3.4 Phase 4: Vokale Humanisierung und Resynthese Behebung der robotischen Stimmcharakteristik durch gezielte DSP-Eingriffe.
Vocal Naturalizer (ComfyUI_MusicTools):
Pitch Humanization: Injektion eines 4,5 Hz Vibratos (max. 0,2 % Variation).
Formant-Variation: Belebung der Klangfarbe zwischen 200 und 3000 Hz.
Quantisierungsmaskierung: Hinzufügen von 0,2 % geformtem Rauschen (1-4 kHz) zur Verdeckung von Treppenstufen-Effekten.
Differential Smoothing: Anwendung eines 50-Hz-Tiefpassfilters auf das differenzielle Signal, um abrupte Pitch-Übergänge zu glätten.
Neuronale Resynthese: Kompletter Ersatz des fehlerhaften Mel-Spektrogramms durch phasenbewusste Vocoder wie FA-GAN (mit RI-Loss) oder BigVGAN.
Polyphonie: Bei Chören oder mehrstimmigem Gesang ist das DisCoder-Modell (430M Parameter) für eine artefaktfreie Rekonstruktion einzusetzen.
3.5 Phase 5: Rekonstruktion der Dynamik und Mixing
Dynamic Range Expansion: Anwendung von Inverse Dynamic Range Compression (DRC), um die Makrodynamik totkomprimierter Signale wiederherzustellen.
Chirurgisches EQing: Nutzung der Pedalboard-Bibliothek für eine gezielte Präsenzanhebung bei 3 kHz. Dies kompensiert die spektralen Lücken, die durch die Durchschnittswert-Approximation der KI-Modelle entstehen.
4. Modulares Finales Mastering
Nach der Restauration stehen zwei Wege offen:
Referenzbasiert: Nutzung von Matchering 2.0, um RMS, Frequenzgang und Stereobreite an einen Ziel-Track anzupassen.
Referenzfrei (Generative EQ): Einsatz von BABE-2 zur „blinden“ Korrektur der spektralen Balance durch interne Priors.
Mastering-Chain DSP: Zentrales Element ist der Hyrax Limiter. Dieser arbeitet als Look-Ahead-System und nutzt einen Butterworth-Filter zur Glättung der Hüllkurve. Dies ermöglicht maximalen Pegel ohne die für Standard-Limiter typischen harmonischen Verzerrungen bei KI-Material.
5. Evaluierung und Qualitätskontrolle
Die Erfolgsmessung der Pipeline erfolgt über drei Metriken:
FAD (Fréchet Audio Distance): Der wichtigste Indikator für die allgemeine Natürlichkeit und statistische Ähnlichkeit zu realen Studioaufnahmen.
LSD (Log-Spectral Distance): Zur Validierung der Genauigkeit der Super-Resolution (Phase 3).
SDR (Signal-to-Distortion Ratio): Maß für die Trennungsschärfe und das Fehlen von Artefakten nach der Quellentrennung.
6. Technische Implementierungshinweise
Software-Stack: Python (libsndfile, librosa, Pedalboard, TorchFX für GPU-beschleunigtes DSP).
Hardware: Aufgrund der Rechenlast von BS-RoFormer und Diffusionsmodellen (AudioSR) ist eine GPU mit mindestens 8-12 GB VRAM zwingend erforderlich (z. B. NVIDIA RTX 4090 oder A100).
Workflow: Implementierung in Node-basierten Umgebungen wie ComfyUI_MusicTools zur flexiblen Orchestrierung der Restaurations-Module.
---
## 🔗 Verwandt
- [[MOC_Pipeline|🗺️ MOC: Pipeline & Architektur]]
- [[07_Lastenheft_Pipeline_Architektur|Lastenheft: Pipeline-Architektur]]
