---
title: "BS-RoFormer: Band Split Roformer"
tags: [quelle, tool, mss, stem-separation, quellentrennung, audio-processing]
created: 2026-04-29
---

# BS-RoFormer: Band Split Roformer

**GitHub:** https://github.com/lucidrains/BS-RoFormer  
**Paper:** [arXiv:2309.02612](https://arxiv.org/abs/2309.02612) (Band Split Roformer)  
**Follow-up:** [arXiv:2310.01809](https://arxiv.org/abs/2310.01809) (MelBand Roformer)  
**Install:** `pip install BS-RoFormer`

## Overview
Implementation of Band Split Roformer — SOTA attention network for music source separation from ByteDance AI Labs. Beat previous first place by a large margin.

## Key Technique
- **Axial attention** across frequency (multi-band) and time
- **Rotary positional encoding** led to huge improvement over learned absolute positions
- Supports stereo training and multiple stem outputs

## Replication & Weights
- Roman (ZFTurbo) replicated the paper and open-sourced weights: [Music-Source-Separation-Training](https://github.com/ZFTurbo/Music-Source-Separation-Training)
- Kimberley Jensen open-sourced a MelBand Roformer vocal model: [Mel-Band-Roformer-Vocal-Model](https://github.com/KimberleyJensen/Mel-Band-Roformer-Vocal-Model)

## Usage (Band Split Roformer)
```python
import torch
from bs_roformer import BSRoformer

model = BSRoformer(
    dim=512,
    depth=12,
    time_transformer_depth=1,
    freq_transformer_depth=1,
    use_pope=False  # successor to rotary embeddings
)

x = torch.randn(2, 352800)
target = torch.randn(2, 352800)
loss = model(x, target=target)
loss.backward()
```

## Usage (MelBand Roformer)
```python
from bs_roformer import MelBandRoformer

model = MelBandRoformer(
    dim=32,
    depth=1,
    time_transformer_depth=1,
    freq_transformer_depth=1,
)
```

## Key Contributions
- Axial attention (Ho et al., 2019) for multidimensional transformers
- Rotary Position Embedding (Su et al., 2021) — RoFormer
- FlashAttention for efficient exact attention

## Citations
```bibtex
@inproceedings{Lu2023MusicSS,
    title={Music Source Separation with Band-Split RoPE Transformer},
    author={Wei-Tsung Lu and Ju-Chiang Wang and Qiuqiang Kong and Yun-Ning Hung},
    year={2023}
}
```
---
## 🔗 Verwandt
- [[MOC_Stem_Separation|🗺️ MOC: Stem Separation]]
- [[02_Quellentrennung_als_Fundament|Quellentrennung als Fundament]]
