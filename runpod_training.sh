#!/bin/bash

# NBA Lineup Optimizer - RunPod Training Script
# This script automates the entire process of training the model on RunPod

set -e  # Exit on any error

# Configuration
POD_NAME="nba-model-training"
TEMPLATE_ID="runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04"  # CPU template
VCPU=8
MEMORY=32
DISK_SIZE=50
PROJECT_DIR="lineupOptimizer"

echo "🚀 Starting NBA Model Training on RunPod..."

# Step 1: Create the pod
echo "📦 Creating RunPod instance..."
runpodctl create pod \
    --name "$POD_NAME" \
    --templateId "$TEMPLATE_ID" \
    --vcpu $VCPU \
    --mem $MEMORY \
    --containerDiskSize $DISK_SIZE \
    --secureCloud

echo "⏳ Waiting for pod to be ready..."
sleep 30

# Step 2: Send the project files
echo "📤 Uploading project files..."
runpodctl send "$POD_NAME" . /workspace/

# Step 3: Execute the setup and training
echo "🔧 Setting up environment and starting training..."
runpodctl exec "$POD_NAME" -- bash -c "
    cd /workspace/$PROJECT_DIR
    
    # Install Docker if not already installed
    if ! command -v docker &> /dev/null; then
        echo 'Installing Docker...'
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        sudo usermod -aG docker \$USER
    fi
    
    # Build the Docker image
    echo 'Building Docker image...'
    docker build -t nba-trainer .
    
    # Start the training in detached mode
    echo 'Starting model training...'
    docker run -d --name model-training-container nba-trainer
    
    echo 'Training started! Container is running in the background.'
    echo 'You can check logs with: docker logs -f model-training-container'
"

echo "✅ Training has been initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Monitor progress: runpodctl exec $POD_NAME -- docker logs -f model-training-container"
echo "2. Check status: runpodctl exec $POD_NAME -- docker ps"
echo "3. When complete, download results: runpodctl receive $POD_NAME /workspace/$PROJECT_DIR/model_coefficients.csv ./"
echo "4. Download supercluster results: runpodctl receive $POD_NAME /workspace/$PROJECT_DIR/supercluster_coefficients.csv ./"
echo "5. Clean up: runpodctl remove $POD_NAME"
echo ""
echo "🎯 Training is now running in the background on RunPod!"
