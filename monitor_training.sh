#!/bin/bash
# Quick monitoring script for local training

echo "📊 Training Status Monitor"
echo "========================"
echo ""

# Check if process is running
PID=$(ps aux | grep "train_full" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
    echo "❌ Training process not found"
    echo "   It may have completed or crashed"
    exit 1
fi

echo "✅ Training is running (PID: $PID)"
echo ""

# Check output directory
if [ -d "stan_model_results_full_matchup" ]; then
    echo "📁 Output directory exists:"
    ls -lh stan_model_results_full_matchup/ | tail -5
else
    echo "📁 Waiting for output directory..."
fi

# Check process stats
echo ""
echo "🔍 Process Information:"
ps -p $PID -o pid,ppid,cmd,%cpu,%mem,etime

# Check if Stan files are being created
echo ""
echo "📈 Stan Output Files:"
ls -lt stan_model_results_full_matchup/*.csv 2>/dev/null | head -10 || echo "  (No output files yet - training in warmup phase)"

echo ""
echo "⏱️  Training started at: 12:05 PM"
echo "   Expected completion: 6-10 AM tomorrow"
echo ""
echo "💡 Tips:"
echo "   - Training runs in background"
echo "   - It will take 30-40 hours"
echo "   - Leave your computer on"
echo "   - Check back tomorrow morning"
echo ""
echo "🛑 To stop: kill $PID"

