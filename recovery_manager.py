"""
ScreenMind v4.0 - 自動リカバリーマネージャー
エラーから自動的に回復し、システムの可用性を最大化。
"""

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    """リカバリー戦略。"""
    RETRY = "retry"  # 再試行
    FALLBACK = "fallback"  # フォールバック
    RESTART = "restart"  # 再起動
    SHUTDOWN = "shutdown"  # シャットダウン


@dataclass
class RecoveryAction:
    """リカバリーアクション。"""
    timestamp: str
    error_type: str
    strategy: str
    success: bool
    details: Dict[str, Any]


class RecoveryManager:
    """自動リカバリーマネージャー。"""

    def __init__(self, recovery_history_file: str = "recovery_history.json"):
        self.recovery_history_file = recovery_history_file
        self.recovery_actions: List[RecoveryAction] = []
        self.max_history_size = 500
        self.lock = threading.RLock()

        # リカバリー戦略の登録
        self.strategies: Dict[str, Callable] = {}
        self._register_default_strategies()

        # リカバリー履歴の読み込み
        self._load_recovery_history()

    def _register_default_strategies(self):
        """デフォルトのリカバリー戦略を登録。"""
        self.strategies[RecoveryStrategy.RETRY.value] = self._strategy_retry
        self.strategies[RecoveryStrategy.FALLBACK.value] = self._strategy_fallback
        self.strategies[RecoveryStrategy.RESTART.value] = self._strategy_restart

    def register_strategy(self, name: str, strategy: Callable):
        """カスタムリカバリー戦略を登録。"""
        self.strategies[name] = strategy
        logger.info("リカバリー戦略を登録: %s", name)

    def attempt_recovery(
        self,
        error: Exception,
        strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
        context: Optional[Dict] = None,
        max_attempts: int = 3
    ) -> bool:
        """リカバリーを試行。"""
        with self.lock:
            logger.info("リカバリーを試行: %s (戦略: %s)", type(error).__name__, strategy.value)

            try:
                strategy_func = self.strategies.get(strategy.value)
                if not strategy_func:
                    logger.error("未知のリカバリー戦略: %s", strategy.value)
                    return False

                success = strategy_func(error, context, max_attempts)

                # リカバリーアクションを記録
                action = RecoveryAction(
                    timestamp=datetime.now().isoformat(),
                    error_type=type(error).__name__,
                    strategy=strategy.value,
                    success=success,
                    details=context or {},
                )
                self.recovery_actions.append(action)

                # 履歴サイズを制限
                if len(self.recovery_actions) > self.max_history_size:
                    self.recovery_actions.pop(0)

                # 履歴を保存
                self._save_recovery_history()

                return success
            except Exception as recovery_error:
                logger.error("リカバリー失敗: %s", recovery_error)
                return False

    def _strategy_retry(
        self,
        error: Exception,
        context: Optional[Dict] = None,
        max_attempts: int = 3
    ) -> bool:
        """再試行戦略。"""
        func = context.get("func") if context else None
        if not func:
            logger.error("再試行戦略: 関数が指定されていません")
            return False

        for attempt in range(max_attempts):
            try:
                logger.info("再試行 %d/%d", attempt + 1, max_attempts)
                result = func()
                logger.info("再試行成功")
                return True
            except Exception as e:
                logger.warning("再試行失敗: %s", e)
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)  # 指数バックオフ

        return False

    def _strategy_fallback(
        self,
        error: Exception,
        context: Optional[Dict] = None,
        max_attempts: int = 3
    ) -> bool:
        """フォールバック戦略。"""
        fallback_func = context.get("fallback_func") if context else None
        if not fallback_func:
            logger.error("フォールバック戦略: フォールバック関数が指定されていません")
            return False

        try:
            logger.info("フォールバック関数を実行")
            result = fallback_func()
            logger.info("フォールバック成功")
            return True
        except Exception as e:
            logger.error("フォールバック失敗: %s", e)
            return False

    def _strategy_restart(
        self,
        error: Exception,
        context: Optional[Dict] = None,
        max_attempts: int = 3
    ) -> bool:
        """再起動戦略。"""
        restart_func = context.get("restart_func") if context else None
        if not restart_func:
            logger.error("再起動戦略: 再起動関数が指定されていません")
            return False

        try:
            logger.info("システムを再起動")
            result = restart_func()
            logger.info("再起動成功")
            return True
        except Exception as e:
            logger.error("再起動失敗: %s", e)
            return False

    def _load_recovery_history(self):
        """リカバリー履歴を読み込み。"""
        if os.path.exists(self.recovery_history_file):
            try:
                with open(self.recovery_history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recovery_actions = [
                        RecoveryAction(**action) for action in data
                    ]
                logger.info("リカバリー履歴を読み込み: %d件", len(self.recovery_actions))
            except Exception as e:
                logger.error("リカバリー履歴の読み込み失敗: %s", e)

    def _save_recovery_history(self):
        """リカバリー履歴を保存。"""
        try:
            with open(self.recovery_history_file, 'w', encoding='utf-8') as f:
                data = [asdict(action) for action in self.recovery_actions]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("リカバリー履歴の保存失敗: %s", e)

    def get_recovery_statistics(self) -> Dict:
        """リカバリー統計を取得。"""
        with self.lock:
            if not self.recovery_actions:
                return {
                    "total_recoveries": 0,
                    "successful_recoveries": 0,
                    "failed_recoveries": 0,
                    "success_rate": 0.0,
                    "by_strategy": {},
                    "by_error_type": {},
                }

            total = len(self.recovery_actions)
            successful = sum(1 for a in self.recovery_actions if a.success)
            failed = total - successful

            # 戦略別の集計
            by_strategy: Dict[str, Dict] = {}
            for action in self.recovery_actions:
                if action.strategy not in by_strategy:
                    by_strategy[action.strategy] = {"total": 0, "successful": 0}
                by_strategy[action.strategy]["total"] += 1
                if action.success:
                    by_strategy[action.strategy]["successful"] += 1

            # エラータイプ別の集計
            by_error_type: Dict[str, Dict] = {}
            for action in self.recovery_actions:
                if action.error_type not in by_error_type:
                    by_error_type[action.error_type] = {"total": 0, "successful": 0}
                by_error_type[action.error_type]["total"] += 1
                if action.success:
                    by_error_type[action.error_type]["successful"] += 1

            return {
                "total_recoveries": total,
                "successful_recoveries": successful,
                "failed_recoveries": failed,
                "success_rate": successful / total if total > 0 else 0.0,
                "by_strategy": by_strategy,
                "by_error_type": by_error_type,
            }

    def get_recent_actions(self, limit: int = 10) -> List[RecoveryAction]:
        """最近のリカバリーアクションを取得。"""
        with self.lock:
            return self.recovery_actions[-limit:]

    def clear_history(self):
        """履歴をクリア。"""
        with self.lock:
            self.recovery_actions.clear()
            self._save_recovery_history()
            logger.info("リカバリー履歴をクリア")


class CircuitBreaker:
    """サーキットブレーカーパターンの実装。"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.name = name

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
        self.lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """サーキットブレーカー経由で関数を呼び出し。"""
        with self.lock:
            if self.state == "open":
                # 回復タイムアウトをチェック
                if self._should_attempt_recovery():
                    self.state = "half-open"
                    logger.info("サーキットブレーカー %s: half-open に遷移", self.name)
                else:
                    raise Exception(f"サーキットブレーカー {self.name} が開いています")

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise

    def _should_attempt_recovery(self) -> bool:
        """回復を試みるべきかチェック。"""
        if not self.last_failure_time:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout_seconds

    def _on_success(self):
        """成功時の処理。"""
        self.failure_count = 0
        self.state = "closed"
        logger.debug("サーキットブレーカー %s: 成功", self.name)

    def _on_failure(self):
        """失敗時の処理。"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning("サーキットブレーカー %s: open に遷移", self.name)
        elif self.state == "half-open":
            self.state = "open"
            logger.warning("サーキットブレーカー %s: half-open から open に戻る", self.name)

    def get_state(self) -> str:
        """サーキットブレーカーの状態を取得。"""
        with self.lock:
            return self.state

    def reset(self):
        """サーキットブレーカーをリセット。"""
        with self.lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = "closed"
            logger.info("サーキットブレーカー %s: リセット", self.name)


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== RecoveryManager のテスト ===\n")

    # 1. RecoveryManager テスト
    print("1️⃣  RecoveryManager テスト:")
    manager = RecoveryManager()

    def test_func():
        return "成功"

    context = {"func": test_func}
    success = manager.attempt_recovery(
        ValueError("テストエラー"),
        RecoveryStrategy.RETRY,
        context
    )
    print(f"   リカバリー成功: {success}")

    stats = manager.get_recovery_statistics()
    print(f"   統計: {stats}")
    print("   ✅ RecoveryManager テスト成功\n")

    # 2. CircuitBreaker テスト
    print("2️⃣  CircuitBreaker テスト:")
    breaker = CircuitBreaker(failure_threshold=3, name="test_breaker")

    def failing_func():
        raise Exception("テストエラー")

    for i in range(5):
        try:
            breaker.call(failing_func)
        except Exception as e:
            print(f"   試行 {i+1}: {breaker.get_state()}")

    print("   ✅ CircuitBreaker テスト成功")
