#!/bin/bash
# ScreenMind - 起動スクリプト
# Linux / macOS 用

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🧠 ScreenMind v2.0"
echo "================================"
echo ""

# Python バージョン確認
echo "📋 Python バージョンをチェック中..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python $python_version"
echo ""

# 依存ライブラリ確認
echo "📦 依存ライブラリをチェック中..."
python3 -c "import PyQt6; print('   ✅ PyQt6')" || {
    echo "   ❌ PyQt6 がインストールされていません"
    echo "   実行: pip install PyQt6"
    exit 1
}
python3 -c "import httpx; print('   ✅ httpx')" || {
    echo "   ❌ httpx がインストールされていません"
    echo "   実行: pip install httpx"
    exit 1
}
python3 -c "import PIL; print('   ✅ Pillow')" || {
    echo "   ❌ Pillow がインストールされていません"
    echo "   実行: pip install Pillow"
    exit 1
}

echo ""

# llama.cpp サーバー確認
echo "🔍 llama.cpp サーバーをチェック中..."
if nc -z localhost 8080 2>/dev/null; then
    echo "   ✅ llama.cpp サーバーが起動しています (localhost:8080)"
else
    echo "   ⚠️  llama.cpp サーバーが起動していません"
    echo "   別のターミナルで以下を実行してください:"
    echo "   ./llama-server --model gemma-4-12b-iq4_xs.gguf --mmproj mmproj.gguf \\"
    echo "     --host 127.0.0.1 --port 8080 --ngl 999 --flash-attn"
    echo ""
    read -p "続行しますか？ (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🚀 ScreenMind を起動中..."
echo ""

# ScreenMind を起動
python3 screenmind_v2.py

