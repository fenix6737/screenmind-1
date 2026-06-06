#!/usr/bin/env python3
"""
ScreenMind v4.1 - インストーラー作成ツール
配布用の完全なインストーラーパッケージを生成。
"""

import os
import sys
import shutil
import zipfile
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class InstallerCreator:
    """ScreenMind インストーラー作成ツール。"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.installer_dir = self.project_root / "installer"
        self.version = "4.1"
        self.build_date = datetime.now().strftime("%Y%m%d")

    def prepare_installer_directory(self) -> bool:
        """インストーラーディレクトリを準備。"""
        logger.info("=== インストーラーディレクトリを準備 ===")

        try:
            # 既存のインストーラーディレクトリを削除
            if self.installer_dir.exists():
                shutil.rmtree(self.installer_dir)

            # 新しいディレクトリを作成
            self.installer_dir.mkdir(parents=True, exist_ok=True)

            # サブディレクトリを作成
            (self.installer_dir / "bin").mkdir(exist_ok=True)
            (self.installer_dir / "docs").mkdir(exist_ok=True)
            (self.installer_dir / "scripts").mkdir(exist_ok=True)

            logger.info("✅ インストーラーディレクトリを準備: %s", self.installer_dir)
            return True
        except Exception as e:
            logger.error("❌ ディレクトリ準備失敗: %s", e)
            return False

    def copy_executable(self) -> bool:
        """実行ファイルをコピー。"""
        logger.info("=== 実行ファイルをコピー ===")

        try:
            exe_file = self.dist_dir / "ScreenMind.exe"
            if not exe_file.exists():
                logger.warning("⚠️  ScreenMind.exe が見つかりません（スキップ）")
                return True

            dest_file = self.installer_dir / "bin" / "ScreenMind.exe"
            shutil.copy2(exe_file, dest_file)
            logger.info("✅ 実行ファイルをコピー: %s", dest_file)
            return True
        except Exception as e:
            logger.error("❌ 実行ファイルコピー失敗: %s", e)
            return False

    def copy_scripts(self) -> bool:
        """インストール/アンインストールスクリプトをコピー。"""
        logger.info("=== スクリプトをコピー ===")

        try:
            # インストーラースクリプト
            installer_vbs = self.dist_dir / "Install_ScreenMind.vbs"
            if installer_vbs.exists():
                shutil.copy2(installer_vbs, self.installer_dir / "scripts" / "Install.vbs")
                logger.info("✅ インストーラースクリプトをコピー")

            # アンインストーラースクリプト
            uninstaller_vbs = self.dist_dir / "Uninstall_ScreenMind.vbs"
            if uninstaller_vbs.exists():
                shutil.copy2(uninstaller_vbs, self.installer_dir / "scripts" / "Uninstall.vbs")
                logger.info("✅ アンインストーラースクリプトをコピー")

            return True
        except Exception as e:
            logger.error("❌ スクリプトコピー失敗: %s", e)
            return False

    def copy_documentation(self) -> bool:
        """ドキュメントをコピー。"""
        logger.info("=== ドキュメントをコピー ===")

        try:
            doc_files = [
                "README.md",
                "README_v2.md",
                "ADVANCED_FEATURES.md",
                "RELEASE_NOTES_v4.0.md",
                "STABILITY_REPORT.md",
                "INSTALL.md",
            ]

            for doc_file in doc_files:
                src = self.dist_dir / doc_file
                if src.exists():
                    dest = self.installer_dir / "docs" / doc_file
                    shutil.copy2(src, dest)
                    logger.info("✅ %s をコピー", doc_file)

            return True
        except Exception as e:
            logger.error("❌ ドキュメントコピー失敗: %s", e)
            return False

    def create_launcher_batch(self) -> bool:
        """起動用バッチファイルを作成。"""
        logger.info("=== 起動用バッチファイルを作成 ===")

        try:
            batch_content = f"""@echo off
REM ScreenMind v{self.version} ランチャー
setlocal enabledelayedexpansion

REM スクリプトの場所を取得
set SCRIPT_DIR=%~dp0
set BIN_DIR=!SCRIPT_DIR!bin

