# 🧠 ScreenMind v2.0

**複数LLM対応版 - AI画面解析アシスタント**

PCに常駐してユーザーの画面をリアルタイムで監視・分析し、複数のLLMから最適なモデルを自動選択して作業効率化を支援するAIデスクトップアシスタント。

> 「ChatGPTやCopilotは月額課金でデータも外部送信される。  
> ScreenMindは完全ローカル・完全無料・複数LLM対応。あなたの画面は、あなただけのもの。」

---

## 🆕 v2.0 の新機能

| 機能 | 説明 |
|------|------|
| **複数LLM対応** | Gemma 4, Mistral, Llama 2, GPT-4など複数モデルをサポート |
| **自動モデル切り替え** | リクエスト内容を分析して最適なモデルを自動選択 |
| **手動モデル選択** | ユーザーが好みのモデルを手動で選択可能 |
| **モデル統計表示** | 各モデルのパフォーマンス・成功率・応答時間を可視化 |
| **ダブルクリック起動** | 実行ファイルをダブルクリックで起動（PyInstaller対応） |
| **ホットキー対応** | Ctrl+Shift+Space でウィンドウ表示/非表示 |

---

## 🚀 クイックスタート

### 1. 依存ライブラリをインストール

```bash
pip install -r requirements.txt
```

### 2. llama.cpp サーバーを起動

```bash
# 別のターミナルで実行
./llama-server \
  --model /path/to/gemma-4-12b-iq4_xs.gguf \
  --mmproj /path/to/mmproj.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --ngl 999 \
  --flash-attn \
  --ctx-size 4096
```

### 3. ScreenMind を起動

**Windows:**
```bash
python screenmind_v2.py
# または
run.bat
```

**macOS / Linux:**
```bash
python3 screenmind_v2.py
# または
bash run.sh
```

---

## 📦 ダブルクリック起動対応（実行ファイル化）

### Windows

```bash
# PyInstaller をインストール
pip install pyinstaller

# ビルドを実行
python build_exe.py
```

完了後、`dist/ScreenMind.exe` をダブルクリックで起動できます。

**ショートカット作成:**
```bash
# create_shortcut.vbs をダブルクリック
# → デスクトップにショートカットが作成されます
```

### macOS

```bash
# PyInstaller をインストール
pip install pyinstaller

# ビルドを実行
python build_exe.py
```

完了後、`dist/ScreenMind.app` をダブルクリックで起動できます。

### Linux

```bash
# PyInstaller をインストール
pip install pyinstaller

# ビルドを実行
python build_exe.py
```

完了後、`dist/ScreenMind` をダブルクリック（またはターミナルで実行）できます。

---

## 🎯 使い方

### 基本操作

1. **質問を入力** → 入力欄にテキストを入力して **Enter** を押す
2. **画面解析** → 送信時にウィンドウが一瞬隠れ、画面全体をキャプチャ
3. **回答表示** → AIの回答がリアルタイムでチャットバブルに表示

### モデル選択

**自動選択モード（デフォルト）:**
- 「自動選択」チェックボックスがON
- リクエスト内容を自動分析して最適なモデルを選択
- 複雑な質問 → 高性能モデル
- 簡単な質問 → 高速モデル
- 画像がある → マルチモーダル対応モデル

**手動選択モード:**
- 「自動選択」チェックボックスをOFF
- ドロップダウンメニューから好みのモデルを選択
- 選択したモデルで全てのリクエストを処理

### その他の機能

| ボタン | 機能 |
|--------|------|
| ＋ | 会話をリセット |
| 📊 | モデル統計情報を表示 |
| 💾 | 会話履歴をJSONで保存 |
| ─ | ウィンドウを最小化 |
| ✕ | アプリケーションを終了 |

**透明度調整:**
- 下部のスライダーで透明度を変更（30〜100%）

**ドラッグ移動:**
- ウィンドウをドラッグして任意の位置に移動

**ホットキー:**
- `Ctrl+Shift+Space` でウィンドウの表示/非表示を切り替え

---

## ⚙️ 設定のカスタマイズ

### config.py

```python
# llama.cpp サーバーのURL
LLAMA_URL = "http://localhost:8080/v1/chat/completions"

# キャプチャ解像度
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720

# ウィンドウサイズ
WINDOW_WIDTH = 380
WINDOW_HEIGHT = 520
```

### models_config.json

複数のLLMモデルを定義・管理します。

```json
{
  "models": {
    "gemma-4-12b-iq4": {
      "id": "gemma-4-12b-iq4",
      "name": "Gemma 4 12B (IQ4)",
      "provider": "local_llama",
      "model_type": "vision",
      "endpoint_url": "http://localhost:8080/v1/chat/completions",
      "model_name": "gemma-4-12b-iq4_xs",
      "max_tokens": 2048,
      "temperature": 0.7,
      "is_multimodal": true,
      "priority": 100
    }
  }
}
```

---

## 📊 モデル統計情報

「📊」ボタンをクリックすると統計ダイアログが表示されます：

