#!/usr/bin/env python3
"""
ScreenMind v4.1 - シンプル EXE ビルドスクリプト
PyInstaller を使用して実行ファイルを生成します
"""

import subprocess
import sys
import os
from pathlib import Path

def build_exe():
    """EXE ファイルをビルド"""
    
    print("=" * 70)
    print("ScreenMind v4.1 - EXE ビルド開始")
    print("=" * 70)
    
    # パスの設定
    build_dir = Path(__file__).parent
    src_dir = build_dir.parent / 'src'
    dist_dir = build_dir / 'dist'
    build_cache_dir = build_dir / 'build_cache'
    
    # screenmind_lite.py のパス
    lite_script = build_dir / 'screenmind_lite.py'
    
    if not lite_script.exists():
        print(f"❌ エラー: {lite_script} が見つかりません")
        return False
    
    # PyInstaller コマンド
    cmd = [
        'pyinstaller',
        '--onefile',                    # 単一ファイルに統合
        '--windowed',                   # コンソール表示なし
        '--name', 'ScreenMind',         # 実行ファイル名
        '--icon', str(build_dir / 'screenmind.ico'),  # アイコン
        '--distpath', str(dist_dir),    # 出力ディレクトリ
        '--workpath', str(build_cache_dir),  # ビルドキャッシュ
        '--specpath', str(build_dir),   # .spec ファイルの場所
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=httpx',
        '--hidden-import=PIL',
        '--collect-all=PyQt6',
        str(lite_script),
    ]
    
    print("\n📦 PyInstaller でビルド中...")
    print(f"   コマンド: {' '.join(cmd[:5])} ...")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        exe_path = dist_dir / 'ScreenMind.exe'
        
        if exe_path.exists():
            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            print(f"\n✅ EXE ビルド成功！")
            print(f"   出力ファイル: {exe_path}")
            print(f"   ファイルサイズ: {file_size:.2f} MB")
            return True
        else:
            print(f"\n❌ EXE ファイルが生成されませんでした")
            print(f"   出力ディレクトリ: {dist_dir}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ ビルドエラー:")
        print(f"   {e.stderr}")
        return False
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return False

def main():
    """メイン処理"""
    try:
        success = build_exe()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  ビルドがキャンセルされました")
        sys.exit(1)

if __name__ == '__main__':
    main()
