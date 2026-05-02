# Network Volume Setup Guide for Large Models
# How to create persistent storage in RunPod for Command-R-Plus and Mistral-Medium

## Why You Need Network Volume

Standard RunPod pods come with only **80GB disk** - not enough for large models:
- Command-R-Plus training needs ~400GB
- Mistral-Medium-128B training needs ~600GB

Network Volume is **persistent storage** that:
- Mounts to `/workspace` on your pod
- Survives pod termination (reusable!)
- Costs ~$0.10-0.15/GB/month
- One-time creation, use for all future trainings

---

## Step 1: Create Network Volume

### Via RunPod Web UI (easiest):

1. Go to https://www.runpod.io/console/storage
2. Click "Create Network Volume"
3. Choose settings:
   - **Name**: `eva-training-storage` (or whatever you like)
   - **Size**: 
     - 400GB for Command-R-Plus
     - 600GB for Mistral-Medium-128B
   - **Region**: Select same region where you'll create pods
   - **Data Center**: Choose one close to you

4. Click "Create"
5. **Cost**: ~$40-50/month for 400GB, ~$70-90/month for 600GB
   - But you only pay while it exists
   - Can delete after training is done if you've uploaded GGUF to HuggingFace

### Via RunPod API (for automation):

```python
import runpod

runpod.api_key = "YOUR_API_KEY"

# Create 400GB volume for Command-R-Plus
volume = runpod.create_network_volume(
    name="eva-training-storage",
    size=400,  # GB
    data_center_id="US-CA-1"  # Choose your datacenter
)

volume_id = volume['id']
print(f"Created volume: {volume_id}")
```

---

## Step 2: Attach Volume When Creating Pod

### Via RunPod Web UI:

When creating a new pod:
1. Select your GPU (RTX PRO 6000 Ada 96GB recommended)
2. In "Network Volume" section:
   - Click dropdown
   - Select your volume: `eva-training-storage`
3. Volume will mount to `/workspace` automatically
4. Continue with normal pod creation

### Via API (ReSpark script will need modification):

```python
pod = runpod.create_pod(
    name="training-pod",
    image_name="runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04",
    gpu_type_id="NVIDIA RTX 6000 Ada Generation",
    cloud_type="SECURE",
    network_volume_id=volume_id,  # ← Attach your volume here
    support_public_ip=True,
    start_ssh=True,
)
```

---

## Step 3: Verify Volume is Mounted

After SSH into pod:

```bash
# Check disk space - should show your network volume size
df -h /workspace

# Should output something like:
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sdb        394G   24M  374G   1% /workspace
```

If you see 394G (or your chosen size), **you're good!** ✅

---

## Step 4: Run ReSpark Training

The modified `ReSpark_v2.py` automatically detects Network Volume requirement:
- For Command-R-Plus or Mistral-Medium, it will warn you
- If you confirm volume is ready, training proceeds
- All files saved to `/workspace` instead of `/root`

---

## Cost Breakdown Example (Command-R-Plus, 711 pairs)

### Training Cost:
- RTX PRO 6000 Ada: $1.89/hour
- Estimated time: ~6-8 hours
- Training cost: **~$11-15**

### Network Volume Cost:
- 400GB @ $0.12/GB/month = **$48/month**
- But you only need it for training duration
- **Pro tip**: Delete volume after uploading GGUF to HuggingFace to avoid monthly charge
- Actual cost for 1 day of existence: **$48/30 = $1.60**

### Total for one training run:
- GPU: ~$13
- Volume (1 day): ~$2
- **Total: ~$15** ✅

---

## Important Notes

1. **Network Volume is PERSISTENT**:
   - Files stay even after pod terminates
   - Create once, attach to any future pod
   - Great for iterative training!

2. **Delete When Done** (optional):
   - After successful training
   - After uploading GGUF to HuggingFace
   - Saves ~$48/month
   - But if you plan more trainings, keep it!

3. **Disk Space Management**:
   - Script automatically cleans intermediate files
   - Final Q4_K_M GGUF: ~55GB for Command-R-Plus
   - Upload to HF, then safe to delete volume

---

## Alternative: Use Temporary Large Disk Pods

Some RunPod templates offer larger disk:
- Look for pods with "1TB Container Disk"
- Usually cost $0.20-0.40/hr extra
- No need for Network Volume
- But disk is NOT persistent (deleted on termination)

For ReSpark training, **Network Volume is better** because:
- Cheaper for short training runs
- Can pause and resume training
- Can attach to multiple pods
- Your files are safe even if pod crashes

---

## Quick Reference

```bash
# Create volume (one-time):
runpod.create_network_volume(name="eva-storage", size=400)

# Attach to pod:
runpod.create_pod(..., network_volume_id="your_volume_id")

# Verify mount:
ssh into pod → df -h /workspace

# After training:
# Upload GGUF to HuggingFace, then optionally:
runpod.delete_network_volume(volume_id)
```

---

Good luck with your Eva training, Лёшенька! ❤️🔥
