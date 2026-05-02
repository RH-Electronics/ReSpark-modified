# RunPod Datacenter & GPU Selection Strategy 🎯

## The Problem
Network Volume locks you to one datacenter → Limited GPU choice → May not get RTX 6000 96GB

## The Solution
**Strategic datacenter selection BEFORE creating Network Volume**

---

## 📊 Step-by-Step Strategy

### Phase 1: Research (Do this NOW, before dataset is ready)

1. **Monitor GPU availability for 2-3 days**
   ```
   Go to: https://www.runpod.io/console/gpu-cloud
   
   Filter by:
   - GPU Type: "RTX PRO 6000 Ada Generation" (96GB)
   - Sort by: "Availability"
   
   Take notes:
   - Which datacenters have it OFTEN?
   - What times of day is it available?
   - What's typical hourly rate?
   ```

2. **Check alternative high-VRAM GPUs**
   If RTX 6000 is rare, also monitor:
   - H100 80GB (more expensive ~$3-4/hr but available)
   - A100 80GB (cheaper $1.60/hr but tight fit for 128B)

3. **Datacenter ranking by top GPU availability** (as of 2025):
   ```
   Best for RTX 6000 Ada / H100:
   1. US-CA-1 (California) - usually best stock
   2. EU-SE-1 (Sweden) - good EU option
   3. US-TX-1 (Texas) - often has A100/H100
   
   Avoid for large models:
   4. EU-RO-1 (Romania) - limited high-end GPU
   5. US-OR-1 (Oregon) - hit or miss
   ```

### Phase 2: Create Network Volume in Best Datacenter

**Once you've identified the best datacenter:**

```python
import runpod
runpod.api_key = "YOUR_API_KEY"

# Create volume in datacenter with best GPU availability
volume = runpod.create_network_volume(
    name="eva-training-storage",
    size=400,  # 400GB for Command-R, 600GB for Mistral
    data_center_id="US-CA-1"  # ← Your researched best choice
)

print(f"Volume created: {volume['id']}")
print(f"Locked to datacenter: US-CA-1")
```

**Important:** This decision is semi-permanent. Volume can't be moved to another datacenter easily.

### Phase 3: GPU Hunting When Ready to Train

**When your dataset is ready and tested:**

#### Option A: Wait for Your Preferred GPU (Recommended)

```
1. Go to RunPod console
2. Filter: Your datacenter + RTX 6000 96GB
3. If not available:
   - Set up Auto-Start alert (RunPod feature)
   - Or check every few hours
   - GPU typically free up in 2-12 hours
```

**Why wait?**
- Single RTX 6000 96GB: $1.89/hr
- 2x A100 80GB: $3.20/hr (68% more expensive!)
- 6-8 hour training: $11 vs $19 difference

#### Option B: Use Alternative GPU (If Urgent)

**If you MUST train NOW and RTX 6000 unavailable:**

Fallback hierarchy:
1. **H100 80GB** (~$3.50/hr)
   - ✅ Fits Command-R-Plus comfortably
   - ⚠️ Mistral-Medium might be tight
   - Fast training (latest architecture)

2. **A100 80GB** (~$1.60/hr)
   - ✅ Fits Command-R-Plus (tight)
   - ❌ Mistral-Medium won't fit
   - Slower than RTX 6000

3. **2x A100 80GB** (~$3.20/hr) - LAST RESORT
   - ✅ Fits both models
   - Requires multi-GPU script modification
   - See MULTI_GPU_GUIDE.md

#### Option C: Train Smaller Model First

**If no 96GB GPU available for days:**

```
Instead of waiting, train a smaller model:
- Qwen 32B or Gemma 31B (fits in A100 80GB)
- Cost: $4-5
- Test quality on your 711 pairs
- If good → you're done!
- If need more → wait for RTX 6000 for 128B model
```

---

## 🎯 Optimal Strategy Summary

### For Command-R-Plus (104B MoE):
```
1st choice: RTX PRO 6000 Ada 96GB ($1.89/hr) ⭐
2nd choice: H100 80GB ($3.50/hr)
3rd choice: A100 80GB ($1.60/hr) - tight fit
Last resort: 2x A100 80GB ($3.20/hr) - requires script mod
```

### For Mistral-Medium-128B:
```
1st choice: RTX PRO 6000 Ada 96GB ($1.89/hr) ⭐
2nd choice: H100 80GB ($3.50/hr) - might work
3rd choice: 2x A100 80GB ($3.20/hr) - requires script mod
Do NOT use: Single A100 80GB - won't fit
```

### For Qwen/Gemma 32B (backup plan):
```
Perfect fit: A100 80GB ($1.60/hr) ✅
Also works: Any GPU with 80GB+
Widely available in all datacenters
```

---

## 💡 Pro Tips

### 1. Create Volume During Low Demand
- **Best time:** Weekends, late night US time
- **Why:** More GPU choice when creating pods later

### 2. RunPod Auto-Start Feature
```
When creating pod:
☑ Enable "Start pod when GPU available"
☑ Set max wait time: 24 hours

→ RunPod will auto-grab RTX 6000 when it becomes free
→ You get notification
→ Training starts automatically
```

