"""
ScreenMind - セットアップウィザード
初回起動時のセットアップを簡単にするウィザード。
"""

import json
import logging
import os
from typing import Dict, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QProgressBar,
)
from PyQt6.QtGui import QFont

import config

logger = logging.getLogger(__name__)


class SetupWizard(QDialog):
    """初期セットアップウィザード。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ScreenMind セットアップウィザード")
        self.setGeometry(100, 100, 600, 500)
        self.setModal(True)

        self.settings = {}
        self._current_step = 0
        self._total_steps = 4

        self._setup_ui()

    def _setup_ui(self):
        """UI を構築する。"""
        layout = QVBoxLayout()

        # タイトル
        title = QLabel("ScreenMind へようこそ！")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # サブタイトル
        subtitle = QLabel("初期セットアップウィザードへようこそ。\n数分で ScreenMind を使い始められます。")
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)

        # ステップインジケーター
        self.progress = QProgressBar()
        self.progress.setMaximum(self._total_steps)
        self.progress.setValue(1)
        layout.addWidget(self.progress)

        # ステップコンテナ
        self.step_container = QVBoxLayout()
        layout.addLayout(self.step_container)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.prev_btn = QPushButton("← 戻る")
        self.prev_btn.clicked.connect(self._on_prev)
        self.prev_btn.setEnabled(False)
        button_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("次へ →")
        self.next_btn.clicked.connect(self._on_next)
        button_layout.addWidget(self.next_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        self._show_step(0)

    def _clear_step_container(self):
        """ステップコンテナをクリアする。"""
        while self.step_container.count():
            item = self.step_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_step(self, step: int):
        """指定されたステップを表示する。"""
        self._clear_step_container()
        self._current_step = step
        self.progress.setValue(step + 1)

        if step == 0:
            self._show_step_model_selection()
        elif step == 1:
            self._show_step_keyboard_settings()
        elif step == 2:
            self._show_step_ui_preferences()
        elif step == 3:
            self._show_step_summary()

        # ボタンの有効/無効を更新
        self.prev_btn.setEnabled(step > 0)
        self.next_btn.setText("完了" if step == self._total_steps - 1 else "次へ →")

    def _show_step_model_selection(self):
        """ステップ 0: モデル選択。"""
        group = QGroupBox("使用するモデルを選択")
        layout = QVBoxLayout()

        # ラジオボタン
        self.model_group = QButtonGroup()

        local_radio = QRadioButton("ローカルモデル（推奨・無料・プライベート）")
        local_radio.setChecked(True)
        self.model_group.addButton(local_radio, 0)
        layout.addWidget(local_radio)

        cloud_radio = QRadioButton("クラウドAPI（高速・有料・インターネット必須）")
        self.model_group.addButton(cloud_radio, 1)
        layout.addWidget(cloud_radio)

        hybrid_radio = QRadioButton("ハイブリッド（ローカル + クラウド）")
        self.model_group.addButton(hybrid_radio, 2)
        layout.addWidget(hybrid_radio)

        group.setLayout(layout)
        self.step_container.addWidget(group)

        info = QLabel(
            "💡 ローカルモデルを推奨します。\n"
            "インターネット接続が不要で、データがプライベートに保たれます。"
        )
        info.setStyleSheet("color: #0066cc; margin-top: 10px;")
        self.step_container.addWidget(info)

        self.step_container.addStretch()

    def _show_step_keyboard_settings(self):
        """ステップ 1: キーボード設定。"""
        group = QGroupBox("キーボード設定")
        layout = QVBoxLayout()

        # ホットキー設定
        hotkey_layout = QHBoxLayout()
        hotkey_label = QLabel("ホットキー:")
        hotkey_label.setMinimumWidth(100)
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setText("Ctrl+Shift+Space")
        self.hotkey_input.setPlaceholderText("例: Ctrl+Shift+Space")
        hotkey_layout.addWidget(hotkey_label)
        hotkey_layout.addWidget(self.hotkey_input)
        layout.addLayout(hotkey_layout)

        # ショートカット有効化
        self.shortcuts_check = QCheckBox("拡張ショートカットを有効化")
        self.shortcuts_check.setChecked(True)
        layout.addWidget(self.shortcuts_check)

        group.setLayout(layout)
        self.step_container.addWidget(group)

        info = QLabel(
            "💡 ホットキーは、ScreenMind が最小化されている時に\n"
            "ウィンドウを表示するために使用されます。"
        )
        info.setStyleSheet("color: #0066cc; margin-top: 10px;")
        self.step_container.addWidget(info)

        self.step_container.addStretch()

    def _show_step_ui_preferences(self):
        """ステップ 2: UI 設定。"""
        group = QGroupBox("UI 設定")
        layout = QVBoxLayout()

        # テーマ選択
        theme_layout = QHBoxLayout()
        theme_label = QLabel("テーマ:")
        theme_label.setMinimumWidth(100)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["ライト", "ダーク", "高コントラスト"])
        self.theme_combo.setCurrentIndex(0)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # 透明度設定
        opacity_layout = QHBoxLayout()
        opacity_label = QLabel("透明度:")
        opacity_label.setMinimumWidth(100)
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setMinimum(30)
        self.opacity_spin.setMaximum(100)
        self.opacity_spin.setValue(85)
        self.opacity_spin.setSuffix("%")
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_spin)
        opacity_layout.addStretch()
        layout.addLayout(opacity_layout)

        # フォントサイズ
        font_layout = QHBoxLayout()
        font_label = QLabel("フォントサイズ:")
        font_label.setMinimumWidth(100)
        self.font_spin = QSpinBox()
        self.font_spin.setMinimum(8)
        self.font_spin.setMaximum(16)
        self.font_spin.setValue(10)
        self.font_spin.setSuffix("pt")
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_spin)
        font_layout.addStretch()
        layout.addLayout(font_layout)

        group.setLayout(layout)
        self.step_container.addWidget(group)

        self.step_container.addStretch()

    def _show_step_summary(self):
        """ステップ 3: 設定確認。"""
        group = QGroupBox("設定確認")
        layout = QVBoxLayout()

        summary_text = QLabel()
        summary_text.setWordWrap(True)

        model_type = ["ローカル", "クラウド", "ハイブリッド"][self.model_group.checkedId()]
        summary = (
            f"<b>セットアップ内容</b><br><br>"
            f"<b>モデル:</b> {model_type}<br>"
            f"<b>ホットキー:</b> {self.hotkey_input.text()}<br>"
            f"<b>テーマ:</b> {self.theme_combo.currentText()}<br>"
            f"<b>透明度:</b> {self.opacity_spin.value()}%<br>"
            f"<b>フォントサイズ:</b> {self.font_spin.value()}pt<br><br>"
            f"これらの設定は後から変更できます。"
        )
        summary_text.setText(summary)
        layout.addWidget(summary_text)

        group.setLayout(layout)
        self.step_container.addWidget(group)

        self.step_container.addStretch()

    def _on_next(self):
        """次へボタンが押された。"""
        if self._current_step == self._total_steps - 1:
            self._save_settings()
            self.accept()
        else:
            self._show_step(self._current_step + 1)

    def _on_prev(self):
        """戻るボタンが押された。"""
        if self._current_step > 0:
            self._show_step(self._current_step - 1)

    def _save_settings(self):
        """設定を保存する。"""
        self.settings = {
            "model_type": ["local", "cloud", "hybrid"][self.model_group.checkedId()],
            "hotkey": self.hotkey_input.text(),
            "shortcuts_enabled": self.shortcuts_check.isChecked(),
            "theme": ["light", "dark", "high_contrast"][self.theme_combo.currentIndex()],
            "opacity": self.opacity_spin.value(),
            "font_size": self.font_spin.value(),
        }

        # 設定をファイルに保存
        try:
            os.makedirs("config", exist_ok=True)
            with open("config/setup_wizard.json", "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.info("セットアップ設定を保存しました")
        except Exception as e:
            logger.error("セットアップ設定の保存に失敗: %s", e)

    def get_settings(self) -> Dict:
        """設定を取得する。"""
        return self.settings


# ===== 単体テスト =====
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    logging.basicConfig(level=logging.INFO)

    app = QApplication(sys.argv)
    wizard = SetupWizard()
    result = wizard.exec()

    if result == QDialog.DialogCode.Accepted:
        print("✅ セットアップ完了")
        print("設定:", json.dumps(wizard.get_settings(), ensure_ascii=False, indent=2))
    else:
        print("❌ セットアップがキャンセルされました")
