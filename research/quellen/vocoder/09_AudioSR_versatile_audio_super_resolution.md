---
title: "AudioSR: Versatile Audio Super-resolution at Scale"
tags: [quelle, tool, vocoder, neural-synthesis, super-resolution]
created: 2026-04-29
---

# AudioSR: Versatile Audio Super-resolution at Scale

**GitHub:** https://github.com/haoheliu/versatile_audio_super_resolution  
**Paper:** [arXiv:2309.07314](https://arxiv.org/abs/2309.07314)  
**PyPI:** `pip install audiosr==0.0.7`

## Overview
AudioSR performs versatile audio super-resolution — any sampling rate → 48kHz. Works on all types of audio (music, speech, environmental sounds) and all input sampling rates.

## Key Features
- Diffusion-based super-resolution using DDIM sampling
- Two model variants: `basic` (general) and `speech` (speech-optimized)
- Gradio demo available (`python app.py`)
- Batch processing supported

## Usage
```shell
# Single file
audiosr -i example/music.wav

# Batch
audiosr -il batch.lst

# With options
audiosr -i input.wav --ddim_steps 50 --guidance_scale 3.5 --model_name basic
```

## Important Limitations
1. **Cutoff Pattern Sensitivity**: AudioSR was trained with low-pass filtering simulation. MP3 compression creates unfamiliar "spectrogram holes" near cutoff that the model can't handle.
2. **Solution**: Apply low-pass filtering to input before AudioSR to normalize the cutoff pattern.
3. **Severe Distortions**: Excessive noise or reverb degrades performance.

## Change Log
- 2025-06-28: LSD calculation pitfall demonstration
- 2024-12-31: Training code released
- 2024-12-16: Important notes on making AudioSR work (failure cases documented)
- 2023-09-24: Replicate demo, Windows fix

## Citation
```bibtex
@inproceedings{liu2024audiosr,
  title={{AudioSR}: Versatile audio super-resolution at scale},
  author={Liu, Haohe and Chen, Ke and Tian, Qiao and Wang, Wenwu and Plumbley, Mark D},
  booktitle={IEEE International Conference on Acoustics, Speech and Signal Processing},
  pages={1076--1080},
  year={2024},
  organization={IEEE}
}
```
---
## 🔗 Verwandt
- [[MOC_Vocoder|🗺️ MOC: Neuronale Vocoder]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]]
