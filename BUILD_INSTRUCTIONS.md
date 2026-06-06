# ScreenMind v4.1 ビルド手順書

**最終更新**: 2026年6月6日  
**対象バージョン**: v4.1 (Installable Edition)

---

## 📋 ビルドプロセス概要

ScreenMind v4.1 を EXE 化してインストーラーを作成するプロセスは、以下の 3 つのステップで構成されています：

1. **EXE ビルド** (`build_v2.py`) - PyInstaller を使用して実行ファイルを生成
2. **インストーラー作成** (`create_installer.py`) - 配布用のインストーラーパッケージを作成
3. **配布パッケージ化** - ZIP ファイルまたは MSI ファイルで配布

---

## 🔧 前提条件

### 必要なソフトウェア
- **Python**: 3.8 以上
- **pip**: Python パッケージマネージャー
- **PyInstaller**: 6.0 以上
- **Git**: バージョン管理用（オプション）

### 必要なライブラリ
```bash
pip install PyQt6 httpx fastapi uvicorn pillow psutil numpy pandas
```

### ディスク容量
- **ビルド用**: 2GB 以上の空き容量
- **最終パッケージ**: 300-500MB

---

## 🚀 ビルド手順

### ステップ 1: 環境準備

```bash
# プロジェクトディレクトリに移動
cd /path/to/screenmind

# 仮想環境を作成（推奨）
python -m venv venv

# 仮想環境を有効化
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 依存ライブラリをインストール
pip install -r requirements.txt
pip install pyinstaller
```

### ステップ 2: EXE ビルド

```bash
# build_v2.py を実行
python build_v2.py
```

**出力**:
- `dist/ScreenMind.exe` - 実行ファイル
- `dist/Install_ScreenMind.vbs` - インストーラースクリプト
- `dist/Uninstall_ScreenMind.vbs` - アンインストーラースクリプト
- `dist/INSTALL.md` - インストール手順書
- `dist/BUILD_INFO.json` - ビルド情報

### ステップ 3: インストーラー作成

```bash
# create_installer.py を実行
python create_installer.py
```

**出力**:
- `installer/` - インストーラーディレクトリ
  - `bin/ScreenMind.exe` - 実行ファイル
  - `scripts/Install.vbs` - インストーラー
  - `scripts/Uninstall.vbs` - アンインストーラー
  - `docs/` - ドキュメント
  - `MANIFEST.json` - マニフェスト
  - `README.md` - インストール手順
- `ScreenMind_v4.1_YYYYMMDD_Installer.zip` - 配布用 ZIP

### ステップ 4: 配布パッケージ化

```bash
# ZIP ファイルが既に作成されているので、そのまま配布可能
ls -lh ScreenMind_v4.1_*.zip
```

---

## 📦 配布方法

### 方法 1: ZIP ファイル配布（推奨）

```bash
# ZIP ファイルをダウンロードサイトにアップロード
# ユーザーが解凍後、Install.vbs を実行
```

### 方法 2: MSI インストーラー作成（高度）

WiX Toolset を使用して MSI ファイルを作成可能：

```bash
# WiX をインストール
# https://wixtoolset.org/

# MSI ファイルを生成
# （別途 WiX スクリプトが必要）
```

### 方法 3: GitHub Releases

```bash
# GitHub にリリースを作成
git tag v4.1
git push origin v4.1

# ZIP ファイルをリリースに添付
```

---

## 🔍 ビルド検証

### ビルド成功の確認

```bash
# 1. EXE ファイルが存在するか確認
ls -lh dist/ScreenMind.exe

# 2. EXE ファイルを実行してみる
dist/ScreenMind.exe

# 3. インストーラーをテスト
scripts/Install.vbs
```

### トラブルシューティング

#### PyInstaller エラー

```
Error: 'screenmind_v2' not found
```

**対策**:
- `screenmind_v2.py` が存在するか確認
- PyInstaller のバージョンを確認: `pyinstaller --version`

#### メモリ不足エラー

```
MemoryError: Unable to allocate X GB
```

**対策**:
- 不要なプロセスを終了
- `--onefile` の代わりに `--onedir` を使用
- `build_v2.py` の `--upx` オプションを削除

#### アイコンエラー

```
Error: Icon file not found
```

**対策**:
- `screenmind.ico` が存在するか確認
- `build_v2.py` の `--icon` パスを修正

---

## 📊 ビルド設定のカスタマイズ

### build_v2.py の修正

```python
# ビルド設定を変更
class ScreenMindBuilder:
    def __init__(self):
        self.version = "4.1"  # バージョン番号
        # ... その他の設定
```

