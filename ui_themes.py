"""
ScreenMind - UIテーマ管理モジュール
ダークモード・ライトモード対応のテーマシステム。
"""

import json
import logging
import os
from typing import Dict, Optional

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class Theme:
    """UIテーマを管理するクラス。"""

    # ライトテーマ
    LIGHT = {
        "name": "Light",
        "bg_color": "#ffffff",
        "bg_secondary": "#f5f5f5",
        "text_color": "#000000",
        "text_muted": "#666666",
        "accent_color": "#007bff",
        "accent_hover": "#0056b3",
        "border_color": "#cccccc",
        "success_color": "#28a745",
        "warning_color": "#ffc107",
        "error_color": "#dc3545",
        "bubble_user": "#e3f2fd",
        "bubble_assistant": "#f5f5f5",
        "button_bg": "#007bff",
        "button_text": "#ffffff",
    }

    # ダークテーマ
    DARK = {
        "name": "Dark",
        "bg_color": "#1e1e1e",
        "bg_secondary": "#2d2d2d",
        "text_color": "#ffffff",
        "text_muted": "#aaaaaa",
        "accent_color": "#0d6efd",
        "accent_hover": "#0a58ca",
        "border_color": "#444444",
        "success_color": "#20c997",
        "warning_color": "#ffc107",
        "error_color": "#dc3545",
        "bubble_user": "#1f4788",
        "bubble_assistant": "#2d2d2d",
        "button_bg": "#0d6efd",
        "button_text": "#ffffff",
    }

    # 高コントラストテーマ
    HIGH_CONTRAST = {
        "name": "High Contrast",
        "bg_color": "#000000",
        "bg_secondary": "#1a1a1a",
        "text_color": "#ffffff",
        "text_muted": "#cccccc",
        "accent_color": "#ffff00",
        "accent_hover": "#cccc00",
        "border_color": "#ffffff",
        "success_color": "#00ff00",
        "warning_color": "#ffff00",
        "error_color": "#ff0000",
        "bubble_user": "#003300",
        "bubble_assistant": "#1a1a1a",
        "button_bg": "#ffff00",
        "button_text": "#000000",
    }

    _current_theme: Optional[Dict[str, str]] = None
    _theme_dir = "themes"

    @classmethod
    def get_available_themes(cls) -> Dict[str, Dict[str, str]]:
        """利用可能なテーマを取得する。"""
        return {
            "light": cls.LIGHT,
            "dark": cls.DARK,
            "high_contrast": cls.HIGH_CONTRAST,
        }

    @classmethod
    def set_theme(cls, theme_name: str) -> bool:
        """テーマを設定する。"""
        themes = cls.get_available_themes()
        if theme_name.lower() not in themes:
            logger.error("不明なテーマ: %s", theme_name)
            return False

        cls._current_theme = themes[theme_name.lower()]
        logger.info("テーマを変更: %s", theme_name)
        return True

    @classmethod
    def get_current_theme(cls) -> Dict[str, str]:
        """現在のテーマを取得する。"""
        if cls._current_theme is None:
            cls.set_theme("light")
        return cls._current_theme

    @classmethod
    def get_color(cls, key: str) -> str:
        """テーマから色を取得する。"""
        theme = cls.get_current_theme()
        return theme.get(key, "#000000")

    @classmethod
    def apply_stylesheet(cls, app: QApplication):
        """PyQt アプリケーションにテーマを適用する。"""
        theme = cls.get_current_theme()

        stylesheet = f"""
            QMainWindow {{
                background-color: {theme['bg_color']};
                color: {theme['text_color']};
            }}

            QWidget {{
                background-color: {theme['bg_color']};
                color: {theme['text_color']};
            }}

            QPushButton {{
                background-color: {theme['button_bg']};
                color: {theme['button_text']};
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {theme['accent_hover']};
            }}

            QPushButton:pressed {{
                background-color: {theme['accent_color']};
            }}

            QLineEdit, QTextEdit {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_color']};
                border: 1px solid {theme['border_color']};
                border-radius: 4px;
                padding: 6px;
            }}

            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {theme['accent_color']};
            }}

            QComboBox {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_color']};
                border: 1px solid {theme['border_color']};
                border-radius: 4px;
                padding: 4px;
            }}

            QComboBox::drop-down {{
                border: none;
            }}

            QComboBox QAbstractItemView {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_color']};
                selection-background-color: {theme['accent_color']};
            }}

            QLabel {{
                color: {theme['text_color']};
            }}

            QGroupBox {{
                color: {theme['text_color']};
                border: 1px solid {theme['border_color']};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }}

            QScrollBar:vertical {{
                background-color: {theme['bg_secondary']};
                width: 12px;
                margin: 0px 0px 0px 0px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {theme['accent_color']};
                border-radius: 6px;
                min-height: 20px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {theme['accent_hover']};
            }}

            QScrollBar:horizontal {{
                background-color: {theme['bg_secondary']};
                height: 12px;
                margin: 0px 0px 0px 0px;
            }}

            QScrollBar::handle:horizontal {{
                background-color: {theme['accent_color']};
                border-radius: 6px;
                min-width: 20px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background-color: {theme['accent_hover']};
            }}

            QDialog {{
                background-color: {theme['bg_color']};
                color: {theme['text_color']};
            }}

            QTableWidget {{
                background-color: {theme['bg_secondary']};
                color: {theme['text_color']};
                gridline-color: {theme['border_color']};
            }}

            QTableWidget::item {{
                padding: 4px;
            }}

            QTableWidget::item:selected {{
                background-color: {theme['accent_color']};
            }}

            QHeaderView::section {{
                background-color: {theme['accent_color']};
                color: {theme['button_text']};
                padding: 4px;
                border: none;
            }}
        """

        app.setStyleSheet(stylesheet)
        logger.info("スタイルシートを適用: %s", theme.get("name", "Unknown"))

    @classmethod
    def save_theme_preference(cls, theme_name: str, config_file: str = "theme_config.json"):
        """テーマ設定をファイルに保存する。"""
        try:
            os.makedirs(cls._theme_dir, exist_ok=True)
            config_path = os.path.join(cls._theme_dir, config_file)

            config = {"current_theme": theme_name}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            logger.info("テーマ設定を保存: %s", config_path)
        except Exception as e:
            logger.error("テーマ設定の保存に失敗: %s", e)

    @classmethod
    def load_theme_preference(cls, config_file: str = "theme_config.json") -> str:
        """保存されたテーマ設定を読み込む。"""
        try:
            config_path = os.path.join(cls._theme_dir, config_file)
            if not os.path.exists(config_path):
                logger.info("テーマ設定ファイルが見つかりません（デフォルトを使用）")
                return "light"

            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            theme_name = config.get("current_theme", "light")
            logger.info("テーマ設定を読み込み: %s", theme_name)
            return theme_name
        except Exception as e:
            logger.error("テーマ設定の読み込みに失敗: %s", e)
            return "light"


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== テーマシステムのテスト ===\n")

    # テーマの取得
    print("1️⃣  利用可能なテーマ:")
    for name, theme in Theme.get_available_themes().items():
        print(f"   - {name}: {theme['name']}")

    # テーマの設定
    print("\n2️⃣  テーマを設定:")
    Theme.set_theme("dark")
    print(f"   現在のテーマ: {Theme.get_current_theme()['name']}")

    # 色の取得
    print("\n3️⃣  テーマから色を取得:")
    print(f"   背景色: {Theme.get_color('bg_color')}")
    print(f"   テキスト色: {Theme.get_color('text_color')}")
    print(f"   アクセント色: {Theme.get_color('accent_color')}")

    # 設定の保存・読み込み
    print("\n4️⃣  設定の保存・読み込み:")
    Theme.save_theme_preference("dark")
    loaded = Theme.load_theme_preference()
    print(f"   読み込んだテーマ: {loaded}")
