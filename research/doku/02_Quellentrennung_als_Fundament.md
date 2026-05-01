---
title: "Quellentrennung als Fundament"
tags: [doku, pipeline, mss, demucs, bs-roformer, quellentrennung, stem-separation]
created: 2026-04-29
---

# Quellentrennung als Fundament

## Einleitung

Die effektive Behebung von KI-Audio-Artefakten in vollständigen Musikmischungen ist nahezu unmöglich, solange das Stereosignal als Ganzes bearbeitet wird. Wendet man einen Vocal Naturalizer auf den kompletten Track an, erhalten auch Gitarren und Synthesizer ein künstliches Vibrato. Wendet man AudioSR auf den Mix an, können die rekonstruierten Becken-Frequenzen zu einer Übersättigung im Sibilanten-Bereich der Stimme führen. Music Source Separation (MSS) — die algorithmische Zerlegung eines fertigen Audiomixes in seine instrumentalen Einzelbestandteile (Stems) — ist daher der zwingend erste Schritt jeder modernen Audiorestaurations-Pipeline.

Dieser Artikel analysiert die technologische Evolution der Quellentrennung, die Architektur der aktuellen State-of-the-Art-Modelle und die Metriken, mit denen ihre Qualität bewertet wird.

## Hauptinhalt

### Warum Quellentrennung unverzichtbar ist

KI-Artefakte sind phasenabhängig und überlagern spezifische Frequenzbänder. Ein Equalizer kann lediglich die Amplitude eines Frequenzbereichs verändern — er heilt nicht die zeitliche Inkohärenz des Signals. Da die Artefakte verschiedener Instrumente in unterschiedlichen Frequenzbändern und mit unterschiedlichen Phasenbeziehungen auftreten, würde ein destruktiver Filter auf das Summensignal unvermeidlich musikalisches Material anderer Instrumente beschädigen (Maskierungseffekt).

Erst durch die Isolierung der Stems gewinnt der Restaurateur die operative Freiheit, jedes Element gezielt zu behandeln: Vocals erhalten Resynthese, Drums erhalten Transienten-Wiederherstellung, und das Instrumental bekommt Super-Resolution — alles ohne gegenseitige Beeinträchtigung.

### Die evolutionäre Entwicklung der MSS-Modelle

#### Spleeter (2019) — Der Pionier mit Schwächen

Das von Deezer veröffentlichte Spleeter basiert auf einer U-Net-CNN-Architektur und operiert ausschließlich auf Frequenzrepräsentationen (Spektrogrammen). Mit bis zu 100-facher Echtzeitgeschwindigkeit war es ein Meilenstein der Zugänglichkeit. Für professionelle Restaurationszwecke reicht die Qualität jedoch nicht mehr: Starkes „Bleeding" (Gesangsfragmente auf der Schlagzeugspur und umgekehrt) und gravierende Phasenverluste machen den Sound schwammig. Die Entwicklung wurde 2022 eingestellt.

#### Demucs v4 (HT-Demucs) — Der aktuelle De-facto-Standard

Die von Meta AI entwickelte Demucs-Architektur hat MSS grundlegend verändert. HT-Demucs (Hybrid Transformer Demucs, v4) nutzt eine duale U-Net-Architektur mit Cross-Domain-Transformer zwischen Encoder und Decoder. Der entscheidende Fortschritt: Im Gegensatz zu Spleeter verarbeitet Demucs das Signal nicht nur im Frequenzbereich, sondern teilweise direkt in der rohen Wellenform (Time-Domain). Diese hybride Architektur bewahrt die wertvollen Phaseninformationen des Originalsignals nahezu perfekt — Transienten von Schlagzeugen bleiben scharf, und der Bassbereich verliert nicht an Definition.

**SDR-Ergebnis auf MUSDB HQ:** 9,00 dB (mit Fine-Tuning). Zum Vergleich: Wave-U-Net erreicht 3,2 dB, Spleeter 5,9 dB. Der Trade-off: HT-Demucs erfordert 6–8 GB VRAM und dedizierte GPU-Beschleunigung.

#### BS-RoFormer — Der Goldstandard der MSR Challenge 2025

Der Band-Split RoPE Transformer (BS-RoFormer) dominiert die akademische Landschaft und war maßgeblich für die Siegersysteme der ICASSP Music Source Restoration (MSR) Challenge 2025 verantwortlich. Die MSR Challenge geht über traditionelle Separationsaufgaben hinaus: Sie erkennt explizit, dass Mischungen keine einfachen linearen Summen sauberer Spuren sind, sondern komplexe, durch Effekte und Kompressionsartefakte degradierte Signale.

**Die Architektur-Neuerungen:**

