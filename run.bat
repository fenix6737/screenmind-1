@echo off
REM ScreenMind - 起動スクリプト
REM Windows 用

setlocal enabledelayedexpansion

echo.
echo 🧠 ScreenMind v2.0
echo ================================
echo.

REM Python バージョン確認
echo 📋 Python バージョンをチェック中...
python --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ Python がインストールされていません
    echo    https://www.python.org/ からダウンロードしてください
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    Python !PYTHON_VERSION!
echo.

REM 依存ライブラリ確認
echo 📦 依存ライブラリをチェック中...
python -c "import PyQt6" >nul 2>&1 || (
    echo    ❌ PyQt6 がインストールされていません
    echo    実行: pip install PyQt6
    pause
    exit /b 1
)
echo    ✅ PyQt6

python -c "import httpx" >nul 2>&1 || (
    echo    ❌ httpx がインストールされていません
    echo    実行: pip install httpx
    pause
    exit /b 1
)
echo    ✅ httpx

python -c "import PIL" >nul 2>&1 || (
    echo    ❌ Pillow がインストールされていません
    echo    実行: pip install Pillow
    pause
    exit /b 1
)
echo    ✅ Pillow

echo.

REM llama.cpp サーバー確認
echo 🔍 llama.cpp サーバーをチェック中...
netstat -an | find ":8080" >nul 2>&1
if errorlevel 1 (
    echo    ⚠️  llama.cpp サーバーが起動していません
    echo    別のターミナルで以下を実行してください:
    echo    llama-server --model gemma-4-12b-iq4_xs.gguf --mmproj mmproj.gguf ^
    echo      --host 127.0.0.1 --port 8080 --ngl 999 --flash-attn
    echo.
    set /p CONTINUE="続行しますか？ (y/n): "
    if /i not "!CONTINUE!"=="y" exit /b 1
) else (
    echo    ✅ llama.cpp サーバーが起動しています (localhost:8080)
)

echo.
echo 🚀 ScreenMind を起動中...
echo.

REM ScreenMind を起動
python screenmind_v2.py

pause
