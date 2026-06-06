# ScreenMind v4.1 - クイックスタートガイド

**最終更新**: 2026年6月6日

---

## 🚀 3 ステップで開始

### ステップ 1: Python をインストール
- **Windows**: https://www.python.org/downloads/ から Python 3.8 以上をダウンロード
- **macOS**: `brew install python3` または https://www.python.org/downloads/
- **Linux**: `sudo apt install python3 python3-pip`

### ステップ 2: 依存ライブラリをインストール
```bash
pip install -r requirements.txt
```

### ステップ 3: ScreenMind を起動
```bash
# Windows
run.bat

# macOS / Linux
bash run.sh
```

---

## 💻 Windows での起動

### 方法 1: バッチファイル（推奨）
1. `run.bat` をダブルクリック
2. ScreenMind が起動します

### 方法 2: コマンドプロンプト
```cmd
python src/screenmind_v2.py
```

---

## 🍎 macOS での起動

### 方法 1: シェルスクリプト（推奨）
```bash
bash run.sh
```

### 方法 2: ターミナル
```bash
python3 src/screenmind_v2.py
```

---

## 🐧 Linux での起動

### 方法 1: シェルスクリプト（推奨）
```bash
bash run.sh
```

### 方法 2: ターミナル
```bash
python3 src/screenmind_v2.py
```

---

## 🔧 トラブルシューティング

### 「Python が見つかりません」
**原因**: Python がインストールされていない、または PATH に登録されていない

**対策**:
1. Python をインストール: https://www.python.org/
2. インストール時に「Add Python to PATH」にチェック
3. PC を再起動

### 「ModuleNotFoundError」
**原因**: 依存ライブラリが不足している

**対策**:
```bash
pip install -r requirements.txt
```

### 「Permission denied」
**原因**: ファイルに実行権限がない（Linux/macOS）

**対策**:
```bash
chmod +x run.sh
bash run.sh
```

### アプリが起動しない
**原因**: llama.cpp サーバーが起動していない

**対策**:
1. llama.cpp サーバーを起動（別ターミナル）
   ```bash
   ./llama-server --model gemma-4-12b-iq4_xs.gguf \
     --host 127.0.0.1 --port 8080 --ngl 999
   ```
2. ScreenMind を再度起動

---

## 📚 次のステップ

1. **初期セットアップ**: ウィザードに従ってモデルとキーボード設定を行う
2. **Web ダッシュボード**: `http://localhost:8000` で統計を確認
3. **詳細ドキュメント**: `docs/` フォルダのマニュアルを参照

---

## 🎯 主要機能

| 機能 | 説明 |
|------|------|
| **複数 LLM** | Gemma 4, Mistral 7B, Llama 2, OpenAI GPT など |
| **自動切り替え** | リクエスト内容に応じて最適なモデルを自動選択 |
| **キャッシング** | 同じ質問に対して 100ms 以下で応答 |
| **Web ダッシュボード** | リアルタイム統計とパフォーマンス分析 |
| **ホットキー** | `Ctrl+Shift+Space` でいつでも呼び出し |

---

## 📞 サポート

問題が発生した場合:
1. `docs/INSTALLATION_GUIDE.md` を確認
2. ログファイルを確認: `logs/screenmind.log`
3. `docs/STABILITY_REPORT.md` でトラブルシューティング

---

## 🎉 ScreenMind へようこそ！

Happy Computing! 🧠✨
