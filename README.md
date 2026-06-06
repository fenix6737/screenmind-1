# 🧠 ScreenMind

**AI画面解析アシスタント** — PCに常駐してユーザーの画面をリアルタイムで監視・分析し、作業効率化を支援するAIデスクトップアシスタント。

> 「ChatGPTやCopilotは月額課金でデータも外部送信される。  
> ScreenMindは完全ローカル・完全無料。あなたの画面は、あなただけのもの。」

---

## 特徴

| 観点 | 既存ツール | ScreenMind |
|------|-----------|------------|
| 入力方式 | テキスト・音声入力が必要 | 画面を見て自動理解 |
| 動作場所 | クラウドAPI依存 | 完全ローカル実行 |
| コスト | 月額課金・API従量課金 | 完全無料（初期開発費のみ） |
| プライバシー | 画面データが外部送信 | データが外部に出ない |

---

## 動作環境

| 項目 | 最小要件 | 推奨環境 |
|------|---------|---------|
| OS | Windows 10 / macOS 12 / Ubuntu 20.04 | Windows 11 |
| CPU | Intel Core i5 10世代以上 | Core i7 12700K |
| RAM | 16 GB | 64 GB |
| GPU VRAM | 8 GB | RTX 3070 Ti 8 GB |
| Python | 3.10 以上 | 3.11 |
| llama.cpp | 最新ビルド（CUDA対応） | `--ngl 999 --flash-attn on` |

---

## セットアップ

### 1. llama.cpp サーバーを起動する

```bash
# llama.cpp をビルド済みの場合（CUDA対応推奨）
./llama-server \
  --model /path/to/gemma-4-12b-iq4_xs.gguf \
  --mmproj /path/to/mmproj.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --ngl 999 \
  --flash-attn \
  --ctx-size 4096
```

> **注意**: `--mmproj` オプションはマルチモーダル（画像解析）に必要です。  
> Gemma 4 のマルチモーダルプロジェクションファイルを別途用意してください。

### 2. Python 依存ライブラリをインストールする

```bash
cd screenmind
pip install -r requirements.txt
```

### 3. ScreenMind を起動する

```bash
python screenmind.py
```

---

## 使い方

1. **起動**: `python screenmind.py` を実行するとフローティングウィンドウが画面右下に表示されます。
2. **質問する**: 入力欄にテキストを入力して **Enter** を押します（Shift+Enter で改行）。
3. **画面解析**: 送信時にウィンドウが一瞬隠れ、画面全体をキャプチャしてAIに送信します。
4. **回答表示**: AIの回答がリアルタイムでチャットバブルに表示されます。
5. **移動**: ウィンドウをドラッグして任意の位置に移動できます。
6. **透明度調整**: 下部のスライダーで透明度を変更できます。
7. **ホットキー**: `Ctrl+Shift+Space` でウィンドウの表示/非表示を切り替えられます。

---

## ファイル構成

```
screenmind/
├── screenmind.py     # メインアプリ（UIコア・PyQt6）
├── capture.py        # 画面キャプチャモジュール
├── ai_client.py      # llama.cpp通信モジュール（QThread）
├── config.py         # 設定値管理
├── requirements.txt  # 依存ライブラリ
├── README.md         # このファイル
└── history/          # 会話履歴保存ディレクトリ（自動生成）
```

---

## 設定のカスタマイズ

`config.py` を編集することで各種設定を変更できます。

```python
# llama.cpp サーバーのURL
LLAMA_URL = "http://localhost:8080/v1/chat/completions"

# モデル名
MODEL_NAME = "gemma-4-12b-iq4_xs"

# キャプチャ解像度
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720

# ウィンドウサイズ
WINDOW_WIDTH = 380
WINDOW_HEIGHT = 520
```

---

## トラブルシューティング

### llama.cpp に接続できない

- llama.cpp サーバーが `localhost:8080` で起動しているか確認してください。
- ファイアウォールの設定を確認してください。
- `config.py` の `LLAMA_URL` が正しいか確認してください。

### 画面キャプチャに失敗する

- **Windows**: 管理者権限で実行してみてください。
- **macOS**: システム環境設定 > セキュリティとプライバシー > 画面収録 で Python に権限を付与してください。
- **Linux**: `scrot` または `gnome-screenshot` をインストールしてください。
  ```bash
  sudo apt install scrot
  ```

### ホットキーが動作しない

- `keyboard` ライブラリが必要です: `pip install keyboard`
- **Linux**: `sudo` で実行するか、ユーザーを `input` グループに追加してください。
  ```bash
  sudo usermod -aG input $USER
  ```

---

## ロードマップ

| フェーズ | 内容 | ステータス |
|---------|------|----------|
| Phase 1 MVP | フローティングUI・キャプチャ・llama.cpp接続 | ✅ 完了 |
| Phase 2 改善 | ホットキー・透明度スライダー・エラー表示改善 | ✅ 完了 |
| Phase 3 拡張 | 履歴保存JSON・複数モデル切替・exe化 | 🔄 進行中 |

---

## ライセンス

MIT License

---

## 作者

ScreenMind Project — v1.0.0 (2026年6月)
