# Multi-GPU Support for ReSpark v2.0
# Use ONLY if single 96GB GPU unavailable and you MUST use 2x A100 80GB

## Modifications needed in ReSpark_v2.py

### 1. Update MODEL_INFO to specify multi-GPU requirement:

```python
"10": {
    "name": "mistral-medium-128b", 
    "gpu": "2x NVIDIA A100 80GB PCIe",  # Multi-GPU
    "gpu_label": "A100 80GB", 
    "cost": 3.20,  # 2x $1.60
    "hf_id": "mistralai/Mistral-Medium-3.5-128B",
    "vram": 160,  # Total across 2 GPUs
    "disk_gb": 600,
    "requires_network_volume": True,
    "requires_multi_gpu": True,  # NEW FLAG
    "num_gpus": 2  # NEW FIELD
},
```

### 2. Update RunPod pod creation (line ~440):

```python
# In start_finetuning() function, when creating pod:

num_gpus = model_info.get('num_gpus', 1)

pod = runpod.create_pod(
    name=f"respark-{model_info['name']}-{int(time.time())}",
    image_name="runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
    gpu_type_id=model_info.get('gpu_label', 'A100 80GB'),
    gpu_count=num_gpus,  # NEW: Request multiple GPUs
    cloud_type="SECURE",
    support_public_ip=True,
    start_ssh=True,
)
```

### 3. Modify generate_training_script() for multi-GPU:

```python
def generate_training_script(model_info, data_path, use_network_volume=False):
    base_dir = "/workspace" if use_network_volume else "/root"
    is_multi_gpu = model_info.get('requires_multi_gpu', False)
    
    # Different training script for multi-GPU
    if is_multi_gpu:
        script = f'''
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from accelerate import Accelerator

# Initialize accelerator for multi-GPU
accelerator = Accelerator()

print(f"Using {{torch.cuda.device_count()}} GPUs")

# Load model with device_map="auto" for multi-GPU distribution
model = AutoModelForCausalLM.from_pretrained(
    "{model_info['hf_id']}",
    load_in_4bit=True,
    device_map="auto",  # Automatically distribute across GPUs
    torch_dtype=torch.bfloat16,
)

tokenizer = AutoTokenizer.from_pretrained("{model_info['hf_id']}")

# Prepare model for training
model = prepare_model_for_kbit_training(model)

# LoRA configuration
lora_config = LoraConfig(
    r=8,
    lora_alpha=8,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

# Load dataset
with open("{data_path}", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

from datasets import Dataset

def format_prompt(example):
    return {{"text": f"<|turn>user\\n{{example['instruction']}}<turn|>\\n<|turn>model\\n{{example['output']}}<turn|>"}}

dataset = Dataset.from_list(raw_data)
dataset = dataset.map(format_prompt)
print(f"Dataset: {{len(dataset)}}")

from trl import SFTTrainer, SFTConfig

trainer = SFTTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=dataset,
    args=SFTConfig(
        dataset_text_field="text",
        max_length=2048,
        packing=True,
        per_device_train_batch_size=2,  # Reduced for multi-GPU
        gradient_accumulation_steps=8,  # Increased to compensate
        warmup_steps=30,
        num_train_epochs=1,
        learning_rate=2e-4,
        bf16=True,
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=3407,
        output_dir="{base_dir}/output",
        report_to="none",
    ),
)

print("Starting multi-GPU training...")
trainer.train()
print("Training complete!")

# Rest of the script same as single-GPU version...
# (merge, GGUF conversion, etc.)
'''
    else:
        # Original single-GPU script
        script = f'''
        # ... (existing single-GPU code)
        '''
    
    return script
```

### 4. Cost calculation update:

In `estimate_training_time()`, account for multi-GPU:

```python
def estimate_training_time(model_size_b, pairs_count):
    base_hours = 3.5
    model_factor = model_size_b / 32.0
    data_factor = pairs_count / 1000.0
    
    if model_size_b > 100:
        model_factor = model_factor * 0.4
    
    estimated = base_hours * model_factor * data_factor
    return estimated
```

Cost in `start_finetuning()`:
```python
num_gpus = model_info.get('num_gpus', 1)
estimated_cost = estimated_hours * model_info['cost']
# model_info['cost'] should already be 2x for multi-GPU models
```

---

## WARNING: Multi-GPU Caveats

1. **Communication overhead**: Training may be slower than expected due to GPU-to-GPU sync
2. **Memory imbalance**: device_map="auto" may not distribute perfectly
3. **Debugging harder**: Errors can be GPU-specific
4. **Cost**: 2x GPU = 2x price (~$3.20/hr vs $1.89/hr)

## Recommendation

**DON'T use multi-GPU unless absolutely necessary!**

Instead:
1. Wait for RTX PRO 6000 Ada 96GB to become available
2. Or use RunPod's "Auto-Start" feature to grab it when free
3. Or train slightly smaller model (Qwen 72B fits in A100 80GB)

Multi-GPU is a last resort option.

---

## Testing Multi-GPU Setup

Before running full training, test GPU detection:

```python
# Quick test script to verify multi-GPU:
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Number of GPUs: {torch.cuda.device_count()}")
for i in range(torch.cuda.device_count()):
    print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
    print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB")
```

Should output:
```
CUDA available: True
Number of GPUs: 2
GPU 0: NVIDIA A100-PCIE-80GB
  Memory: 80.00 GB
GPU 1: NVIDIA A100-PCIE-80GB
  Memory: 80.00 GB
```

If you see only 1 GPU, pod wasn't created correctly with multi-GPU.