REM ScreenMind.exe を起動
if exist "!BIN_DIR!\\ScreenMind.exe" (
    start "" "!BIN_DIR!\\ScreenMind.exe"
) else (
    echo ScreenMind.exe が見つかりません。
    echo インストールが正しく完了していない可能性があります。
    pause
)
"""
            launcher_path = self.installer_dir / "ScreenMind.bat"
            with open(launcher_path, 'w', encoding='utf-8') as f:
                f.write(batch_content)

            logger.info("✅ 起動用バッチファイルを作成: %s", launcher_path)
            return True
        except Exception as e:
            logger.error("❌ バッチファイル作成失敗: %s", e)
            return False

    def create_manifest(self) -> bool:
        """インストーラーマニフェストを作成。"""
        logger.info("=== インストーラーマニフェストを作成 ===")

        try:
            manifest = {
                "name": "ScreenMind",
                "version": self.version,
                "build_date": datetime.now().isoformat(),
                "description": "AI-Powered Workflow Platform",
                "author": "ScreenMind Team",
                "license": "MIT",
                "system_requirements": {
                    "os": "Windows 7 or later",
                    "memory_mb": 2048,
                    "disk_space_mb": 500,
                },
                "files": {
                    "executable": "bin/ScreenMind.exe",
                    "installer": "scripts/Install.vbs",
                    "uninstaller": "scripts/Uninstall.vbs",
                },
                "features": [
                    "Multiple LLM Support",
                    "Auto Model Switching",
                    "Response Caching",
                    "Web Dashboard",
                    "System Monitoring",
                    "Error Recovery",
                    "Structured Logging",
                ],
            }

            manifest_path = self.installer_dir / "MANIFEST.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            logger.info("✅ マニフェストを作成: %s", manifest_path)
            return True
        except Exception as e:
            logger.error("❌ マニフェスト作成失敗: %s", e)
            return False

    def create_readme_installer(self) -> bool:
        """インストーラー用 README を作成。"""
        logger.info("=== インストーラー用 README を作成 ===")

        try:
            readme = f"""# ScreenMind v{self.version} インストーラー

## 📦 内容物

- `bin/ScreenMind.exe` - メインアプリケーション
- `scripts/Install.vbs` - インストーラー
- `scripts/Uninstall.vbs` - アンインストーラー
- `docs/` - ドキュメント
- `ScreenMind.bat` - クイック起動スクリプト

## 🚀 インストール方法

### 方法 1: 自動インストール（推奨）
1. `scripts/Install.vbs` をダブルクリック
2. インストール先を確認
3. スタートメニューとデスクトップにショートカットが作成されます

### 方法 2: 手動インストール
1. `bin/ScreenMind.exe` を `C:\\Program Files\\ScreenMind\\` にコピー
2. `ScreenMind.bat` をダブルクリックして起動

### 方法 3: ポータブル実行
1. `ScreenMind.bat` をダブルクリック
2. ScreenMind が起動します（インストール不要）

## ⚙️ システム要件

- **OS**: Windows 7 以上
- **メモリ**: 2GB 以上
- **ディスク容量**: 500MB 以上
- **.NET Framework**: 不要（スタンドアロン実行ファイル）

## 🗑️ アンインストール

### 方法 1: スクリプト使用
1. `scripts/Uninstall.vbs` をダブルクリック
2. 確認ダイアログで「はい」を選択

### 方法 2: 手動削除
1. `C:\\Program Files\\ScreenMind\\` を削除
2. スタートメニューのショートカットを削除
3. デスクトップのショートカットを削除

## 📝 トラブルシューティング

### 起動しない場合
- `logs/screenmind.log` を確認
- Windows Defender がブロックしていないか確認
- 管理者権限で実行してみてください

### インストール失敗
- ウイルス対策ソフトを一時的に無効化
- `C:\\Program Files\\ScreenMind\\` が存在しないことを確認
- 管理者権限でインストーラーを実行

### パフォーマンスが低い
- `STABILITY_REPORT.md` を確認
- システムリソースを確認（CPU、メモリ）
- ダッシュボード（http://localhost:8000）でモニタリング

## 📚 ドキュメント

詳細なドキュメントは `docs/` フォルダを参照してください：

- `README.md` - 基本的な使い方
- `README_v2.md` - 高度な機能
- `ADVANCED_FEATURES.md` - 詳細な機能説明
- `RELEASE_NOTES_v4.0.md` - v4.0 の新機能
- `STABILITY_REPORT.md` - 安定性テストレポート

## 🔧 設定

初回起動時にセットアップウィザードが表示されます：

1. **モデル選択**: 使用するLLMを選択
2. **キーボード設定**: ホットキーを設定
3. **UI設定**: テーマ、透明度、フォントサイズを設定

