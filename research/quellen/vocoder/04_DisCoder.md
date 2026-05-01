---
title: "DisCoder: High-Fidelity Music Vocoder Using Neural Audio Codecs"
tags: [quelle, tool, vocoder, neural-synthesis, audio-processing]
created: 2026-04-29
---

# DisCoder: High-Fidelity Music Vocoder Using Neural Audio Codecs

- **GitHub:** https://github.com/ETH-DISCO/discoder
- **Paper:** https://arxiv.org/abs/2502.12759
- **Modell:** https://huggingface.co/disco-eth/discoder
- **Samples:** https://lucala.github.io/discoder/
- **Lizenz:** MIT
- **Sprache:** Python 3.11
- **Präsentiert bei:** ICASSP 2025
- **Organisation:** ETH DISCO Lab

## Überblick
DisCoder ist ein **neuraler Vocoder**, der eine GAN-basierte Encoder-Decoder-Architektur verwendet, um hochqualitatives 44.1kHz-Audio aus Mel-Spektrogrammen zu rekonstruieren.

### Innovationsansatz
1. **Mel → Codec-Latent → Audio:** Statt direkt Mel→Audio (wie HiFi-GAN), transformiert DisCoder das Mel-Spektrogramm zuerst in eine niederdimensionale Repräsentation, die am **Descript Audio Codec (DAC)** latent space ausgerichtet ist.
2. **Fein-getunter DAC-Decoder:** Die Audio-Rekonstruktion erfolgt durch einen fine-getunten DAC-Decoder, der auf Musik statt auf Sprache trainiert wurde.

## Technische Details
- **Architektur:** GAN Encoder-Decoder mit DAC-Informierung
- **Sample-Rate:** 44.1 kHz
- **Mel-Bins:** 128
- **Z Prediction Target:** Das Modell verwendet eine Z-Vorhersage für die Codec-Latent-Repräsentation
- **Qualitätsmetrik:** ViSQOL (Virtual Speech Quality Objective Listener) für Validierung

## Installation & Nutzung
```bash
git clone https://github.com/ETH-DISCO/discoder
conda create -n discoder python=3.11
conda activate discoder
pip install -r requirements.txt
```

Inference via HuggingFace:
```python
discoder = DisCoder.from_pretrained("disco-eth/discoder").eval().to(device)
mel = utils.get_mel_spectrogram_from_config(audio, discoder.config)
wav_recon = discoder(mel)
```

Batch-Inference:
```bash
python inference.py --input_dir input/ --output_dir output/ \
  --checkpoint_file model.pt --config configs/config_z.json
```

## Relevanz für die Pipeline
DisCoder ist als **Endstufe (Vocoder)** in der Restaurations-Pipeline relevant — er kann restaurierte Mel-Spektrogramme in hochqualitatives Audio zurückwandeln. Sein Ansatz, den DAC-Latent-Raum als Zwischenrepräsentation zu nutzen, könnte die Artefakt-Problematik von direkten Mel→Audio-Vocodern (wie HiFi-GAN) reduzieren.

## Bezug zu anderen Quellen
- **Quelle 08** (APNet): Alternativer Vocoder-Ansatz (Amplituden-/Phasenprädiktion)
- **Quelle 12** (HiFi-GAN): Der etablierte Standard-Vocoder, den DisCoder verbessern will
- **Quelle 25** (APNet2): Weiterentwicklung des APNet-Ansatzes
---
## 🔗 Verwandt
- [[MOC_Vocoder|🗺️ MOC: Neuronale Vocoder]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]]
