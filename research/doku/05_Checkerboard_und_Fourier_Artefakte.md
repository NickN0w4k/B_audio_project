---
title: "Checkerboard und Fourier-Artefakte"
tags: [doku, artefakt, checkerboard, fourier, detektion, spektralanalyse]
created: 2026-04-29
---

# Checkerboard und Fourier-Artefakte

## Einleitung

Eines der signifikantesten und am leichtesten detektierbaren Merkmale KI-generierten Audios sind systematische Frequenzanomalien, die als Checkerboard-Artefakte bekannt sind. Diese Artefakte sind keine zufälligen Störungen und auch keine Folge unzureichenden Trainings — sie sind mathematische Gewissheiten, die zwangsläufig aus der Architektur der Upsampling-Module generativer Modelle entstehen. Das ISMIR-2025-Best-Paper von Afchar et al. (Deezer) hat diesen Zusammenhang erstmals formal bewiesen und eine einfache Fourier-basierte Detektionsmethode vorgestellt, die >99 % Genauigkeit erreicht.

Dieser Artikel analysiert die Architektur-Ursachen der Checkerboard-Artefakte, die Fourier-basierte Detektionsmethodik und die Implikationen für Produktion und Streaming-Plattformen.

## Hauptinhalt

### Die Architektur-Ursache: Transposed Convolutions

Fast alle generativen Audio-Modelle nutzen Transposed Convolutions (Dekonvolutionsschichten) in ihren Decodern, um die niederdimensionale latente Repräsentation zurück in hochauflösende Audiosignale zu upsamplen. Das Problem: Wenn die Schrittweite (Stride) der Faltung die Kernel-Größe nicht ohne Rest teilt, entstehen ungleichmäßige, asymmetrische Überlappungen.

**Im Bildbereich** (wo das Phänomen erstmals 2016 von Odena et al. bei Google beschrieben wurde) manifestiert sich dies als sichtbares Schachbrettmuster — Pixel erhalten ungleiche „Beiträge" von der Faltung, was zu periodischen Helligkeitsschwankungen führt.

**Im Audiobereich** transformiert sich dieses Phänomen: Die mikroskopischen Amplitudenmodulationen im Zeitbereich werden durch eine Short-Time Fourier Transform (STFT) sichtbar als markante, unnatürliche spektrale Spitzen (Spectral Peaks). Diese Peaks treten periodisch auf und bilden ein charakteristisches Gittermuster im Spektrogramm — das akustische Äquivalent des visuellen Checkerboard-Musters.

**Der entscheidende Punkt:** Diese Artefakte sind architektur-bedingt, nicht trainings-bedingt. Egal wie gut das Modell trainiert ist — die Deconvolution-Operation erzeugt sie zwangsläufig. Nur eine Änderung der Upsampling-Architektur kann sie vermeiden.

### Plattformspezifische Signaturen

Die Checkerboard-Artefakte weisen plattformspezifische Muster auf, die wie akustische Fingerabdrücke funktionieren:

**Suno** (diffusionsbasiert, 32 kHz intern): Harter spektraler Cutoff bei 16 kHz (Nyquist-Frequenz der internen Abtastrate). Oberhalb davon: lediglich Aliasing-Rauschen. Im Bereich 8–16 kHz: „Digital Haze" als breitflächiger, hochfrequenter Schleier. Die Peaks im Spektrogramm sind viel periodischer und stechen deutlich hervor mit sehr scharfem Frequenz-Cutoff.

**Udio** (transformatorbasiert, 44,1 kHz nativ): Periodische „Ripples" in der spektralen Hüllkurve — direkte mathematische Artefakte der verwendeten Attention-Windows. Die Separation der Instrumente wirkt künstlich „sauber", aber es fehlt die mikrodynamische Interaktion echter Aufnahmen.

**MusicGen** (autoregressive Token-Generierung): Quantisierungsartefakte bei 50 Hz, geprägt durch die Codec-Latent-Space-Signatur des EnCodec.

**Generelle CNN-Decoder:** Systematische spektrale Spitzen durch ungleiche Kernel-Überlappung.

### Die Fourier-basierte Detektionsmethode

Die Methode von Afchar et al. ist bemerkenswert durch ihre Einfachheit und Interpretierbarkeit:

1. **STFT berechnen:** Konvertiere das Audio mittels Short-Time Fourier Transform in den Frequenzbereich.
2. **Mittlungsspektrum:** Berechne das Durchschnittsspektrum über die Zeit mit einem Sliding Window.
3. **Peaks detektieren:** Identifiziere Spitzenwerte im gemittelten Spektrum.
4. **Lokale Minima subtrahieren:** Ziehe die lokalen Minima des Spektrums ab, um die lokalen Variationen hervorzuheben und irrelevante Bandbreite zu entfernen (Filterung auf 5–16 kHz).

