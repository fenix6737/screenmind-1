"""
ScreenMind v2.0 - メインアプリケーション（複数LLM対応版）
PyQt6によるフローティングチャットUIを提供する。
複数LLMの管理・自動切り替え・統計表示をサポートする。
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import (
    Qt,
    QPoint,
    QTimer,
    QThread,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QColor,
    QFont,
)
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)

import config
from ai_client import AIWorker, ConversationHistory
from capture import capture_screen
from model_config import ModelConfigManager, ModelType
from model_manager import ModelManager
from auto_switcher import AutoSwitcher
from cache_manager import CacheManager
from history_compressor import AdaptiveHistoryManager
from analytics import AnalyticsCollector

logger = logging.getLogger(__name__)


# ===== メッセージバブルウィジェット =====

class MessageBubble(QFrame):
    """チャットメッセージを表示するバブルウィジェット。"""

    def __init__(self, text: str, role: str, parent=None):
        super().__init__(parent)
        self.role = role
        self._full_text = text
        self._setup_ui(text)

    def _setup_ui(self, text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        role_label = QLabel("あなた" if self.role == "user" else "🧠 ScreenMind")
        role_label.setStyleSheet(
            f"color: {config.COLOR_TEXT_MUTED}; font-size: {config.FONT_SIZE_SMALL}pt;"
        )

        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.text_label.setStyleSheet(
            f"color: {config.COLOR_TEXT}; font-size: {config.FONT_SIZE_NORMAL}pt;"
            " line-height: 1.5;"
        )

        layout.addWidget(role_label)
        layout.addWidget(self.text_label)

        if self.role == "user":
            bg = config.COLOR_USER_BUBBLE
            self.setStyleSheet(
                f"QFrame {{ background-color: {bg}; border-radius: 10px;"
                f" border: 1px solid #1a4a7a; }}"
            )
        else:
            bg = config.COLOR_AI_BUBBLE
            self.setStyleSheet(
                f"QFrame {{ background-color: {bg}; border-radius: 10px;"
                f" border: 1px solid {config.COLOR_BORDER}; }}"
            )

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def append_text(self, token: str):
        """ストリーミングトークンをリアルタイムで追記する。"""
        self._full_text += token
        self.text_label.setText(self._full_text)

    def get_text(self) -> str:
        return self._full_text


# ===== ローディングインジケータ =====

class LoadingIndicator(QLabel):
    """点滅アニメーションのローディング表示。"""

    def __init__(self, parent=None):
        super().__init__("　", parent)
        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self.setStyleSheet(
            f"color: {config.COLOR_ACCENT}; font-size: {config.FONT_SIZE_NORMAL}pt;"
        )

    def start(self):
        self._dots = 0
        self._timer.start(400)
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _update(self):
        self._dots = (self._dots + 1) % 4
        self.setText("解析中" + "." * self._dots)


# ===== モデル統計ダイアログ =====

class ModelStatsDialog(QDialog):
    """モデルの統計情報を表示するダイアログ。"""

    def __init__(self, model_manager: ModelManager, parent=None):
        super().__init__(parent)
        self.model_manager = model_manager
        self.setWindowTitle("📊 モデル統計")
        self.setGeometry(100, 100, 700, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 概要
        stats = self.model_manager.get_statistics()
        summary_text = (
            f"総モデル数: {stats['total_models']} | "
            f"有効: {stats['enabled_models']} | "
            f"健全: {stats['healthy_models']} | "
            f"総リクエスト: {stats['total_requests']} | "
            f"成功率: {stats['overall_success_rate']:.1%}"
        )
        summary_label = QLabel(summary_text)
        summary_label.setStyleSheet(
            f"color: {config.COLOR_TEXT}; font-size: {config.FONT_SIZE_NORMAL}pt; "
            "padding: 8px; background-color: rgba(255,255,255,0.05); border-radius: 4px;"
        )
        layout.addWidget(summary_label)

        # テーブル
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "モデル", "プロバイダー", "有効", "リクエスト", "成功率", "応答時間", "トークン"
        ])
        table.setStyleSheet(
            f"QTableWidget {{ background-color: {config.COLOR_BG}; "
            f"color: {config.COLOR_TEXT}; }}"
        )

        for row, model_data in enumerate(stats["models"]):
            table.insertRow(row)
            model = self.model_manager.get_model(model_data["id"])
            metrics = model_data.get("metrics", {})

            items = [
                model_data["id"],
                model.provider.value if model else "N/A",
                "✓" if model_data["enabled"] else "✗",
                str(metrics.get("request_count", 0)),
                metrics.get("success_rate", "N/A"),
                metrics.get("avg_response_time_ms", "N/A"),
                str(metrics.get("total_tokens", 0)),
            ]

            for col, text in enumerate(items):
                item = QTableWidgetItem(str(text))
                item.setForeground(QColor(config.COLOR_TEXT))
                table.setItem(row, col, item)

        layout.addWidget(table)

        # 閉じるボタン
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


# ===== メインウィンドウ =====

class ScreenMindWindow(QMainWindow):
    """ScreenMindのメインウィンドウ（複数LLM対応版）。"""

    def __init__(self):
        super().__init__()
        self.history = ConversationHistory()
        self.model_manager = ModelManager()
        self.auto_switcher = AutoSwitcher(self.model_manager)
        self.cache_manager = CacheManager()
        self.history_manager = AdaptiveHistoryManager(context_window_tokens=4096)
        self.analytics_collector = AnalyticsCollector()

        self._current_ai_bubble: Optional[MessageBubble] = None
        self._ai_worker: Optional[AIWorker] = None
        self._drag_pos: Optional[QPoint] = None
        self._is_processing = False
        self._current_model_id: Optional[str] = None
        self._auto_mode = True

        self._setup_window()
        self._setup_ui()
        self._apply_stylesheet()
        self._setup_hotkey()

        # 起動メッセージ
        self._add_system_message(
            "🧠 ScreenMind v2.0 へようこそ！\n"
            "複数LLM対応版です。\n"
            "質問を入力してEnterを押すと、最適なモデルで解析します。"
        )

    # ===== ウィンドウ初期設定 =====

    def _setup_window(self):
        """ウィンドウの基本設定を行う。"""
        self.setWindowTitle("🧠 ScreenMind v2.0")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        self.setMinimumSize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        self.setWindowOpacity(config.WINDOW_OPACITY)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.right() - config.WINDOW_WIDTH - 20
            y = geo.bottom() - config.WINDOW_HEIGHT - 40
            self.move(x, y)

    # ===== UI構築 =====

    def _setup_ui(self):
        """UIレイアウトを構築する。"""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self._create_header())
        main_layout.addWidget(self._create_model_selector())
        main_layout.addWidget(self._create_chat_area(), stretch=1)

        self.loading_indicator = LoadingIndicator()
        self.loading_indicator.hide()
        loading_container = QWidget()
        loading_container.setObjectName("loadingContainer")
        lc_layout = QHBoxLayout(loading_container)
        lc_layout.setContentsMargins(12, 4, 12, 4)
        lc_layout.addWidget(self.loading_indicator)
        lc_layout.addStretch()
        main_layout.addWidget(loading_container)

        main_layout.addWidget(self._create_input_area())
        main_layout.addWidget(self._create_toolbar())

    def _create_header(self) -> QWidget:
        """ヘッダーウィジェットを作成する。"""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(44)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 0, 8, 0)

        title = QLabel("🧠 ScreenMind v2.0")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        layout.addStretch()

        new_btn = QPushButton("＋")
        new_btn.setObjectName("iconButton")
        new_btn.setToolTip("会話をリセット")
        new_btn.setFixedSize(28, 28)
        new_btn.clicked.connect(self._on_new_conversation)
        layout.addWidget(new_btn)

        stats_btn = QPushButton("📊")
        stats_btn.setObjectName("iconButton")
        stats_btn.setToolTip("統計情報")
        stats_btn.setFixedSize(28, 28)
        stats_btn.clicked.connect(self._on_show_stats)
        layout.addWidget(stats_btn)

        save_btn = QPushButton("💾")
        save_btn.setObjectName("iconButton")
        save_btn.setToolTip("会話履歴を保存")
        save_btn.setFixedSize(28, 28)
        save_btn.clicked.connect(self._on_save_history)
        layout.addWidget(save_btn)

        min_btn = QPushButton("─")
        min_btn.setObjectName("iconButton")
        min_btn.setToolTip("最小化")
        min_btn.setFixedSize(28, 28)
        min_btn.clicked.connect(self.showMinimized)
        layout.addWidget(min_btn)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.setToolTip("終了")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)

        return header

    def _create_model_selector(self) -> QWidget:
        """モデル選択パネルを作成する。"""
        container = QWidget()
        container.setObjectName("modelSelectorContainer")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        # オートモード チェックボックス
        self.auto_mode_checkbox = QCheckBox("自動選択")
        self.auto_mode_checkbox.setChecked(True)
        self.auto_mode_checkbox.stateChanged.connect(self._on_auto_mode_changed)
        self.auto_mode_checkbox.setStyleSheet(
            f"color: {config.COLOR_TEXT}; font-size: {config.FONT_SIZE_SMALL}pt;"
        )
        layout.addWidget(self.auto_mode_checkbox)

        # モデル選択 ComboBox
        self.model_combo = QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self.model_combo.setEnabled(False)  # 初期状態は無効
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)

        # モデルを追加
        for model in self.model_manager.get_enabled_models():
            self.model_combo.addItem(model.name, model.id)

        layout.addWidget(self.model_combo)

        # 現在のモデル情報ラベル
        self.model_info_label = QLabel("モデル: 自動選択")
        self.model_info_label.setStyleSheet(
            f"color: {config.COLOR_TEXT_MUTED}; font-size: {config.FONT_SIZE_SMALL}pt;"
        )
        layout.addWidget(self.model_info_label)
        layout.addStretch()

        return container

    def _create_chat_area(self) -> QScrollArea:
        """チャット表示エリアを作成する。"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("chatScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.chat_container = QWidget()
        self.chat_container.setObjectName("chatContainer")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        return self.scroll_area

    def _create_input_area(self) -> QWidget:
        """テキスト入力エリアを作成する。"""
        container = QWidget()
        container.setObjectName("inputContainer")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        self.input_box = QTextEdit()
        self.input_box.setObjectName("inputBox")
        self.input_box.setPlaceholderText("質問を入力... (Enter で送信)")
        self.input_box.setFixedHeight(72)
        self.input_box.installEventFilter(self)

        send_btn = QPushButton("送信")
        send_btn.setObjectName("sendButton")
        send_btn.setFixedSize(56, 56)
        send_btn.clicked.connect(self._on_send)

        layout.addWidget(self.input_box)
        layout.addWidget(send_btn)
        return container

    def _create_toolbar(self) -> QWidget:
        """ツールバーを作成する。"""
        toolbar = QWidget()
        toolbar.setObjectName("toolbar")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 4, 10, 6)
        layout.setSpacing(8)

        opacity_label = QLabel("透明度:")
        opacity_label.setObjectName("toolbarLabel")

        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setObjectName("opacitySlider")
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(int(config.WINDOW_OPACITY * 100))
        self.opacity_slider.setFixedWidth(80)
        self.opacity_slider.valueChanged.connect(
            lambda v: self.setWindowOpacity(v / 100)
        )

        layout.addWidget(opacity_label)
        layout.addWidget(self.opacity_slider)
        layout.addStretch()

        self.status_label = QLabel("待機中")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        return toolbar

    # ===== スタイルシート =====

    def _apply_stylesheet(self):
        """アプリ全体のスタイルシートを適用する。"""
        self.setStyleSheet(f"""
            QWidget#centralWidget {{
                background-color: {config.COLOR_BG};
                border-radius: 12px;
                border: 1px solid {config.COLOR_BORDER};
            }}
            QWidget#header {{
                background-color: {config.COLOR_HEADER};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid {config.COLOR_BORDER};
            }}
            QLabel#titleLabel {{
                color: {config.COLOR_TEXT};
                font-size: {config.FONT_SIZE_TITLE}pt;
                font-weight: bold;
            }}
            QWidget#modelSelectorContainer {{
                background-color: {config.COLOR_HEADER};
                border-bottom: 1px solid {config.COLOR_BORDER};
            }}
            QComboBox#modelCombo {{
                background-color: {config.COLOR_INPUT_BG};
                color: {config.COLOR_TEXT};
                border: 1px solid {config.COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
                font-size: {config.FONT_SIZE_NORMAL}pt;
            }}
            QComboBox#modelCombo:enabled {{
                border: 1px solid {config.COLOR_ACCENT};
            }}
            QPushButton#iconButton {{
                background-color: transparent;
                color: {config.COLOR_TEXT_MUTED};
                border: none;
                border-radius: 4px;
                font-size: 13px;
            }}
            QPushButton#iconButton:hover {{
                background-color: rgba(255,255,255,0.1);
                color: {config.COLOR_TEXT};
            }}
            QPushButton#closeButton {{
                background-color: transparent;
                color: {config.COLOR_TEXT_MUTED};
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton#closeButton:hover {{
                background-color: #c0392b;
                color: white;
            }}
            QScrollArea#chatScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QWidget#chatContainer {{
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: {config.COLOR_BG};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {config.COLOR_BORDER};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QWidget#inputContainer {{
                background-color: {config.COLOR_HEADER};
                border-top: 1px solid {config.COLOR_BORDER};
            }}
            QTextEdit#inputBox {{
                background-color: {config.COLOR_INPUT_BG};
                color: {config.COLOR_TEXT};
                border: 1px solid {config.COLOR_BORDER};
                border-radius: 8px;
                padding: 6px 8px;
                font-size: {config.FONT_SIZE_NORMAL}pt;
            }}
            QTextEdit#inputBox:focus {{
                border: 1px solid {config.COLOR_ACCENT};
            }}
            QPushButton#sendButton {{
                background-color: {config.COLOR_ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: {config.FONT_SIZE_NORMAL}pt;
                font-weight: bold;
            }}
            QPushButton#sendButton:hover {{
                background-color: #c0392b;
            }}
            QPushButton#sendButton:disabled {{
                background-color: #555;
                color: #888;
            }}
            QWidget#toolbar {{
                background-color: {config.COLOR_HEADER};
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top: 1px solid {config.COLOR_BORDER};
            }}
            QLabel#toolbarLabel {{
                color: {config.COLOR_TEXT_MUTED};
                font-size: {config.FONT_SIZE_SMALL}pt;
            }}
            QLabel#statusLabel {{
                color: {config.COLOR_TEXT_MUTED};
                font-size: {config.FONT_SIZE_SMALL}pt;
            }}
            QSlider#opacitySlider::groove:horizontal {{
                background: {config.COLOR_BORDER};
                height: 4px;
                border-radius: 2px;
            }}
            QSlider#opacitySlider::handle:horizontal {{
                background: {config.COLOR_ACCENT};
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }}
            QWidget#loadingContainer {{
                background-color: transparent;
            }}
        """)

    # ===== ホットキー =====

    def _setup_hotkey(self):
        """グローバルホットキーを設定する。"""
        try:
            import keyboard
            keyboard.add_hotkey(
                config.HOTKEY_TOGGLE,
                self._toggle_visibility,
                suppress=False,
            )
            logger.info("ホットキー設定完了: %s", config.HOTKEY_TOGGLE)
        except ImportError:
            logger.warning("keyboard ライブラリが見つかりません")
        except Exception as e:
            logger.warning("ホットキー設定失敗: %s", e)

    def _toggle_visibility(self):
        """ウィンドウの表示/非表示を切り替える。"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()

    # ===== イベントハンドラ =====

    def eventFilter(self, obj, event):
        """入力ボックスのキーイベントを処理する。"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent

        if obj is self.input_box and event.type() == QEvent.Type.KeyPress:
            key_event: QKeyEvent = event
            if (
                key_event.key() == Qt.Key.Key_Return
                and not (key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            ):
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        """ドラッグ開始位置を記録する。"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """ドラッグ移動を処理する。"""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        """ドラッグ終了。"""
        self._drag_pos = None

    # ===== モデル選択 =====

    @pyqtSlot(int)
    def _on_auto_mode_changed(self, state):
        """オートモード切り替え。"""
        self._auto_mode = self.auto_mode_checkbox.isChecked()
        self.model_combo.setEnabled(not self._auto_mode)
        if self._auto_mode:
            self.model_info_label.setText("モデル: 自動選択")
        logger.info("オートモード: %s", self._auto_mode)

    @pyqtSlot(int)
    def _on_model_changed(self, index):
        """手動モデル選択。"""
        if not self._auto_mode and index >= 0:
            model_id = self.model_combo.currentData()
            self._current_model_id = model_id
            model = self.model_manager.get_model(model_id)
            if model:
                self.model_info_label.setText(f"モデル: {model.name}")
                logger.info("モデルを選択: %s", model_id)

    # ===== 送信処理 =====

    @pyqtSlot()
    def _on_send(self):
        """送信ボタン / Enterキー押下時の処理。"""
        if self._is_processing:
            return

        text = self.input_box.toPlainText().strip()
        if not text:
            return

        self._last_query = text  # 後でキャッシュに保存するため記録
        self.input_box.clear()
        self._start_processing(text)

    def _start_processing(self, user_text: str):
        """処理を開始する。"""
        self._is_processing = True
        self._set_ui_enabled(False)
        self._update_status("キャッシュを確認中...")

        self._add_message_bubble(user_text, "user")

        # キャッシュを確認
        cached_response = self.cache_manager.get(user_text, self._current_model_id or "auto")
        if cached_response:
            self._add_message_bubble(cached_response, "assistant")
            self._add_system_message("💾 キャッシュから取得しました")
            self.analytics_collector.record_cache_hit(user_text, self._current_model_id or "auto")
            self._is_processing = False
            self._set_ui_enabled(True)
            self._update_status("待機中")
            return

        self.hide()
        QTimer.singleShot(150, lambda: self._do_capture_and_send(user_text))

    def _do_capture_and_send(self, user_text: str):
        """キャプチャを実行してAIワーカーを起動する。"""
        image_b64 = capture_screen()
        if image_b64 is None:
            logger.warning("スクリーンキャプチャに失敗")
            self._update_status("キャプチャ失敗（テキストのみ）")

        self.show()
        self.raise_()

        # モデルを選択
        if self._auto_mode:
            analysis = self.auto_switcher.analyze_request(user_text, bool(image_b64))
            model_id = self.auto_switcher.select_model_auto(analysis, strategy="balanced")
            if model_id:
                model = self.model_manager.get_model(model_id)
                self.model_info_label.setText(f"モデル: {model.name} (自動)")
                self._current_model_id = model_id
                # モデル選択をログに記録
                self.analytics_collector.record_model_selection(
                    query=user_text,
                    selected_model_id=model_id,
                    candidate_models=[m.id for m in self.model_manager.get_enabled_models()],
                    selection_reason=f"{analysis.complexity.value} / {analysis.purpose.value}",
                    is_auto=True,
                )
        else:
            model_id = self._current_model_id
            if model_id:
                # 手動選択をログに記録
                self.analytics_collector.record_model_selection(
                    query=user_text,
                    selected_model_id=model_id,
                    candidate_models=[m.id for m in self.model_manager.get_enabled_models()],
                    selection_reason="manual_selection",
                    is_auto=False,
                )

        if not model_id:
            self._add_system_message("⚠️ 利用可能なモデルが見つかりません")
            self._is_processing = False
            self._set_ui_enabled(True)
            return

        self.loading_indicator.start()
        self._current_ai_bubble = self._add_message_bubble("", "assistant")

        # AIワーカーを起動
        self._ai_worker = AIWorker(
            user_message=user_text,
            image_base64=image_b64,
            history=self.history.get_messages(),
            model_id=model_id,
            model_manager=self.model_manager,
        )
        self._ai_worker.token_received.connect(self._on_token_received)
        self._ai_worker.response_complete.connect(self._on_response_complete)
        self._ai_worker.error_occurred.connect(self._on_error)
        self._ai_worker.start()

        self.history.add_user(user_text, image_b64)

    # ===== AIワーカーシグナルハンドラ =====

    @pyqtSlot(str)
    def _on_token_received(self, token: str):
        """ストリーミングトークンを受信。"""
        if self._current_ai_bubble:
            self._current_ai_bubble.append_text(token)
            self._scroll_to_bottom()

    @pyqtSlot(str)
    def _on_response_complete(self, full_text: str):
        """AIの回答が完了。"""
        self.loading_indicator.stop()
        self._is_processing = False
        self._set_ui_enabled(True)
        self._update_status("待機中")

        if full_text:
            self.history.add_assistant(full_text)
            # キャッシュに保存
            if hasattr(self, '_last_query'):
                self.cache_manager.set(
                    query=self._last_query,
                    response=full_text,
                    model_id=self._current_model_id or "auto",
                    ttl_seconds=86400,  # 24時間
                )
            # 履歴を管理（必要に応じて圧縮）
            messages = self.history.get_messages()
            original_count = len(messages)
            managed_messages = self.history_manager.manage_history(
                messages,
                config.SYSTEM_PROMPT,
            )
            if len(managed_messages) < original_count:
                logger.info("履歴を圧縮しました")
                # 圧縮をログに記録
                self.analytics_collector.record_history_compression(
                    original_count=original_count,
                    compressed_count=len(managed_messages),
                    compression_ratio=len(managed_messages) / original_count,
                )

        self._current_ai_bubble = None
        self._scroll_to_bottom()
        self.input_box.setFocus()

    @pyqtSlot(str)
    def _on_error(self, error_msg: str):
        """エラー発生。"""
        self.loading_indicator.stop()
        self._is_processing = False
        self._set_ui_enabled(True)
        self._update_status("エラー")

        if self._current_ai_bubble:
            self._current_ai_bubble.append_text(f"\n\n⚠️ エラー: {error_msg}")
        else:
            self._add_system_message(f"⚠️ エラー: {error_msg}")

        self._current_ai_bubble = None
        self._scroll_to_bottom()

    # ===== UI操作ヘルパー =====

    def _add_message_bubble(self, text: str, role: str) -> MessageBubble:
        """チャットエリアにメッセージバブルを追加。"""
        bubble = MessageBubble(text, role)
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, bubble)
        self._scroll_to_bottom()
        return bubble

    def _add_system_message(self, text: str):
        """システムメッセージを追加。"""
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            f"color: {config.COLOR_TEXT_MUTED}; font-size: {config.FONT_SIZE_SMALL}pt;"
            " padding: 8px; background-color: transparent;"
        )
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, label)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        """チャットエリアを最下部にスクロール。"""
        QTimer.singleShot(50, lambda: (
            self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        ))

    def _set_ui_enabled(self, enabled: bool):
        """入力UIの有効/無効を切り替え。"""
        self.input_box.setEnabled(enabled)
        for widget in self.findChildren(QPushButton, "sendButton"):
            widget.setEnabled(enabled)

    def _update_status(self, text: str):
        """ステータスラベルを更新。"""
        self.status_label.setText(text)

    # ===== メニューアクション =====

    def _on_new_conversation(self):
        """会話をリセット。"""
        self.history.clear()
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._add_system_message("会話をリセットしました。")

    def _on_save_history(self):
        """会話履歴を保存。"""
        os.makedirs(config.HISTORY_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(config.HISTORY_DIR, f"history_{timestamp}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self.history.to_json())
            self._add_system_message(f"履歴を保存: {filepath}")
            logger.info("履歴保存: %s", filepath)
        except Exception as e:
            self._add_system_message(f"保存失敗: {e}")
            logger.error("履歴保存失敗: %s", e)

    def _on_show_stats(self):
        """統計情報ダイアログを表示。"""
        dialog = ModelStatsDialog(self.model_manager, self)
        dialog.exec()

    def _on_close(self):
        """アプリケーションを終了。"""
        if self._ai_worker and self._ai_worker.isRunning():
            self._ai_worker.cancel()
            self._ai_worker.wait(2000)
        logger.info("データを保存中...")
        self.model_manager.save_config()
        self.auto_switcher.save_decision_log()
        logger.info("ScreenMind を終了します")
        QApplication.quit()


# ===== エントリポイント =====

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("ScreenMind v2.0")
    app.setApplicationVersion("2.0.0")

    font = QFont()
    font.setFamilies(config.FONT_FAMILY.split(", "))
    font.setPointSize(config.FONT_SIZE_NORMAL)
    app.setFont(font)

    window = ScreenMindWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