## 🌐 Web ダッシュボード

ScreenMind の統計情報をブラウザで確認できます：

```
http://localhost:8000
```

## 📞 サポート

問題が発生した場合：

1. `logs/screenmind.log` でエラーを確認
2. `error_report.json` をエクスポート
3. `STABILITY_REPORT.md` の「トラブルシューティング」を参照

## 📄 ライセンス

ScreenMind v{self.version} は MIT ライセンスの下で公開されています。

---

**ScreenMind v{self.version} - AI-Powered Workflow Platform**

Happy Computing! 🧠✨
"""
            readme_path = self.installer_dir / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme)

            logger.info("✅ README を作成: %s", readme_path)
            return True
        except Exception as e:
            logger.error("❌ README 作成失敗: %s", e)
            return False

    def create_zip_package(self) -> bool:
        """インストーラーをZIPパッケージ化。"""
        logger.info("=== インストーラーをZIPパッケージ化 ===")

        try:
            zip_name = f"ScreenMind_v{self.version}_{self.build_date}_Installer.zip"
            zip_path = self.project_root.parent / zip_name

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.installer_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.installer_dir.parent)
                        zipf.write(file_path, arcname)

            logger.info("✅ ZIPパッケージを作成: %s", zip_path)
            logger.info("   ファイルサイズ: %.2f MB", zip_path.stat().st_size / (1024 * 1024))
            return True
        except Exception as e:
            logger.error("❌ ZIPパッケージ作成失敗: %s", e)
            return False

    def create_summary(self) -> bool:
        """インストーラー作成サマリーを出力。"""
        logger.info("=== インストーラー作成サマリー ===\n")

        try:
            summary = f"""
📦 ScreenMind v{self.version} インストーラー作成完了

📂 インストーラーディレクトリ: {self.installer_dir}

📋 内容物:
  ✅ bin/ScreenMind.exe - メインアプリケーション
  ✅ scripts/Install.vbs - インストーラー
  ✅ scripts/Uninstall.vbs - アンインストーラー
  ✅ docs/ - ドキュメント
  ✅ ScreenMind.bat - クイック起動スクリプト
  ✅ MANIFEST.json - パッケージマニフェスト
  ✅ README.md - インストール手順

🚀 配布方法:

1. ZIP パッケージを配布
   - ファイル: ScreenMind_v{self.version}_{self.build_date}_Installer.zip
   - ユーザーが解凍後、Install.vbs を実行

2. フォルダ全体を配布
   - ユーザーが installer フォルダを任意の場所に配置
   - Install.vbs を実行してインストール

3. ポータブル版として配布
   - ScreenMind.bat をダブルクリックで即座に起動
   - インストール不要

📝 ユーザー向け手順:

1. インストーラーを解凍または配置
2. scripts/Install.vbs をダブルクリック
3. インストール完了後、ScreenMind が自動起動
4. スタートメニューまたはデスクトップから起動可能

✨ 特徴:

  ✓ ワンクリックインストール
  ✓ 自動ショートカット作成
  ✓ アンインストール機能
  ✓ ポータブル実行対応
  ✓ 詳細なドキュメント付属

---
準備完了！ユーザーへの配布をお願いします。
"""
            logger.info(summary)
            return True
        except Exception as e:
            logger.error("❌ サマリー出力失敗: %s", e)
            return False

    def create(self) -> bool:
        """完全なインストーラーを作成。"""
        logger.info("=" * 60)
        logger.info("ScreenMind v%s - インストーラー作成開始", self.version)
        logger.info("=" * 60 + "\n")

        # ディレクトリ準備
        if not self.prepare_installer_directory():
            return False

        # 実行ファイルコピー
        if not self.copy_executable():
            return False

        # スクリプトコピー
        if not self.copy_scripts():
            return False

        # ドキュメントコピー
        if not self.copy_documentation():
            return False

        # ランチャー作成
        if not self.create_launcher_batch():
            return False

        # マニフェスト作成
        if not self.create_manifest():
            return False

        # README 作成
        if not self.create_readme_installer():
            return False

        # ZIP パッケージ化
        if not self.create_zip_package():
            return False

        # サマリー出力
        if not self.create_summary():
            return False

        logger.info("\n" + "=" * 60)
        logger.info("✅ インストーラー作成完了")
        logger.info("=" * 60)

        return True


if __name__ == "__main__":
    creator = InstallerCreator()
    success = creator.create()
    sys.exit(0 if success else 1)
