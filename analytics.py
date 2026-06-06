"""
ScreenMind - 分析・ログモジュール
ユーザーの利用パターン、モデル選択、パフォーマンスを詳細に分析する。
"""

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AnalyticsEvent:
    """分析イベントを表すクラス。"""

    def __init__(
        self,
        event_type: str,
        event_data: Dict,
        timestamp: Optional[str] = None,
    ):
        self.event_type = event_type
        self.event_data = event_data
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """辞書に変換する。"""
        return {
            "event_type": self.event_type,
            "event_data": self.event_data,
            "timestamp": self.timestamp,
        }


class AnalyticsCollector:
    """
    ScreenMindの利用データを収集・分析するクラス。
    """

    def __init__(self, log_dir: str = "analytics"):
        self.log_dir = log_dir
        self._events: List[AnalyticsEvent] = []
        self._load_events()

    def _get_log_path(self) -> str:
        """ログファイルのパスを取得する。"""
        os.makedirs(self.log_dir, exist_ok=True)
        return os.path.join(self.log_dir, "analytics.json")

    def _load_events(self):
        """ディスクからイベントを読み込む。"""
        log_path = self._get_log_path()
        if not os.path.exists(log_path):
            logger.info("分析ログが見つかりません（初回実行）")
            return

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._events = [
                AnalyticsEvent(
                    event_type=item["event_type"],
                    event_data=item["event_data"],
                    timestamp=item.get("timestamp"),
                )
                for item in data
            ]
            logger.info("分析ログを読み込み: %d イベント", len(self._events))
        except Exception as e:
            logger.error("分析ログの読み込みに失敗: %s", e)

    def _save_events(self):
        """ディスクにイベントを保存する。"""
        log_path = self._get_log_path()
        try:
            data = [event.to_dict() for event in self._events]
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("分析ログを保存: %d イベント", len(self._events))
        except Exception as e:
            logger.error("分析ログの保存に失敗: %s", e)

    def record_request(
        self,
        query: str,
        model_id: str,
        response_time_ms: float,
        tokens: int,
        success: bool = True,
        error_msg: Optional[str] = None,
    ):
        """リクエストイベントを記録する。"""
        event = AnalyticsEvent(
            event_type="request",
            event_data={
                "query_length": len(query),
                "model_id": model_id,
                "response_time_ms": response_time_ms,
                "tokens": tokens,
                "success": success,
                "error_msg": error_msg,
            },
        )
        self._events.append(event)
        self._save_events()
        logger.debug("リクエストイベントを記録: %s", model_id)

    def record_model_selection(
        self,
        query: str,
        selected_model_id: str,
        candidate_models: List[str],
        selection_reason: str,
        is_auto: bool = True,
    ):
        """モデル選択イベントを記録する。"""
        event = AnalyticsEvent(
            event_type="model_selection",
            event_data={
                "query_length": len(query),
                "selected_model": selected_model_id,
                "candidates": candidate_models,
                "reason": selection_reason,
                "is_auto": is_auto,
            },
        )
        self._events.append(event)
        self._save_events()
        logger.debug("モデル選択イベントを記録: %s", selected_model_id)

    def record_cache_hit(self, query: str, model_id: str):
        """キャッシュヒットイベントを記録する。"""
        event = AnalyticsEvent(
            event_type="cache_hit",
            event_data={
                "query_length": len(query),
                "model_id": model_id,
            },
        )
        self._events.append(event)
        self._save_events()

    def record_history_compression(
        self,
        original_count: int,
        compressed_count: int,
        compression_ratio: float,
    ):
        """履歴圧縮イベントを記録する。"""
        event = AnalyticsEvent(
            event_type="history_compression",
            event_data={
                "original_message_count": original_count,
                "compressed_message_count": compressed_count,
                "compression_ratio": compression_ratio,
            },
        )
        self._events.append(event)
        self._save_events()

    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """イベントを取得する。"""
        events = self._events
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return [e.to_dict() for e in events[-limit:]]

    def get_statistics(self, hours: int = 24) -> Dict:
        """指定時間内の統計情報を取得する。"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_events = [
            e for e in self._events
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]

        request_events = [e for e in recent_events if e.event_type == "request"]
        cache_events = [e for e in recent_events if e.event_type == "cache_hit"]
        model_selection_events = [
            e for e in recent_events if e.event_type == "model_selection"
        ]

        # リクエスト統計
        total_requests = len(request_events)
        successful_requests = sum(
            1 for e in request_events if e.event_data.get("success", False)
        )
        avg_response_time = (
            sum(e.event_data.get("response_time_ms", 0) for e in request_events)
            / max(total_requests, 1)
        )
        total_tokens = sum(
            e.event_data.get("tokens", 0) for e in request_events
        )

        # モデル別統計
        model_stats = defaultdict(lambda: {"count": 0, "avg_time": 0, "tokens": 0})
        for event in request_events:
            model_id = event.event_data.get("model_id", "unknown")
            model_stats[model_id]["count"] += 1
            model_stats[model_id]["avg_time"] += event.event_data.get("response_time_ms", 0)
            model_stats[model_id]["tokens"] += event.event_data.get("tokens", 0)

        for model_id in model_stats:
            count = model_stats[model_id]["count"]
            model_stats[model_id]["avg_time"] /= max(count, 1)

        # キャッシュ統計
        cache_hit_rate = len(cache_events) / max(total_requests, 1)

        # 自動選択統計
        auto_selections = sum(
            1 for e in model_selection_events
            if e.event_data.get("is_auto", False)
        )

        return {
            "period_hours": hours,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / max(total_requests, 1),
            "avg_response_time_ms": avg_response_time,
            "total_tokens": total_tokens,
            "cache_hit_rate": cache_hit_rate,
            "model_statistics": dict(model_stats),
            "auto_selections": auto_selections,
            "manual_selections": len(model_selection_events) - auto_selections,
        }

    def get_model_performance(self, model_id: str, hours: int = 24) -> Dict:
        """特定モデルのパフォーマンスを取得する。"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        events = [
            e for e in self._events
            if datetime.fromisoformat(e.timestamp) > cutoff_time
            and e.event_type == "request"
            and e.event_data.get("model_id") == model_id
        ]

        if not events:
            return {
                "model_id": model_id,
                "request_count": 0,
                "success_rate": 0.0,
                "avg_response_time_ms": 0.0,
                "total_tokens": 0,
            }

        successful = sum(1 for e in events if e.event_data.get("success", False))
        avg_time = sum(
            e.event_data.get("response_time_ms", 0) for e in events
        ) / len(events)
        total_tokens = sum(e.event_data.get("tokens", 0) for e in events)

        return {
            "model_id": model_id,
            "request_count": len(events),
            "success_rate": successful / len(events),
            "avg_response_time_ms": avg_time,
            "total_tokens": total_tokens,
        }

    def get_usage_patterns(self, hours: int = 24) -> Dict:
        """ユーザーの利用パターンを分析する。"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        request_events = [
            e for e in self._events
            if datetime.fromisoformat(e.timestamp) > cutoff_time
            and e.event_type == "request"
        ]

        # 時間帯別の利用
        hourly_usage = defaultdict(int)
        for event in request_events:
            timestamp = datetime.fromisoformat(event.timestamp)
            hour = timestamp.hour
            hourly_usage[hour] += 1

        # クエリ長の分布
        query_lengths = [
            e.event_data.get("query_length", 0) for e in request_events
        ]
        avg_query_length = sum(query_lengths) / max(len(query_lengths), 1)

        # レスポンス時間の分布
        response_times = [
            e.event_data.get("response_time_ms", 0) for e in request_events
        ]
        response_times.sort()

        return {
            "total_requests": len(request_events),
            "avg_query_length": avg_query_length,
            "hourly_usage": dict(hourly_usage),
            "response_time_percentiles": {
                "p50": response_times[len(response_times) // 2] if response_times else 0,
                "p95": response_times[int(len(response_times) * 0.95)] if response_times else 0,
                "p99": response_times[int(len(response_times) * 0.99)] if response_times else 0,
            },
        }

    def generate_report(self, hours: int = 24) -> str:
        """HTML形式のレポートを生成する。"""
        stats = self.get_statistics(hours)
        patterns = self.get_usage_patterns(hours)

        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScreenMind 分析レポート</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a2e;
            border-bottom: 3px solid #e94560;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #1a1a2e;
            margin-top: 30px;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 15px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #e94560;
        }}
        .stat-label {{
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #e0e0e0;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #f0f0f0;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #999;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 ScreenMind 分析レポート</h1>
        <p>レポート期間: 過去 {hours} 時間</p>

        <h2>📊 概要</h2>
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_requests']}</div>
                <div class="stat-label">総リクエスト数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['success_rate']:.1%}</div>
                <div class="stat-label">成功率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['avg_response_time_ms']:.0f}ms</div>
                <div class="stat-label">平均応答時間</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['cache_hit_rate']:.1%}</div>
                <div class="stat-label">キャッシュヒット率</div>
            </div>
        </div>

        <h2>🤖 モデル別統計</h2>
        <table>
            <tr>
                <th>モデル</th>
                <th>リクエスト数</th>
                <th>平均応答時間</th>
                <th>使用トークン</th>
            </tr>
"""
        for model_id, data in stats['model_statistics'].items():
            html += f"""
            <tr>
                <td>{model_id}</td>
                <td>{data['count']}</td>
                <td>{data['avg_time']:.0f}ms</td>
                <td>{data['tokens']}</td>
            </tr>
"""
        html += """
        </table>

        <h2>📈 利用パターン</h2>
        <p>平均クエリ長: {:.0f} 文字</p>
        <p>レスポンス時間（パーセンタイル）:</p>
        <ul>
            <li>P50: {:.0f}ms</li>
            <li>P95: {:.0f}ms</li>
            <li>P99: {:.0f}ms</li>
        </ul>

        <div class="footer">
            <p>生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>ScreenMind v2.0</p>
        </div>
    </div>
</body>
</html>
""".format(
            patterns['avg_query_length'],
            patterns['response_time_percentiles']['p50'],
            patterns['response_time_percentiles']['p95'],
            patterns['response_time_percentiles']['p99'],
        )

        return html


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== 分析コレクターのテスト ===\n")

    collector = AnalyticsCollector()

    # テストイベントを記録
    print("1️⃣  イベントを記録中...\n")
    for i in range(5):
        collector.record_request(
            query=f"テスト質問{i+1}",
            model_id="gemma-4-12b-iq4",
            response_time_ms=100 + i * 20,
            tokens=256 + i * 50,
            success=True,
        )

    collector.record_cache_hit("テスト質問1", "gemma-4-12b-iq4")

    # 統計を表示
    print("2️⃣  統計情報:\n")
    stats = collector.get_statistics(hours=24)
    print(f"   総リクエスト数: {stats['total_requests']}")
    print(f"   成功率: {stats['success_rate']:.1%}")
    print(f"   キャッシュヒット率: {stats['cache_hit_rate']:.1%}\n")

    # モデルパフォーマンス
    print("3️⃣  モデルパフォーマンス:\n")
    perf = collector.get_model_performance("gemma-4-12b-iq4")
    print(f"   リクエスト数: {perf['request_count']}")
    print(f"   成功率: {perf['success_rate']:.1%}")
    print(f"   平均応答時間: {perf['avg_response_time_ms']:.0f}ms\n")
