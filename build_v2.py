#!/usr/bin/env python3
"""
ScreenMind v4.1 - EXE ビルド自動化スクリプト
PyInstaller を使用して実行ファイルを生成。
"""

import os
import sys
import subprocess
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScreenMindBuilder:
    """ScreenMind EXE ビルダー。"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.spec_file = self.project_root / "screenmind.spec"
        self.version = "4.1"

    def check_requirements(self) -> bool:
        """ビルド前提条件をチェック。"""
        logger.info("=== ビルド前提条件をチェック ===")

        # PyInstaller チェック
        try:
            import PyInstaller
            logger.info("✅ PyInstaller: %s", PyInstaller.__version__)
        except ImportError:
            logger.error("❌ PyInstaller がインストールされていません")
            return False

        # PyQt6 チェック
        try:
            import PyQt6
            logger.info("✅ PyQt6: インストール済み")
        except ImportError:
            logger.error("❌ PyQt6 がインストールされていません")
            return False

        # メインスクリプト確認
        if not (self.project_root / "screenmind_v2.py").exists():
            logger.error("❌ screenmind_v2.py が見つかりません")
            return False

        logger.info("✅ すべての前提条件を満たしています\n")
        return True

    def create_icon(self) -> bool:
        """アイコンを作成（ICO ファイル）。"""
        logger.info("=== アイコンを作成 ===")

        try:
            from PIL import Image, ImageDraw
            
            # 256x256 のアイコンを作成
            size = 256
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # グラデーション背景
            for y in range(size):
                r = int(102 + (118 - 102) * (y / size))
                g = int(126 + (75 - 126) * (y / size))
                b = int(234 + (162 - 234) * (y / size))
                draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

            # 脳のシンボル（簡易版）
            draw.ellipse([60, 60, 196, 196], fill=(255, 255, 255, 200), outline=(255, 255, 255, 255), width=3)
            draw.text((100, 110), "🧠", fill=(255, 255, 255, 255))

            # ICO ファイルとして保存
            icon_path = self.project_root / "screenmind.ico"
            img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            logger.info("✅ アイコンを作成: %s", icon_path)
            return True
        except Exception as e:
            logger.warning("⚠️  アイコン作成失敗（スキップ）: %s", e)
            return False

    def build_exe(self) -> bool:
        """EXE ファイルをビルド。"""
        logger.info("=== EXE ファイルをビルド ===")

        try:
            # PyInstaller コマンド
            cmd = [
                "pyinstaller",
                "--onefile",  # 単一ファイル
                "--windowed",  # GUI モード
                "--name", "ScreenMind",
                "--add-data", f"{self.project_root / 'README.md'}{os.pathsep}.",
                "--add-data", f"{self.project_root / 'STABILITY_REPORT.md'}{os.pathsep}.",
                "--hidden-import=PyQt6.QtCore",
                "--hidden-import=PyQt6.QtGui",
                "--hidden-import=PyQt6.QtWidgets",
                "--hidden-import=httpx",
                "--hidden-import=fastapi",
                "--hidden-import=psutil",
                "--icon", str(self.project_root / "screenmind.ico"),
                str(self.project_root / "screenmind_v2.py"),
            ]

            logger.info("コマンド実行: %s", " ".join(cmd))
            result = subprocess.run(cmd, cwd=str(self.project_root), capture_output=True, text=True)

            if result.returncode != 0:
                logger.error("❌ ビルド失敗:")
                logger.error(result.stderr)
                return False

            logger.info("✅ EXE ビルド成功\n")
            return True
        except Exception as e:
            logger.error("❌ ビルドエラー: %s", e)
            return False

    def create_installer_script(self) -> bool:
        """インストーラースクリプトを作成。"""
        logger.info("=== インストーラースクリプトを作成 ===")

        try:
            exe_path = self.dist_dir / "ScreenMind.exe"
            if not exe_path.exists():
                logger.error("❌ ScreenMind.exe が見つかりません")
                return False

            # インストーラースクリプト（VBScript）
            installer_script = f"""
