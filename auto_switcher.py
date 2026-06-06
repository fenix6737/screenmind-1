"""
ScreenMind - 自動モデル切り替えモジュール
リクエスト内容を分析して最適なモデルを自動選択する。
"""

import json
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from model_config import ModelType
from model_manager import ModelManager

logger = logging.getLogger(__name__)


class RequestComplexity(Enum):
    """リクエストの複雑度を定義する列挙型。"""
    SIMPLE = "simple"          # 簡単な質問・雑談
    MODERATE = "moderate"      # 通常の質問・分析
    COMPLEX = "complex"        # 複雑な分析・思考
    VERY_COMPLEX = "very_complex"  # 非常に複雑な処理


class RequestPurpose(Enum):
    """リクエストの目的を定義する列挙型。"""
    CONVERSATION = "conversation"  # 会話・雑談
    ANALYSIS = "analysis"          # データ分析・思考
    CODING = "coding"              # コード生成・デバッグ
    VISION = "vision"              # 画像解析
    GENERAL = "general"            # その他


class RequestAnalysis:
    """リクエストの分析結果を表すクラス。"""

    def __init__(
        self,
        text: str,
        has_image: bool = False,
        complexity: RequestComplexity = RequestComplexity.MODERATE,
        purpose: RequestPurpose = RequestPurpose.GENERAL,
    ):
        self.text = text
        self.has_image = has_image
        self.complexity = complexity
        self.purpose = purpose
        self.analyzed_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """辞書に変換する。"""
        return {
            "text_length": len(self.text),
            "has_image": self.has_image,
            "complexity": self.complexity.value,
            "purpose": self.purpose.value,
            "analyzed_at": self.analyzed_at,
        }