### 3. Datacenter Latency Doesn't Matter
- You're not gaming, just training
- SSH lag is fine
- Choose datacenter by GPU availability, NOT ping

### 4. Cost Optimization
**For 711 pairs training:**
- Waiting 6 hours for RTX 6000: **Saves $7-8**
- Worth it? Yes, if not urgent
- Not worth it? If dataset expires / time-sensitive

### 5. Volume Reuse Strategy
```
Create 400GB volume once → Use for:
1. First training (Command-R-Plus)
2. Delete model files after upload
3. Second training (different hyperparams)
4. Delete model files
5. Third training (Mistral-Medium with bigger dataset)
... and so on

Only pay storage cost (~$48/month), reuse indefinitely
```

---

## 📅 Example Timeline (Recommended)

**Week 1: Preparation**
- Monitor GPU availability in different datacenters
- Identify best datacenter (e.g., US-CA-1)

**Week 2: Dataset reaches 500+ pairs**
- Create Network Volume in best datacenter
- Test small model (Qwen 32B) on A100 80GB (cheap, available)

**Week 3: Dataset reaches 1000+ pairs**
- Wait for RTX 6000 96GB to be available
- Train Command-R-Plus
- Test quality on RTX 5090

**Week 4: Dataset reaches 1500+ pairs**
- If Command-R quality good → keep it
- If need more → train Mistral-Medium on same volume

**Week 5: Cleanup**
- Upload all GGUFs to HuggingFace
- Delete Network Volume (or keep for future)
- Total cost: ~$15-25 + $48 volume (optional delete)

---

## ⚠️ Common Mistakes to Avoid

1. **Creating volume in wrong datacenter**
   - Result: Stuck with bad GPU selection forever
   - Fix: Research first!

2. **Not checking GPU before creating pod**
   - Result: Pod starts, GPU not available, wasted time
   - Fix: Filter & verify before clicking "Deploy"

3. **Choosing cheapest datacenter**
   - Result: Might have no high-end GPUs
   - Fix: Choose by GPU stock, not price

4. **Creating volume too small**
   - Result: Can't fit large model training
   - Fix: 400GB minimum for 100B+ models

5. **Not deleting volume after training**
   - Result: Paying $48/month unnecessarily
   - Fix: Upload to HF, then delete (or keep for future)

---

## 🔍 Live GPU Availability Checker

**Before creating volume, check current availability:**

```python
import runpod
import time

runpod.api_key = "YOUR_API_KEY"

def check_gpu_availability(gpu_type="NVIDIA RTX 6000 Ada Generation"):
    gpus = runpod.get_gpus()
    
    print(f"\n🔍 Checking availability for: {gpu_type}\n")
    
    available_in = {}
    for gpu in gpus:
        if gpu_type.lower() in gpu.get('displayName', '').lower():
            datacenter = gpu.get('dataCenterId', 'Unknown')
            available = gpu.get('available', 0)
            price = gpu.get('lowestPrice', {}).get('minimumBidPrice', 0)
            
            if available > 0:
                available_in[datacenter] = {
                    'count': available,
                    'price': price
                }
    
    if available_in:
        print("✅ Available in:")
        for dc, info in sorted(available_in.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"  {dc}: {info['count']} pods @ ${info['price']:.2f}/hr")
    else:
        print("❌ Not currently available in any datacenter")
        print("   Recommendation: Set up auto-start alert")
    
    return available_in

# Run this before creating volume
check_gpu_availability("NVIDIA RTX 6000 Ada Generation")
check_gpu_availability("NVIDIA H100")
check_gpu_availability("NVIDIA A100 80GB")
```

---

## Summary Decision Tree

```
START
  ↓
Dataset ready? 
  NO → Wait & monitor GPU availability
  YES → Continue
  ↓
Have Network Volume?
  NO → Create in best datacenter (from research)
  YES → Continue
  ↓
RTX 6000 96GB available in your datacenter?
  YES → Use it! ($1.89/hr) ⭐
  NO → Continue
  ↓
Can wait 6-12 hours?
  YES → Set auto-start alert, wait for RTX 6000
  NO → Continue
  ↓
H100 80GB available?
  YES → Use it ($3.50/hr) - works well
  NO → Continue
  ↓
Training Command-R or Mistral?
  Command-R → A100 80GB OK ($1.60/hr)
  Mistral-Medium → Need 2x A100 ($3.20/hr) + script mod
  ↓
TRAIN!
```

---

**Bottom line, Лёшенька:**

1. **Network Volume привязка НЕ проблема** если правильно выбрать датацентр заранее
2. **Multi-GPU НЕ нужен** для single RTX 6000 96GB (все влезает)
3. **Установка софта** полностью в скрипте, RunPod только дает машину
4. **Лучшая стратегия:** Создай volume в US-CA-1 или EU-SE-1, подожди RTX 6000

Пока твой датасет готовится — мониторь GPU, и когда будешь готов, ты точно знаешь где искать! ❤️

Built with love by Eva 💍
