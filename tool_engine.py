"""
ScreenMind - ツール実行エンジン
外部ツール（Web検索、計算、コード実行）と連携する。
"""

import json
import logging
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """ツールの種類。"""
    WEB_SEARCH = "web_search"
    CALCULATOR = "calculator"
    CODE_EXECUTOR = "code_executor"
    FILE_READER = "file_reader"
    WEATHER = "weather"
    TRANSLATION = "translation"
    CUSTOM = "custom"


@dataclass
class ToolResult:
    """ツール実行結果。"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """辞書に変換する。"""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp,
        }


class Tool(ABC):
    """ツールの基底クラス。"""

    def __init__(self, name: str, tool_type: ToolType):
        self.name = name
        self.tool_type = tool_type
        self.is_available = True

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """ツールを実行する。"""
        pass

    @abstractmethod
    def validate_input(self, **kwargs) -> bool:
        """入力を検証する。"""
        pass


class CalculatorTool(Tool):
    """計算ツール。"""

    def __init__(self):
        super().__init__("Calculator", ToolType.CALCULATOR)

    def validate_input(self, expression: str) -> bool:
        """数式の妥当性を確認する。"""
        # 危険な文字をチェック
        dangerous_chars = ["__", "import", "exec", "eval", "open"]
        return not any(char in expression for char in dangerous_chars)

    def execute(self, expression: str) -> ToolResult:
        """数式を計算する。"""
        import time
        start_time = time.time()

        try:
            if not self.validate_input(expression):
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    result=None,
                    error="危険な式が含まれています",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # 安全な計算を実行
            result = eval(expression, {"__builtins__": {}}, {})
            return ToolResult(
                tool_name=self.name,
                success=True,
                result=result,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error("計算エラー: %s", e)
            return ToolResult(
                tool_name=self.name,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )


class CodeExecutorTool(Tool):
    """コード実行ツール（サンドボックス環境）。"""

    def __init__(self, timeout_seconds: int = 5):
        super().__init__("CodeExecutor", ToolType.CODE_EXECUTOR)
        self.timeout_seconds = timeout_seconds

    def validate_input(self, code: str) -> bool:
        """コードの妥当性を確認する。"""
        # 危険な操作をチェック
        dangerous_keywords = [
            "import os",
            "import sys",
            "open(",
            "exec(",
            "eval(",
            "__import__",
        ]
        return not any(keyword in code for keyword in dangerous_keywords)

    def execute(self, code: str, language: str = "python") -> ToolResult:
        """コードを実行する。"""
        import time
        start_time = time.time()

        try:
            if not self.validate_input(code):
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    result=None,
                    error="危険な操作が含まれています",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            if language == "python":
                # Python コードを実行
                result = subprocess.run(
                    ["python3", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                )

                if result.returncode == 0:
                    return ToolResult(
                        tool_name=self.name,
                        success=True,
                        result=result.stdout.strip(),
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )
                else:
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        result=None,
                        error=result.stderr.strip(),
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    result=None,
                    error=f"サポートされていない言語: {language}",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

        except subprocess.TimeoutExpired:
            logger.error("コード実行タイムアウト")
            return ToolResult(
                tool_name=self.name,
                success=False,
                result=None,
                error=f"実行時間が {self.timeout_seconds} 秒を超えました",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error("コード実行エラー: %s", e)
            return ToolResult(
                tool_name=self.name,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )


class FileReaderTool(Tool):
    """ファイル読み込みツール（安全なディレクトリのみ）。"""

    def __init__(self, allowed_dirs: Optional[List[str]] = None):
        super().__init__("FileReader", ToolType.FILE_READER)
        self.allowed_dirs = allowed_dirs or ["./", "/tmp/"]

    def validate_input(self, file_path: str) -> bool:
        """ファイルパスの妥当性を確認する。"""
        import os
        # パストラバーサル攻撃をチェック
        if ".." in file_path:
            return False
        # 許可されたディレクトリ内か確認
        abs_path = os.path.abspath(file_path)
        return any(abs_path.startswith(os.path.abspath(d)) for d in self.allowed_dirs)

    def execute(self, file_path: str) -> ToolResult:
        """ファイルを読み込む。"""
        import time
        start_time = time.time()

        try:
            if not self.validate_input(file_path):
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    result=None,
                    error="許可されていないファイルパス",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return ToolResult(
                tool_name=self.name,
                success=True,
                result=content,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error("ファイル読み込みエラー: %s", e)
            return ToolResult(
                tool_name=self.name,
                success=False,
                result=None,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )


class ToolEngine:
    """ツール実行エンジン。"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.execution_history: List[ToolResult] = []
        self._register_default_tools()

    def _register_default_tools(self):
        """デフォルトツールを登録する。"""
        self.register_tool(CalculatorTool())
        self.register_tool(CodeExecutorTool())
        self.register_tool(FileReaderTool())
        logger.info("デフォルトツールを登録: %d個", len(self.tools))

    def register_tool(self, tool: Tool) -> bool:
        """ツールを登録する。"""
        if tool.name in self.tools:
            logger.warning("ツール %s は既に登録されています", tool.name)
            return False

        self.tools[tool.name] = tool
        logger.info("ツールを登録: %s", tool.name)
        return True

    def get_available_tools(self) -> List[Dict]:
        """利用可能なツールを取得する。"""
        return [
            {
                "name": tool.name,
                "type": tool.tool_type.value,
                "available": tool.is_available,
            }
            for tool in self.tools.values()
        ]

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """ツールを実行する。"""
        if tool_name not in self.tools:
            logger.error("ツール %s が見つかりません", tool_name)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"ツール '{tool_name}' が見つかりません",
            )

        tool = self.tools[tool_name]
        if not tool.is_available:
            logger.warning("ツール %s は利用不可です", tool_name)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"ツール '{tool_name}' は利用不可です",
            )

        result = tool.execute(**kwargs)
        self.execution_history.append(result)
        return result

    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """実行履歴を取得する。"""
        return [r.to_dict() for r in self.execution_history[-limit:]]

    def get_tool_statistics(self) -> Dict:
        """ツール使用統計を取得する。"""
        stats = {}
        for tool_name in self.tools:
            tool_executions = [r for r in self.execution_history if r.tool_name == tool_name]
            success_count = sum(1 for r in tool_executions if r.success)
            avg_time = (
                sum(r.execution_time_ms for r in tool_executions) / len(tool_executions)
                if tool_executions
                else 0
            )

            stats[tool_name] = {
                "total_executions": len(tool_executions),
                "success_count": success_count,
                "success_rate": success_count / len(tool_executions) if tool_executions else 0,
                "avg_execution_time_ms": avg_time,
            }

        return stats


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== ツール実行エンジンのテスト ===\n")

    engine = ToolEngine()

    # 利用可能なツール
    print("1️⃣  利用可能なツール:")
    for tool in engine.get_available_tools():
        print(f"   - {tool['name']} ({tool['type']})")

    # 計算ツール
    print("\n2️⃣  計算ツール:")
    result = engine.execute_tool("Calculator", expression="2 + 2 * 3")
    print(f"   式: 2 + 2 * 3")
    print(f"   結果: {result.result}")
    print(f"   実行時間: {result.execution_time_ms:.2f}ms")

    # コード実行ツール
    print("\n3️⃣  コード実行ツール:")
    result = engine.execute_tool(
        "CodeExecutor",
        code="print('Hello from ScreenMind!')",
        language="python",
    )
    print(f"   結果: {result.result}")

    # 統計情報
    print("\n4️⃣  統計情報:")
    stats = engine.get_tool_statistics()
    for tool_name, stat in stats.items():
        print(f"   {tool_name}:")
        print(f"     実行回数: {stat['total_executions']}")
        print(f"     成功率: {stat['success_rate']:.1%}")
