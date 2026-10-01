# Low-Level Memory and GPU VRAM Diagnostics Utility
# Evaluates host RAM and GPU VRAM thresholds

$os = Get-CimInstance Win32_OperatingSystem
$totalRamMB = [math]::Round($os.TotalVisibleMemorySize / 1024, 2)
$freeRamMB = [math]::Round($os.FreePhysicalMemory / 1024, 2)
$usedRamMB = [math]::Round($totalRamMB - $freeRamMB, 2)

Write-Host "================ [MEMORY ARCHITECTURE REPORT] ================" -ForegroundColor Cyan
Write-Host "HOST RAM:"
Write-Host "  Total Visible : $totalRamMB MB"
Write-Host "  Used Physical : $usedRamMB MB"
Write-Host "  Free Physical : $freeRamMB MB"

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    $gpuStats = nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
    $parts = $gpuStats.Split(',')
    Write-Host "`nGPU VRAM (NVIDIA OptiX / CUDA):"
    Write-Host "  Device Name   : $($parts[0].Trim())"
    Write-Host "  Total VRAM    : $($parts[1].Trim()) MB"
    Write-Host "  Used VRAM     : $($parts[2].Trim()) MB"
    Write-Host "  Free VRAM     : $($parts[3].Trim()) MB"
} else {
    Write-Host "`nnvidia-smi not detected."
}
Write-Host "==============================================================" -ForegroundColor Cyan
