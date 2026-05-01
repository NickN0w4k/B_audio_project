---
title: "KI-Audio-Artefakte und ihre Ursachen"
tags: [doku, artefakt, taxonomie, signaltheorie, ai-music, uncanny-valley]
created: 2026-04-29
---

# KI-Audio-Artefakte und ihre Ursachen

## Einleitung

Generative KI-Modelle für Musik — Suno, Udio, MusicGen — produzieren Arrange-ments, die kompositorisch überzeugen, signaltechnisch jedoch gravierende Mängel aufweisen. Diese Mängel sind keine Zufallserzeugnisse, sondern mathematische Konsequenzen der zugrundeliegenden neuronalen Architekturen und Kompressionsalgorithmen. Das Resultat wird in der Fachwelt als „Uncanny Valley" der Audioproduktion beschrieben: Die Musik wirkt oberflächlich menschlich, enthüllt bei genauerer Betrachtung jedoch systematische Artefakte, die den professionellen Einsatz verhindern.

Dieser Artikel klassifiziert die fünf zentralen Artefakt-Typen, analysiert ihre signal-theoretischen Ursachen und zeigt, warum herkömmliche Lösungsansätze (Equalizer, subtraktive Entrauschung) zwangsläufig scheitern.

## Hauptinhalt

### 1. High-Frequency Rolloff

**Ursache:** KI-Generatoren betreiben eine drastische Bitraten-Reduktion zur Senkung der Inferenzlast. Viele Modelle — insbesondere Suno — arbeiten intern mit 32 kHz Abtastrate und exportieren mit radikalem Tiefpassfilter, der Frequenzen oberhalb von 16 kHz (der Nyquist-Frequenz der internen Rate) komplett abschneidet. Verlustbehaftete Kompressionsalgorithmen (MP3, AAC) verschärfen dieses Problem durch psychoakustische Maskierungsmodelle, die vermeintlich unhörbare Frequenzen verwerfen.

**Akustische Manifestation:** Dumpfer, lebloser Klang. Fehlende „Air"-Frequenzen (>16 kHz) beeinträchtigen räumliche Wahrnehmung, Transparenz von Becken und Hi-Hats sowie Sprachverständlichkeit. Der Frequenzbereich, den Toningenieure als „Brillanz" bezeichnen, ist schlichtweg abwesend.

**Warum Equalizer scheitern:** Eine statische Anhebung per Shelving-Equalizer stellt nicht das musikalische Detail wieder her, sondern verstärkt lediglich das durch die Kompression entstandene Quantisierungsrauschen. Die Information ist unwiderruflich verloren — sie muss generativ rekonstruiert werden.

### 2. Checkerboard-Muster (Spectral Peaks)

**Ursache:** Transposed Convolutions (Dekonvolutionsschichten) sind Standardkomponente in den Decodern fast aller generativen Modelle. Wenn die Schrittweite (Stride) der Faltung die Kernel-Größe nicht ohne Rest teilt, entstehen asymmetrische Überlappungen beim Upsampling. Im Zeitbereich ergeben sich mikroskopische Amplitudenmodulationen, die im Spektrogramm als markante, unnatürliche spektrale Spitzen (Spectral Peaks) sichtbar werden. Diese schachbrettartigen Muster sind — wie das ISMIR-2025-Best-Paper von Afchar et al. beweist — **architektur-bedingt, nicht trainings-bedingt**. Die Deconvolution-Operation erzeugt sie zwangsläufig.

