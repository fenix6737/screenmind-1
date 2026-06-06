"""
ScreenMind - ユーザープロファイル管理
ユーザーの好みと使用パターンを学習・管理する。
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class UserPreferences:
    """ユーザーの設定。"""
    theme: str = "light"  # light, dark, high_contrast
    font_size: int = 10
    opacity: int = 85
    auto_model_selection: bool = True
    preferred_model: Optional[str] = None
    hotkey: str = "Ctrl+Shift+Space"
    shortcuts_enabled: bool = True
    cache_enabled: bool = True
    history_compression_enabled: bool = True
    notifications_enabled: bool = True
    auto_save_enabled: bool = True
    save_interval_minutes: int = 5


@dataclass
class UsageStatistics:
    """使用統計。"""
    total_queries: int = 0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    average_response_time_ms: float = 0.0
    most_used_model: Optional[str] = None
    most_used_task_type: Optional[str] = None
    last_used: Optional[str] = None
    session_count: int = 0
    total_session_time_minutes: int = 0


@dataclass
class LearningProfile:
    """学習プロファイル。"""
    preferred_task_types: Dict[str, int] = field(default_factory=dict)  # タスク型 -> 使用回数
    preferred_models: Dict[str, int] = field(default_factory=dict)  # モデル -> 使用回数
    keyword_preferences: Dict[str, float] = field(default_factory=dict)  # キーワード -> スコア
    time_of_day_preferences: Dict[str, int] = field(default_factory=dict)  # 時間帯 -> 使用回数
    response_quality_ratings: List[Dict] = field(default_factory=list)  # 回答品質評価


class UserProfile:
    """ユーザープロファイルを管理するクラス。"""

    def __init__(self, user_id: str, profile_dir: str = "profiles"):
        self.user_id = user_id
        self.profile_dir = profile_dir
        self.preferences = UserPreferences()
        self.statistics = UsageStatistics()
        self.learning_profile = LearningProfile()
        self.created_at = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()

        os.makedirs(profile_dir, exist_ok=True)
        self._load_profile()

    def _get_profile_path(self) -> str:
        """プロファイルファイルのパスを取得する。"""
        return os.path.join(self.profile_dir, f"{self.user_id}_profile.json")

    def _load_profile(self):
        """プロファイルをファイルから読み込む。"""
        profile_path = self._get_profile_path()
        if not os.path.exists(profile_path):
            logger.info("新しいプロファイルを作成: %s", self.user_id)
            return

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 設定を復元
            if "preferences" in data:
                pref_data = data["preferences"]
                self.preferences = UserPreferences(**pref_data)

            # 統計を復元
            if "statistics" in data:
                stat_data = data["statistics"]
                self.statistics = UsageStatistics(**stat_data)

            # 学習プロファイルを復元
            if "learning_profile" in data:
                learn_data = data["learning_profile"]
                self.learning_profile = LearningProfile(**learn_data)

            self.created_at = data.get("created_at", self.created_at)
            self.last_updated = data.get("last_updated", self.last_updated)

            logger.info("プロファイルを読み込み: %s", self.user_id)
        except Exception as e:
            logger.error("プロファイル読み込みエラー: %s", e)

    def save_profile(self):
        """プロファイルをファイルに保存する。"""
        try:
            profile_path = self._get_profile_path()
            self.last_updated = datetime.now().isoformat()

            data = {
                "user_id": self.user_id,
                "created_at": self.created_at,
                "last_updated": self.last_updated,
                "preferences": asdict(self.preferences),
                "statistics": asdict(self.statistics),
                "learning_profile": {
                    "preferred_task_types": self.learning_profile.preferred_task_types,
                    "preferred_models": self.learning_profile.preferred_models,
                    "keyword_preferences": self.learning_profile.keyword_preferences,
                    "time_of_day_preferences": self.learning_profile.time_of_day_preferences,
                    "response_quality_ratings": self.learning_profile.response_quality_ratings,
                },
            }

            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info("プロファイルを保存: %s", self.user_id)
        except Exception as e:
            logger.error("プロファイル保存エラー: %s", e)

    def update_usage_statistics(
        self,
        tokens_used: int,
        cost: float,
        response_time_ms: float,
        model_id: str,
        task_type: str,
    ):
        """使用統計を更新する。"""
        self.statistics.total_queries += 1
        self.statistics.total_tokens_used += tokens_used
        self.statistics.total_cost += cost
        self.statistics.average_response_time_ms = (
            (self.statistics.average_response_time_ms * (self.statistics.total_queries - 1) +
             response_time_ms) / self.statistics.total_queries
        )
        self.statistics.most_used_model = model_id
        self.statistics.most_used_task_type = task_type
        self.statistics.last_used = datetime.now().isoformat()

        # 学習プロファイルを更新
        self._update_learning_profile(model_id, task_type)

    def _update_learning_profile(self, model_id: str, task_type: str):
        """学習プロファイルを更新する。"""
        # モデル使用回数を更新
        self.learning_profile.preferred_models[model_id] = (
            self.learning_profile.preferred_models.get(model_id, 0) + 1
        )

        # タスク型使用回数を更新
        self.learning_profile.preferred_task_types[task_type] = (
            self.learning_profile.preferred_task_types.get(task_type, 0) + 1
        )

        # 時間帯の使用パターンを記録
        hour = datetime.now().strftime("%H")
        self.learning_profile.time_of_day_preferences[hour] = (
            self.learning_profile.time_of_day_preferences.get(hour, 0) + 1
        )

    def add_quality_rating(
        self,
        query: str,
        response: str,
        rating: float,  # 0.0-1.0
        model_id: str,
    ):
        """回答品質を評価する。"""
        rating_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],  # 最初の100文字
            "response": response[:100],
            "rating": rating,
            "model_id": model_id,
        }
        self.learning_profile.response_quality_ratings.append(rating_entry)

        # キーワード好みを更新
        words = query.lower().split()
        for word in words:
            if len(word) > 3:  # 短い単語は除外
                self.learning_profile.keyword_preferences[word] = (
                    self.learning_profile.keyword_preferences.get(word, 0) + rating
                )

    def get_recommended_model(self) -> Optional[str]:
        """推奨モデルを取得する。"""
        if not self.learning_profile.preferred_models:
            return None

        # 最も使用されたモデルを返す
        return max(
            self.learning_profile.preferred_models.items(),
            key=lambda x: x[1],
        )[0]

    def get_recommended_task_type(self) -> Optional[str]:
        """推奨タスク型を取得する。"""
        if not self.learning_profile.preferred_task_types:
            return None

        # 最も使用されたタスク型を返す
        return max(
            self.learning_profile.preferred_task_types.items(),
            key=lambda x: x[1],
        )[0]

    def get_peak_usage_hours(self, top_n: int = 3) -> List[str]:
        """ピーク使用時間帯を取得する。"""
        if not self.learning_profile.time_of_day_preferences:
            return []

        sorted_hours = sorted(
            self.learning_profile.time_of_day_preferences.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return [hour for hour, _ in sorted_hours[:top_n]]

    def get_average_quality_rating(self) -> float:
        """平均品質評価を取得する。"""
        if not self.learning_profile.response_quality_ratings:
            return 0.0

        total_rating = sum(r["rating"] for r in self.learning_profile.response_quality_ratings)
        return total_rating / len(self.learning_profile.response_quality_ratings)

    def get_profile_summary(self) -> Dict[str, Any]:
        """プロファイルの概要を取得する。"""
        return {
            "user_id": self.user_id,
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "statistics": {
                "total_queries": self.statistics.total_queries,
                "total_tokens_used": self.statistics.total_tokens_used,
                "total_cost": f"${self.statistics.total_cost:.2f}",
                "average_response_time_ms": f"{self.statistics.average_response_time_ms:.1f}ms",
                "most_used_model": self.statistics.most_used_model,
                "most_used_task_type": self.statistics.most_used_task_type,
            },
            "preferences": asdict(self.preferences),
            "learning_insights": {
                "recommended_model": self.get_recommended_model(),
                "recommended_task_type": self.get_recommended_task_type(),
                "peak_usage_hours": self.get_peak_usage_hours(),
                "average_quality_rating": f"{self.get_average_quality_rating():.2f}/1.00",
            },
        }

    def export_profile_as_html(self) -> str:
        """プロファイルをHTMLでエクスポートする。"""
        summary = self.get_profile_summary()

        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>ScreenMind ユーザープロファイル</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 20px;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 15px 0;
        }}
        .stat-box {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #007bff;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .stat-value {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>👤 ScreenMind ユーザープロファイル</h1>
        
        <h2>📊 統計情報</h2>
        <div class="stat-grid">
            <div class="stat-box">
                <div class="stat-label">総クエリ数</div>
                <div class="stat-value">{summary['statistics']['total_queries']}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">使用トークン</div>
                <div class="stat-value">{summary['statistics']['total_tokens_used']:,}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">総コスト</div>
                <div class="stat-value">{summary['statistics']['total_cost']}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">平均応答時間</div>
                <div class="stat-value">{summary['statistics']['average_response_time_ms']}</div>
            </div>
        </div>

        <h2>🤖 学習インサイト</h2>
        <div class="stat-grid">
            <div class="stat-box">
                <div class="stat-label">推奨モデル</div>
                <div class="stat-value">{summary['learning_insights']['recommended_model'] or 'N/A'}</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">平均品質評価</div>
                <div class="stat-value">{summary['learning_insights']['average_quality_rating']}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""
        return html


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== ユーザープロファイルのテスト ===\n")

    profile = UserProfile("user_001")

    # 使用統計を更新
    print("1️⃣  使用統計を更新:")
    profile.update_usage_statistics(
        tokens_used=500,
        cost=0.01,
        response_time_ms=1200,
        model_id="gemma-4-12b",
        task_type="analysis",
    )
    print("   ✅ 統計を記録\n")

    # 品質評価を追加
    print("2️⃣  品質評価を追加:")
    profile.add_quality_rating(
        query="Pythonでデータ分析するには？",
        response="Pandasライブラリを使用します...",
        rating=0.9,
        model_id="gemma-4-12b",
    )
    print("   ✅ 評価を記録\n")

    # プロファイルを保存
    print("3️⃣  プロファイルを保存:")
    profile.save_profile()
    print("   ✅ 保存完了\n")

    # プロファイルの概要
    print("4️⃣  プロファイルの概要:")
    summary = profile.get_profile_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