- **総モデル数** / **有効なモデル数** / **健全なモデル数**
- **総リクエスト数** / **全体成功率**
- **各モデルの詳細:**
  - リクエスト数
  - 成功率
  - 平均応答時間
  - 使用トークン数

---

## 🔧 トラブルシューティング

### llama.cpp に接続できない

```
⚠️ エラー: llama.cppサーバーに接続できません
```

**解決方法:**
1. llama.cpp サーバーが `localhost:8080` で起動しているか確認
2. ファイアウォール設定を確認
3. `config.py` の `LLAMA_URL` が正しいか確認

### 画面キャプチャに失敗する

```
⚠️ エラー: スクリーンキャプチャに失敗しました
```

**解決方法:**
- **Windows**: 管理者権限で実行
- **macOS**: システム環境設定 > セキュリティとプライバシー > 画面収録 で Python に権限を付与
- **Linux**: `sudo apt install scrot` で scrot をインストール

### モデルが見つからない

```
⚠️ エラー: 利用可能なモデルが見つかりません
```

**解決方法:**
1. `models_config.json` でモデルが定義されているか確認
2. モデルの `is_enabled` が `true` か確認
3. llama.cpp に正しいモデルが読み込まれているか確認

### ホットキーが動作しない

**解決方法:**
- **Linux**: `sudo usermod -aG input $USER` でユーザーを input グループに追加
- **macOS**: システム環境設定 > セキュリティとプライバシー > アクセシビリティ で Python に権限を付与

---

## 📁 ファイル構成

```
screenmind/
├── screenmind_v2.py           # メインアプリ（複数LLM対応版）
├── ai_client.py               # AIクライアント（モデル対応）
├── capture.py                 # 画面キャプチャモジュール
├── config.py                  # 設定値管理
├── model_config.py            # モデル設定管理（新規）
├── model_manager.py           # モデル管理・ヘルスチェック（新規）
├── auto_switcher.py           # 自動モデル切り替え（新規）
├── build_exe.py               # PyInstaller ビルドスクリプト
├── run.sh                      # Linux/macOS 起動スクリプト
├── run.bat                     # Windows 起動スクリプト
├── requirements.txt           # 依存ライブラリ
├── models_config.json         # LLMモデル設定（自動生成）
├── decision_log.json          # 自動選択ログ（自動生成）
├── history/                   # 会話履歴保存ディレクトリ
└── README_v2.md               # このファイル
```

---

## 🎓 開発者向け情報

### モジュール説明

| モジュール | 役割 |
|-----------|------|
| `model_config.py` | モデル設定の定義・管理 |
| `model_manager.py` | 複数モデルの初期化・ヘルスチェック・メトリクス追跡 |
| `auto_switcher.py` | リクエスト分析・自動モデル選択ロジック |
| `screenmind_v2.py` | UIの統合・モデル選択UI |
| `ai_client.py` | llama.cpp 通信・モデル別パラメータ対応 |

### 自動選択ロジック

```python
# リクエスト分析
analysis = switcher.analyze_request(text, has_image=True)
# → RequestComplexity (SIMPLE / MODERATE / COMPLEX / VERY_COMPLEX)
# → RequestPurpose (CONVERSATION / ANALYSIS / CODING / VISION)

# 最適モデル選択
model_id = switcher.select_model_auto(analysis, strategy="balanced")
# strategy: "balanced" / "fast" / "accurate"
```

### パフォーマンスメトリクス

各モデルのメトリクスは自動的に記録されます：

```python
manager.record_request(
    model_id="gemma-4-12b-iq4",
    success=True,
    response_time_ms=150.5,
    tokens=512
)

# メトリクスを取得
metrics = manager.get_performance_metrics("gemma-4-12b-iq4")
print(f"成功率: {metrics.success_rate:.1%}")
print(f"平均応答時間: {metrics.avg_response_time_ms:.1f}ms")
```

---

## 🔄 ロードマップ

| フェーズ | 内容 | ステータス |
|---------|------|----------|
| Phase 1 MVP | フローティングUI・キャプチャ・llama.cpp接続 | ✅ 完了 |
| Phase 2 改善 | ホットキー・透明度・エラー表示 | ✅ 完了 |
| Phase 3 複数LLM | モデル管理・自動切り替え・統計表示 | ✅ 完了 |
| Phase 4 ダブルクリック起動 | PyInstaller・実行ファイル化 | ✅ 完了 |
| Phase 5 拡張 | Webダッシュボード・複数ユーザー対応 | 🔄 検討中 |

---

## 📝 ライセンス

MIT License

---

## 👥 サポート

問題が発生した場合：

1. README_v2.md のトラブルシューティングを確認
2. `decision_log.json` で自動選択の履歴を確認
3. `models_config.json` でモデル設定を確認
4. ログ出力を確認（ターミナルを参照）

---

## 🙏 謝辞

- **llama.cpp**: 高速なローカルLLM推論エンジン
- **PyQt6**: クロスプラットフォーム GUI フレームワーク
- **Gemma, Mistral, Llama**: オープンソース LLM モデル

---

**ScreenMind Project — v2.0.0 (2026年6月)**
