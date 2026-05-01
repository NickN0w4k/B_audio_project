---
title: "ComfyUI Music Tools"
tags: [quelle, tool, denoising, comfyui, workflow, audio-processing]
created: 2026-04-29
---

# ComfyUI Music Tools

**GitHub:** https://github.com/jeankassio/ComfyUI_MusicTools  
**License:** MIT  
**Requires:** Python 3.8+, ComfyUI

## Overview
Professional audio processing and mastering suite for ComfyUI. Built specifically for post-processing AI-generated audio (Ace-Step, Suno, Udio, etc.).

## Key Feature: Vocal Naturalizer (Dec 2025)
Removes robotic/auto-tune artifacts from AI-generated vocals:
- **Pitch Humanization**: Natural vibrato and pitch variation (~4.5 Hz)
- **Formant Variation**: Humanizes timbre and vocal character (200-3000 Hz)
- **Artifact Removal**: Eliminates metallic digital artifacts (6-10 kHz)
- **Quantization Masking**: Smooths pitch steps with shaped noise (1-4 kHz)
- **Transition Smoothing**: Natural glides between notes (50 Hz low-pass)
- Performance: ~10ms per second of audio (102x realtime)

## All 12 Nodes
1. **Music_MasterAudioEnhancement** — Complete mastering chain (all-in-one)
2. **Music_NoiseRemove** — Spectral noise reduction
3. **Music_AudioUpscale** — Sample rate upscaling (16-192 kHz)
4. **Music_StereoEnhance** — Stereo widening and imaging
5. **Music_LufsNormalizer** — LUFS-based loudness normalization
6. **Music_Equalize** — 3-band parametric EQ
7. **Music_Reverb** — Algorithmic reverb
8. **Music_Compressor** — Dynamic range compression
9. **Music_Gain** — Volume adjustment (-24 to +24 dB)
10. **Music_AudioMixer** — Mix two audio streams
11. **Music_StemSeparation** — 4-stem extraction (Demucs/Spleeter)
12. **Music_StemRecombination** — Remix separated stems

## Master Audio Enhancement Node
Complete mastering chain:
- **Denoise**: Hiss-only, full, or off
- **AI Enhancement**: SpeechBrain MetricGAN+ neural enhancer
- **3-Band Parametric EQ**: Bass (80 Hz), mid (1 kHz), treble (8 kHz)
- **Clarity Enhancement**: Transient shaper + harmonic exciter + presence boost
- **Multiband Compression**: Independent low/mid/high bands
- **True-Peak Limiter**: Brick-wall with 5ms lookahead
- **Vocal Processing**: De-esser, breath smoother, reverb, naturalizer
- **LUFS Normalization**: -23 to -9 LUFS (streaming/broadcast/CD standards)

## Performance
| Component | Speedup | Time (3-min song) |
|-----------|---------|-------------------|
| Vocal Enhancement | 43x | ~3.4ms |
| True-Peak Limiter | 34x | ~14.7ms |
| Multiband Compression | 6x | ~85ms |
| **Total Pipeline** | **~26x** | **~5 seconds** |

## Recommended Settings for AI Vocals
```
Denoise Mode: "Hiss Only"
Vocal Enhance: True
Naturalize Vocal: 0.5 (adjust 0.3-0.7)
De-esser Amount: 0.5
LUFS Target: -14.0 (Spotify/YouTube)
```

## Dependencies
- numpy, scipy, librosa, soundfile, pyloudnorm, noisereduce
- Optional: spleeter/demucs (stem separation), speechbrain (AI enhancement)
---
## 🔗 Verwandt
- [[MOC_Denoising|🗺️ MOC: Denoising & Restaurierung]]
- [[03_Neuronale_Vocoder_und_Signalrestaurierung|Neuronale Vocoder und Signalrestaurierung]]