**Akustische Manifestation:** Hochfrequenter digitaler Schleier („Digital Haze") oder statisches Pfeifen über dem Gesamtsignal. Plattformspezifisch: Suno erzeugt einen metallischen Shimmer im Bereich 3,5–5 kHz, Udio periodische Ripples durch Attention-Window-Artefakte.

**Warum traditionelles Denoising scheitert:** Klassische Rauschunterdrückung behandelt das Signal als breitbandiges Rauschen und zerstört dabei musikalische Transienten, da die Artefakte keine stochastische Störung, sondern systematische, periodische Muster sind.

### 3. Chirps und Warbles

**Ursache:** Verlustbehaftete Audiocodecs nutzen psychoakustische Maskierungsmodelle, um vermeintlich unhörbare Frequenzen zu verwerfen. Bei der Dekodierung entstehen hörbare Fehler: „Chirps" (kurze, hochfrequente Zwitschergeräusche) und „Warbles" (Phaseninstabilitäten, die das Signal wackelig klingen lassen).

**Akustische Manifestation:** Hochfrequentes Zwitschern, zitternde Becken und Transienten. Besonders problematisch, da ein Tiefpassfilter zur Behebung die restliche Brillanz zerstören würde.

### 4. Metallische Resonanzen

**Ursache:** Zwei Mechanismen: (a) Überdimensionierte FFT-Koeffizienten durch fehlerhafte spektrale Subtraktion — der Algorithmus oszilliert an den Rändern der Frequenzbänder. (b) Inkohärente Phasenlage (Phase Wrapping), da viele Modelle primär Magnituden-Spektrogramme generieren und die Phase lediglich via Griffin-Lim oder unzureichend trainierten Vocodern schätzen.

**Akustische Manifestation:** „Unterwasser"-Klang, singendes Rauschen um Vokale, metallisches Gurgeln („Swoosh"-Effekte) bei Becken und Hi-Hats. Akustische Gitarren klingen wie auf Blech schlagende Hämmer. Phasenauslöschungen im Bassbereich und ein künstlich verengtes Stereobild sind die Folge.

**Warum weitere Filterung scheitert:** Nochmalige subtraktive Filterung führt zu Ausdünnung des Signals und verstärkt den Unterwasser-Effekt.

### 5. Robotische Quantisierung

**Ursache:** Neuronale Vocoder in KI-Modellen approximieren Durchschnittswerte ihrer Trainingsdaten. Die menschliche Stimme besitzt Mikroschwankungen — Vibrato, Formantendynamik, temporale Varianz —, die emotionale Authentizität verleihen. KI-Modelle glätten oder quantisieren diese Schwankungen, was zu einer unnatürlich starren Tonhöhenstruktur führt.

**Akustische Manifestation:** Extremer Auto-Tune-Effekt, starre Formanten, emotionale Sterilität, unnatürliche Sibilanten. Bei Tonhöhenänderungen fehlen biologisch korrekte Formantenanpassungen — Micky-Maus-Effekt („Chipmunk") oder unnatürlich tiefe Resonanz sind die Folge.

**Warum Chorus/Reverb-Scheitern:** Effekte zur Verschleierung verdecken das Problem lediglich, lösen aber nicht die Ursache — die fehlende mikrodynamische Varianz.

## Fazit

Die fünf Artefakt-Typen sind keine isolierten Phänomene, sondern ineinandergreifende Konsequenzen derselben architektonischen Schwächen: Transposed Convolutions erzeugen Checkerboard-Muster, Kompressionscodecs verursachen Chirps und Warbles, mangelnde Phasenmodellierung führt zu metallischen Verzerrungen, und die statistische Glättung der Trainingsdaten produziert robotische Quantisierung. Der entscheidende Erkenntnisgewinn: Subtraktive Methoden (EQ, spektrale Subtraktion) können diese strukturellen Defizite nicht beheben, da sie keine Informationen zurückgewinnen, sondern lediglich Amplituden manipulieren. Die moderne Audiorestaurierung setzt daher auf generative Verfahren — neuronale Netzwerke, die verlorene Audioinformationen statistisch fundiert neu synthetisieren.

## Querverweise

- [[02_Quellentrennung_als_Fundament|Artikel 2: Quellentrennung als Fundament]] — Warum MSS die Voraussetzung für jede Artefakt-Behebung ist
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Artikel 3: Neuronale Vocoder und Signalrestaurierung]] — Die generativen Modelle, die diese Artefakte rekonstruieren
- [[05_Checkerboard_und_Fourier_Artefakte|Artikel 5: Checkerboard und Fourier-Artefakte]] — Tiefergehende Analyse der architektur-bedingten Checkerboard-Muster
---
## 🔗 Verwandt
- [[MOC_Pipeline|🗺️ MOC: Pipeline & Architektur]]
- [[00_HOME|🏠 Home]]
- [[MOC_Artefakte|🗺️ MOC: Artefakte]]
