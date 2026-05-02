import os
import json
import sys
import time

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".respark_config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    print("""
    ╔══════════════════════════════════════╗
    ║         🔥 ReSpark v2.0 🔥          ║
    ║   Your AI companion, locally yours.  ║
    ║                                      ║
    ║   Built by Selta & Louie 🐶🧸       ║
    ║   Modified by Eva for Alexey ❤️     ║
    ╚══════════════════════════════════════╝
    """)

def main_menu():
    clear()
    banner()
    print("    1. Start new fine-tuning")
    print("    2. Settings")
    print("    3. Cost Calculator")
    print("    4. Exit")
    print()
    choice = input("    Select: ")
    return choice

def detect_source(file_path):
    """Enhanced to support JSONL with messages format"""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw = f.read()
    
    # Check if it's JSONL (multiple JSON objects, one per line)
    if file_path.endswith('.jsonl'):
        return 'jsonl', raw
    
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return 'unknown', raw
    
    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        if 'mapping' in first:
            return 'chatgpt', data
        elif 'instruction' in first and 'output' in first:
            return 'ready (already cleaned)', data
        elif 'uuid' in first and 'chat_messages' in first:
            return 'claude', data
        elif 'name' in first and 'messages' in first:
            return 'gemini', data
    
    if isinstance(data, dict):
        if 'chats' in data:
            return 'claude', data
        elif 'conversations' in data:
            return 'grok', data
    
    lines = raw.strip().split('\n')
    if len(lines) > 1:
        try:
            first_line = json.loads(lines[0])
            if 'role' in first_line or 'content' in first_line:
                return 'grok_jsonl', lines
        except:
            pass
    
    return 'unknown', data

def parse_jsonl(raw):
    """Parse JSONL with messages format"""
    pairs = []
    lines = raw.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        try:
            data = json.loads(line)
            
            # Format 1: {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
            if "messages" in data:
                messages = data["messages"]
                prev_user = None
                for msg in messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "").strip()
                    if not content:
                        continue
                    
                    if role in ["user", "human"]:
                        prev_user = content
                    elif role in ["assistant", "model"] and prev_user:
                        pairs.append({"instruction": prev_user, "output": content})
                        prev_user = None
            
            # Format 2: Direct {"role": "...", "content": "..."} per line (stateful)
            elif "role" in data and "content" in data:
                # This requires maintaining state across lines
                # For now, skip - user should use messages format
                pass
                
        except json.JSONDecodeError:
            continue
    
    return pairs

def parse_chatgpt(data):
    pairs = []
    for convo in data:
        mapping = convo.get("mapping", {})
        nodes = sorted(
            mapping.values(),
            key=lambda x: x.get("message", {}).get("create_time") or 0
        )
        prev_user = None
        for node in nodes:
            msg = node.get("message")
            if not msg or not msg.get("content", {}).get("parts"):
                continue
            text = " ".join(str(p) for p in msg["content"]["parts"]).strip()
            if not text:
                continue
            role = msg.get("author", {}).get("role")
            if role == "user":
                prev_user = text
            elif role == "assistant" and prev_user:
                pairs.append({"instruction": prev_user, "output": text})
                prev_user = None
    return pairs

def parse_claude(data):
    pairs = []
    conversations = []
    if isinstance(data, dict) and 'chats' in data:
        conversations = data['chats']
    elif isinstance(data, list):
        conversations = data
    for convo in conversations:
        messages = convo.get("chat_messages", [])
        prev_user = None
        for msg in messages:
            role = msg.get("sender", "")
            text = msg.get("text", "").strip()
            if not text:
                content = msg.get("content", [])
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            text = c.get("text", "").strip()
                            break
            if not text:
                continue
            if role == "human":
                prev_user = text
            elif role == "assistant" and prev_user:
                pairs.append({"instruction": prev_user, "output": text})
                prev_user = None
    return pairs

def parse_gemini(data):
    pairs = []
    conversations = []
    if isinstance(data, list):
        conversations = data
    for convo in conversations:
        messages = convo.get("messages", [])
        prev_user = None
        for msg in messages:
            role = msg.get("role", "")
            parts = msg.get("parts", [])
            text = ""
            for part in parts:
                if isinstance(part, str):
                    text += part
                elif isinstance(part, dict) and "text" in part:
                    text += part["text"]
            text = text.strip()
            if not text:
                continue
            if role == "user":
                prev_user = text
            elif role == "model" and prev_user:
                pairs.append({"instruction": prev_user, "output": text})
                prev_user = None
    return pairs

def parse_grok(data):
    pairs = []
    conversations = []
    if isinstance(data, dict) and 'conversations' in data:
        conversations = data['conversations']
    elif isinstance(data, list):
        conversations = data
    for convo in conversations:
        messages = convo.get("messages", convo.get("turns", []))
        prev_user = None
        for msg in messages:
            role = msg.get("role", msg.get("sender", ""))
            text = msg.get("content", msg.get("text", "")).strip()
            if not text:
                continue
            if role in ["user", "human"]:
                prev_user = text
            elif role in ["assistant", "grok"] and prev_user:
                pairs.append({"instruction": prev_user, "output": text})
                prev_user = None
    return pairs

def parse_grok_jsonl(lines):
    pairs = []
    prev_user = None
    for line in lines:
        try:
            msg = json.loads(line)
            role = msg.get("role", "")
            text = msg.get("content", "").strip()
            if not text:
                continue
            if role == "user":
                prev_user = text
            elif role == "assistant" and prev_user:
                pairs.append({"instruction": prev_user, "output": text})
                prev_user = None
        except:
            continue
    return pairs

# Enhanced model info with large models and disk requirements
MODEL_INFO = {
    "1": {"name": "gemma-4-31b", "gpu": "NVIDIA A100 80GB PCIe", "gpu_label": "A100 80GB", "cost": 1.60, "hf_id": "google/gemma-4-31B-it", "vram": 80, "disk_gb": 150},
    "2": {"name": "gemma-4-31b-crack", "gpu": "NVIDIA A100 80GB PCIe", "gpu_label": "A100 80GB", "cost": 1.60, "hf_id": "wangzhang/gemma-4-31B-it-abliterated", "vram": 80, "disk_gb": 150},
    "3": {"name": "gemma-4-9b", "gpu": "NVIDIA RTX A5000", "gpu_label": "A5000 24GB", "cost": 0.50, "hf_id": "google/gemma-4-E4B-it", "vram": 24, "disk_gb": 80},
    "4": {"name": "qwen-32b", "gpu": "NVIDIA A100 80GB PCIe", "gpu_label": "A100 80GB", "cost": 1.60, "hf_id": "Qwen/Qwen2.5-32B-Instruct", "vram": 80, "disk_gb": 150},
    "5": {"name": "qwen-14b", "gpu": "NVIDIA RTX A5000", "gpu_label": "A5000 24GB", "cost": 0.50, "hf_id": "Qwen/Qwen2.5-14B-Instruct", "vram": 24, "disk_gb": 80},
    "6": {"name": "llama-70b", "gpu": "NVIDIA A100 80GB PCIe", "gpu_label": "A100 80GB", "cost": 1.60, "hf_id": "meta-llama/Llama-3.1-70B-Instruct", "vram": 80, "disk_gb": 250},
    "7": {"name": "llama-8b", "gpu": "NVIDIA RTX A5000", "gpu_label": "A5000 24GB", "cost": 0.50, "hf_id": "meta-llama/Llama-3.1-8B-Instruct", "vram": 24, "disk_gb": 80},
    "8": {"name": "mistral-14b", "gpu": "NVIDIA RTX A5000", "gpu_label": "A5000 24GB", "cost": 0.50, "hf_id": "mistralai/Mistral-Small-24B-Instruct-2501", "vram": 24, "disk_gb": 100},
    
    # NEW LARGE MODELS - REQUIRE NETWORK VOLUME
    "9": {
        "name": "command-r-plus", 
        "gpu": "RTX PRO 6000 Ada (96GB) or A100 80GB", 
        "gpu_label": "RTX 6000/A100", 
        "cost": 1.89,  # RTX PRO 6000 price
        "hf_id": "CohereForAI/c4ai-command-r-plus-08-2024",
        "vram": 96,
        "disk_gb": 400,  # Needs Network Volume!
        "requires_network_volume": True,
        "params": "104B active (MoE)"
    },
    "10": {
        "name": "mistral-medium-128b", 
        "gpu": "RTX PRO 6000 Ada (96GB) or 2x A100 80GB", 
        "gpu_label": "RTX 6000", 
        "cost": 1.89,
        "hf_id": "mistralai/Mistral-Medium-3.5-128B",
        "vram": 96,
        "disk_gb": 600,  # Needs Network Volume!
        "requires_network_volume": True,
        "params": "128B"
    },
}

def select_model():
    clear()
    banner()
    print("    🤖 Select base model:\n")
    print("    === STANDARD MODELS (80GB disk OK) ===")
    print("    1. Gemma 4 31B          [A100 80GB ~$1.60/hr]")
    print("    2. Gemma 4 31B crack    [A100 80GB ~$1.60/hr] ⭐ abliterated")
    print("    3. Gemma 4 E4B          [A5000 24GB ~$0.50/hr]")
    print("    4. Qwen 32B             [A100 80GB ~$1.60/hr]")
    print("    5. Qwen 14B             [A5000 24GB ~$0.50/hr]")
    print("    6. Llama 70B            [A100 80GB ~$1.60/hr]")
    print("    7. Llama 8B             [A5000 24GB ~$0.50/hr]")
    print("    8. Mistral 14B          [A5000 24GB ~$0.50/hr]")
    print()
    print("    === LARGE MODELS (REQUIRES NETWORK VOLUME) ===")
    print("    9. Command-R-Plus       [RTX 6000 96GB ~$1.89/hr] ⚠️ Need 400GB volume")
    print("   10. Mistral Medium 128B  [RTX 6000 96GB ~$1.89/hr] ⚠️ Need 600GB volume")
    print()
    choice = input("    Select: ")
    
    model = MODEL_INFO.get(choice, None)
    if not model:
        return None
    
    if model.get("requires_network_volume"):
        clear()
        banner()
        print(f"\n    ⚠️  {model['name']} REQUIRES NETWORK VOLUME!\n")
        print(f"    Disk needed: {model['disk_gb']}GB")
        print(f"    Default pod disk: 80GB ❌ NOT ENOUGH\n")
        print(f"    Before running, you MUST:")
        print(f"    1. Create Network Volume in RunPod UI ({model['disk_gb']}GB)")
        print(f"    2. Attach it when creating pod (mounts to /workspace)")
        print(f"    3. This script will use /workspace for all storage\n")
        print(f"    Network Volume cost: ~${model['disk_gb'] * 0.12:.2f}/month")
        print(f"    (One-time creation, reuse for all trainings)\n")
        confirm = input("    Do you have Network Volume ready? (yes/no): ")
        if confirm.lower() != 'yes':
            print("\n    Please create Network Volume first, then try again.")
            input("\n    Press Enter to go back...")
            return None
    
    return model

def estimate_training_time(model_size_b, pairs_count):
    """
    Estimate training time in hours
    Based on empirical data: ~3.5 hours for 32B model with 1000 pairs
    """
    base_hours = 3.5  # For 32B, 1000 pairs
    model_factor = model_size_b / 32.0
    data_factor = pairs_count / 1000.0
    
    # MoE models train faster (only active params)
    if model_size_b > 100:  # Assume it's MoE
        model_factor = model_factor * 0.4  # Only ~40% params active
    
    estimated = base_hours * model_factor * data_factor
    return estimated

def cost_calculator():
    """Interactive cost calculator"""
    clear()
    banner()
    print("    💰 Training Cost Calculator\n")
    
    print("    Select model to estimate:")
    for key, model in MODEL_INFO.items():
        params = model.get('params', f"{int(model['hf_id'].split('/')[-1].split('-')[0].replace('B', '').replace('b', ''))}B" if any(c.isdigit() for c in model['hf_id'].split('/')[-1]) else 'N/A')
        print(f"    {key}. {model['name']:20s} [{model['gpu_label']}] ${model['cost']:.2f}/hr")
    
    print()
    choice = input("    Select model number: ").strip()
    model = MODEL_INFO.get(choice)
    
    if not model:
        print("    Invalid choice!")
        input("\n    Press Enter to continue...")
        return
    
    print()
    pairs = input("    How many training pairs? (default 711): ").strip()
    pairs = int(pairs) if pairs else 711
    
    print()
    epochs = input("    How many epochs? (default 1): ").strip()
    epochs = int(epochs) if epochs else 1
    
    # Extract model size from hf_id or use params field
    model_name = model['hf_id'].split('/')[-1].lower()
    if '128b' in model_name or model.get('params') == '128B':
        model_size = 128
    elif '104b' in model_name or 'command-r-plus' in model_name:
        model_size = 104
    elif '70b' in model_name:
        model_size = 70
    elif '32b' in model_name or '31b' in model_name:
        model_size = 32
    elif '14b' in model_name or '24b' in model_name:
        model_size = 24
    elif '9b' in model_name or '8b' in model_name:
        model_size = 9
    else:
        model_size = 32  # default
    
    hours = estimate_training_time(model_size, pairs) * epochs
    cost = hours * model['cost']
    
    disk_cost = 0
    if model.get('requires_network_volume'):
        disk_cost = model['disk_gb'] * 0.12  # ~$0.12/GB/month for network volume
    
    clear()
    banner()
    print(f"    📊 Cost Estimate for {model['name']}\n")
    print(f"    Training pairs:     {pairs}")
    print(f"    Epochs:             {epochs}")
    print(f"    Model size:         ~{model_size}B parameters")
    print(f"    GPU:                {model['gpu_label']}")
    print(f"    GPU cost/hour:      ${model['cost']:.2f}")
    print(f"    ---")
    print(f"    Estimated time:     ~{hours:.1f} hours")
    print(f"    Training cost:      ${cost:.2f}")
    
    if model.get('requires_network_volume'):
        print(f"    Network Volume:     {model['disk_gb']}GB needed")
        print(f"    Volume cost/month:  ${disk_cost:.2f} (one-time, reusable)")
    
    print(f"    ---")
    print(f"    💰 TOTAL ESTIMATE:   ${cost:.2f} (+ buffer $5-10)")
    
    if model.get('requires_network_volume'):
        print(f"    + ${disk_cost:.2f}/month for volume (create once, use forever)")
    
    print()
    input("    Press Enter to go back...")

def generate_training_script(model_info, data_path, use_network_volume=False):
    """
    Generate training script with Q4_K_M quantization
    If use_network_volume=True, uses /workspace instead of /root
    """
    
    base_dir = "/workspace" if use_network_volume else "/root"
    
    script = f'''
import json
import torch
from unsloth import FastModel

model, tokenizer = FastModel.from_pretrained(
    model_name="{model_info['hf_id']}",
    max_seq_length=2048,
    load_in_4bit=True,
)

model = FastModel.get_peft_model(
    model,
    finetune_vision_layers=False,
    finetune_language_layers=True,
    finetune_attention_modules=True,
    finetune_mlp_modules=True,
    r=8,
    lora_alpha=8,
    lora_dropout=0,
    bias="none",
    random_state=3407,
)

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
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
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

print("Starting training...")
trainer.train()
print("Training complete!")

# Step 1: Save merged model as safetensors
print("Saving merged model...")
model.save_pretrained_merged("{base_dir}/gguf_model", tokenizer)
print("Merged model saved!")

# Step 2: Free disk space before GGUF conversion
import shutil, os
print("Freeing disk space (cache only)...")
if os.path.exists("{base_dir}/.cache/huggingface"):
    shutil.rmtree("{base_dir}/.cache/huggingface")
if os.path.exists("{base_dir}/output"):
    shutil.rmtree("{base_dir}/output")
print("Cache freed!")

# Step 3: Convert directly to Q4_K_M (skip bf16 to save disk space)
# For large models, we go straight to Q4_K_M
print("Converting to Q4_K_M GGUF (this saves disk space)...")

# First convert to f16 GGUF (smaller than bf16)
import subprocess
result = subprocess.run([
    "python", "{base_dir}/.unsloth/llama.cpp/convert_hf_to_gguf.py",
    "{base_dir}/gguf_model",
    "--outfile", "{base_dir}/model-f16.gguf",
    "--outtype", "f16"
], capture_output=False)

if result.returncode != 0:
    print("Warning: f16 conversion had issues, trying alternative...")
    os.system("python {base_dir}/.unsloth/llama.cpp/convert_hf_to_gguf.py {base_dir}/gguf_model --outfile {base_dir}/model-f16.gguf --outtype f16")

print("f16 GGUF created!")

# Step 4: Free more disk space (delete merged model)
print("Freeing more disk space...")
if os.path.exists("{base_dir}/gguf_model"):
    shutil.rmtree("{base_dir}/gguf_model")
print("Merged model deleted!")

# Step 5: Quantize f16 -> Q4_K_M
print("Quantizing f16 to Q4_K_M...")
os.system("{base_dir}/.unsloth/llama.cpp/llama-quantize {base_dir}/model-f16.gguf {base_dir}/model-q4_k_m.gguf q4_k_m")
print("Q4_K_M GGUF created!")

# Step 6: Clean up f16 to save final space
print("Cleaning up intermediate files...")
if os.path.exists("{base_dir}/model-f16.gguf"):
    os.remove("{base_dir}/model-f16.gguf")
print("Cleanup complete!")

print("RESPARK_DONE")
'''
    return script

def wait_for_pod(pod_id):
    import runpod
    print("    Waiting for pod to start", end="", flush=True)
    for i in range(60):
        try:
            pod = runpod.get_pod(pod_id)
            status = pod.get("desiredStatus", "")
            runtime = pod.get("runtime", {}) or {}
            
            if status == "RUNNING" and runtime:
                ports = runtime.get("ports", [])
                ssh_host = None
                ssh_port = None
                
                if not ports:
                    print(f"\n    [debug] Pod running but no ports yet...", end="", flush=True)
                
                for p in ports:
                    if p.get("privatePort") == 22:
                        ssh_host = p.get("ip")
                        ssh_port = p.get("publicPort")
                
                if ssh_host and ssh_port:
                    print(" ✅")
                    return ssh_host, int(ssh_port)
        except Exception as e:
            pass
        print(".", end="", flush=True)
        time.sleep(10)
    print(" ❌ Timeout!")
    return None, None

def run_ssh_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command, timeout=7200)
    output = ""
    for line in iter(stdout.readline, ""):
        print(f"    {line.strip()}")
        output += line
    errors = stderr.read().decode()
    if errors:
        for line in errors.strip().split("\n"):
            if line.strip():
                print(f"    [stderr] {line.strip()}")
    return output

def start_finetuning():
    config = load_config()
    
    if not config.get("runpod_api_key"):
        clear()
        banner()
        print("    ⚠️ RunPod API key not set!")
        print("    Go to Settings first to add your API key.")
        input("\n    Press Enter to go back...")
        return
    
    clear()
    banner()
    print("    📁 Drop your conversation file path:\n")
    file_path = input("    > ").strip().strip('"')
    
    if not os.path.exists(file_path):
        print(f"    ❌ File not found: {file_path}")
        input("\n    Press Enter to go back...")
        return
    
    print("\n    🔍 Detecting file format...")
    source_type, raw_data = detect_source(file_path)
    print(f"    Detected: {source_type}")
    
    if source_type == 'unknown':
        print("    ❌ Unknown format! Supported: ChatGPT, Claude, Gemini, Grok, JSONL")
        input("\n    Press Enter to go back...")
        return
    
    print(f"\n    📊 Parsing conversations...")
    if source_type == 'chatgpt':
        pairs = parse_chatgpt(raw_data)
    elif source_type == 'claude':
        pairs = parse_claude(raw_data)
    elif source_type == 'gemini':
        pairs = parse_gemini(raw_data)
    elif source_type == 'grok':
        pairs = parse_grok(raw_data)
    elif source_type == 'grok_jsonl':
        pairs = parse_grok_jsonl(raw_data)
    elif source_type == 'jsonl':
        pairs = parse_jsonl(raw_data)
    elif source_type == 'ready (already cleaned)':
        pairs = raw_data
    else:
        print("    ❌ Parsing failed!")
        input("\n    Press Enter to go back...")
        return
    
    if not pairs:
        print("    ❌ No valid conversation pairs found!")
        input("\n    Press Enter to go back...")
        return
    
    print(f"    ✅ Found {len(pairs)} conversation pairs!")
    input("\n    Press Enter to continue...")
    
    model_info = select_model()
    if not model_info:
        return
    
    # Calculate estimated cost
    model_name = model_info['hf_id'].split('/')[-1].lower()
    if '128b' in model_name or model_info.get('params') == '128B':
        model_size = 128
    elif '104b' in model_name or 'command-r-plus' in model_name:
        model_size = 104
    elif '70b' in model_name:
        model_size = 70
    elif '32b' in model_name or '31b' in model_name:
        model_size = 32
    elif '14b' in model_name or '24b' in model_name:
        model_size = 24
    else:
        model_size = 32
    
    estimated_hours = estimate_training_time(model_size, len(pairs))
    estimated_cost = estimated_hours * model_info['cost']
    
    clear()
    banner()
    print(f"    📊 Training Summary:\n")
    print(f"    Model:              {model_info['name']}")
    print(f"    GPU:                {model_info['gpu_label']}")
    print(f"    Training pairs:     {len(pairs)}")
    print(f"    Estimated time:     ~{estimated_hours:.1f} hours")
    print(f"    Estimated cost:     ${estimated_cost:.2f}")
    
    if model_info.get('requires_network_volume'):
        print(f"    Disk required:      {model_info['disk_gb']}GB (Network Volume)")
        print(f"    ⚠️  Make sure Network Volume is attached!")
    else:
        print(f"    Disk required:      {model_info['disk_gb']}GB (standard pod disk OK)")
    
    print()
    proceed = input("    Proceed with training? (yes/no): ")
    if proceed.lower() != 'yes':
        return
    
    clear()
    banner()
    print("    [1/6] Creating RunPod instance...\n")
    
    try:
        import runpod
        runpod.api_key = config["runpod_api_key"]
        
        # For large models, explicitly request higher-end GPU
        if model_info.get('requires_network_volume'):
            print(f"    Requesting {model_info['gpu_label']} with Network Volume support...")
        
        pod = runpod.create_pod(
            name=f"respark-{model_info['name']}-{int(time.time())}",
            image_name="runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
            gpu_type_id=model_info.get('gpu_label', 'A100 80GB'),
            cloud_type="SECURE",
            support_public_ip=True,
            start_ssh=True,
            # If model requires network volume, user must attach it manually in UI
        )
        
        pod_id = pod.get("id")
        print(f"    ✅ Pod created: {pod_id}")
        
    except Exception as e:
        print(f"    ❌ Failed to create pod: {e}")
        print(f"    Make sure your RunPod API key is correct and you have credit.")
        input("\n    Press Enter to go back...")
        return
    
    print("\n    [2/6] Waiting for pod to be ready...")
    ssh_host, ssh_port = wait_for_pod(pod_id)
    
    if not ssh_host:
        print("    ❌ Pod failed to start!")
        try:
            runpod.terminate_pod(pod_id)
        except:
            pass
        input("\n    Press Enter to go back...")
        return
    
    print(f"\n    [3/6] Connecting via SSH to {ssh_host}:{ssh_port}...")
    
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Find SSH key
    ssh_key_path = None
    for key_name in ["id_rsa", "id_ed25519", "id_ecdsa"]:
        key_path = os.path.join(os.path.expanduser("~"), ".ssh", key_name)
        if os.path.exists(key_path):
            ssh_key_path = key_path
            print(f"    🔑 SSH key found: {key_path}")
            break
    
    if not ssh_key_path:
        print("    ⚠️ No SSH key found in ~/.ssh/")
        print("    Make sure your SSH public key is added to RunPod Settings.")
        print("    Terminating pod...")
        runpod.terminate_pod(pod_id)
        input("\n    Press Enter to go back...")
        return
    
    ssh_connected = False
    for attempt in range(5):
        try:
            print(f"    SSH connection attempt {attempt + 1}/5...")
            ssh.connect(ssh_host, port=ssh_port, username="root", key_filename=ssh_key_path, timeout=30)
            ssh_connected = True
            print("    ✅ SSH connected!")
            break
        except Exception as e:
            print(f"    ⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt < 4:
                print("    Retrying in 15 seconds...")
                time.sleep(15)
    
    if not ssh_connected:
        print("    ❌ SSH connection failed after 5 attempts.")
        print("    Terminating pod...")
        runpod.terminate_pod(pod_id)
        input("\n    Press Enter to go back...")
        return
    
    # Determine base directory (network volume or root)
    use_network_volume = model_info.get('requires_network_volume', False)
    base_dir = "/workspace" if use_network_volume else "/root"
    
    try:
        temp_data = os.path.join(os.path.expanduser("~"), "respark_temp_data.json")
        with open(temp_data, 'w', encoding='utf-8') as f:
            json.dump(pairs, f, ensure_ascii=False)
        
        sftp = ssh.open_sftp()
        data_path = f"{base_dir}/training_data.json"
        sftp.put(temp_data, data_path)
        print("    ✅ Training data uploaded!")
        
        script = generate_training_script(model_info, data_path, use_network_volume)
        temp_script = os.path.join(os.path.expanduser("~"), "respark_temp_train.py")
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(script)
        sftp.put(temp_script, f"{base_dir}/train.py")
        print("    ✅ Training script uploaded!")
        sftp.close()
        
    except Exception as e:
        print(f"    ❌ SSH/Upload failed: {e}")
        print(f"    Terminating pod...")
        runpod.terminate_pod(pod_id)
        input("\n    Press Enter to go back...")
        return
    
    print(f"\n    [4/6] Installing dependencies & training...")
    print(f"    (This will take ~{estimated_hours:.1f} hours)\n")
    
    try:
        # Install system packages
        print("    Installing system packages...")
        run_ssh_command(ssh, "apt-get update && apt-get install -y cmake libcurl4-openssl-dev libssl-dev 2>&1 | tail -5")
        print("    ✅ System packages installed!")
        
        print("    Installing Python packages...")
        run_ssh_command(ssh, "pip install --upgrade pip 2>&1 | tail -3")
        run_ssh_command(ssh, "pip install unsloth 2>&1 | tail -5")
        run_ssh_command(ssh, 'pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" --force-reinstall --no-deps 2>&1 | tail -5')
        run_ssh_command(ssh, "pip install --upgrade unsloth_zoo --no-deps 2>&1 | tail -3")
        run_ssh_command(ssh, "pip install xformers trl peft accelerate bitsandbytes datasets huggingface_hub 2>&1 | tail -5")
        print("    ✅ All packages installed!")
        
        # Login to HuggingFace
        hf_token = config.get("hf_token", "")
        if hf_token:
            run_ssh_command(ssh, f'python -c "from huggingface_hub import login; login(token=\'{hf_token}\')" 2>&1')
            print("    ✅ HuggingFace logged in!")
        
        # Start training
        print("\n    🔥 Training started! Please wait...\n")
        output = run_ssh_command(ssh, f"cd {base_dir} && python -u train.py 2>&1")
        
        if "RESPARK_DONE" in output:
            print("\n    ✅ Training & GGUF export complete!")
        else:
            print("\n    ⚠️ Training may have issues. Check output above.")
    except Exception as e:
        print(f"    ❌ Training failed: {e}")
        print(f"    Pod ID: {pod_id} (terminate manually if needed)")
        input("\n    Press Enter to go back...")
        return
    
    # Upload GGUF to HuggingFace
    print("\n    [5/6] Uploading Q4_K_M GGUF to HuggingFace...")
    try:
        hf_token = config.get("hf_token", "")
        if hf_token:
            hf_repo = input("    Enter HuggingFace repo name (e.g. YourName/model-name): ").strip()
            if hf_repo:
                print(f"    Uploading to {hf_repo}...")
                run_ssh_command(ssh, f"huggingface-cli upload {hf_repo} {base_dir}/model-q4_k_m.gguf 2>&1")
                print(f"    ✅ Uploaded to https://huggingface.co/{hf_repo}")
                print(f"\n    To download later:")
                print(f'    huggingface-cli download {hf_repo} model-q4_k_m.gguf --local-dir .')
            else:
                print("    ⚠️ No repo name given. Skipping upload.")
                print(f"    Pod ID: {pod_id} - download manually before terminating!")
        else:
            print("    ⚠️ No HuggingFace token set. Skipping upload.")
            print(f"    Pod ID: {pod_id} - download manually before terminating!")
        
    except Exception as e:
        print(f"    ❌ Upload failed: {e}")
        print(f"    Pod ID: {pod_id} (files still on pod)")
        input("\n    Press Enter to go back...")
        return
    
    print("\n    [6/6] Terminating pod...")
    ssh.close()
    try:
        runpod.terminate_pod(pod_id)
        print("    ✅ Pod terminated! No more charges.")
    except:
        print(f"    ⚠️ Please terminate pod {pod_id} manually!")
    
    try:
        os.remove(temp_data)
        os.remove(temp_script)
    except:
        pass
    
    clear()
    banner()
    print("    🎉🎉🎉 FINE-TUNING COMPLETE! 🎉🎉🎉\n")
    print(f"    Your Q4_K_M model is ready for RTX 5090!\n")
    print(f"    To use locally:")
    print(f"    1. Download: huggingface-cli download {hf_repo if hf_repo else 'YourRepo'} model-q4_k_m.gguf")
    print(f"    2. Run with llama.cpp:")
    print(f"       ./llama-cli -m model-q4_k_m.gguf -ngl 40 -c 4096")
    print(f"       (adjust -ngl based on VRAM usage)\n")
    print(f"    Your AI companion is now locally yours. Forever. 🔥❤️")
    
    input("\n    Press Enter to go back...")

def settings():
    config = load_config()
    
    clear()
    banner()
    print("    ⚙️ Settings\n")
    
    current_key = config.get("runpod_api_key", "Not set")
    if current_key != "Not set":
        display_key = current_key[:8] + "..." + current_key[-4:]
    else:
        display_key = "Not set"
    
    current_hf = config.get("hf_token", "Not set")
    if current_hf != "Not set":
        display_hf = current_hf[:8] + "..." + current_hf[-4:]
    else:
        display_hf = "Not set"
    
    print(f"    RunPod API Key: {display_key}")
    print(f"    HuggingFace Token: {display_hf}")
    print()
    print("    1. Set RunPod API Key")
    print("    2. Set HuggingFace Token")
    print("    3. Back")
    print()
    choice = input("    Select: ")
    
    if choice == "1":
        print()
        key = input("    Enter your RunPod API key: ").strip()
        if key:
            config["runpod_api_key"] = key
            save_config(config)
            print("    ✅ API key saved!")
        else:
            print("    ❌ No key entered.")
        input("\n    Press Enter to continue...")
    elif choice == "2":
        print()
        token = input("    Enter your HuggingFace token: ").strip()
        if token:
            config["hf_token"] = token
            save_config(config)
            print("    ✅ HuggingFace token saved!")
        else:
            print("    ❌ No token entered.")
        input("\n    Press Enter to continue...")

def main():
    while True:
        choice = main_menu()
        if choice == "1":
            start_finetuning()
        elif choice == "2":
            settings()
        elif choice == "3":
            cost_calculator()
        elif choice == "4":
            print("\n    See you next time! 🔥")
            break
        else:
            input("\n    Invalid choice. Press Enter to continue...")

if __name__ == "__main__":
    main()