**Das Resultat:** Für einen Suno-generierten Track sind die Peaks viel periodischer und stechen mit scharfem Cutoff hervor. Für einen echten Track (z.B. Radioheads „Everything in Its Right Place") sind die Peaks relativ uniform und über den gesamten Frequenzbereich verstreut — sie sehen aus wie natürliche harmonische Inhalte.

**Klassifikation:** Mit diesen Fingerabdrücken kann ein einfacher linearer Klassifikator trainiert werden. Da verschiedene Modelle verschiedene Peak-Muster aufweisen, ist sogar eine Klassifizierung zwischen Modellversionen möglich (z.B. Suno v2 vs. Suno v3).

### >99 % Detektionsgenauigkeit

Die Autoren berichten von einer Detektionsgenauigkeit von über 99 % für KI-generierte Musik. Dies wurde sowohl auf Open-Source-Modelle als auch auf kommerzielle Generatoren (Suno, Udio) validiert. Die Robustheit der Methode beruht darauf, dass sie ein fundamentales Architektur-Feature detektiert, das nicht durch Training oder Post-Processing beseitigt werden kann.

**Caveat:** Die Methode ist nicht vollständig robust. Einfache Audio-Manipulationen wie Pitch-Shifting können die Peak-Frequenzen verändern und den Klassifikator brechen. Zukünftige Modelle könnten zudem modifizierte Upsampling-Mechanismen verwenden, die die Artefakte vermeiden.

### Implikationen für Produktion und Streaming

**Für Streaming-Plattformen:** Die Fourier-Detektion bietet einen effizienten, interpretierbaren Ansatz zur Identifizierung KI-generierter Musik — ohne komplexe KI-Detektionsmodelle trainieren zu müssen. Ein einfacher STFT-basierter Test kann bei der Skalierung millionenfach angewendet werden.

**Für die Musikindustrie:** Die Existenz plattformspezifischer Signaturen ermöglicht Forensik auf einem neuen Niveau. Nicht nur kann erkannt werden, *dass* ein Track KI-generiert ist, sondern auch *womit* — was für Urheberrechtsfragen relevant wird.

**Für die Restaurations-Pipeline:** Checkerboard-Artefakte können nicht durch subtraktives Denoising entfernt werden — sie müssen durch Denoising Autoencoder (DAEs) oder Wave-U-Net adressiert werden, die das systematische Muster explizit gelernt haben. Das Wave-U-Net vermeidet die Erzeugung eigener Checkerboard-Artefakte, indem es traditionelle Strided-Convolutions durch lineare Interpolation und nachfolgende normale Faltung ersetzt.

**Für zukünftige Modell-Architekturen:** Die Erkenntnis, dass Transposed Convolutions architektur-bedingt Artefakte erzeugen, drängt zur Entwicklung alternativer Upsampling-Mechanismen. Modelle, die Interpolation + Konvolution statt Deconvolution verwenden, könnten diese Artefakte von vornherein vermeiden.

### Benn Jordan und die öffentliche Wahrnehmung

Benn Jordan (The Flashbulb) hat in seinem YouTube-Video mit über 420.000 Aufrufen die KI-Musik-Detektionsthematik einer breiten Öffentlichkeit zugänglich gemacht. Er verweist explizit auf das Deezer-ISMIR-Paper und betont: Die Detektion KI-generierter Musik erfordert keine Millionen-Parameter-Modelle — manchmal reicht eine STFT.

## Fazit

Checkerboard-Artefakte sind keine Bugs, sondern mathematische Gewissheiten, die aus der Architektur von Transposed Convolutions resultieren. Die Fourier-basierte Detektionsmethode von Afchar et al. beweist, dass >99 % Genauigkeit mit interpretierbaren, einfachen Mitteln erreichbar ist. Für die Restaurations-Pipeline bedeutet dies: Diese Artefakte müssen durch spezialisierte Autoencoder adressiert werden, die das systematische Muster gelernt haben, nicht durch subtraktive Filter. Für die Industrie bedeutet es: KI-Musik ist forensisch nachweisbar — und zwar auf eine Art, die selbst einfache Modifikationen übersteht, solange die zugrundeliegende Architektur unverändert bleibt.

## Querverweise

- [[01_KI_Audio_Artefakte_und_ihre_Ursachen|Artikel 1: KI-Audio-Artefakte und ihre Ursachen]] — Die übergeordnete Taxonomie der Artefakte
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Artikel 3: Neuronale Vocoder und Signalrestaurierung]] — Wave-U-Net und DAEs als Gegenmaßnahmen
- [[07_Lastenheft_Pipeline_Architektur|Artikel 7: Lastenheft Pipeline-Architektur]] — Wie die Pipeline diese Artefakte adressiert
---
## 🔗 Verwandt
- [[MOC_Pipeline|🗺️ MOC: Pipeline & Architektur]]
- [[00_HOME|🏠 Home]]
- [[MOC_Artefakte|🗺️ MOC: Artefakte]]
