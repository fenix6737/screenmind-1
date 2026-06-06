"""
ScreenMind - モデル管理モジュール
複数のLLMモデルを初期化・管理し、ヘルスチェック・パフォーマンス追跡を行う。
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx

from model_config import ModelConfig, ModelConfigManager, ModelType

logger = logging.getLogger(__name__)


class ModelHealthStatus:
    """モデルのヘルスチェック結果を表すクラス。"""

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.is_healthy = False
        self.response_time_ms = 0.0
        self.error_message = ""
        self.checked_at = datetime.now().isoformat()

    def __str__(self) -> str:
        status = "✅ 正常" if self.is_healthy else "❌ 異常"
        return f"{self.model_id}: {status} ({self.response_time_ms:.0f}ms)"


class ModelPerformanceMetrics:
    """モデルのパフォーマンスメトリクスを記録するクラス。"""

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_response_time_ms = 0.0
        self.total_tokens = 0
        self.min_response_time_ms = float("inf")
        self.max_response_time_ms = 0.0

    def record_request(
        self,
        success: bool,
        response_time_ms: float,
        tokens: int = 0,
    ):
        """リクエスト結果を記録する。"""
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

        self.total_response_time_ms += response_time_ms
        self.total_tokens += tokens
        self.min_response_time_ms = min(self.min_response_time_ms, response_time_ms)
        self.max_response_time_ms = max(self.max_response_time_ms, response_time_ms)

    @property
    def success_rate(self) -> float:
        """成功率を計算する（0.0〜1.0）。"""
        if self.request_count == 0:
            return 1.0
        return self.success_count / self.request_count

    @property
    def avg_response_time_ms(self) -> float:
        """平均応答時間を計算する。"""
        if self.request_count == 0:
            return 0.0
        return self.total_response_time_ms / self.request_count

    def to_dict(self) -> Dict:
        """辞書に変換する。"""
        return {
            "model_id": self.model_id,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": f"{self.success_rate:.1%}",
            "avg_response_time_ms": f"{self.avg_response_time_ms:.1f}",
            "min_response_time_ms": f"{self.min_response_time_ms:.1f}",
            "max_response_time_ms": f"{self.max_response_time_ms:.1f}",
            "total_tokens": self.total_tokens,
        }


class ModelManager:
    """
    複数のLLMモデルを管理し、ヘルスチェック・パフォーマンス追跡を行う。
    """

    def __init__(self, config_file: str = "models_config.json"):
        self.config_manager = ModelConfigManager(config_file)
        self.health_status: Dict[str, ModelHealthStatus] = {}
        self.performance_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self._initialize_metrics()

    def _initialize_metrics(self):
        """全モデルのメトリクスを初期化する。"""
        for model_id in self.config_manager.models.keys():
            self.performance_metrics[model_id] = ModelPerformanceMetrics(model_id)

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """モデル設定を取得する。"""
        return self.config_manager.get_model(model_id)

    def get_all_models(self) -> List[ModelConfig]:
        """全モデルを取得する。"""
        return list(self.config_manager.models.values())

    def get_enabled_models(self) -> List[ModelConfig]:
        """有効なモデルを取得する。"""
        return self.config_manager.get_enabled_models()

    async def health_check(self, model_id: str) -> ModelHealthStatus:
        """
        単一モデルのヘルスチェックを実行する。
        簡単なテストリクエストを送信して応答時間を測定する。
        """
        model = self.get_model(model_id)
        if not model:
            status = ModelHealthStatus(model_id)
            status.error_message = "モデルが見つかりません"
            return status

        status = ModelHealthStatus(model_id)
        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "model": model.model_name,
                    "messages": [
                        {"role": "user", "content": "OK"}
                    ],
                    "max_tokens": 10,
                    "stream": False,
                }

                response = await client.post(
                    model.endpoint_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                elapsed_ms = (time.time() - start_time) * 1000
                status.response_time_ms = elapsed_ms

                if response.status_code == 200:
                    status.is_healthy = True
                    logger.info("✅ %s: ヘルスチェック成功 (%d ms)", model_id, int(elapsed_ms))
                else:
                    status.error_message = f"HTTP {response.status_code}"
                    logger.warning("❌ %s: HTTP エラー %d", model_id, response.status_code)

        except httpx.TimeoutException:
            status.error_message = "タイムアウト"
            logger.warning("❌ %s: タイムアウト", model_id)
        except httpx.ConnectError:
            status.error_message = "接続失敗"
            logger.warning("❌ %s: 接続失敗", model_id)
        except Exception as e:
            status.error_message = str(e)
            logger.warning("❌ %s: エラー %s", model_id, e)

        self.health_status[model_id] = status
        return status

    async def health_check_all(self) -> Dict[str, ModelHealthStatus]:
        """全モデルのヘルスチェックを並行実行する。"""
        tasks = [
            self.health_check(model_id)
            for model_id in self.config_manager.models.keys()
        ]
        results = await asyncio.gather(*tasks)
        return {status.model_id: status for status in results}

    def get_health_status(self, model_id: str) -> Optional[ModelHealthStatus]:
        """モデルのヘルスチェック結果を取得する。"""
        return self.health_status.get(model_id)

    def get_all_health_status(self) -> Dict[str, ModelHealthStatus]:
        """全モデルのヘルスチェック結果を取得する。"""
        return dict(self.health_status)

    def record_request(
        self,
        model_id: str,
        success: bool,
        response_time_ms: float,
        tokens: int = 0,
    ):
        """モデルのリクエスト結果を記録する。"""
        if model_id not in self.performance_metrics:
            self.performance_metrics[model_id] = ModelPerformanceMetrics(model_id)

        metrics = self.performance_metrics[model_id]
        metrics.record_request(success, response_time_ms, tokens)

        # 設定マネージャーのメトリクスも更新
        self.config_manager.update_model_metrics(
            model_id,
            success=success,
            tokens_used=tokens,
            timestamp=datetime.now().isoformat(),
        )

    def get_performance_metrics(self, model_id: str) -> Optional[ModelPerformanceMetrics]:
        """モデルのパフォーマンスメトリクスを取得する。"""
        return self.performance_metrics.get(model_id)

    def get_all_performance_metrics(self) -> Dict[str, ModelPerformanceMetrics]:
        """全モデルのパフォーマンスメトリクスを取得する。"""
        return dict(self.performance_metrics)

    def get_fastest_healthy_model(self) -> Optional[ModelConfig]:
        """
        健全で最速のモデルを取得する。
        ヘルスチェック結果を考慮して選択する。
        """
        candidates = []
        for model in self.get_enabled_models():
            status = self.get_health_status(model.id)
            # ヘルスチェック未実施 or 正常なモデルのみ
            if status is None or status.is_healthy:
                candidates.append(model)

        if not candidates:
            return None

        return max(candidates, key=lambda m: m.avg_tokens_per_second)

    def get_best_model_for_type(self, model_type: ModelType) -> Optional[ModelConfig]:
        """
        用途に最適で健全なモデルを取得する。
        """
        candidates = []
        for model in self.config_manager.get_models_by_type(model_type):
            if not model.is_enabled:
                continue
            status = self.get_health_status(model.id)
            if status is None or status.is_healthy:
                candidates.append(model)

        if not candidates:
            return None

        return max(candidates, key=lambda m: m.priority)

    def get_statistics(self) -> Dict:
        """統計情報を取得する。"""
        all_models = self.get_all_models()
        enabled_models = self.get_enabled_models()
        healthy_models = [
            m for m in enabled_models
            if self.get_health_status(m.id) and self.get_health_status(m.id).is_healthy
        ]

        total_requests = sum(m.request_count for m in self.performance_metrics.values())
        total_success = sum(m.success_count for m in self.performance_metrics.values())
        total_tokens = sum(m.total_tokens for m in self.performance_metrics.values())

        return {
            "total_models": len(all_models),
            "enabled_models": len(enabled_models),
            "healthy_models": len(healthy_models),
            "total_requests": total_requests,
            "total_success": total_success,
            "overall_success_rate": (
                total_success / total_requests if total_requests > 0 else 1.0
            ),
            "total_tokens_used": total_tokens,
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "enabled": m.is_enabled,
                    "healthy": (
                        self.get_health_status(m.id).is_healthy
                        if self.get_health_status(m.id)
                        else None
                    ),
                    "metrics": self.get_performance_metrics(m.id).to_dict()
                    if self.get_performance_metrics(m.id)
                    else None,
                }
                for m in all_models
            ],
        }

    def save_config(self) -> bool:
        """設定をファイルに保存する。"""
        return self.config_manager.save_to_file()


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== モデルマネージャーのテスト ===\n")

    manager = ModelManager()

    # モデル一覧
    print("=== 登録されているモデル ===")
    for model in manager.get_enabled_models():
        print(f"  {model.name} ({model.id})")

    # パフォーマンスメトリクスをシミュレート
    print("\n=== パフォーマンスメトリクス（シミュレーション） ===")
    manager.record_request("gemma-4-12b-iq4", success=True, response_time_ms=150, tokens=512)
    manager.record_request("gemma-4-12b-iq4", success=True, response_time_ms=160, tokens=480)
    manager.record_request("mistral-7b", success=True, response_time_ms=80, tokens=256)
    manager.record_request("mistral-7b", success=False, response_time_ms=5000, tokens=0)

    for model_id, metrics in manager.get_all_performance_metrics().items():
        print(f"\n{model_id}:")
        for key, value in metrics.to_dict().items():
            if key != "model_id":
                print(f"  {key}: {value}")

    # 統計情報
    print("\n=== 統計情報 ===")
    stats = manager.get_statistics()
    print(f"総モデル数: {stats['total_models']}")
    print(f"有効なモデル: {stats['enabled_models']}")
    print(f"総リクエスト数: {stats['total_requests']}")
    print(f"総成功数: {stats['total_success']}")
    print(f"全体成功率: {stats['overall_success_rate']:.1%}")
    print(f"使用トークン総数: {stats['total_tokens_used']}")
