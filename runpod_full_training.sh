#!/bin/bash

# Train Full Matchup-Specific Model on RunPod
# This trains the 612-parameter model on 96K possessions
# Expected time: 30-40 hours

set -e

# Configuration
POD_NAME="nba-matchup-training"
PROJECT_DIR="."

echo "🚀 Starting Full Matchup-Specific Model Training on RunPod..."
echo "Expected time: 30-40 hours"
echo ""

# Step 1: Ensure we have the RunPod CLI
if ! command -v runpodctl &> /dev/null; then
    echo "❌ runpodctl not found. Install from: https://github.com/runpod/runpod-cli"
    exit 1
fi

# Step 2: Create a pod (CPU is fine for MCMC, Stan doesn't use GPU)
echo "📦 Creating RunPod instance..."
echo "  CPU: 8 vCPU"
echo "  RAM: 32 GB"
echo "  Disk: 100 GB"

POD_ID=$(runpodctl create pod \
    --name "$POD_NAME" \
    --templateId "runpod/template-python:3.11" \
    --vcpu 8 \
    --mem 32 \
    --disk 100)

echo "✅ Pod created: $POD_ID"
echo ""

# Step 3: Upload necessary files
echo "📤 Uploading files..."
runpodctl send $POD_ID \
    matchup_specific_bayesian_data_full.csv \
    bayesian_model_k8_matchup_specific.stan \
    train_full_matchup_specific_runpod.py \
    requirements.txt \
    /workspace/nba_training/

echo "✅ Files uploaded"
echo ""

# Step 4: Install dependencies and start training
echo "🔧 Setting up environment..."
runpodctl exec $POD_ID -- bash -c "
    cd /workspace/nba_training
    
    # Install dependencies
    pip install -r requirements.txt
    pip install cmdstanpy
    
    # Verify Stan installation
    python -c 'import cmdstanpy; print(f\"Stan version: {cmdstanpy.__version__}\")'
    
    # Start training
    echo ''
    echo 'Starting training (this will take 30-40 hours)...'
    python train_full_matchup_specific_runpod.py \
        --data matchup_specific_bayesian_data_full.csv \
        --stan bayesian_model_k8_matchup_specific.stan \
        --draws 2000 \
        --tune 1000 \
        --chains 4 \
        --adapt-delta 0.99 \
        --output stan_model_results_full_matchup
"

echo ""
echo "✅ Training initiated on RunPod!"
echo ""
echo "To monitor progress:"
echo "  runpodctl exec $POD_ID -- bash -c 'tail -f /workspace/nba_training/*.log'"
echo ""
echo "To download results when complete:"
echo "  runpodctl receive $POD_ID /workspace/nba_training/stan_model_results_full_matchup/ ./"
echo ""
echo "To check pod status:"
echo "  runpodctl get pods"
echo ""
echo "To stop/remove pod:"
echo "  runpodctl remove $POD_ID"