1. **Band-Split-Modul:** Statt das gesamte Frequenzspektrum gleichmäßig durch ein neuronales Netz zu schleusen, zerlegt der BS-RoFormer das Spektrum in musikalisch sinnvolle, unterschiedlich breite, sich nicht überlappende Frequenzbänder. Hierarchische Transformer-Schichten analysieren Muster sowohl innerhalb eines einzelnen Bandes (Inner-band) als auch die Interaktionen zwischen verschiedenen Bändern (Inter-band).

2. **Rotary Position Embeddings (RoPE):** Da der Attention-Mechanismus von Natur aus positionsinvariant ist, injiziert RoPE zeitliche Informationen durch Rotationsmatrizen direkt in die Aufmerksamkeitsgewichte. Dies ermöglicht eine bisher unerreichte Genauigkeit bei der Maskenschätzung.

**Trainingsstrategie (CP-JKU-Ansatz):**
- **Stufe 1 (Warm-Start):** Fine-Tuning auf sauberen 4-Stem-Mischungen via LoRA.
- **Stufe 2 (Degradations-Lernen):** Training auf künstlich degradierte Mischungen mit gezielt hinzugefügten Verzerrungen, MP3-Kompression und unnatürlichem Hall.
- **Stufe 3 (Head Expansion):** Erweiterung auf 8 Stems bei eingefrorenem Backbone.

### SDR als Leitmetrik

Die Signal-to-Distortion Ratio (SDR) ist die zentrale objektive Metrik zur Bewertung der Quellentrennungsqualität. Sie vergleicht die Energie des gewollten Signals mit der Energie der Interferenz, des Rauschens und der Artefakte. Höhere SDR-Werte bedeuten sauberere Separation.

| Modell | SDR auf MUSDB HQ | Anmerkung |
|--------|-------------------|-----------|
| Wave-U-Net | 3,2 dB | Veraltet, Phasenverluste |
| Spleeter | 5,9 dB | Eingestellt, starkes Bleeding |
| Hybrid Demucs v3 | 7,7 dB | Solider Zwischenschritt |
| **HT-Demucs ft (v4)** | **9,0 dB** | Aktueller Standard |
| **BS-RoFormer** | **>9,0 dB** | Goldstandard, MSR Challenge |

### Praxis: Ultimate Vocal Remover (UVR5)

In der Open-Source-Community hat sich UVR5 als De-facto-Standard-Oberfläche etabliert. Es bündelt verschiedene Modelle (Demucs v4, MDX-Net, VR Architecture) und ermöglicht Kaskadierung: Erst Vocals vom Instrumental trennen, dann das Instrumental weiter zerlegen. UVR5 ist ausschließlich ein Separations-Tool — die perfekte Vorstufe für nachgeschaltete Restaurationswerkzeuge.

Im kommerziellen Bereich bietet LALAL.AI phasenakkurate Separation mit Null-Test-Garantie (die Summe der Stems löscht bei Phasenumkehr exakt das Originalsignal aus). AudioShake positioniert sich im Enterprise-Bereich für Dolby Atmos und immersive Formate.

## Fazit

Music Source Separation ist weit mehr als ein DJ-Tool — sie ist das chirurgische Besteck der Audio-Forensik. Ohne sie bleibt jede Restaurationsbemühung ein Kompromiss, da Maskierungseffekte auf dem Summensignal unvermeidlich sind. Die Evolution von Spleeter über Demucs zum BS-RoFormer hat die Trennqualität von 5,9 dB auf über 9 dB SDR gesteigert und ermöglicht erstmals forensisch saubere Stems, die für die nachfolgende Restaurierung tatsächlich brauchbar sind. Der BS-RoFormer mit seinem Band-Split-Modul und RoPE-Mechanismus repräsentiert den aktuellen Höhepunkt dieser Entwicklung und bildet das operative Fundament der gesamten Pipeline.

## Querverweise

- [[01_KI_Audio_Artefakte_und_ihre_Ursachen|Artikel 1: KI-Audio-Artefakte und ihre Ursachen]] — Die Artefakte, die nach der Separation auf Stem-Ebene behandelt werden
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Artikel 3: Neuronale Vocoder und Signalrestaurierung]] — Die Restaurationsmodelle, die auf die isolierten Stems angewendet werden
- [[07_Lastenheft_Pipeline_Architektur|Artikel 7: Lastenheft Pipeline-Architektur]] — Der vollständige Blueprint mit MSS als Phase 1
---
## 🔗 Verwandt
- [[MOC_Pipeline|🗺️ MOC: Pipeline & Architektur]]
- [[00_HOME|🏠 Home]]
- [[MOC_Stem_Separation|🗺️ MOC: Stem Separation]]
