"""
ScreenMind - キーボードショートカット管理モジュール
拡張ショートカット機能を提供する。
"""

import json
import logging
import os
from typing import Dict, Callable, Optional, List

from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import QShortcut, QMainWindow

logger = logging.getLogger(__name__)


class KeyboardShortcuts:
    """キーボードショートカットを管理するクラス。"""

    # デフォルトショートカット
    DEFAULT_SHORTCUTS = {
        "send_message": "Ctrl+Return",
        "clear_history": "Ctrl+L",
        "toggle_auto_model": "Ctrl+M",
        "export_log": "Ctrl+E",
        "copy_response": "Ctrl+Shift+C",
        "toggle_theme": "Ctrl+T",
        "open_dashboard": "Ctrl+D",
        "show_stats": "Ctrl+Shift+S",
        "toggle_transparency": "Ctrl+Shift+T",
        "quit_app": "Ctrl+Q",
        "focus_input": "Ctrl+F",
        "undo": "Ctrl+Z",
        "redo": "Ctrl+Y",
    }

    _shortcuts: Dict[str, str] = {}
    _shortcut_objects: Dict[str, QShortcut] = {}
    _config_dir = "config"

    @classmethod
    def initialize(cls):
        """ショートカットを初期化する。"""
        cls._shortcuts = cls.DEFAULT_SHORTCUTS.copy()
        cls.load_shortcuts()
        logger.info("キーボードショートカットを初期化: %d個", len(cls._shortcuts))

    @classmethod
    def get_shortcut(cls, action: str) -> str:
        """ショートカットを取得する。"""
        if not cls._shortcuts:
            cls.initialize()
        return cls._shortcuts.get(action, "")

    @classmethod
    def set_shortcut(cls, action: str, key_sequence: str) -> bool:
        """ショートカットを設定する。"""
        # キーシーケンスの妥当性を確認
        if not QKeySequence(key_sequence).isEmpty():
            cls._shortcuts[action] = key_sequence
            logger.info("ショートカットを設定: %s = %s", action, key_sequence)
            return True
        else:
            logger.error("無効なキーシーケンス: %s", key_sequence)
            return False

    @classmethod
    def register_shortcut(
        cls,
        window: QMainWindow,
        action: str,
        callback: Callable,
    ) -> Optional[QShortcut]:
        """ショートカットをウィンドウに登録する。"""
        key_sequence = cls.get_shortcut(action)
        if not key_sequence:
            logger.warning("ショートカットが見つかりません: %s", action)
            return None

        try:
            shortcut = QShortcut(QKeySequence(key_sequence), window)
            shortcut.activated.connect(callback)
            cls._shortcut_objects[action] = shortcut
            logger.debug("ショートカットを登録: %s (%s)", action, key_sequence)
            return shortcut
        except Exception as e:
            logger.error("ショートカット登録エラー: %s", e)
            return None

    @classmethod
    def register_all_shortcuts(
        cls,
        window: QMainWindow,
        callbacks: Dict[str, Callable],
    ):
        """複数のショートカットを一括登録する。"""
        for action, callback in callbacks.items():
            cls.register_shortcut(window, action, callback)
        logger.info("ショートカットを一括登録: %d個", len(callbacks))

    @classmethod
    def get_all_shortcuts(cls) -> Dict[str, str]:
        """すべてのショートカットを取得する。"""
        if not cls._shortcuts:
            cls.initialize()
        return cls._shortcuts.copy()

    @classmethod
    def get_shortcut_description(cls) -> Dict[str, Dict[str, str]]:
        """ショートカットの説明を取得する。"""
        descriptions = {
            "send_message": {
                "key": cls.get_shortcut("send_message"),
                "description": "メッセージを送信",
            },
            "clear_history": {
                "key": cls.get_shortcut("clear_history"),
                "description": "会話履歴をクリア",
            },
            "toggle_auto_model": {
                "key": cls.get_shortcut("toggle_auto_model"),
                "description": "自動モデル選択を切り替え",
            },
            "export_log": {
                "key": cls.get_shortcut("export_log"),
                "description": "ログをエクスポート",
            },
            "copy_response": {
                "key": cls.get_shortcut("copy_response"),
                "description": "最後の回答をコピー",
            },
            "toggle_theme": {
                "key": cls.get_shortcut("toggle_theme"),
                "description": "テーマを切り替え",
            },
            "open_dashboard": {
                "key": cls.get_shortcut("open_dashboard"),
                "description": "Webダッシュボードを開く",
            },
            "show_stats": {
                "key": cls.get_shortcut("show_stats"),
                "description": "統計情報を表示",
            },
            "toggle_transparency": {
                "key": cls.get_shortcut("toggle_transparency"),
                "description": "透明度を切り替え",
            },
            "quit_app": {
                "key": cls.get_shortcut("quit_app"),
                "description": "アプリケーションを終了",
            },
        }
        return descriptions

    @classmethod
    def save_shortcuts(cls, config_file: str = "shortcuts.json"):
        """ショートカット設定をファイルに保存する。"""
        try:
            os.makedirs(cls._config_dir, exist_ok=True)
            config_path = os.path.join(cls._config_dir, config_file)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(cls._shortcuts, f, ensure_ascii=False, indent=2)

            logger.info("ショートカット設定を保存: %s", config_path)
        except Exception as e:
            logger.error("ショートカット設定の保存に失敗: %s", e)

    @classmethod
    def load_shortcuts(cls, config_file: str = "shortcuts.json"):
        """保存されたショートカット設定を読み込む。"""
        try:
            config_path = os.path.join(cls._config_dir, config_file)
            if not os.path.exists(config_path):
                logger.info("ショートカット設定ファイルが見つかりません（デフォルトを使用）")
                return

            with open(config_path, "r", encoding="utf-8") as f:
                cls._shortcuts = json.load(f)

            logger.info("ショートカット設定を読み込み: %s", config_path)
        except Exception as e:
            logger.error("ショートカット設定の読み込みに失敗: %s", e)

    @classmethod
    def reset_to_defaults(cls):
        """デフォルトショートカットにリセットする。"""
        cls._shortcuts = cls.DEFAULT_SHORTCUTS.copy()
        logger.info("ショートカットをデフォルトにリセット")

    @classmethod
    def get_shortcut_help_text(cls) -> str:
        """ショートカットのヘルプテキストを生成する。"""
        descriptions = cls.get_shortcut_description()
        help_text = "⌨️ キーボードショートカット\n\n"
        for action, info in descriptions.items():
            help_text += f"{info['key']:20} - {info['description']}\n"
        return help_text

    @classmethod
    def export_shortcuts_to_html(cls) -> str:
        """ショートカット一覧をHTMLで生成する。"""
        descriptions = cls.get_shortcut_description()

        html = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ScreenMind キーボードショートカット</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #007bff;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background: #f9f9f9;
        }
        .key {
            font-family: 'Courier New', monospace;
            background: #f0f0f0;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⌨️ ScreenMind キーボードショートカット</h1>
        <table>
            <tr>
                <th>キー</th>
                <th>説明</th>
            </tr>
"""
        for action, info in descriptions.items():
            html += f"""
            <tr>
                <td><span class="key">{info['key']}</span></td>
                <td>{info['description']}</td>
            </tr>
"""
        html += """
        </table>
    </div>
</body>
</html>
"""
        return html


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== キーボードショートカットのテスト ===\n")

    # 初期化
    print("1️⃣  ショートカットを初期化")
    KeyboardShortcuts.initialize()
    print("   ✅ 初期化完了\n")

    # ショートカット取得
    print("2️⃣  ショートカットを取得:")
    shortcuts = KeyboardShortcuts.get_all_shortcuts()
    for action, key in list(shortcuts.items())[:5]:
        print(f"   {action}: {key}")
    print(f"   ... 他 {len(shortcuts) - 5} 個\n")

    # ショートカット設定
    print("3️⃣  ショートカットを設定:")
    KeyboardShortcuts.set_shortcut("send_message", "Ctrl+Shift+Return")
    print(f"   send_message: {KeyboardShortcuts.get_shortcut('send_message')}\n")

    # ヘルプテキスト
    print("4️⃣  ヘルプテキスト:")
    print(KeyboardShortcuts.get_shortcut_help_text())

    # 設定の保存
    print("5️⃣  設定を保存:")
    KeyboardShortcuts.save_shortcuts()
    print("   ✅ 保存完了")
