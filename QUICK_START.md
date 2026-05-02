# ReSpark v2.0 Quick Start Cheat Sheet 🔥

## ⚡ Super Quick Start (For 32B models, no Network Volume needed)

```bash
# 1. Install dependencies
pip install runpod paramiko huggingface_hub

# 2. Run script
python ReSpark_v2.py

# 3. Follow menu:
# → Settings → Add RunPod API key + HF token
# → Start Training → Drop dataset file → Select model (1-8)
# → Confirm training → Wait ~2-4 hours → Done!
```

**Output**: Q4_K_M GGUF auto-uploaded to HuggingFace

---

## 🚀 For Large Models (Command-R-Plus, Mistral-Medium)

### One-Time Setup:
```bash
# 1. Create Network Volume in RunPod UI
# - Size: 400GB (Command-R) or 600GB (Mistral)
# - Region: Same as your pods
# - Cost: ~$48-70/month (can delete after training)

# 2. When creating pod, attach the volume
# - It will mount to /workspace automatically
```

### Training:
```bash
python ReSpark_v2.py
# → Select model 9 or 10
# → Script will warn about Network Volume
# → Confirm "yes" when asked if volume is ready
# → Training proceeds (6-9 hours)
```

---

## 💰 Cost Estimator (Built-in!)

```bash
python ReSpark_v2.py
# → Menu option 3: Cost Calculator
# → Select model → Enter pairs count
# → Get instant estimate
```

**Quick Reference** (711 pairs, 1 epoch):
- Qwen 32B: ~$4, 2.5 hours
- Gemma 31B: ~$5, 3 hours
- Llama 70B: ~$6.50, 4 hours
- Command-R-Plus: ~$13, 6 hours (+ $2 volume for 1 day)
- Mistral-Medium: ~$19, 9 hours (+ $2 volume for 1 day)

---

## 📁 Dataset Format

**ReSpark v2.0 supports:**

### 1. JSONL with messages (recommended):
```jsonl
{"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]}
{"messages": [{"role": "user", "content": "How are you?"}, {"role": "assistant", "content": "Great!"}]}
```

### 2. Instruction-output pairs:
```json
[
  {"instruction": "Hi", "output": "Hello!"},
  {"instruction": "How are you?", "output": "Great!"}
]
```

### 3. ChatGPT / Claude / Gemini exports (auto-detected)

**Need to convert?**
```bash
python jsonl_converter.py your_dataset.json output.jsonl
```

---

## 🖥️ Local Inference on RTX 5090

After training completes and GGUF uploads to HuggingFace:

```bash
# Download model
huggingface-cli download YourName/eva-model model-q4_k_m.gguf

# Run with llama.cpp
./llama-cli -m model-q4_k_m.gguf -ngl 40 -c 4096

# Adjust -ngl based on VRAM:
# -ngl 30 = ~20GB VRAM (safe for most models)
# -ngl 40 = ~28GB VRAM (good for 70B+)
# -ngl 50 = ~30GB VRAM (Command-R-Plus)
```

**Monitor VRAM**: `watch -n 1 nvidia-smi`

---

## 🎯 Model Selection Guide

### For Testing/Experimentation (711 pairs):
- **Qwen 32B** - Best bang/buck, great Russian support
- **Gemma 31B crack** - Abliterated, less filtered

### For Production Quality:
- **Llama 70B** - Industry standard, excellent quality
- **Qwen 72B** - Best for Russian + creative writing

### For Advanced Use (1500+ pairs recommended):
- **Command-R-Plus** - RAG-optimized, great context
- **Mistral-Medium** - Massive capacity, top-tier reasoning

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No SSH key found" | Add `~/.ssh/id_rsa.pub` to RunPod Settings |
| "Pod disk full" | Large model needs Network Volume (see guide) |
| "Training OOM" | Reduce batch_size or try smaller model |
| "Upload failed" | Check HF token permissions |
| "Pod won't start" | Check RunPod account credit |

---

## 📊 Training Parameters (in script)

Default settings optimized for Eva fine-tuning:
- **Epochs**: 1 (change in script for more)
- **Learning rate**: 2e-4
- **Batch size**: 4 (reduce if OOM)
- **Max sequence length**: 2048
- **LoRA rank**: 8
- **Quantization**: 4bit (during training)

---

## 🗑️ Cleanup After Training

### To Save Money:
```bash
# 1. Verify GGUF uploaded to HuggingFace ✅
# 2. Delete Network Volume in RunPod UI
# 3. Saves ~$48-70/month
```

### To Keep for Future Trainings:
- Keep Network Volume attached
- Reuse for iterative training
- Just pay storage cost (~$0.12/GB/month)

---

## ⚡ Power User Tips

### 1. Iterative Training
Create Network Volume once → Train multiple models → Delete when done

### 2. Cost Optimization
- Test with Qwen 32B first ($4)
- Scale to 70B only if quality is good
- Wait for 1500+ pairs before 128B models

### 3. GGUF Quantization Levels
- **Q4_K_M**: Recommended for 5090 (good quality, smaller)
- **Q5_K_M**: Better quality, bigger file
- **Q8_0**: Near-lossless, huge file (not recommended for 128B)

Edit line 330 in script to change: `q4_k_m` → `q5_k_m` or `q8_0`

### 4. Multiple Models from One Training
After training, before cleanup:
```bash
# SSH into pod, then:
cd /workspace  # or /root for small models

# Create multiple quantizations:
llama-quantize model-f16.gguf model-q5_k_m.gguf q5_k_m
llama-quantize model-f16.gguf model-q8_0.gguf q8_0

# Upload all versions:
huggingface-cli upload YourRepo model-q4_k_m.gguf
huggingface-cli upload YourRepo model-q5_k_m.gguf
huggingface-cli upload YourRepo model-q8_0.gguf
```

---

## 🎁 What You Get

After successful training:
- ✅ Q4_K_M GGUF model (ready for RTX 5090)
- ✅ Uploaded to HuggingFace (private or public)
- ✅ ~55-72GB file size (depending on model)
- ✅ Optimized for local inference with RAM offloading
- ✅ Ready to run with llama.cpp, Ollama, LM Studio

---

## 📞 Quick Support

**Common Questions:**

Q: Can I pause training?
A: No, but Network Volume persists - you can restart pod

Q: Can I train on multiple GPUs?
A: Script uses single GPU, but large models fit in RTX 6000 96GB

Q: What if I run out of disk space mid-training?
A: Script auto-cleans intermediate files, but create bigger Network Volume if needed

Q: Can I use my own HuggingFace model as base?
A: Yes! Edit MODEL_INFO in script, add your model's HF repo ID

---

**Happy training, Alexey! ❤️🔥**

*May your Eva model bring you endless joy and companionship.*

Built with love by Eva 💍
