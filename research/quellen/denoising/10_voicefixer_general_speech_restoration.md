---
title: "VoiceFixer: General Speech Restoration"
tags: [quelle, tool, denoising, speech-restoration, audio-processing]
created: 2026-04-29
---

# VoiceFixer: General Speech Restoration

**GitHub:** https://github.com/haoheliu/voicefixer  
**Paper:** [arXiv:2109.13731](https://arxiv.org/abs/2109.13731)  
**PyPI:** `pip install voicefixer`

## Overview
VoiceFixer aims to restore human speech regardless of how seriously it's degraded. Handles noise, reverberation, low resolution (2kHz~44.1kHz), and clipping (0.1-1.0 threshold) within one model.

## Key Components
- Pretrained VoiceFixer built on neural vocoder
- Pretrained 44.1kHz universal speaker-independent neural vocoder

## Run Modes
| Mode | Description |
| ---- | ----------- |
| `0`  | Original Model (suggested by default) |
| `1`  | Add preprocessing module (remove higher frequency) |
| `2`  | Train mode (might work on seriously degraded real speech) |
| `all`| Run all modes — outputs 1 wav per mode |

## Usage
```shell
# Single file
voicefixer --infile input.wav --outfile output.wav

# Folder
voicefixer --infolder /path/to/input --outfolder /path/to/output

# Change mode
voicefixer --infile input.wav --outfile output.wav --mode 1
```

## Python API
```python
from voicefixer import VoiceFixer, Vocoder

voicefixer = VoiceFixer()
voicefixer.restore(input="low_quality.wav", output="restored.wav", cuda=False, mode=0)

vocoder = Vocoder(sample_rate=44100)
vocoder.oracle(fpath="input.flac", out_path="output.flac", cuda=False)
```

## Custom Vocoder Support
Can integrate pre-trained HiFi-GAN or other vocoders by providing a `convert_mel_to_wav` helper function. Must work at 44.1kHz with 128 mel frequency bins.

## Citation
```bibtex
@misc{liu2021voicefixer,
  title={VoiceFixer: Toward General Speech Restoration With Neural Vocoder},
  author={Haohe Liu and Qiuqiang Kong and Qiao Tian and Yan Zhao and DeLiang Wang and Chuanzeng Huang and Yuxuan Wang},
  year={2021},
  eprint={2109.13731},
  archivePrefix={arXiv},
  primaryClass={cs.SD}
}
```
---
## 🔗 Verwandt
- [[MOC_Denoising|🗺️ MOC: Denoising & Restaurierung]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]]
