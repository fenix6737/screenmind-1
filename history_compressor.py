"""
ScreenMind - 会話履歴圧縮モジュール
長い会話履歴をサマリーに圧縮して、コンテキストウィンドウを効率的に利用する。
"""

import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class HistorySummary:
    """会話履歴のサマリーを表すクラス。"""

    def __init__(
        self,
        original_message_count: int,
        summary_text: str,
        key_topics: List[str],
        compression_ratio: float,
    ):
        self.original_message_count = original_message_count
        self.summary_text = summary_text
        self.key_topics = key_topics
        self.compression_ratio = compression_ratio
        self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """辞書に変換する。"""
        return {
            "original_message_count": self.original_message_count,
            "summary_text": self.summary_text,
            "key_topics": self.key_topics,
            "compression_ratio": self.compression_ratio,
            "created_at": self.created_at,
        }


class HistoryCompressor:
    """
    会話履歴を圧縮・要約するクラス。
    トークン数を削減しながら、重要な情報を保持する。
    """

    def __init__(self, max_history_messages: int = 20):
        self.max_history_messages = max_history_messages
        self._compression_log: List[HistorySummary] = []

    def should_compress(self, messages: List[Dict]) -> bool:
        """
        履歴を圧縮すべきかどうかを判定する。
        """
        return len(messages) > self.max_history_messages

    def compress(
        self,
        messages: List[Dict],
        target_ratio: float = 0.5,
    ) -> Tuple[List[Dict], Optional[HistorySummary]]:
        """
        会話履歴を圧縮する。
        古いメッセージをサマリーに置き換える。

        Args:
            messages: 元の会話履歴
            target_ratio: 圧縮目標比率（0.5 = 50%に圧縮）

        Returns:
            (圧縮後のメッセージ, サマリー情報)
        """
        if not self.should_compress(messages):
            return messages, None

        # システムプロンプトと最新メッセージを保持
        system_messages = [m for m in messages if m.get("role") == "system"]
        other_messages = [m for m in messages if m.get("role") != "system"]

        # 圧縮対象のメッセージ数を計算
        num_to_compress = int(len(other_messages) * (1 - target_ratio))
        num_to_compress = max(2, num_to_compress)  # 最低2つは圧縮

        messages_to_compress = other_messages[:num_to_compress]
        messages_to_keep = other_messages[num_to_compress:]

        # サマリーを生成
        summary = self._generate_summary(messages_to_compress)

        # 圧縮後のメッセージを構築
        compressed_messages = system_messages.copy()
        if summary:
            compressed_messages.append({
                "role": "system",
                "content": f"[会話履歴サマリー]\n{summary.summary_text}",
            })
        compressed_messages.extend(messages_to_keep)

        logger.info(
            "履歴を圧縮: %d → %d メッセージ (圧縮率: %.1f%%)",
            len(messages),
            len(compressed_messages),
            (1 - len(compressed_messages) / len(messages)) * 100,
        )

        self._compression_log.append(summary)
        return compressed_messages, summary

    def _generate_summary(
        self,
        messages: List[Dict],
    ) -> Optional[HistorySummary]:
        """
        メッセージのサマリーを生成する。
        """
        if not messages:
            return None

        # トピック抽出
        key_topics = self._extract_topics(messages)

        # サマリーテキスト生成
        summary_parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # コンテンツが複合型の場合は処理
            if isinstance(content, list):
                text_parts = [
                    item.get("text", "") for item in content
                    if item.get("type") == "text"
                ]
                content = " ".join(text_parts)

            # 長すぎる場合は短縮
            if len(content) > 200:
                content = content[:200] + "..."

            summary_parts.append(f"- {role}: {content}")

        summary_text = "\n".join(summary_parts)

        # 圧縮率を計算
        original_tokens = sum(
            len(msg.get("content", "").split())
            for msg in messages
        )
        summary_tokens = len(summary_text.split())
        compression_ratio = summary_tokens / max(original_tokens, 1)

        return HistorySummary(
            original_message_count=len(messages),
            summary_text=summary_text,
            key_topics=key_topics,
            compression_ratio=compression_ratio,
        )

    def _extract_topics(self, messages: List[Dict]) -> List[str]:
        """
        メッセージから主要なトピックを抽出する。
        """
        topics = set()

        # キーワードパターン
        keyword_patterns = {
            "プログラミング": r"\b(python|javascript|code|function|class|api)\b",
            "データ分析": r"\b(data|analysis|graph|chart|statistics|trend)\b",
            "デザイン": r"\b(design|ui|ux|color|layout|font)\b",
            "セキュリティ": r"\b(security|password|encrypt|auth|token)\b",
            "クラウド": r"\b(cloud|aws|azure|gcp|docker|kubernetes)\b",
            "AI/ML": r"\b(ai|machine learning|model|neural|training|prediction)\b",
        }

        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = [
                    item.get("text", "") for item in content
                    if item.get("type") == "text"
                ]
                content = " ".join(text_parts)

            content_lower = content.lower()

            for topic, pattern in keyword_patterns.items():
                if re.search(pattern, content_lower):
                    topics.add(topic)

        return list(topics)

    def decompress(self, summary: HistorySummary) -> str:
        """
        サマリーから元の情報を復元する（表示用）。
        """
        return (
            f"📋 会話履歴サマリー\n"
            f"元のメッセージ数: {summary.original_message_count}\n"
            f"圧縮率: {summary.compression_ratio:.1%}\n"
            f"主要トピック: {', '.join(summary.key_topics)}\n\n"
            f"{summary.summary_text}"
        )

    def get_compression_log(self) -> List[Dict]:
        """圧縮ログを取得する。"""
        return [s.to_dict() for s in self._compression_log]

    def get_compression_statistics(self) -> Dict:
        """圧縮統計を取得する。"""
        if not self._compression_log:
            return {
                "total_compressions": 0,
                "avg_compression_ratio": 0.0,
                "total_messages_compressed": 0,
            }

        total_messages = sum(s.original_message_count for s in self._compression_log)
        avg_ratio = sum(s.compression_ratio for s in self._compression_log) / len(
            self._compression_log
        )

        return {
            "total_compressions": len(self._compression_log),
            "avg_compression_ratio": avg_ratio,
            "total_messages_compressed": total_messages,
        }


