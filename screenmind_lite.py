#!/usr/bin/env python3
"""
ScreenMind v4.1 Lite Edition
軽量版メインアプリケーション（EXE化用）
"""

import sys
import os
from pathlib import Path

# ScreenMind のモジュールパスを追加
SCREENMIND_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SCREENMIND_ROOT / 'src'))

def main():
    """メインエントリーポイント"""
    try:
        # PyQt6 のインポート
        from PyQt6.QtWidgets import QApplication
        from screenmind_v2 import ScreenMindApp
        
        # アプリケーションの初期化
        app = QApplication(sys.argv)
        
        # ScreenMind ウィンドウを作成
        window = ScreenMindApp()
        window.show()
        
        # イベントループを開始
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ エラー: 必要なライブラリが見つかりません")
        print(f"   {e}")
        print(f"\n依存ライブラリをインストールしてください:")
        print(f"   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
