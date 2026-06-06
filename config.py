"""
ScreenMind - 設定管理モジュール
全設定値を一元管理する
"""

# ===== llama.cpp サーバー設定 =====
LLAMA_URL = "http://localhost:8080/v1/chat/completions"
MODEL_NAME = "gemma-4-12b-iq4_xs"  # llama.cppに読み込まれているモデル名

# ===== AI推論設定 =====
MAX_TOKENS = 1024
TEMPERATURE = 0.7
MAX_HISTORY = 6          # 保持する会話履歴の最大メッセージ数（ペア数ではなくメッセージ数）
REQUEST_TIMEOUT = 120.0  # HTTPリクエストタイムアウト（秒）

# ===== 画面キャプチャ設定 =====
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720
CAPTURE_QUALITY = 85     # JPEG品質（1-95）

# ===== ウィンドウ設定 =====
WINDOW_WIDTH = 380
WINDOW_HEIGHT = 520
WINDOW_OPACITY = 0.93    # ウィンドウ透明度（0.0〜1.0）
WINDOW_MIN_WIDTH = 300
WINDOW_MIN_HEIGHT = 400

# ===== UIカラー設定 =====
COLOR_BG = "#1a1a2e"
COLOR_HEADER = "#16213e"
COLOR_USER_BUBBLE = "#0f3460"
COLOR_AI_BUBBLE = "#1e2a3a"
COLOR_INPUT_BG = "#0d1117"
COLOR_ACCENT = "#e94560"
COLOR_TEXT = "#e0e0e0"
COLOR_TEXT_MUTED = "#888888"
COLOR_BORDER = "#2a2a4a"

# ===== フォント設定 =====
FONT_FAMILY = "Yu Gothic UI, Meiryo, Segoe UI, Arial"
FONT_SIZE_NORMAL = 10
FONT_SIZE_SMALL = 9
FONT_SIZE_TITLE = 11

# ===== ホットキー設定 =====
HOTKEY_TOGGLE = "ctrl+shift+space"

# ===== 会話履歴保存設定 =====
HISTORY_DIR = "history"
HISTORY_MAX_FILES = 30   # 保存する履歴ファイルの最大数

# ===== システムプロンプト =====
SYSTEM_PROMPT = (
    "あなたはScreenMindというAIアシスタントです。"
    "ユーザーのPC画面のスクリーンショットを解析し、"
    "作業内容を理解した上で的確なサポートを提供します。"
    "回答は簡潔かつ実用的にしてください。"
    "日本語で回答してください。"
)