### PyInstaller オプション

```bash
# 単一ファイル（推奨）
pyinstaller --onefile screenmind_v2.py

# フォルダ形式
pyinstaller --onedir screenmind_v2.py

# コンソール表示
pyinstaller --console screenmind_v2.py

# GUI モード（推奨）
pyinstaller --windowed screenmind_v2.py
```

---

## 🔐 署名と検証

### コード署名（Windows）

```bash
# 証明書を取得
# https://www.digicert.com/

# EXE ファイルに署名
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com dist/ScreenMind.exe
```

### ハッシュ値の検証

```bash
# SHA256 ハッシュを生成
certutil -hashfile dist/ScreenMind.exe SHA256

# ユーザーが検証
certutil -hashfile ScreenMind.exe SHA256
```

---

## 📈 パフォーマンス最適化

### ビルドサイズの削減

```bash
# UPX 圧縮を有効化
pyinstaller --upx-dir=/path/to/upx screenmind_v2.py

# 不要なモジュールを除外
pyinstaller --exclude-module=matplotlib screenmind_v2.py
```

### 起動時間の短縮

```bash
# キャッシュを使用
pyinstaller --cache-dir=.pyinstaller_cache screenmind_v2.py

# 最適化オプション
pyinstaller -O screenmind_v2.py
```

---

## 🧪 テスト手順

### ユニットテスト

```bash
# テストスイートを実行
python test_suite.py
```

### インストーラーテスト

```bash
# 1. クリーンな環境で Install.vbs を実行
scripts/Install.vbs

# 2. ScreenMind が正常に起動するか確認
# スタートメニューから起動

# 3. 基本機能をテスト
# - ホットキー（Ctrl+Shift+Space）で呼び出し
# - キャプチャ機能
# - AI 応答

# 4. アンインストール
scripts/Uninstall.vbs

# 5. アンインストール後、ファイルが削除されたか確認
```

### パフォーマンステスト

```bash
# ダッシュボードでモニタリング
http://localhost:8000

# 統計情報を確認
# - 応答時間
# - メモリ使用量
# - エラー率
```

---

## 📝 チェックリスト

ビルド前に以下を確認してください：

- [ ] Python 3.8 以上がインストール済み
- [ ] すべての依存ライブラリがインストール済み
- [ ] `screenmind_v2.py` が存在
- [ ] `screenmind.ico` が存在
- [ ] `models_config.json` が正しく設定されている
- [ ] `requirements.txt` が最新
- [ ] テストスイートがすべてパス
- [ ] ディスク容量が十分（2GB 以上）

---

## 🚀 リリース手順

### リリース前チェック

```bash
# 1. バージョン番号を更新
# build_v2.py, create_installer.py の version を更新

# 2. ビルド
python build_v2.py
python create_installer.py

# 3. テスト
python test_suite.py

# 4. ドキュメント更新
# RELEASE_NOTES_v4.0.md を更新
```

### リリース

```bash
# 1. ZIP ファイルを作成
# create_installer.py が自動作成

# 2. ハッシュ値を計算
certutil -hashfile ScreenMind_v4.1_*.zip SHA256

# 3. 配布サイトにアップロード
# GitHub Releases, SourceForge, 独自サーバーなど

# 4. ユーザーに通知
# メール、SNS、ブログなど
```

---

## 📞 トラブルシューティング

### よくある問題

| 問題 | 原因 | 解決策 |
|-----|------|--------|
| EXE が起動しない | 依存ライブラリが不足 | `pip install -r requirements.txt` を再実行 |
| インストール失敗 | 権限不足 | 管理者権限で実行 |
| ファイルサイズが大きい | 不要なモジュールが含まれている | `--exclude-module` で除外 |
| 起動が遅い | キャッシュがない | 2 回目以降は高速化 |

### ログの確認

```bash
# ビルドログ
build_output.log

# 実行ログ
logs/screenmind.log

# エラーログ
logs/screenmind_errors.log
```

---

## 📚 参考資料

- **PyInstaller ドキュメント**: https://pyinstaller.org/
- **Python パッケージング**: https://packaging.python.org/
- **WiX Toolset**: https://wixtoolset.org/

---

## 🎯 次のステップ

1. ✅ ビルド完了
2. ✅ テスト完了
3. ✅ ドキュメント準備完了
4. 🚀 **リリース準備完了！**

---

**ScreenMind v4.1 ビルド完了！**

🎉 配布準備ができました。

Happy Building! 🚀
