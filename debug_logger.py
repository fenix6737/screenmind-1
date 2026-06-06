"""
ScreenMind v4.0 - 詳細なロギングとデバッグツール
構造化ログ、パフォーマンスプロファイリング、エラートレース。
"""

import functools
import json
import logging
import logging.handlers
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

# ===== 構造化ログフォーマッター =====

class StructuredLogFormatter(logging.Formatter):
    """JSON形式の構造化ログフォーマッター。"""

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式でフォーマット。"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 例外情報を含める
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exc(),
            }

        # 追加情報を含める
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


class DebugLogger:
    """詳細なデバッグロギング機能を提供。"""

    def __init__(self, name: str = "screenmind", log_dir: str = "logs"):
        self.name = name
        self.log_dir = log_dir
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # ログディレクトリを作成
        Path(log_dir).mkdir(exist_ok=True)

        # ハンドラーを設定
        self._setup_handlers()

    def _setup_handlers(self):
        """ログハンドラーを設定。"""
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # ファイルハンドラー（全ログ）
        all_log_file = os.path.join(self.log_dir, "screenmind.log")
        file_handler = logging.handlers.RotatingFileHandler(
            all_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # JSON構造化ログファイルハンドラー
        json_log_file = os.path.join(self.log_dir, "screenmind_structured.jsonl")
        json_handler = logging.handlers.RotatingFileHandler(
            json_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        json_handler.setLevel(logging.DEBUG)
        json_formatter = StructuredLogFormatter()
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)

        # エラーログファイルハンドラー
        error_log_file = os.path.join(self.log_dir, "screenmind_errors.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s'
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)

    def debug(self, message: str, **kwargs):
        """デバッグログ。"""
        self.logger.debug(message, extra={"extra_data": kwargs} if kwargs else None)

    def info(self, message: str, **kwargs):
        """情報ログ。"""
        self.logger.info(message, extra={"extra_data": kwargs} if kwargs else None)

    def warning(self, message: str, **kwargs):
        """警告ログ。"""
        self.logger.warning(message, extra={"extra_data": kwargs} if kwargs else None)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """エラーログ。"""
        self.logger.error(message, exc_info=exc_info, extra={"extra_data": kwargs} if kwargs else None)

    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """致命的エラーログ。"""
        self.logger.critical(message, exc_info=exc_info, extra={"extra_data": kwargs} if kwargs else None)


# ===== パフォーマンスプロファイラー =====

class PerformanceProfiler:
    """パフォーマンスプロファイリング機能。"""

    def __init__(self, logger: DebugLogger):
        self.logger = logger
        self.measurements: Dict[str, List[float]] = {}
        self.lock = __import__('threading').RLock()

    def measure(self, name: str):
        """パフォーマンス計測デコレーター。"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    elapsed = time.time() - start_time
                    self._record_measurement(name, elapsed)
                    self.logger.debug(
                        f"{name} 実行時間: {elapsed:.3f}秒",
                        function=name,
                        elapsed_seconds=elapsed
                    )
            return wrapper
        return decorator

    def _record_measurement(self, name: str, elapsed: float):
        """計測結果を記録。"""
        with self.lock:
            if name not in self.measurements:
                self.measurements[name] = []
            self.measurements[name].append(elapsed)

    def get_statistics(self, name: str) -> Optional[Dict]:
        """統計情報を取得。"""
        with self.lock:
            if name not in self.measurements or not self.measurements[name]:
                return None

            measurements = self.measurements[name]
            return {
                "count": len(measurements),
                "min": min(measurements),
                "max": max(measurements),
                "avg": sum(measurements) / len(measurements),
                "total": sum(measurements),
            }

    def get_all_statistics(self) -> Dict[str, Dict]:
        """すべての統計情報を取得。"""
        with self.lock:
            return {
                name: self.get_statistics(name)
                for name in self.measurements
            }

    def print_report(self):
        """統計レポートを出力。"""
        stats = self.get_all_statistics()
        self.logger.info("=== パフォーマンスレポート ===")
        for name, stat in stats.items():
            if stat:
                self.logger.info(
                    f"{name}: 実行 {stat['count']}回, "
                    f"平均 {stat['avg']:.3f}秒, "
                    f"最小 {stat['min']:.3f}秒, "
                    f"最大 {stat['max']:.3f}秒"
                )


# ===== エラートレース =====

class ErrorTracer:
    """エラーの詳細なトレース機能。"""

    def __init__(self, logger: DebugLogger):
        self.logger = logger
        self.error_stack: List[Dict] = []
        self.lock = __import__('threading').RLock()

    def trace_exception(self, exc: Exception, context: Optional[Dict] = None):
        """例外をトレース。"""
        with self.lock:
            trace_info = {
                "timestamp": datetime.now().isoformat(),
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc(),
                "context": context or {},
            }
            self.error_stack.append(trace_info)

            self.logger.error(
                f"例外をトレース: {type(exc).__name__}",
                exc_info=True,
                context=context
            )

    def get_error_history(self, limit: int = 10) -> List[Dict]:
        """エラー履歴を取得。"""
        with self.lock:
            return self.error_stack[-limit:]

    def export_error_report(self, filename: str = "error_report.json"):
        """エラーレポートをエクスポート。"""
        with self.lock:
            report = {
                "export_timestamp": datetime.now().isoformat(),
                "total_errors": len(self.error_stack),
                "errors": self.error_stack,
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            self.logger.info(f"エラーレポートをエクスポート: {filename}")


# ===== デバッグコンソール =====

class DebugConsole:
    """インタラクティブなデバッグコンソール。"""

    def __init__(self, logger: DebugLogger, profiler: PerformanceProfiler):
        self.logger = logger
        self.profiler = profiler
        self.commands = {
            "stats": self._cmd_stats,
            "profile": self._cmd_profile,
            "help": self._cmd_help,
            "quit": self._cmd_quit,
        }

    def run(self):
        """デバッグコンソールを実行。"""
        print("=== ScreenMind デバッグコンソール ===")
        print("'help' でコマンド一覧を表示します")

        while True:
            try:
                command = input("\n> ").strip()
                if not command:
                    continue

                parts = command.split()
                cmd = parts[0]

                if cmd in self.commands:
                    self.commands[cmd](*parts[1:])
                else:
                    print(f"未知のコマンド: {cmd}")
            except KeyboardInterrupt:
                print("\n終了します")
                break
            except Exception as e:
                print(f"エラー: {e}")

    def _cmd_stats(self, *args):
        """統計情報を表示。"""
        stats = self.profiler.get_all_statistics()
        print("\n=== パフォーマンス統計 ===")
        for name, stat in stats.items():
            if stat:
                print(f"{name}:")
                print(f"  実行回数: {stat['count']}")
                print(f"  平均時間: {stat['avg']:.3f}秒")
                print(f"  最小時間: {stat['min']:.3f}秒")
                print(f"  最大時間: {stat['max']:.3f}秒")

    def _cmd_profile(self, *args):
        """プロファイル情報を表示。"""
        self.profiler.print_report()

    def _cmd_help(self, *args):
        """ヘルプを表示。"""
        print("\n=== コマンド一覧 ===")
        for cmd in self.commands:
            print(f"  {cmd}")

    def _cmd_quit(self, *args):
        """終了。"""
        raise KeyboardInterrupt()


# ===== 単体テスト =====
if __name__ == "__main__":
    print("=== DebugLogger のテスト ===\n")

    # 1. DebugLogger テスト
    print("1️⃣  DebugLogger テスト:")
    debug_logger = DebugLogger()
    debug_logger.info("テスト情報ログ", key="value")
    debug_logger.warning("テスト警告ログ")
    print("   ✅ DebugLogger テスト成功\n")

    # 2. PerformanceProfiler テスト
    print("2️⃣  PerformanceProfiler テスト:")
    profiler = PerformanceProfiler(debug_logger)

    @profiler.measure("test_function")
    def test_func():
        time.sleep(0.1)
        return "result"

    for _ in range(3):
        test_func()

    stats = profiler.get_statistics("test_function")
    print(f"   統計: {stats}")
    print("   ✅ PerformanceProfiler テスト成功\n")

    # 3. ErrorTracer テスト
    print("3️⃣  ErrorTracer テスト:")
    tracer = ErrorTracer(debug_logger)
    try:
        raise ValueError("テストエラー")
    except Exception as e:
        tracer.trace_exception(e, {"context": "test"})

    history = tracer.get_error_history()
    print(f"   エラー履歴: {len(history)}件")
    print("   ✅ ErrorTracer テスト成功")
