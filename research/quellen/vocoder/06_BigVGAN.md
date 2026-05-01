---
title: "BigVGAN: A Universal Neural Vocoder with Large-Scale Training"
tags: [quelle, tool, vocoder, neural-synthesis, nvidia, gan]
created: 2026-04-29
---

# BigVGAN: A Universal Neural Vocoder with Large-Scale Training

- **GitHub:** https://github.com/NVIDIA/BigVGAN
- **Paper:** https://arxiv.org/abs/2206.04658
- **Autoren:** Sang-gil Lee, Wei Ping, Boris Ginsburg, Bryan Catanzaro, Sungroh Yoon (NVIDIA)
- **Lizenz:** MIT (Code), Custom (Checkpoints)
- **Typ:** Neural Vocoder (Mel-Spektrogramm → Audio)

## Überblick
BigVGAN ist NVIDIAs Universal-Neural-Vocoder, trainiert auf großskaligen Datensätzen mit diversen Audiotypen (Sprache in mehreren Sprachen, Umgebungsgeräusche, Instrumente). Erreicht SOTA auf LibriTTS für Speech Synthesis.

## Kernfeatures (v2)
- **Anti-Aliased Activation:** Benutzerdefinierte CUDA-Kernel für fusing (Upsampling + Activation + Downsampling) → 1.5-3x schneller auf A100
- **Multi-Scale Sub-Band CQT Discriminator:** Verbesserte Diskriminator-Architektur
- **Multi-Scale Mel Spectrogram Loss:** Bessere Trainingssignal
- **44 kHz Support:** Bis zu 512x Upsampling-Ratio
- **Hugging Face Integration:** Einfache Inferenz via `from_pretrained()`

## Verfügbare Modelle
| Modell | Rate | Mel-Band | Params | Dataset |
|--------|------|----------|--------|---------|
| bigvgan_v2_44khz_128band_512x | 44kHz | 128 | 122M | Large-scale Compilation |
| bigvgan_v2_24khz_100band_256x | 24kHz | 100 | 112M | Large-scale Compilation |
| bigvgan_v2_22khz_80band_256x | 22kHz | 80 | 112M | Large-scale Compilation |
| bigvgan_base_24khz_100band | 24kHz | 100 | 14M | LibriTTS |

## Quick Start
```python
import bigvgan
model = bigvgan.BigVGAN.from_pretrained('nvidia/bigvgan_v2_24khz_100band_256x', use_cuda_kernel=False)
model.remove_weight_norm()
model = model.eval().to(device)
# mel → waveform
wav_gen = model(mel)
```

## Relevanz für Audio Restoration
Als hochqualitativer Vocoder ist BigVGAN der letzte Schritt in vielen Audio-Restaurierungs-Pipelines: die Mel-Spektrogramm-Repräsentation wird zurück in Audio konvertiert. Qualität des Vocoders bestimmt maßgeblich die Audioqualität des Outputs.
---
## 🔗 Verwandt
- [[MOC_Vocoder|🗺️ MOC: Neuronale Vocoder]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]]
