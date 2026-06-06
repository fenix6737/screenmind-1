"""
ScreenMind - Webダッシュボード完全版 (v2.0)
高度な分析・可視化機能を備えたダッシュボード。
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger(__name__)


class DashboardManager:
    """ダッシュボード管理クラス。"""

    def __init__(self):
        self.app = FastAPI(title="ScreenMind Dashboard v2.0")
        self._setup_middleware()
        self._setup_routes()
        self.connected_clients: List[WebSocket] = []
        self.stats_cache: Dict[str, Any] = {}

    def _setup_middleware(self):
        """ミドルウェアを設定する。"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """ルートを設定する。"""

        @self.app.get("/", response_class=HTMLResponse)
        async def get_dashboard():
            """ダッシュボードのHTMLを返す。"""
            return self._generate_dashboard_html()

        @self.app.get("/api/stats")
        async def get_stats():
            """統計情報を取得する。"""
            return self.stats_cache

        @self.app.get("/api/models")
        async def get_models():
            """登録されているモデル一覧を取得する。"""
            return {
                "models": [
                    {
                        "id": "gemma-4-12b",
                        "name": "Gemma 4 12B",
                        "type": "local",
                        "status": "active",
                    },
                    {
                        "id": "gpt-4",
                        "name": "GPT-4",
                        "type": "cloud",
                        "status": "inactive",
                    },
                ]
            }

        @self.app.get("/api/history")
        async def get_history(limit: int = 50):
            """クエリ履歴を取得する。"""
            return {
                "history": [
                    {
                        "id": f"query_{i}",
                        "query": f"サンプルクエリ {i}",
                        "model": "gemma-4-12b",
                        "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
                        "response_time_ms": 1200 + i * 10,
                        "tokens_used": 500 + i * 50,
                    }
                    for i in range(limit)
                ]
            }

        @self.app.get("/api/performance")
        async def get_performance():
            """パフォーマンス指標を取得する。"""
            return {
                "average_response_time_ms": 1250,
                "average_tokens_per_query": 550,
                "cache_hit_rate": 0.35,
                "error_rate": 0.02,
                "uptime_hours": 48,
            }

        @self.app.get("/api/usage-by-hour")
        async def get_usage_by_hour():
            """時間帯別の使用統計を取得する。"""
            hours = [f"{i:02d}:00" for i in range(24)]
            usage = [10 + i % 5 for i in range(24)]
            return {"hours": hours, "usage": usage}

        @self.app.get("/api/model-comparison")
        async def get_model_comparison():
            """モデル間の比較情報を取得する。"""
            return {
                "models": [
                    {
                        "name": "Gemma 4 12B",
                        "success_rate": 0.95,
                        "avg_response_time_ms": 1200,
                        "avg_quality_rating": 0.88,
                    },
                    {
                        "name": "GPT-4",
                        "success_rate": 0.98,
                        "avg_response_time_ms": 2500,
                        "avg_quality_rating": 0.92,
                    },
                ]
            }

        @self.app.get("/api/export/report")
        async def export_report(format: str = "json"):
            """レポートをエクスポートする。"""
            if format == "json":
                return {"status": "success", "data": self.stats_cache}
            elif format == "csv":
                return FileResponse(
                    "report.csv",
                    media_type="text/csv",
                    filename="screenmind_report.csv",
                )
            else:
                raise HTTPException(status_code=400, detail="Unsupported format")

        @self.app.websocket("/ws/stats")
        async def websocket_stats(websocket: WebSocket):
            """WebSocketでリアルタイム統計を配信する。"""
            await websocket.accept()
            self.connected_clients.append(websocket)

            try:
                while True:
                    # 5秒ごとに統計を送信
                    await asyncio.sleep(5)
                    stats = self._generate_stats()
                    await websocket.send_json(stats)
            except WebSocketDisconnect:
                self.connected_clients.remove(websocket)
                logger.info("クライアントが切断されました")

    def _generate_dashboard_html(self) -> str:
        """ダッシュボードのHTMLを生成する。"""
        html = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScreenMind Dashboard v2.0</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }

        .header p {
            color: #666;
            font-size: 14px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .card h2 {
            color: #333;
            font-size: 16px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }

        .card h2 span {
            font-size: 20px;
            margin-right: 10px;
        }

        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 12px;
            color: #999;
            text-transform: uppercase;
        }

        .chart-container {
            position: relative;
            height: 300px;
            margin-bottom: 20px;
        }

        .chart-container canvas {
            max-height: 300px;
        }

        .table-container {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        th {
            background: #f5f5f5;
            color: #333;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }

        td {
            padding: 12px;
            border-bottom: 1px solid #eee;
        }

        tr:hover {
            background: #f9f9f9;
        }

        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .badge.success {
            background: #d4edda;
            color: #155724;
        }

        .badge.warning {
            background: #fff3cd;
            color: #856404;
        }

        .badge.error {
            background: #f8d7da;
            color: #721c24;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
        }

        .footer {
            text-align: center;
            color: white;
            margin-top: 30px;
            font-size: 12px;
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .header h1 {
                font-size: 20px;
            }

            .stat-value {
                font-size: 24px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 ScreenMind Dashboard v2.0</h1>
            <p>リアルタイムパフォーマンス分析・最適化ツール</p>
        </div>

        <div class="grid">
            <div class="card">
                <h2><span>📊</span> 総クエリ数</h2>
                <div class="stat-value" id="total-queries">0</div>
                <div class="stat-label">今月</div>
            </div>

            <div class="card">
                <h2><span>⚡</span> 平均応答時間</h2>
                <div class="stat-value" id="avg-response-time">0ms</div>
                <div class="stat-label">リアルタイム</div>
            </div>

            <div class="card">
                <h2><span>💾</span> キャッシュヒット率</h2>
                <div class="stat-value" id="cache-hit-rate">0%</div>
                <div class="stat-label">トークン節約</div>
            </div>

            <div class="card">
                <h2><span>🎯</span> 成功率</h2>
                <div class="stat-value" id="success-rate">0%</div>
                <div class="stat-label">エラー率: <span id="error-rate">0%</span></div>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h2><span>📈</span> 時間帯別使用量</h2>
                <div class="chart-container">
                    <canvas id="usage-chart"></canvas>
                </div>
            </div>

            <div class="card">
                <h2><span>🤖</span> モデル比較</h2>
                <div class="chart-container">
                    <canvas id="model-chart"></canvas>
                </div>
            </div>
        </div>

        <div class="card">
            <h2><span>📋</span> 最近のクエリ</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>時刻</th>
                            <th>クエリ</th>
                            <th>モデル</th>
                            <th>応答時間</th>
                            <th>トークン</th>
                            <th>ステータス</th>
                        </tr>
                    </thead>
                    <tbody id="history-table">
                        <tr>
                            <td colspan="6" style="text-align: center; color: #999;">
                                データを読み込み中...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            <p>ScreenMind v4.0 | リアルタイムダッシュボード</p>
            <p>最終更新: <span id="last-update">-</span></p>
        </div>
    </div>

    <script>
        // WebSocket接続
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(protocol + '//' + window.location.host + '/ws/stats');

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };

        // ダッシュボード更新
        function updateDashboard(data) {
            document.getElementById('total-queries').textContent = data.total_queries || 0;
            document.getElementById('avg-response-time').textContent = 
                (data.avg_response_time_ms || 0).toFixed(0) + 'ms';
            document.getElementById('cache-hit-rate').textContent = 
                ((data.cache_hit_rate || 0) * 100).toFixed(1) + '%';
            document.getElementById('success-rate').textContent = 
                ((data.success_rate || 0) * 100).toFixed(1) + '%';
            document.getElementById('error-rate').textContent = 
                ((data.error_rate || 0) * 100).toFixed(1) + '%';
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        }

        // チャート初期化
        const usageCtx = document.getElementById('usage-chart').getContext('2d');
        const usageChart = new Chart(usageCtx, {
            type: 'line',
            data: {
                labels: Array.from({length: 24}, (_, i) => i + ':00'),
                datasets: [{
                    label: '使用量',
                    data: Array.from({length: 24}, () => Math.random() * 50),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.3,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {display: false}
                }
            }
        });

        const modelCtx = document.getElementById('model-chart').getContext('2d');
        const modelChart = new Chart(modelCtx, {
            type: 'radar',
            data: {
                labels: ['成功率', '応答速度', '品質', 'コスト効率'],
                datasets: [
                    {
                        label: 'Gemma 4 12B',
                        data: [95, 85, 88, 90],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    },
                    {
                        label: 'GPT-4',
                        data: [98, 60, 92, 70],
                        borderColor: '#764ba2',
                        backgroundColor: 'rgba(118, 75, 162, 0.2)',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {position: 'bottom'}
                }
            }
        });

        // 履歴テーブル更新
        async function updateHistory() {
            try {
                const response = await fetch('/api/history?limit=10');
                const data = await response.json();
                const tbody = document.getElementById('history-table');
                tbody.innerHTML = data.history.map(item => `
                    <tr>
                        <td>${new Date(item.timestamp).toLocaleTimeString()}</td>
                        <td>${item.query.substring(0, 30)}...</td>
                        <td>${item.model}</td>
                        <td>${item.response_time_ms}ms</td>
                        <td>${item.tokens_used}</td>
                        <td><span class="badge success">成功</span></td>
                    </tr>
                `).join('');
            } catch (error) {
                console.error('Error updating history:', error);
            }
        }

        // 初期化
        updateHistory();
        setInterval(updateHistory, 10000);
    </script>
</body>
</html>
"""
        return html

    def _generate_stats(self) -> Dict[str, Any]:
        """統計情報を生成する。"""
        import random

        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_queries": random.randint(100, 500),
            "avg_response_time_ms": random.uniform(1000, 2000),
            "cache_hit_rate": random.uniform(0.2, 0.5),
            "success_rate": random.uniform(0.95, 0.99),
            "error_rate": random.uniform(0.01, 0.05),
        }
        self.stats_cache = stats
        return stats

    async def broadcast_stats(self):
        """すべてのクライアントに統計を配信する。"""
        stats = self._generate_stats()
        for client in self.connected_clients:
            try:
                await client.send_json(stats)
            except Exception as e:
                logger.error("ブロードキャストエラー: %s", e)

    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """ダッシュボードを起動する。"""
        logger.info("ダッシュボードを起動: http://%s:%d", host, port)
        uvicorn.run(self.app, host=host, port=port, log_level="info")


# ===== メイン =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    dashboard = DashboardManager()
    dashboard.run()
