"""
ScreenMind - AIクライアントモジュール
llama.cpp（OpenAI互換API）との通信を担当する。
QThreadを継承したワーカークラスでUIをブロックせずに推論を実行する。
"""

import json
import logging
import time
from typing import List, Dict, Optional

import httpx
from PyQt6.QtCore import QThread, pyqtSignal

import config

logger = logging.getLogger(__name__)


class AIWorker(QThread):
    """
    llama.cppへのリクエストをバックグラウンドスレッドで実行するワーカー。

    Signals:
        token_received(str): ストリーミングトークンを受信するたびに発火
        response_complete(str): 完全なレスポンスが揃ったときに発火
        error_occurred(str): エラー発生時に発火
    """

    token_received = pyqtSignal(str)
    response_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        user_message: str,
        image_base64: Optional[str],
        history: List[Dict],
        model_id: Optional[str] = None,
        model_manager = None,
        parent=None,
    ):
        super().__init__(parent)
        self.user_message = user_message
        self.image_base64 = image_base64
        self.history = history
        self.model_id = model_id
        self.model_manager = model_manager
        self._is_cancelled = False
        self._start_time = 0.0

    def cancel(self):
        """リクエストをキャンセルする。"""
        self._is_cancelled = True

    def run(self):
        """スレッド実行エントリポイント。"""
        self._start_time = time.time()
        try:
            messages = self._build_messages()
            payload = self._build_payload(messages)
            self._send_request(payload)
        except Exception as e:
            logger.error("AIWorker実行エラー: %s", e, exc_info=True)
            if not self._is_cancelled:
                self.error_occurred.emit(f"予期しないエラーが発生しました: {e}")

    def _build_messages(self) -> List[Dict]:
        """
        llama.cpp送信用のメッセージリストを構築する。
        システムプロンプト + 会話履歴 + 今回のユーザーメッセージ。
        """
        messages = [
            {"role": "system", "content": config.SYSTEM_PROMPT}
        ]

        # 直近N件の会話履歴を追加
        recent_history = self.history[-config.MAX_HISTORY:]
        messages.extend(recent_history)

        # 今回のユーザーメッセージ（画像付き or テキストのみ）
        if self.image_base64:
            user_content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{self.image_base64}"
                    },
                },
                {
                    "type": "text",
                    "text": self.user_message,
                },
            ]
        else:
            user_content = self.user_message

        messages.append({"role": "user", "content": user_content})
        return messages

    def _build_payload(self, messages: List[Dict]) -> Dict:
        """APIリクエストのペイロードを構築する。"""
        # model_id が指定されている場合はそれを使用
        model_name = config.MODEL_NAME
        max_tokens = config.MAX_TOKENS
        temperature = config.TEMPERATURE

        if self.model_id and self.model_manager:
            model = self.model_manager.get_model(self.model_id)
            if model:
                model_name = model.model_name
                max_tokens = model.max_tokens
                temperature = model.temperature

        return {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

    def _send_request(self, payload: Dict):
        """
        llama.cppにHTTPリクエストを送信し、ストリーミングレスポンスを処理する。
        """
        full_response = []

        try:
            with httpx.Client(timeout=config.REQUEST_TIMEOUT) as client:
                with client.stream(
                    "POST",
                    config.LLAMA_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status_code != 200:
                        error_body = response.read().decode("utf-8", errors="replace")
                        raise RuntimeError(
                            f"HTTPエラー {response.status_code}: {error_body[:200]}"
                        )

                    for line in response.iter_lines():
                        if self._is_cancelled:
                            logger.info("リクエストがキャンセルされました")
                            return

                        line = line.strip()
                        if not line or line == "data: [DONE]":
                            continue
                        if line.startswith("data: "):
                            line = line[6:]

                        try:
                            chunk = json.loads(line)
                            delta = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if delta:
                                full_response.append(delta)
                                self.token_received.emit(delta)
                        except json.JSONDecodeError:
                            logger.debug("JSON解析スキップ: %s", line[:100])

        except httpx.ConnectError:
            msg = (
                "llama.cppサーバーに接続できません。\n"
                f"サーバーが {config.LLAMA_URL} で起動しているか確認してください。"
            )
            logger.error(msg)
            if not self._is_cancelled:
                self.error_occurred.emit(msg)
            return

        except httpx.TimeoutException:
            msg = (
                f"リクエストがタイムアウトしました（{config.REQUEST_TIMEOUT}秒）。\n"
                "モデルの処理に時間がかかっています。"
            )
            logger.error(msg)
            if not self._is_cancelled:
                self.error_occurred.emit(msg)
            return

        except RuntimeError as e:
            if not self._is_cancelled:
                self.error_occurred.emit(str(e))
            return

        if not self._is_cancelled:
            complete_text = "".join(full_response)
            # メトリクスを記録
            if self.model_id and self.model_manager:
                elapsed_ms = (time.time() - self._start_time) * 1000
                self.model_manager.record_request(
                    self.model_id,
                    success=True,
                    response_time_ms=elapsed_ms,
                    tokens=len(complete_text.split()),
                )
            self.response_complete.emit(complete_text)


class ConversationHistory:
    """
    会話履歴を管理するクラス。
    最大N件のメッセージを保持し、古いものから削除する。
    """

    def __init__(self, max_messages: int = config.MAX_HISTORY):
        self.max_messages = max_messages
        self._messages: List[Dict] = []

    def add_user(self, text: str, image_base64: Optional[str] = None):
        """ユーザーメッセージを履歴に追加する。"""
        if image_base64:
            content = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                },
                {"type": "text", "text": text},
            ]
        else:
            content = text
        self._messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant(self, text: str):
        """アシスタントメッセージを履歴に追加する。"""
        self._messages.append({"role": "assistant", "content": text})
        self._trim()

    def get_messages(self) -> List[Dict]:
        """現在の履歴メッセージリストを返す（コピー）。"""
        return list(self._messages)

    def clear(self):
        """履歴をクリアする。"""
        self._messages.clear()

    def _trim(self):
        """最大件数を超えた古いメッセージを削除する。"""
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]

    def __len__(self) -> int:
        return len(self._messages)

    def to_json(self) -> str:
        """履歴をJSON文字列に変換する（保存用）。"""
        return json.dumps(self._messages, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ConversationHistory":
        """JSON文字列から履歴を復元する。"""
        instance = cls()
        try:
            instance._messages = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error("履歴のJSON解析失敗: %s", e)
        return instance


# ===== 単体テスト =====
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)

    print("llama.cppへのテスト接続を開始します...")
    print(f"接続先: {config.LLAMA_URL}")

    history = ConversationHistory()
    worker = AIWorker(
        user_message="こんにちは。簡単な自己紹介をしてください。",
        image_base64=None,
        history=history.get_messages(),
    )

    def on_token(token):
        print(token, end="", flush=True)

    def on_complete(text):
        print(f"\n\n完了: {len(text)}文字")
        app.quit()

    def on_error(msg):
        print(f"\nエラー: {msg}")
        app.quit()

    worker.token_received.connect(on_token)
    worker.response_complete.connect(on_complete)
    worker.error_occurred.connect(on_error)
    worker.start()

    sys.exit(app.exec())
