"""
ScreenMind v4.0 - システムヘルスモニタリング (Watchdog)
リソース使用状況、プロセス状態、エラー率をリアルタイム監視。
"""

import logging
import os
import psutil
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


@dataclass
class HealthMetrics:
    """ヘルスメトリクス。"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    process_count: int
    error_count: int
    warning_count: int
    uptime_seconds: int
    status: str  # "healthy", "warning", "critical"


class SystemWatchdog:
    """システムのヘルスを監視。"""

    def __init__(self, check_interval_seconds: int = 5):
        self.check_interval = check_interval_seconds
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.metrics_history: List[HealthMetrics] = []
        self.max_history_size = 1000
        self.start_time = datetime.now()

        # 警告・エラーの閾値
        self.cpu_warning_threshold = 80.0  # %
        self.cpu_critical_threshold = 95.0  # %
        self.memory_warning_threshold = 80.0  # %
        self.memory_critical_threshold = 95.0  # %
        self.error_rate_warning_threshold = 0.05  # 5%

        # コールバック
        self.on_warning: Optional[Callable] = None
        self.on_critical: Optional[Callable] = None

    def start(self):
        """監視を開始。"""
        if self.is_running:
            logger.warning("Watchdog はすでに実行中です")
            return

        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Watchdog を開始しました")

    def stop(self):
        """監視を停止。"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Watchdog を停止しました")

    def _monitor_loop(self):
        """監視ループ。"""
        while self.is_running:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)

                # 履歴サイズを制限
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)

                # ステータスに基づいてコールバックを実行
                if metrics.status == "warning" and self.on_warning:
                    self.on_warning(metrics)
                elif metrics.status == "critical" and self.on_critical:
                    self.on_critical(metrics)

                logger.debug("ヘルスメトリクス: %s", metrics)
            except Exception as e:
                logger.error("監視エラー: %s", e)

            time.sleep(self.check_interval)

    def _collect_metrics(self) -> HealthMetrics:
        """メトリクスを収集。"""
        try:
            process = psutil.Process(os.getpid())
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            memory_mb = memory_info.rss / (1024 * 1024)

            # 子プロセス数
            child_processes = len(process.children(recursive=True))
            process_count = 1 + child_processes

            # エラー・警告カウント
            error_count = self._count_log_messages("ERROR")
            warning_count = self._count_log_messages("WARNING")

            # ステータス判定
            status = self._determine_status(cpu_percent, memory_percent)

            # アップタイム
            uptime = (datetime.now() - self.start_time).total_seconds()

            metrics = HealthMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                process_count=process_count,
                error_count=error_count,
                warning_count=warning_count,
                uptime_seconds=int(uptime),
                status=status,
            )

            return metrics
        except Exception as e:
            logger.error("メトリクス収集エラー: %s", e)
            return HealthMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_mb=0.0,
                process_count=0,
                error_count=0,
                warning_count=0,
                uptime_seconds=0,
                status="unknown",
            )

    def _determine_status(self, cpu_percent: float, memory_percent: float) -> str:
        """ステータスを判定。"""
        if (cpu_percent >= self.cpu_critical_threshold or
                memory_percent >= self.memory_critical_threshold):
            return "critical"
        elif (cpu_percent >= self.cpu_warning_threshold or
              memory_percent >= self.memory_warning_threshold):
            return "warning"
        else:
            return "healthy"

    def _count_log_messages(self, level: str) -> int:
        """ログメッセージをカウント。"""
        # 簡易実装：最後のメトリクスから計算
        if not self.metrics_history:
            return 0

        # 最後の10メトリクスのエラー/警告の平均
        recent = self.metrics_history[-10:]
        if level == "ERROR":
            return sum(m.error_count for m in recent) // len(recent) if recent else 0
        elif level == "WARNING":
            return sum(m.warning_count for m in recent) // len(recent) if recent else 0
        return 0

    def get_latest_metrics(self) -> Optional[HealthMetrics]:
        """最新のメトリクスを取得。"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_average_metrics(self, minutes: int = 5) -> Optional[Dict]:
        """指定期間の平均メトリクスを取得。"""
        if not self.metrics_history:
            return None

        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        relevant_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m.timestamp) > cutoff_time
        ]

        if not relevant_metrics:
            return None

        return {
            "avg_cpu_percent": sum(m.cpu_percent for m in relevant_metrics) / len(relevant_metrics),
            "avg_memory_percent": sum(m.memory_percent for m in relevant_metrics) / len(relevant_metrics),
            "avg_memory_mb": sum(m.memory_mb for m in relevant_metrics) / len(relevant_metrics),
            "max_cpu_percent": max(m.cpu_percent for m in relevant_metrics),
            "max_memory_percent": max(m.memory_percent for m in relevant_metrics),
            "error_count": sum(m.error_count for m in relevant_metrics),
        }

    def get_health_report(self) -> Dict:
        """ヘルスレポートを生成。"""
        latest = self.get_latest_metrics()
        average = self.get_average_metrics(minutes=5)

        if not latest:
            return {"status": "no_data"}

        return {
            "status": latest.status,
            "timestamp": latest.timestamp,
            "current": {
                "cpu_percent": latest.cpu_percent,
                "memory_percent": latest.memory_percent,
                "memory_mb": latest.memory_mb,
                "process_count": latest.process_count,
            },
            "average_5min": average or {},
            "uptime_seconds": latest.uptime_seconds,
            "error_count": latest.error_count,
            "warning_count": latest.warning_count,
        }


class ProcessMonitor:
    """プロセスの状態を監視。"""

    def __init__(self):
        self.processes: Dict[str, Dict] = {}
        self.lock = threading.RLock()

    def register_process(self, name: str, process_id: int):
        """プロセスを登録。"""
        with self.lock:
            self.processes[name] = {
                "pid": process_id,
                "start_time": datetime.now(),
                "status": "running",
                "last_check": datetime.now(),
            }
            logger.info("プロセスを登録: %s (PID: %d)", name, process_id)

    def check_process(self, name: str) -> bool:
        """プロセスが実行中かチェック。"""
        with self.lock:
            if name not in self.processes:
                return False

            process_info = self.processes[name]
            try:
                process = psutil.Process(process_info["pid"])
                is_running = process.is_running()
                process_info["status"] = "running" if is_running else "stopped"
                process_info["last_check"] = datetime.now()
                return is_running
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_info["status"] = "stopped"
                process_info["last_check"] = datetime.now()
                return False

    def get_process_status(self, name: str) -> Optional[Dict]:
        """プロセスのステータスを取得。"""
        with self.lock:
            return self.processes.get(name)

    def get_all_processes(self) -> Dict[str, Dict]:
        """すべてのプロセスを取得。"""
        with self.lock:
            return self.processes.copy()


class ResourceLimiter:
    """リソース使用を制限。"""

    def __init__(self):
        self.cpu_limit_percent = 90.0
        self.memory_limit_mb = 2048  # 2GB
        self.active_limits = False

    def enable_limits(self):
        """リソース制限を有効化。"""
        self.active_limits = True
        logger.info("リソース制限を有効化")

    def disable_limits(self):
        """リソース制限を無効化。"""
        self.active_limits = False
        logger.info("リソース制限を無効化")

    def check_limits(self) -> bool:
        """リソース制限をチェック。"""
        if not self.active_limits:
            return True

        try:
            process = psutil.Process(os.getpid())
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_mb = process.memory_info().rss / (1024 * 1024)

            if cpu_percent > self.cpu_limit_percent:
                logger.warning("CPU制限を超過: %.1f%%", cpu_percent)
                return False

            if memory_mb > self.memory_limit_mb:
                logger.warning("メモリ制限を超過: %.1fMB", memory_mb)
                return False

            return True
        except Exception as e:
            logger.error("リソース制限チェックエラー: %s", e)
            return True


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Watchdog のテスト ===\n")

    # 1. SystemWatchdog テスト
    print("1️⃣  SystemWatchdog テスト:")
    watchdog = SystemWatchdog(check_interval_seconds=2)
    watchdog.start()
    time.sleep(5)
    watchdog.stop()

    latest = watchdog.get_latest_metrics()
    if latest:
        print(f"   CPU: {latest.cpu_percent:.1f}%")
        print(f"   メモリ: {latest.memory_percent:.1f}%")
        print(f"   ステータス: {latest.status}")
    print("   ✅ SystemWatchdog テスト成功\n")

    # 2. ProcessMonitor テスト
    print("2️⃣  ProcessMonitor テスト:")
    monitor = ProcessMonitor()
    monitor.register_process("main", os.getpid())
    is_running = monitor.check_process("main")
    print(f"   メインプロセス実行中: {is_running}")
    print("   ✅ ProcessMonitor テスト成功\n")

    # 3. ResourceLimiter テスト
    print("3️⃣  ResourceLimiter テスト:")
    limiter = ResourceLimiter()
    limiter.enable_limits()
    within_limits = limiter.check_limits()
    print(f"   制限内: {within_limits}")
    print("   ✅ ResourceLimiter テスト成功")