' ScreenMind v{self.version} インストーラー
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' インストール先ディレクトリ
installDir = objShell.SpecialFolders("ProgramFiles") & "\\ScreenMind"

' ディレクトリ作成
If Not objFSO.FolderExists(installDir) Then
    objFSO.CreateFolder(installDir)
End If

' EXE ファイルをコピー
sourcePath = "{exe_path}"
destPath = installDir & "\\ScreenMind.exe"

If objFSO.FileExists(sourcePath) Then
    objFSO.CopyFile sourcePath, destPath, True
    
    ' スタートメニューにショートカットを作成
    Set objLink = objShell.CreateShortCut(objShell.SpecialFolders("StartMenu") & "\\ScreenMind.lnk")
    objLink.TargetPath = destPath
    objLink.WorkingDirectory = installDir
    objLink.Description = "ScreenMind v{self.version}"
    objLink.Save
    
    ' デスクトップにショートカットを作成
    Set objLink = objShell.CreateShortCut(objShell.SpecialFolders("Desktop") & "\\ScreenMind.lnk")
    objLink.TargetPath = destPath
    objLink.WorkingDirectory = installDir
    objLink.Description = "ScreenMind v{self.version}"
    objLink.Save
    
    MsgBox "ScreenMind v{self.version} をインストールしました。", vbInformation, "インストール完了"
Else
    MsgBox "インストールファイルが見つかりません。", vbCritical, "エラー"
End If
"""
            installer_path = self.dist_dir / "Install_ScreenMind.vbs"
            with open(installer_path, 'w', encoding='utf-8') as f:
                f.write(installer_script)

            logger.info("✅ インストーラースクリプトを作成: %s", installer_path)
            return True
        except Exception as e:
            logger.error("❌ インストーラースクリプト作成失敗: %s", e)
            return False

    def create_uninstaller_script(self) -> bool:
        """アンインストーラースクリプトを作成。"""
        logger.info("=== アンインストーラースクリプトを作成 ===")

        try:
            uninstaller_script = f"""
' ScreenMind v{self.version} アンインストーラー
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

installDir = objShell.SpecialFolders("ProgramFiles") & "\\ScreenMind"

If MsgBox("ScreenMind v{self.version} をアンインストールしますか？", vbYesNo, "確認") = vbYes Then
    ' ショートカットを削除
    On Error Resume Next
    objFSO.DeleteFile objShell.SpecialFolders("StartMenu") & "\\ScreenMind.lnk"
    objFSO.DeleteFile objShell.SpecialFolders("Desktop") & "\\ScreenMind.lnk"
    On Error GoTo 0
    
    ' インストールディレクトリを削除
    If objFSO.FolderExists(installDir) Then
        objFSO.DeleteFolder installDir, True
    End If
    
    MsgBox "ScreenMind v{self.version} をアンインストールしました。", vbInformation, "完了"
Else
    MsgBox "アンインストールがキャンセルされました。", vbInformation, "キャンセル"
End If
"""
            uninstaller_path = self.dist_dir / "Uninstall_ScreenMind.vbs"
            with open(uninstaller_path, 'w', encoding='utf-8') as f:
                f.write(uninstaller_script)

            logger.info("✅ アンインストーラースクリプトを作成: %s", uninstaller_path)
            return True
        except Exception as e:
            logger.error("❌ アンインストーラースクリプト作成失敗: %s", e)
            return False

    def create_readme(self) -> bool:
        """インストール手順書を作成。"""
        logger.info("=== インストール手順書を作成 ===")

        try:
            readme = f"""# ScreenMind v{self.version} インストール手順

## 📦 インストール方法

### Windows (推奨)
1. `Install_ScreenMind.vbs` をダブルクリック
2. インストール先を確認
3. スタートメニュー/デスクトップにショートカットが作成されます

### 手動インストール
1. `ScreenMind.exe` を `C:\\Program Files\\ScreenMind\\` にコピー
2. ショートカットを作成（オプション）

## 🚀 起動方法
- スタートメニューから「ScreenMind」を選択
- またはデスクトップのショートカットをダブルクリック

