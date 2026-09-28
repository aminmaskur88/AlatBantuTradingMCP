@echo off
setlocal EnableDelayedExpansion

title AlatBantuTrading Launcher
color 0F

echo ============================================================================
echo           ALAT BANTU TRADING - 1-CLICK LAUNCHER
echo ============================================================================
echo.

:: 1. Cek apakah sudah berjalan sebagai Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [STATUS] Belum berjalan sebagai Administrator.
    echo [AKSI]   Mencoba membuka jendela baru dengan izin Administrator...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd.exe -ArgumentList '/k \"\"%~dpnx0\"\" elevated' -Verb RunAs"
    if %errorLevel% neq 0 (
        echo [PERINGATAN] Gagal memicu prompt Administrator secara otomatis.
        echo Melanjutkan eksekusi dalam mode pengguna biasa...
        goto :START_APP
    )
    echo Jendela Administrator telah dibuka. Jendela awal ini dapat Anda tutup.
    timeout /t 3 >nul
    exit /b
)

:START_APP
:: 2. Pastikan direktori kerja tepat di folder script
cd /d "%~dp0"
title AlatBantuTrading [ADMINISTRATOR]
color 0A

echo ============================================================================
echo  DIREKTORI KERJA : %cd%
echo  HAK AKSES       : ADMINISTRATOR
echo ============================================================================
echo.

:: 3. Cek lokasi Python
where python >nul 2>&1
if %errorLevel% neq 0 (
    color 0C
    echo [ERROR] Python tidak terdeteksi di PATH!
    echo Silakan install Python atau tambahkan ke environment variable PATH.
    echo.
    pause
    exit /b 1
)

for /f "delims=" %%i in ('where python') do (
    echo [INFO] Python Executable: %%i
    goto :PYTHON_FOUND
)
:PYTHON_FOUND

echo.
echo ----------------------------------------------------------------------------
echo [1/3] Menjalankan Web Server (app.py) di port 5000...
echo ----------------------------------------------------------------------------
:: Gunakan cmd /k agar jendela server tetap terbuka jika ada error
start "AlatBantuTrading Web Server (Port 5000)" cmd /k "cd /d "%cd%" && title AlatBantuTrading Web Server && python app.py || (echo. && echo [SERVER BERHENTI / ERROR] Periksa pesan di atas. && pause)"

echo [2/3] Menunggu web server menyala...
powershell -Command "Start-Sleep -Seconds 4"

echo.
echo ----------------------------------------------------------------------------
echo [3/3] Memeriksa status MCP Server & Localhost...
echo ----------------------------------------------------------------------------
python mcp-server/test_mcp.py

echo.
echo ============================================================================
echo  STATUS SISTEM
echo ============================================================================
echo  - Web Application : http://127.0.0.1:5000
echo  - MCP Bridge      : Siap digunakan oleh AGY CLI / Gemini CLI
echo ============================================================================
echo.

echo Membuka browser ke http://127.0.0.1:5000...
start http://127.0.0.1:5000

echo.
echo Script selesai. Jendela ini tetap terbuka agar Anda bisa melihat log.
echo Tekan sembarang tombol untuk menutup jendela ini...
pause >nul
