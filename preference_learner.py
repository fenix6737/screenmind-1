"""
ScreenMind - ユーザー好み学習エンジン
ユーザーの行動パターンから最適な設定を学習・推奨する。
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LearningSession:
    """学習セッション。"""
    session_id: str
    start_time: str
    end_time: Optional[str] = None
    queries: List[str] = None
    preferred_models: List[str] = None
    user_ratings: List[float] = None

    def __post_init__(self):
        if self.queries is None:
            self.queries = []
        if self.preferred_models is None:
            self.preferred_models = []
        if self.user_ratings is None:
            self.user_ratings = []


class PreferenceLearner:
    """ユーザーの好みを学習・推奨するエンジン。"""

    def __init__(self, learning_window_days: int = 30):
        self.learning_window_days = learning_window_days
        self.sessions: List[LearningSession] = []
        self.query_patterns: Dict[str, int] = {}  # クエリパターン -> 出現回数
        self.model_preferences: Dict[str, float] = {}  # モデル -> 平均評価
        self.time_patterns: Dict[str, Dict] = {}  # 時間帯 -> パターン
        self.context_history: List[Dict] = []

    def record_session(self, session: LearningSession):
        """セッションを記録する。"""
        self.sessions.append(session)
        self._update_patterns(session)
        logger.info("セッションを記録: %s", session.session_id)

    def _update_patterns(self, session: LearningSession):
        """セッションからパターンを抽出して更新する。"""
        # クエリパターンを抽出
        for query in session.queries:
            # クエリの最初の5単語をパターンとして使用
            pattern = " ".join(query.split()[:5])
            self.query_patterns[pattern] = self.query_patterns.get(pattern, 0) + 1

        # モデル評価を更新
        for model_id, rating in zip(session.preferred_models, session.user_ratings):
            if model_id not in self.model_preferences:
                self.model_preferences[model_id] = []
            self.model_preferences[model_id].append(rating)

        # 時間帯パターンを記録
        hour = datetime.fromisoformat(session.start_time).strftime("%H")
        if hour not in self.time_patterns:
            self.time_patterns[hour] = {"count": 0, "avg_rating": 0.0}

        self.time_patterns[hour]["count"] += 1
        if session.user_ratings:
            avg_rating = sum(session.user_ratings) / len(session.user_ratings)
            self.time_patterns[hour]["avg_rating"] = (
                (self.time_patterns[hour]["avg_rating"] * (self.time_patterns[hour]["count"] - 1) +
                 avg_rating) / self.time_patterns[hour]["count"]
            )

    def recommend_model(self, query: str) -> Optional[Tuple[str, float]]:
        """クエリに基づいてモデルを推奨する。"""
        # クエリの類似性をチェック
        best_match_pattern = None
        best_match_score = 0.0

        for pattern in self.query_patterns:
            # 簡単な類似度計算（単語の重複度）
            query_words = set(query.lower().split())
            pattern_words = set(pattern.lower().split())
            overlap = len(query_words & pattern_words)
            similarity = overlap / max(len(query_words), len(pattern_words))

            if similarity > best_match_score:
                best_match_score = similarity
                best_match_pattern = pattern

        # 類似パターンが見つかった場合、対応するモデルを推奨
        if best_match_pattern and best_match_score > 0.5:
            # パターンに対応するセッションを探す
            for session in self.sessions:
                if any(best_match_pattern in q for q in session.queries):
                    if session.preferred_models:
                        model_id = session.preferred_models[0]
                        rating = (
                            sum(self.model_preferences.get(model_id, [0])) /
                            len(self.model_preferences.get(model_id, [1]))
                        )
                        return (model_id, rating)

        # デフォルトは最も評価の高いモデル
        if self.model_preferences:
            best_model = max(
                self.model_preferences.items(),
                key=lambda x: sum(x[1]) / len(x[1]),
            )
            avg_rating = sum(best_model[1]) / len(best_model[1])
            return (best_model[0], avg_rating)

        return None

    def recommend_settings(self) -> Dict:
        """ユーザーの行動パターンから最適な設定を推奨する。"""
        recommendations = {}

        # 1. 最適な時間帯を推奨
        if self.time_patterns:
            best_hour = max(
                self.time_patterns.items(),
                key=lambda x: x[1]["avg_rating"],
            )
            recommendations["optimal_usage_hour"] = best_hour[0]
            recommendations["optimal_usage_hour_rating"] = best_hour[1]["avg_rating"]

        # 2. 推奨モデルを推奨
        if self.model_preferences:
            best_model = max(
                self.model_preferences.items(),
                key=lambda x: sum(x[1]) / len(x[1]),
            )
            avg_rating = sum(best_model[1]) / len(best_model[1])
            recommendations["recommended_model"] = best_model[0]
            recommendations["model_rating"] = avg_rating

        # 3. 推奨クエリパターンを推奨
        if self.query_patterns:
            most_common_pattern = max(
                self.query_patterns.items(),
                key=lambda x: x[1],
            )
            recommendations["most_common_query_pattern"] = most_common_pattern[0]
            recommendations["pattern_frequency"] = most_common_pattern[1]

        # 4. UI設定の推奨
        recommendations["ui_settings"] = self._recommend_ui_settings()

        return recommendations

    def _recommend_ui_settings(self) -> Dict:
        """UI設定を推奨する。"""
        # セッション数が少ない場合はデフォルト推奨
        if len(self.sessions) < 3:
            return {
                "theme": "light",
                "font_size": 10,
                "opacity": 85,
            }

        # 使用時間帯から推奨テーマを決定
        peak_hour = int(max(self.time_patterns.items(), key=lambda x: x[1]["count"])[0])

        # 夜間（20:00-08:00）の使用が多い場合はダークモードを推奨
        if peak_hour >= 20 or peak_hour < 8:
            theme = "dark"
        else:
            theme = "light"

        # セッション数から推奨フォントサイズを決定
        if len(self.sessions) > 20:
            font_size = 11  # 頻繁に使用している場合は大きめ
        else:
            font_size = 10

        return {
            "theme": theme,
            "font_size": font_size,
            "opacity": 85,
        }

    def get_learning_summary(self) -> Dict:
        """学習の概要を取得する。"""
        return {
            "total_sessions": len(self.sessions),
            "total_queries": sum(len(s.queries) for s in self.sessions),
            "unique_query_patterns": len(self.query_patterns),
            "tracked_models": list(self.model_preferences.keys()),
            "peak_usage_hour": (
                max(self.time_patterns.items(), key=lambda x: x[1]["count"])[0]
                if self.time_patterns else None
            ),
            "average_model_rating": (
                sum(sum(ratings) / len(ratings) for ratings in self.model_preferences.values()) /
                len(self.model_preferences)
                if self.model_preferences else 0.0
            ),
        }

    def export_learning_data(self) -> str:
        """学習データをJSON形式でエクスポートする。"""
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "learning_summary": self.get_learning_summary(),
            "query_patterns": self.query_patterns,
            "model_preferences": {
                model: {
                    "ratings": ratings,
                    "average": sum(ratings) / len(ratings),
                }
                for model, ratings in self.model_preferences.items()
            },
            "time_patterns": self.time_patterns,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def get_personalized_prompt(self, base_prompt: str) -> str:
        """ユーザーの好みに基づいてプロンプトをパーソナライズする。"""
        # ユーザーの好みに基づいてプロンプトを調整
        recommendations = self.recommend_settings()

        # 推奨モデルに基づいてプロンプトを調整
        if "recommended_model" in recommendations:
            model = recommendations["recommended_model"]
            if "code" in model.lower():
                # コーディング特化モデルの場合
                base_prompt += "\n\n[コード例を含めてください]"
            elif "analysis" in model.lower():
                # 分析特化モデルの場合
                base_prompt += "\n\n[詳細な分析結果を含めてください]"

        return base_prompt

    def should_suggest_model_switch(self) -> Optional[Tuple[str, str, float]]:
        """モデル切り替えを提案すべきかを判定する。"""
        # 現在のモデルの評価が低い場合、別のモデルを提案
        if not self.model_preferences:
            return None

        # 最後に使用されたモデルを取得
        if not self.sessions:
            return None

        last_session = self.sessions[-1]
        if not last_session.preferred_models:
            return None

        current_model = last_session.preferred_models[-1]
        current_rating = (
            sum(self.model_preferences.get(current_model, [0])) /
            len(self.model_preferences.get(current_model, [1]))
        )

        # 最高評価のモデルを取得
        best_model = max(
            self.model_preferences.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
        )
        best_model_id = best_model[0]
        best_rating = sum(best_model[1]) / len(best_model[1])

        # 評価差が0.2以上の場合、提案
        if best_rating - current_rating > 0.2:
            return (current_model, best_model_id, best_rating)

        return None


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== ユーザー好み学習エンジンのテスト ===\n")

    learner = PreferenceLearner()

    # セッションを記録
    print("1️⃣  セッションを記録:")
    session1 = LearningSession(
        session_id="session_001",
        start_time=datetime.now().isoformat(),
        queries=["Pythonでデータ分析するには？", "Pandasの使い方"],
        preferred_models=["gemma-4-12b", "gemma-4-12b"],
        user_ratings=[0.9, 0.85],
    )
    learner.record_session(session1)
    print("   ✅ セッション1を記録\n")

    # 推奨設定を取得
    print("2️⃣  推奨設定を取得:")
    recommendations = learner.recommend_settings()
    print(f"   推奨テーマ: {recommendations['ui_settings']['theme']}")
    print(f"   推奨モデル: {recommendations.get('recommended_model', 'N/A')}\n")

    # 学習概要
    print("3️⃣  学習概要:")
    summary = learner.get_learning_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
