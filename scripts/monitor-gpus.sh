#!/bin/bash
# monitor-gpus.sh - Monitor GPU usage during inference
#
# This script provides real-time monitoring of GPU utilization, memory usage,
# and temperature during llama.cpp inference.
#
# Usage:
#   ./scripts/monitor-gpus.sh

echo "========================================"
echo "GPU Monitoring for llama.cpp"
echo "========================================"
echo ""
echo "Press Ctrl+C to exit"
echo ""

# Check if nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: nvidia-smi not found"
    echo "Please ensure NVIDIA drivers are installed"
    exit 1
fi

# Show GPU topology (NVLink connections)
echo "GPU Topology (NVLink/PCIe connections):"
echo "----------------------------------------"
nvidia-smi topo -m
echo ""
echo "Note: 'NV#' indicates NVLink connections (best for multi-GPU)"
echo "      'SYS' indicates PCIe connections (slower)"
echo ""
read -p "Press Enter to start monitoring..."
echo ""

# Real-time monitoring
watch -n 1 '
echo "=== GPU Utilization & Memory Usage ==="
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw \
    --format=csv,noheader,nounits | \
    awk -F, '\''{
        printf "GPU %s: %s\n", $1, $2;
        printf "  Utilization: %s%%\n", $3;
        printf "  Memory: %s MB / %s MB (%.1f%%)\n", $4, $5, ($4/$5)*100;
        printf "  Temperature: %s°C\n", $6;
        printf "  Power: %s W\n\n", $7;
    }'\''

echo "=== Per-GPU Process Info ==="
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader | \
    awk -F, '\''{printf "  PID %s: %s - %s\n", $1, $2, $3}'\'' || echo "  No GPU processes running"

echo ""
echo "=== Aggregate Stats ==="
echo -n "Total GPU Memory Used: "
nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | \
    awk '\''{sum+=$1} END {printf "%.2f GB\n", sum/1024}'\''

echo -n "Average GPU Utilization: "
nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | \
    awk '\''{sum+=$1; count++} END {printf "%.1f%%\n", sum/count}'\''

echo -n "Max Temperature: "
nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | \
    sort -n | tail -1 | awk '\''{printf "%s°C\n", $1}'\''
'
