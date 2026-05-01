---
title: "HiFi-GAN: Generative Adversarial Networks for Efficient and High Fidelity Speech Synthesis"
tags: [quelle, tool, vocoder, neural-synthesis, gan, speech]
created: 2026-04-29
---

# HiFi-GAN: Generative Adversarial Networks for Efficient and High Fidelity Speech Synthesis

**GitHub:** https://github.com/jik876/hifi-gan  
**Paper:** [arXiv:2010.05646](https://arxiv.org/abs/2010.05646)  
**Authors:** Jungil Kong, Jaehyeon Kim, Jaekyoung Bae

## Overview
GAN-based model for high-fidelity speech synthesis. Key insight: modeling periodic patterns of audio is crucial for enhancing sample quality.

## Key Results
- Generates 22.05 kHz high-fidelity audio **167.9x faster than real-time** on single V100 GPU
- Small footprint version: 13.4x faster than real-time on CPU
- Mean Opinion Score (MOS) indicates human-quality speech

## Architecture
- Multiple discriminator types for different periodic patterns
- Multi-scale spectrogram loss
- Three generator variants: V1, V2, V3

## Pretrained Models
| Folder | Generator | Dataset | Fine-Tuned |
|--------|-----------|---------|------------|
| LJ_V1/V2/V3 | V1/V2/V3 | LJSpeech | No |
| LJ_FT_T2_V1/V2/V3 | V1/V2/V3 | LJSpeech | Yes (Tacotron2) |
| VCTK_V1/V2/V3 | V1/V2/V3 | VCTK | No |
| UNIVERSAL_V1 | V1 | Universal | No |

## Training
```bash
python train.py --config config_v1.json
```

## Inference
```bash
# From wav
python inference.py --checkpoint_file [path]

# End-to-end (from mel spectrogram)
python inference_e2e.py --checkpoint_file [path]
```

## Fine-Tuning
1. Generate mel-spectrograms with Tacotron2 (teacher-forcing)
2. Create `ft_dataset` folder with .npy files
3. Run: `python train.py --fine_tuning True --config config_v1.json`

## Relevance to AI Audio Restoration
HiFi-GAN serves as the neural vocoder backbone in several restoration pipelines (VoiceFixer, APNet) — converting mel spectrograms back to high-fidelity waveforms.
---
## 🔗 Verwandt
- [[MOC_Vocoder|🗺️ MOC: Neuronale Vocoder]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]]
