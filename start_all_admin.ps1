# ============================================================================
# AlatBantuTrading - 1-Click Administrator Launcher (PowerShell)
# Menjalankan seluruh sistem (Web App & MCP Bridge) dengan hak akses Administrator
# ============================================================================

# 1. Self-Elevation ke Administrator jika belum berjalan sebagai admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[INFO] Meminta hak akses Administrator (UAC)..." -ForegroundColor Yellow
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

# 2. Pindah ke direktori script
Set-Location -Path $PSScriptRoot
$host.UI.RawUI.WindowTitle = "AlatBantuTrading - Mode Administrator"

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "          ALAT BANTU TRADING - ADMINISTRATOR LAUNCHER (POWERSHELL)" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " Direktori Kerja : $PSScriptRoot"
Write-Host " Hak Akses       : ADMINISTRATOR (Active)" -ForegroundColor Green
Write-Host " Waktu Mulai     : $(Get-Date -Format 'dd-MM-yyyy HH:mm:ss')"
Write-Host "============================================================================`n" -ForegroundColor Cyan

# 3. Jalankan Web App di proses terpisah dengan hak Admin
Write-Host "[1/3] Menjalankan Web Application (app.py) di port 5000..." -ForegroundColor Yellow
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"Set-Location '$PSScriptRoot'; `$host.UI.RawUI.WindowTitle = 'AlatBantuTrading Web Server'; python app.py`""

# 4. Tunggu inisialisasi server
Write-Host "[2/3] Menunggu web server aktif..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# 5. Uji Protokol MCP
Write-Host "[3/3] Memeriksa koneksi protokol MCP Server..." -ForegroundColor Yellow
python mcp-server/test_mcp.py

Write-Host "`n============================================================================" -ForegroundColor Green
Write-Host " SELURUH SISTEM TELAH AKTIF!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Green
Write-Host " 1. Web Interface : http://127.0.0.1:5000"
Write-Host " 2. MCP Server    : Terhubung via stdio ke AGY CLI / Gemini CLI"
Write-Host "============================================================================`n" -ForegroundColor Green

# 6. Buka browser otomatis
Start-Process "http://127.0.0.1:5000"

Write-Host "Tekan Enter untuk menutup jendela launcher ini..." -ForegroundColor Gray
Read-Host
