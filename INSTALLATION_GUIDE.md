# ScreenMind v4.1 インストールガイド

**最終更新**: 2026年6月6日  
**バージョン**: v4.1 (Installable Edition)

---

## 📋 目次

1. [システム要件](#システム要件)
2. [インストール方法](#インストール方法)
3. [初期セットアップ](#初期セットアップ)
4. [トラブルシューティング](#トラブルシューティング)
5. [アンインストール](#アンインストール)

---

## システム要件

### 最小要件
- **OS**: Windows 7 SP1 以上、macOS 10.13 以上、Linux (Ubuntu 18.04 以上)
- **CPU**: Intel Core i5 相当以上
- **メモリ**: 2GB 以上（推奨: 4GB）
- **ディスク容量**: 500MB 以上の空き容量
- **.NET Framework**: 不要（スタンドアロン実行ファイル）

### 推奨要件
- **OS**: Windows 10/11、macOS 12 以上、Ubuntu 22.04 LTS
- **CPU**: Intel Core i7 相当以上
- **メモリ**: 8GB 以上
- **ディスク容量**: 1GB 以上の空き容量
- **GPU**: NVIDIA CUDA 対応 GPU（オプション、高速化用）

### ネットワーク
- インターネット接続（初回セットアップ時）
- ローカルネットワーク接続（オプション、複数PC間での連携用）

---

## インストール方法

### Windows

#### 方法 1: 自動インストーラー（推奨）

1. **ダウンロード**
   - `ScreenMind_v4.1_YYYYMMDD_Installer.zip` をダウンロード
   - 任意のフォルダに解凍

2. **インストール実行**
   - `scripts/Install.vbs` をダブルクリック
   - ユーザーアカウント制御（UAC）の確認画面で「はい」をクリック
   - インストール完了メッセージが表示されたら「OK」をクリック

3. **起動確認**
   - スタートメニューから「ScreenMind」を検索して起動
   - またはデスクトップのショートカットをダブルクリック

#### 方法 2: 手動インストール

1. **フォルダ作成**
   ```
   C:\Program Files\ScreenMind
   ```

2. **ファイルコピー**
   - `bin/ScreenMind.exe` を上記フォルダにコピー
   - `docs/` フォルダもコピー（オプション）

3. **ショートカット作成**
   - `ScreenMind.exe` を右クリック
   - 「ショートカットを作成」を選択
   - ショートカットをスタートメニューまたはデスクトップに配置

4. **起動**
   - ショートカットをダブルクリック

#### 方法 3: ポータブル実行（インストール不要）

1. **解凍**
   - `ScreenMind_v4.1_YYYYMMDD_Installer.zip` を任意の場所に解凍

2. **起動**
   - `ScreenMind.bat` をダブルクリック
   - ScreenMind が即座に起動します

### macOS

1. **ダウンロード**
   - `ScreenMind_v4.1_macOS.dmg` をダウンロード

2. **インストール**
   - DMG ファイルをダブルクリック
   - `ScreenMind.app` を `Applications` フォルダにドラッグ&ドロップ

3. **起動**
   - Launchpad から「ScreenMind」を検索して起動
   - または `Applications/ScreenMind.app` をダブルクリック

### Linux

1. **ダウンロード**
   ```bash
   wget https://example.com/ScreenMind_v4.1_linux.tar.gz
   ```

2. **解凍とインストール**
   ```bash
   tar xzf ScreenMind_v4.1_linux.tar.gz
   cd ScreenMind
   ./install.sh
   ```

3. **起動**
   ```bash
   screenmind
   # または
   ~/.local/bin/ScreenMind
   ```

---

## 初期セットアップ

### 1. セットアップウィザード

初回起動時に以下の 4 ステップが表示されます：

#### ステップ 1: モデル選択
- **ローカルモデル**: Gemma 4, Mistral 7B, Llama 2 など
- **クラウドモデル**: OpenAI GPT-4, GPT-3.5 など
- 推奨: 最初は「Gemma 4 12B」を選択

#### ステップ 2: キーボード設定
- **ホットキー**: `Ctrl+Shift+Space` で ScreenMind を呼び出し
- **カスタマイズ**: 別のキーバインディングに変更可能

#### ステップ 3: UI 設定
- **テーマ**: ライト / ダーク / 高コントラスト
- **透明度**: 30% ～ 100%
- **フォントサイズ**: 小 / 中 / 大

#### ステップ 4: 確認
- 設定内容を確認して「完了」をクリック

### 2. llama.cpp サーバーの起動（ローカルモデル使用時）

ローカルモデルを使用する場合は、llama.cpp サーバーを起動してください：

```bash
# llama.cpp のダウンロード
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# サーバー起動
./server --model path/to/gemma-4-12b-iq4_xs.gguf \
         --host 127.0.0.1 --port 8080 \
         --ngl 999 --flash-attn
```

### 3. Web ダッシュボードへのアクセス

統計情報をブラウザで確認できます：

```
http://localhost:8000
```

ダッシュボードでは以下が確認できます：
- リアルタイムの使用統計
- モデル別のパフォーマンス
- エラー率とリカバリー情報
- キャッシュヒット率

---

## トラブルシューティング

### 起動しない

**症状**: ScreenMind をクリックしても何も起こらない

**対策**:
1. ログファイルを確認
   ```
   Windows: %APPDATA%\ScreenMind\logs\screenmind.log
   macOS: ~/Library/Application Support/ScreenMind/logs/screenmind.log
   Linux: ~/.config/ScreenMind/logs/screenmind.log
   ```

2. Windows Defender がブロックしていないか確認
   - Windows Defender を一時的に無効化して試す

3. 管理者権限で実行
   - `ScreenMind.exe` を右クリック → 「管理者として実行」

### インストール失敗

**症状**: Install.vbs を実行してもインストールされない

**対策**:
1. ウイルス対策ソフトを一時的に無効化
2. `C:\Program Files\ScreenMind\` が存在しないことを確認
3. 管理者権限でインストーラーを実行
4. VBScript が有効になっているか確認

### パフォーマンスが低い

**症状**: 応答が遅い、CPU/メモリ使用率が高い

**対策**:
1. ダッシュボード（http://localhost:8000）でモニタリング
2. 使用中のモデルを確認
   - 軽量モデル（Mistral 7B）に切り替えてみる
3. キャッシュをクリア
   - 設定 → キャッシュ → クリア

### llama.cpp サーバーに接続できない

**症状**: 「llama.cpp サーバーが見つかりません」というエラー

**対策**:
1. llama.cpp サーバーが起動しているか確認
   ```bash
   curl http://localhost:8080/health
   ```

2. ポート 8080 が使用可能か確認
   ```bash
   # Windows
   netstat -ano | findstr :8080
   
   # macOS/Linux
   lsof -i :8080
   ```

3. ファイアウォール設定を確認
   - ローカルホスト（127.0.0.1）への接続を許可

### エラーメッセージが表示される

**症状**: 「エラーが発生しました」というメッセージ

**対策**:
1. エラーレポートをエクスポート
   - 設定 → 診断 → エラーレポートをエクスポート

2. エラーログを確認
   ```
   logs/screenmind_errors.log
   ```

3. 詳細なログを有効化
   - 設定 → デバッグ → ログレベル → DEBUG

---

## アンインストール

### Windows

#### 方法 1: スクリプト使用（推奨）
1. インストーラーフォルダから `scripts/Uninstall.vbs` をダブルクリック
2. 確認ダイアログで「はい」をクリック
3. アンインストール完了

#### 方法 2: 手動削除
1. `C:\Program Files\ScreenMind\` を削除
2. スタートメニューのショートカットを削除
3. デスクトップのショートカットを削除
4. `%APPDATA%\ScreenMind\` を削除（設定・ログを完全削除）

### macOS
1. `Applications` フォルダから `ScreenMind.app` をゴミ箱に移動
2. ゴミ箱を空にする
3. （オプション）`~/Library/Application Support/ScreenMind/` を削除

### Linux
```bash
~/.local/bin/ScreenMind --uninstall
# または
rm -rf ~/.local/bin/ScreenMind ~/.config/ScreenMind/
```

---

## 設定ファイルの場所

### Windows
- **設定**: `%APPDATA%\ScreenMind\config.json`
- **ログ**: `%APPDATA%\ScreenMind\logs\`
- **キャッシュ**: `%APPDATA%\ScreenMind\cache\`

### macOS
- **設定**: `~/Library/Application Support/ScreenMind/config.json`
- **ログ**: `~/Library/Application Support/ScreenMind/logs/`
- **キャッシュ**: `~/Library/Application Support/ScreenMind/cache/`

### Linux
- **設定**: `~/.config/ScreenMind/config.json`
- **ログ**: `~/.config/ScreenMind/logs/`
- **キャッシュ**: `~/.cache/ScreenMind/`

---

## よくある質問（FAQ）

### Q: ScreenMind は何ですか？
A: AI を活用した知的ワークフロープラットフォームです。複数の LLM を自動的に切り替えながら、画面キャプチャと組み合わせて高度な分析や推論を行います。

### Q: オフラインで使用できますか？
A: はい。ローカルモデル（Gemma 4, Mistral 7B など）を使用すれば、インターネット接続なしで動作します。

### Q: データはどこに保存されますか？
A: すべてのデータはローカルマシンに保存されます。クラウドには送信されません（クラウドモデル使用時を除く）。

### Q: GPU を使用できますか？
A: はい。NVIDIA CUDA 対応 GPU がある場合、llama.cpp で `--ngl 999` オプションを使用すれば GPU 高速化が可能です。

### Q: 複数のユーザーで使用できますか？
A: 現在のバージョンではシングルユーザー対応です。マルチユーザー対応は v4.2 で予定されています。

### Q: テクニカルサポートはありますか？
A: 本ドキュメントとログファイルで問題解決ができない場合は、`STABILITY_REPORT.md` のトラブルシューティングセクションを参照してください。

---

## 次のステップ

1. **セットアップウィザードを完了**
2. **Web ダッシュボードにアクセス** (http://localhost:8000)
3. **チュートリアルを実行**
4. **詳細ドキュメントを読む** (`README_v2.md`, `ADVANCED_FEATURES.md`)

---

## 追加リソース

- **README.md**: 基本的な使い方
- **README_v2.md**: 高度な機能
- **ADVANCED_FEATURES.md**: 詳細な機能説明
- **RELEASE_NOTES_v4.0.md**: v4.0 の新機能
- **STABILITY_REPORT.md**: 安定性テストレポート

---

**ScreenMind v4.1 へようこそ！**

🧠 AI-Powered Workflow Platform

Happy Computing! ✨