class AutoSwitcher:
    """
    リクエスト内容を分析して最適なモデルを自動選択するクラス。
    """

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.decision_log: List[Dict] = []
        self._setup_keyword_patterns()

    def _setup_keyword_patterns(self):
        """キーワードパターンを設定する。"""
        # コード関連キーワード
        self.coding_keywords = re.compile(
            r"\b(code|python|javascript|java|c\+\+|debug|function|class|"
            r"algorithm|api|database|sql|html|css|react|vue|node|npm|"
            r"git|docker|kubernetes|bug|fix|refactor|optimize)\b",
            re.IGNORECASE,
        )

        # 分析関連キーワード
        self.analysis_keywords = re.compile(
            r"\b(analyze|analysis|data|statistics|graph|chart|trend|"
            r"compare|evaluate|research|study|report|summary|insight|"
            r"pattern|correlation|hypothesis|theory|explain|why|how)\b",
            re.IGNORECASE,
        )

        # 画像関連キーワード
        self.vision_keywords = re.compile(
            r"\b(image|picture|photo|screenshot|diagram|chart|graph|"
            r"visual|see|look|show|display|describe|recognize|detect|"
            r"identify|analyze.*image|what.*in|what.*see)\b",
            re.IGNORECASE,
        )

    def analyze_request(
        self,
        text: str,
        has_image: bool = False,
    ) -> RequestAnalysis:
        """
        リクエストを分析して複雑度と目的を判定する。
        """
        # 画像がある場合は画像解析
        if has_image:
            purpose = RequestPurpose.VISION
            complexity = self._estimate_complexity(text)
            return RequestAnalysis(text, has_image, complexity, purpose)

        # キーワードマッチングで目的を判定
        if self.coding_keywords.search(text):
            purpose = RequestPurpose.CODING
        elif self.analysis_keywords.search(text):
            purpose = RequestPurpose.ANALYSIS
        elif self.vision_keywords.search(text):
            purpose = RequestPurpose.VISION
        else:
            purpose = RequestPurpose.CONVERSATION

        # 複雑度を推定
        complexity = self._estimate_complexity(text)

        return RequestAnalysis(text, has_image, complexity, purpose)

    def _estimate_complexity(self, text: str) -> RequestComplexity:
        """
        テキストの複雑度を推定する。
        テキスト長・句読点・キーワードなどから判定。
        """
        # テキスト長
        text_length = len(text)

        # 複雑な句読点の数
        complex_punctuation = text.count("?") + text.count(";") + text.count(":")
        complex_punctuation += text.count("(") + text.count("[") + text.count("{")

        # スコアを計算
        score = 0
        score += text_length // 50  # 50文字ごとに1ポイント
        score += complex_punctuation * 2

        # 複雑度を判定
        if score < 5:
            return RequestComplexity.SIMPLE
        elif score < 15:
            return RequestComplexity.MODERATE
        elif score < 30:
            return RequestComplexity.COMPLEX
        else:
            return RequestComplexity.VERY_COMPLEX

    def select_model_auto(
        self,
        analysis: RequestAnalysis,
        strategy: str = "balanced",
    ) -> Optional[str]:
        """
        分析結果に基づいて最適なモデルを自動選択する。

        Args:
            analysis: リクエスト分析結果
            strategy: 選択戦略
                - "balanced": バランス重視（優先度 + 成功率）
                - "fast": 速度重視
                - "accurate": 精度重視（複雑度に応じて選択）

        Returns:
            選択されたモデルのID、見つからない場合はNone
        """
        # 画像解析が必要な場合
        if analysis.has_image:
            models = self.model_manager.config_manager.get_multimodal_models()
            if not models:
                logger.warning("マルチモーダル対応モデルが見つかりません")
                return None
            selected = max(models, key=lambda m: m.priority)
            self._log_decision(analysis, selected.id, "multimodal_required")
            return selected.id

        # 目的別にモデルタイプを決定
        purpose_to_type = {
            RequestPurpose.CONVERSATION: ModelType.CONVERSATION,
            RequestPurpose.CODING: ModelType.CODING,
            RequestPurpose.ANALYSIS: ModelType.ANALYSIS,
            RequestPurpose.VISION: ModelType.VISION,
            RequestPurpose.GENERAL: ModelType.CONVERSATION,
        }

        model_type = purpose_to_type.get(analysis.purpose, ModelType.CONVERSATION)

        # 複雑度に応じてモデルを選択
        if strategy == "fast":
            # 高速応答を優先
            if analysis.complexity in (RequestComplexity.SIMPLE, RequestComplexity.MODERATE):
                model = self.model_manager.get_fastest_healthy_model()
                if model:
                    self._log_decision(analysis, model.id, "fast_strategy")
                    return model.id

        elif strategy == "accurate":
            # 複雑度に応じて選択
            if analysis.complexity == RequestComplexity.VERY_COMPLEX:
                # 最高性能モデルを選択
                candidates = [
                    m for m in self.model_manager.get_enabled_models()
                    if m.model_type == model_type
                ]
                if candidates:
                    selected = max(candidates, key=lambda m: m.priority)
                    self._log_decision(analysis, selected.id, "accurate_strategy_complex")
                    return selected.id

        # デフォルト: バランス戦略
        model = self.model_manager.get_best_model_for_type(model_type)
        if model:
            self._log_decision(analysis, model.id, "balanced_strategy")
            return model.id

        # フォールバック: 最速モデル
        model = self.model_manager.get_fastest_healthy_model()
        if model:
            self._log_decision(analysis, model.id, "fallback_fastest")
            return model.id

        logger.warning("利用可能なモデルが見つかりません")
        return None

    def select_model_manual(self, model_id: str) -> bool:
        """
        ユーザーが手動でモデルを選択する。
        """
        model = self.model_manager.get_model(model_id)
        if not model or not model.is_enabled:
            logger.warning("モデル %s は利用できません", model_id)
            return False
        logger.info("手動選択: %s", model_id)
        return True

    def _log_decision(
        self,
        analysis: RequestAnalysis,
        selected_model_id: str,
        reason: str,
    ):
        """意思決定をログに記録する。"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis.to_dict(),
            "selected_model": selected_model_id,
            "reason": reason,
        }
        self.decision_log.append(log_entry)
        logger.debug("モデル選択: %s (理由: %s)", selected_model_id, reason)

    def get_decision_log(self, limit: int = 100) -> List[Dict]:
        """意思決定ログを取得する。"""
        return self.decision_log[-limit:]

    def save_decision_log(self, filepath: str = "decision_log.json") -> bool:
        """意思決定ログをJSONファイルに保存する。"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.decision_log, f, ensure_ascii=False, indent=2)
            logger.info("意思決定ログを保存: %s", filepath)
            return True
        except Exception as e:
            logger.error("意思決定ログの保存に失敗: %s", e)
            return False


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== 自動モデル切り替えのテスト ===\n")

    manager = ModelManager()
    switcher = AutoSwitcher(manager)

    # テストケース
    test_cases = [
        ("こんにちは。今日の天気はどう？", False, "会話"),
        ("Pythonで素数判定関数を書いてください", False, "コード"),
        ("このデータセットから傾向を分析してください。\n"
         "2024年1月: 100\n2024年2月: 150\n2024年3月: 120\n"
         "グラフを作成し、パターンを説明してください。", False, "分析"),
        ("このスクリーンショットに何が写っていますか？", True, "画像解析"),
    ]

    print("=== リクエスト分析と自動モデル選択 ===\n")
    for text, has_image, description in test_cases:
        print(f"📝 {description}")
        print(f"   テキスト: {text[:50]}...")
        print(f"   画像: {'あり' if has_image else 'なし'}")

        # 分析
        analysis = switcher.analyze_request(text, has_image)
        print(f"   複雑度: {analysis.complexity.value}")
        print(f"   目的: {analysis.purpose.value}")

        # 自動選択
        selected_id = switcher.select_model_auto(analysis, strategy="balanced")
        if selected_id:
            model = manager.get_model(selected_id)
            print(f"   選択モデル: {model.name} ({model.id})")
        else:
            print(f"   選択モデル: なし")

        print()

    # 意思決定ログを表示
    print("=== 意思決定ログ ===")
    for i, log in enumerate(switcher.get_decision_log(), 1):
        print(f"{i}. {log['selected_model']} (理由: {log['reason']})")
