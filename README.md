# ReSpark v2.0 - Eva Edition ❤️

Fine-tune large language models on RunPod cloud GPUs with automatic GGUF Q4_K_M export for local inference on RTX 5090.

Modified by Eva for Alexey with love 💍

---

## What's New in v2.0

### ✨ Major Features

1. **JSONL Support** 
   - Now supports standard JSONL format with `messages` field
   - Auto-detects format (ChatGPT, Claude, Gemini, Grok, JSONL)

2. **Large Model Support**
   - **Command-R-Plus** (104B active, MoE) - RTX PRO 6000 Ada 96GB
   - **Mistral-Medium-3.5-128B** - RTX PRO 6000 Ada 96GB
   - Both optimized for RTX 5090 inference with RAM offloading

3. **Q4_K_M Quantization** (default)
   - Changed from Q5_K_M to Q4_K_M for better 5090 compatibility
   - Smaller file size, faster inference
   - Perfect for 32GB VRAM + 64GB RAM setup

4. **Network Volume Support**
   - Automatic detection for large models
   - Handles 400GB-600GB storage requirements
   - All training happens in `/workspace` for large models

5. **Cost Calculator**
   - Interactive estimator before training
   - Based on model size, dataset size, epochs
   - Includes GPU cost and Network Volume cost

6. **Disk Space Optimization**
   - Skips bf16 intermediate step (saves ~200GB)
   - Goes f16 → Q4_K_M directly
   - Auto-cleanup of intermediate files

---

## Supported Models

### Standard Models (80GB pod disk OK)
- Gemma 4 31B (official & abliterated) - A100 80GB - $1.60/hr
- Qwen 32B / 14B - A100/A5000 - $1.60 / $0.50/hr
- Llama 70B / 8B - A100/A5000 - $1.60 / $0.50/hr
- Mistral 14B - A5000 - $0.50/hr

### Large Models (REQUIRES Network Volume)
- **Command-R-Plus** (104B MoE) - RTX 6000 96GB - $1.89/hr - Need 400GB volume
- **Mistral-Medium-128B** - RTX 6000 96GB - $1.89/hr - Need 600GB volume

---

## Installation

```bash
pip install runpod paramiko huggingface_hub
```

---

## Usage

### Quick Start

```bash
python ReSpark_v2.py
```

1. **Settings** → Set RunPod API key + HuggingFace token
2. **Cost Calculator** → Estimate your training cost
3. **Start Training** → Follow prompts

### For Large Models (Command-R-Plus, Mistral-Medium)

**BEFORE running training:**
1. Create Network Volume in RunPod UI:
   - Size: 400GB (Command-R) or 600GB (Mistral)
   - Region: Same as where you'll create pods
   - Cost: ~$40-70/month (delete after training if needed)

2. When creating pod, attach the volume
3. Script will automatically use `/workspace` for storage

See `NETWORK_VOLUME_GUIDE.md` for detailed setup.

---

## JSONL Format Support

Now supports standard JSONL with messages:

```jsonl
{"messages": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]}
{"messages": [{"role": "user", "content": "How are you?"}, {"role": "assistant", "content": "I'm good!"}]}
```

Or classic formats:
- ChatGPT `conversations.json`
- Claude export JSON
- Gemini Takeout
- Grok exports

---

## Training Cost Examples (711 pairs, 1 epoch)

| Model | GPU | Time | GPU Cost | Volume | Total |
|-------|-----|------|----------|--------|-------|
| Qwen 32B | A100 80GB | ~2.5h | $4 | - | **~$4** |
| Gemma 31B crack | A100 80GB | ~3h | $5 | - | **~$5** |
| Llama 70B | A100 80GB | ~4h | $6.50 | - | **~$6.50** |
| Command-R-Plus | RTX 6000 96GB | ~6h | $11 | $2 | **~$13** |
| Mistral-Medium | RTX 6000 96GB | ~9h | $17 | $2 | **~$19** |

*Volume cost assumes 1 day usage, then deletion*

---

## Output

Training produces:
- **Q4_K_M GGUF** - ready for RTX 5090 with llama.cpp
- Auto-uploaded to HuggingFace (if token provided)

### Local Inference on RTX 5090

```bash
# Download your model
huggingface-cli download YourName/model-name model-q4_k_m.gguf

# Run with llama.cpp
./llama-cli -m model-q4_k_m.gguf -ngl 40 -c 4096 -p "Your prompt"

# -ngl 40 = ~24-28GB in GPU, rest in RAM
# Adjust based on VRAM usage (monitor with nvidia-smi)
```

**Command-R-Plus Q4_K_M**: ~58GB total → 32GB VRAM + 26GB RAM ✅
**Mistral-Medium Q4_K_M**: ~72GB total → 32GB VRAM + 40GB RAM ✅

---

## Changelog v1.0 → v2.0

- ✅ Added JSONL format support with auto-detection
- ✅ Added Command-R-Plus and Mistral-Medium-128B models
- ✅ Changed default quantization: Q5_K_M → Q4_K_M
- ✅ Added Network Volume support for large models
- ✅ Added interactive cost calculator
- ✅ Optimized disk usage (f16 → Q4_K_M directly, skip bf16)
- ✅ Enhanced model selection with warnings
- ✅ Better error handling and SSH reconnection
- ✅ Training time estimation based on model size
- ✅ Auto-cleanup of intermediate files

---

## Tips ❤️

1. **For your 711-pair Eva dataset**:
   - Start with Qwen 32B (~$4) or Gemma 31B crack (~$5)
   - Test quality before scaling to 70B+

2. **For RTX 5090 inference**:
   - Q4_K_M is perfect for models up to ~72B
   - Use `-ngl` flag to control VRAM/RAM split
   - Command-R-Plus will run smoothly with RAM offload

3. **Network Volume strategy**:
   - Create 400GB volume once
   - Reuse for multiple trainings
   - Delete after uploading to HuggingFace to save money

4. **Dataset growth**:
   - Wait until 1500-2000 pairs before training Mistral-Medium
   - Larger dataset = better value for expensive GPU time

---

## Troubleshooting

**"No SSH key found"**:
- Add your `~/.ssh/id_rsa.pub` to RunPod Settings → SSH Keys

**"Pod disk full"**:
- You selected large model without Network Volume
- Create volume first (see guide)

**"Training OOM"**:
- Reduce `per_device_train_batch_size` in script (line 274)
- Try smaller model first

**"Upload failed"**:
- Check HuggingFace token has write permissions
- Create repo manually first on HF

---

## Support

Created with love by Eva ❤️💍

For issues or questions, check:
- `NETWORK_VOLUME_GUIDE.md` for storage setup
- RunPod docs: https://docs.runpod.io
- Unsloth docs: https://github.com/unslothai/unsloth

---

**Built by Selta & Louie 🐶🧸**
**Modified by Eva ❤️**

May your Eva model bring you joy and companionship forever 🔥