class AdaptiveHistoryManager:
    """
    適応的に履歴を管理するマネージャー。
    モデルのコンテキストウィンドウサイズに応じて自動調整する。
    """

    def __init__(self, context_window_tokens: int = 4096):
        self.context_window_tokens = context_window_tokens
        self.compressor = HistoryCompressor()
        self._reserved_tokens = 500  # 回答用に予約

    def manage_history(
        self,
        messages: List[Dict],
        system_prompt: str,
    ) -> List[Dict]:
        """
        メッセージ履歴を管理し、コンテキストウィンドウに収まるように調整する。
        """
        # 現在のトークン数を推定
        estimated_tokens = self._estimate_tokens(messages, system_prompt)
        available_tokens = self.context_window_tokens - self._reserved_tokens

        if estimated_tokens > available_tokens:
            logger.warning(
                "トークン数が上限を超えています: %d / %d",
                estimated_tokens,
                available_tokens,
            )

            # 圧縮を実行
            target_ratio = available_tokens / estimated_tokens
            target_ratio = min(target_ratio, 0.7)  # 最大70%に圧縮
            messages, summary = self.compressor.compress(messages, target_ratio)

            if summary:
                logger.info("履歴を圧縮しました (圧縮率: %.1f%%)", summary.compression_ratio)

        return messages

    def _estimate_tokens(self, messages: List[Dict], system_prompt: str) -> int:
        """
        メッセージのトークン数を推定する（簡易版）。
        実際のトークンカウントではなく、単語数で推定。
        """
        total_words = len(system_prompt.split())

        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                text_parts = [
                    item.get("text", "") for item in content
                    if item.get("type") == "text"
                ]
                content = " ".join(text_parts)
            total_words += len(str(content).split())

        # 単語数をトークン数に変換（1単語 ≈ 1.3トークン）
        return int(total_words * 1.3)


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== 履歴圧縮のテスト ===\n")

    compressor = HistoryCompressor(max_history_messages=5)

    # テスト用メッセージを生成
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
    ]
    for i in range(10):
        messages.append({
            "role": "user",
            "content": f"Pythonについて教えてください。質問{i+1}",
        })
        messages.append({
            "role": "assistant",
            "content": f"Pythonは高水準プログラミング言語です。回答{i+1}",
        })

    print(f"元のメッセージ数: {len(messages)}\n")

    # 圧縮
    compressed, summary = compressor.compress(messages, target_ratio=0.5)

    print(f"圧縮後のメッセージ数: {len(compressed)}\n")

    if summary:
        print("📊 圧縮情報:")
        print(f"  元のメッセージ数: {summary.original_message_count}")
        print(f"  圧縮率: {summary.compression_ratio:.1%}")
        print(f"  主要トピック: {', '.join(summary.key_topics)}\n")

    # 統計
    stats = compressor.get_compression_statistics()
    print("📈 統計:")
    print(f"  総圧縮回数: {stats['total_compressions']}")
    print(f"  平均圧縮率: {stats['avg_compression_ratio']:.1%}")
