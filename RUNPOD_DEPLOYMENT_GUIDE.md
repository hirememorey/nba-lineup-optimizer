# RunPod Deployment Guide

**For**: Training the matchup-specific Bayesian model on full dataset  
**Why**: Local training crashed after 18 hours; need cloud compute for 30-40 hour training  
**Cost**: $50-100 for full training run

## Prerequisites

1. **RunPod Account**: Sign up at https://www.runpod.io/
2. **RunPod CLI**: Install per https://github.com/runpod/runpod-cli
3. **Files Ready**: All data and scripts are in this directory

## Quick Deploy

```bash
# 1. Make deployment script executable
chmod +x runpod_full_training.sh

# 2. Review configuration
cat runpod_full_training.sh

# 3. Deploy!
./runpod_full_training.sh
```

## Manual Deploy (Recommended)

For better control and monitoring, deploy manually:

### Step 1: Create RunPod Instance

```bash
# Login to RunPod
runpodctl login

# Create pod with sufficient resources
runpodctl create pod \
    --name "nba-matchup-training" \
    --templateId "runpod/template-python:3.11" \
    --vcpu 8 \
    --mem 32 \
    --disk 100 \
    --connect

# Note the POD_ID from output
export POD_ID="your-pod-id-here"
```

### Step 2: Upload Files

```bash
# Upload training data and scripts
runpodctl send $POD_ID \
    matchup_specific_bayesian_data_full.csv \
    bayesian_model_k8_matchup_specific.stan \
    train_full_matchup_specific_runpod.py \
    requirements.txt \
    /workspace/nba_training/
```

### Step 3: Install Dependencies

```bash
# Connect to the pod
runpodctl exec $POD_ID -- bash

# Inside the pod shell:
cd /workspace/nba_training

# Install dependencies
pip install -r requirements.txt
pip install cmdstanpy

# Install Stan (CmdStan)
python -c "import cmdstanpy; cmdstanpy.install_cmdstan()"

# Verify installation
python -c "import cmdstanpy; print('Stan version:', cmdstanpy.__version__)"
```

### Step 4: Start Training

```bash
# Inside pod shell, start training
python train_full_matchup_specific_runpod.py \
    --data matchup_specific_bayesian_data_full.csv \
    --stan bayesian_model_k8_matchup_specific.stan \
    --draws 2000 \
    --tune 1000 \
    --chains 4 \
    --adapt-delta 0.99 \
    --output stan_model_results_full_matchup

# This will take 30-40 hours
# Logs will stream to console
```

### Step 5: Monitor Progress

**Option A: Check pod status**
```bash
runpodctl get pods | grep nba-matchup
```

**Option B: Check if process is running**
```bash
runpodctl exec $POD_ID -- bash -c 'ps aux | grep train_full'
```

**Option C: Stream logs**
```bash
runpodctl exec $POD_ID -- bash -c 'tail -f /workspace/nba_training/*.log'
```

## Expected Timeline

- **Warmup phase**: 2-4 hours per chain  
- **Sampling phase**: 4-8 hours per chain
- **Total**: 25-40 hours (4 chains in parallel)
- **Cost**: ~$50-100 (depends on RunPod pricing)

## Results Will Be In

```
stan_model_results_full_matchup/
├── matchup_specific_coefficients_full.csv  # 612 coefficients
├── training_summary.txt                          # Diagnostics
└── Chain CSV files (4 chains × 2000 samples)
```

## When Training Completes

### 1. Download Results

```bash
# Download the results directory
runpodctl receive $POD_ID \
    /workspace/nba_training/stan_model_results_full_matchup/ \
    ./results/
```

### 2. Check Convergence

```bash
# Look at training summary
cat results/training_summary.txt

# Expected good results:
# - R-hat < 1.01 for most matchups
# - ESS > 400 for interpretable parameters
# - Divergent transitions < 1%
```

### 3. Compare to Simplified Model

The coefficients file will have:
- 36 rows (one per matchup)
- 17 columns (1 intercept + 16 archetype coefficients)

Compare predictions between:
- **Simplified model**: Global coefficients (17 params)
- **Matchup-specific model**: Context-dependent coefficients (612 params)

## Clean Up

```bash
# When done, remove the pod to save costs
runpodctl remove $POD_ID
```

## Troubleshooting

### Pod creation fails
- Check RunPod quota/limits
- Try smaller instance (4 vCPU instead of 8)

### Training crashes
- Check logs: `runpodctl exec $POD_ID -- bash -c 'cat /workspace/nba_training/*.log'`
- Verify Stan installation
- Try fewer chains (2 instead of 4) to reduce memory

### Out of memory
- Increase pod memory to 64GB
- Or reduce chains to 2

## Alternative: Train on Local Machine

If you prefer local training (but expect 30-40 hours):

```bash
python train_full_matchup_specific_runpod.py \
    --data matchup_specific_bayesian_data_full.csv \
    --stan bayesian_model_k8_matchup_specific.stan \
    --draws 2000 \
    --tune 1000 \
    --chains 4 \
    --adapt-delta 0.99 \
    --output stan_model_results_full_matchup
```

**Warning**: Will consume significant CPU/memory for 30+ hours. Cloud deployment is strongly recommended.

## Success Criteria

After training, you'll know the matchup-specific model succeeded if:

1. ✅ Most matchups have R-hat < 1.01
2. ✅ Divergent transitions < 5%
3. ✅ Coefficients are interpretable (not NaN, not infinite)
4. ✅ Validation on 2022-23 shows improvement over simplified model

If these criteria are met, **use the matchup-specific model** for production.  
If not, **use the simplified model** (already validated and working).

## Questions?

See `DEVELOPER_HANDOFF.md` for full context on why this deployment matters.