## 🗑️ アンインストール
1. `Uninstall_ScreenMind.vbs` をダブルクリック
2. 確認ダイアログで「はい」を選択

## ⚙️ システム要件
- Windows 7 以上
- メモリ: 2GB 以上
- ディスク容量: 500MB 以上

## 📝 トラブルシューティング
- 起動しない場合: `logs/screenmind.log` を確認
- エラーが発生した場合: `error_report.json` をご確認ください

## 📞 サポート
問題が発生した場合は、同梱の `STABILITY_REPORT.md` をご参照ください。

---
ScreenMind v{self.version} - AI-Powered Workflow Platform
"""
            readme_path = self.dist_dir / "INSTALL.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme)

            logger.info("✅ インストール手順書を作成: %s", readme_path)
            return True
        except Exception as e:
            logger.error("❌ インストール手順書作成失敗: %s", e)
            return False

    def create_build_info(self) -> bool:
        """ビルド情報を記録。"""
        logger.info("=== ビルド情報を記録 ===")

        try:
            build_info = {
                "version": self.version,
                "build_date": datetime.now().isoformat(),
                "platform": sys.platform,
                "python_version": sys.version,
                "files": {
                    "exe": str(self.dist_dir / "ScreenMind.exe"),
                    "installer": str(self.dist_dir / "Install_ScreenMind.vbs"),
                    "uninstaller": str(self.dist_dir / "Uninstall_ScreenMind.vbs"),
                }
            }

            info_path = self.dist_dir / "BUILD_INFO.json"
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(build_info, f, ensure_ascii=False, indent=2)

            logger.info("✅ ビルド情報を記録: %s", info_path)
            return True
        except Exception as e:
            logger.error("❌ ビルド情報記録失敗: %s", e)
            return False

    def cleanup(self):
        """一時ファイルをクリーンアップ。"""
        logger.info("=== 一時ファイルをクリーンアップ ===")

        try:
            # build ディレクトリを削除
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                logger.info("✅ build ディレクトリを削除")

            # __pycache__ を削除
            for pycache in self.project_root.glob("**/__pycache__"):
                shutil.rmtree(pycache)
                logger.info("✅ __pycache__ を削除")
        except Exception as e:
            logger.warning("⚠️  クリーンアップエラー: %s", e)

    def build(self) -> bool:
        """完全なビルドプロセスを実行。"""
        logger.info("=" * 60)
        logger.info("ScreenMind v%s - EXE ビルドプロセス開始", self.version)
        logger.info("=" * 60 + "\n")

        # 前提条件チェック
        if not self.check_requirements():
            return False

        # アイコン作成
        self.create_icon()

        # EXE ビルド
        if not self.build_exe():
            return False

        # インストーラースクリプト作成
        if not self.create_installer_script():
            return False

        # アンインストーラースクリプト作成
        if not self.create_uninstaller_script():
            return False

        # インストール手順書作成
        if not self.create_readme():
            return False

        # ビルド情報記録
        if not self.create_build_info():
            return False

        # クリーンアップ
        self.cleanup()

        logger.info("\n" + "=" * 60)
        logger.info("✅ ビルド完了")
        logger.info("=" * 60)
        logger.info("\n📦 配布ファイル:")
        logger.info("  - %s", self.dist_dir / "ScreenMind.exe")
        logger.info("  - %s", self.dist_dir / "Install_ScreenMind.vbs")
        logger.info("  - %s", self.dist_dir / "Uninstall_ScreenMind.vbs")
        logger.info("  - %s", self.dist_dir / "INSTALL.md")
        logger.info("\n🚀 次のステップ:")
        logger.info("  1. dist フォルダ内のファイルを配布")
        logger.info("  2. ユーザーが Install_ScreenMind.vbs を実行")
        logger.info("  3. ScreenMind が自動インストール・起動")

        return True


if __name__ == "__main__":
    builder = ScreenMindBuilder()
    success = builder.build()
    sys.exit(0 if success else 1)
