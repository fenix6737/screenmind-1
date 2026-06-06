"""
ScreenMind - AIエージェント・オーケストレーター
複数のAIモデルが協力してタスクを解決する高度な推論エンジン。
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """タスクの種類。"""
    SIMPLE_QA = "simple_qa"  # 単純な質問応答
    ANALYSIS = "analysis"  # データ分析
    CODE_GENERATION = "code_generation"  # コード生成
    CREATIVE = "creative"  # 創造的なタスク
    RESEARCH = "research"  # リサーチ
    MULTI_STEP = "multi_step"  # 複数ステップのタスク


class AgentRole(Enum):
    """エージェントの役割。"""
    COORDINATOR = "coordinator"  # タスク調整役
    ANALYZER = "analyzer"  # 分析専門
    GENERATOR = "generator"  # 生成専門
    VALIDATOR = "validator"  # 検証役
    RESEARCHER = "researcher"  # リサーチ役


@dataclass
class Task:
    """タスクを表すクラス。"""
    task_id: str
    description: str
    task_type: TaskType
    priority: int = 1  # 1-10, 高いほど優先度高
    required_agents: List[AgentRole] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[str] = None
    sub_tasks: List["Task"] = field(default_factory=list)


@dataclass
class Agent:
    """AIエージェントを表すクラス。"""
    agent_id: str
    role: AgentRole
    model_id: str
    capabilities: List[str]  # 得意な分野
    performance_score: float = 0.0  # 過去のパフォーマンススコア
    is_active: bool = True
    last_used: Optional[str] = None


class AgentOrchestrator:
    """
    複数のAIエージェントを調整・管理するオーケストレーター。
    """

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
        self.execution_log: List[Dict] = []
        self._task_counter = 0

    def register_agent(
        self,
        agent_id: str,
        role: AgentRole,
        model_id: str,
        capabilities: List[str],
    ) -> bool:
        """エージェントを登録する。"""
        if agent_id in self.agents:
            logger.warning("エージェント %s は既に登録されています", agent_id)
            return False

        agent = Agent(
            agent_id=agent_id,
            role=role,
            model_id=model_id,
            capabilities=capabilities,
        )
        self.agents[agent_id] = agent
        logger.info("エージェントを登録: %s (%s)", agent_id, role.value)
        return True

    def get_agents_by_role(self, role: AgentRole) -> List[Agent]:
        """指定された役割のエージェントを取得する。"""
        return [a for a in self.agents.values() if a.role == role and a.is_active]

    def get_best_agent_for_task(self, task: Task) -> Optional[Agent]:
        """タスクに最適なエージェントを選択する。"""
        # 必要な役割のエージェントを取得
        candidates = []
        for required_role in task.required_agents:
            agents = self.get_agents_by_role(required_role)
            candidates.extend(agents)

        if not candidates:
            logger.warning("タスク %s に適したエージェントが見つかりません", task.task_id)
            return None

        # パフォーマンススコアが最も高いエージェントを選択
        best_agent = max(candidates, key=lambda a: a.performance_score)
        return best_agent

    def create_task(
        self,
        description: str,
        task_type: TaskType,
        priority: int = 1,
        required_agents: Optional[List[AgentRole]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """新しいタスクを作成する。"""
        self._task_counter += 1
        task_id = f"task_{self._task_counter}_{datetime.now().timestamp()}"

        task = Task(
            task_id=task_id,
            description=description,
            task_type=task_type,
            priority=priority,
            required_agents=required_agents or [],
            context=context or {},
        )

        self.tasks[task_id] = task
        logger.info("タスクを作成: %s (%s)", task_id, task_type.value)
        return task

    def decompose_task(self, task: Task) -> List[Task]:
        """複雑なタスクをサブタスクに分解する。"""
        if task.task_type != TaskType.MULTI_STEP:
            return [task]

        sub_tasks = []

        # タスク説明から自動的にサブタスクを生成
        # （実際の実装では、LLMを使用してタスク分解を行う）
        if "分析" in task.description:
            sub_tasks.append(
                self.create_task(
                    f"{task.description} - データ収集",
                    TaskType.ANALYSIS,
                    priority=task.priority,
                    required_agents=[AgentRole.ANALYZER],
                )
            )
            sub_tasks.append(
                self.create_task(
                    f"{task.description} - 分析実行",
                    TaskType.ANALYSIS,
                    priority=task.priority,
                    required_agents=[AgentRole.ANALYZER],
                )
            )
            sub_tasks.append(
                self.create_task(
                    f"{task.description} - 結果検証",
                    TaskType.ANALYSIS,
                    priority=task.priority,
                    required_agents=[AgentRole.VALIDATOR],
                )
            )

        task.sub_tasks = sub_tasks
        logger.info("タスクを分解: %d個のサブタスク", len(sub_tasks))
        return sub_tasks

    async def execute_task(
        self,
        task: Task,
        execute_fn: Callable,
    ) -> bool:
        """タスクを実行する。"""
        task.status = "in_progress"

        try:
            # 最適なエージェントを選択
            agent = self.get_best_agent_for_task(task)
            if not agent:
                task.status = "failed"
                logger.error("タスク実行失敗: エージェントが見つかりません")
                return False

            # タスクを実行
            logger.info("タスクを実行: %s (エージェント: %s)", task.task_id, agent.agent_id)
            result = await execute_fn(task, agent)

            task.result = result
            task.status = "completed"

            # エージェントのパフォーマンススコアを更新
            agent.performance_score = min(1.0, agent.performance_score + 0.1)
            agent.last_used = datetime.now().isoformat()

            # 実行ログを記録
            self.execution_log.append({
                "task_id": task.task_id,
                "agent_id": agent.agent_id,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
            })

            logger.info("タスク完了: %s", task.task_id)
            return True

        except Exception as e:
            task.status = "failed"
            logger.error("タスク実行エラー: %s", e)

            self.execution_log.append({
                "task_id": task.task_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })

            return False

    async def execute_multi_step_task(
        self,
        task: Task,
        execute_fn: Callable,
    ) -> bool:
        """複数ステップのタスクを実行する。"""
        # タスクを分解
        sub_tasks = self.decompose_task(task)

        # 各サブタスクを順序に実行
        for sub_task in sub_tasks:
            success = await self.execute_task(sub_task, execute_fn)
            if not success:
                task.status = "failed"
                logger.error("サブタスク実行失敗: %s", sub_task.task_id)
                return False

        task.status = "completed"
        task.result = " ".join([st.result for st in sub_tasks if st.result])
        return True

    def get_task_status(self, task_id: str) -> Optional[str]:
        """タスクのステータスを取得する。"""
        task = self.tasks.get(task_id)
        return task.status if task else None

    def get_execution_statistics(self) -> Dict:
        """実行統計を取得する。"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == "completed")
        failed_tasks = sum(1 for t in self.tasks.values() if t.status == "failed")

        agent_stats = {}
        for agent_id, agent in self.agents.items():
            agent_tasks = [
                log for log in self.execution_log
                if log["agent_id"] == agent_id
            ]
            success_count = sum(1 for log in agent_tasks if log["status"] == "success")
            agent_stats[agent_id] = {
                "role": agent.role.value,
                "total_tasks": len(agent_tasks),
                "success_count": success_count,
                "performance_score": agent.performance_score,
            }

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / max(total_tasks, 1),
            "agent_statistics": agent_stats,
        }

    def export_execution_log(self) -> str:
        """実行ログをJSON形式でエクスポートする。"""
        return json.dumps(self.execution_log, ensure_ascii=False, indent=2)

    def get_agent_recommendations(self, task: Task) -> List[Dict]:
        """タスクに対する推奨エージェントを取得する。"""
        recommendations = []

        for agent in self.agents.values():
            if not agent.is_active:
                continue

            # タスク型とエージェントの能力をマッチング
            match_score = 0.0

            # 役割のマッチング
            if agent.role in task.required_agents:
                match_score += 0.5

            # 能力のマッチング
            for capability in agent.capabilities:
                if capability in task.description.lower():
                    match_score += 0.2

            # パフォーマンススコアを加味
            match_score += agent.performance_score * 0.3

            if match_score > 0:
                recommendations.append({
                    "agent_id": agent.agent_id,
                    "role": agent.role.value,
                    "model_id": agent.model_id,
                    "match_score": min(1.0, match_score),
                })

        # スコアでソート
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return recommendations


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== エージェント・オーケストレーターのテスト ===\n")

    orchestrator = AgentOrchestrator()

    # エージェントを登録
    print("1️⃣  エージェントを登録:")
    orchestrator.register_agent(
        "agent_1",
        AgentRole.ANALYZER,
        "gemma-4-12b-iq4",
        ["分析", "データ処理"],
    )
    orchestrator.register_agent(
        "agent_2",
        AgentRole.GENERATOR,
        "gemma-4-12b-iq4",
        ["コード生成", "テキスト生成"],
    )
    orchestrator.register_agent(
        "agent_3",
        AgentRole.VALIDATOR,
        "gemma-4-12b-iq4",
        ["検証", "品質チェック"],
    )
    print("   ✅ 3個のエージェントを登録\n")

    # タスクを作成
    print("2️⃣  タスクを作成:")
    task = orchestrator.create_task(
        "Pythonのデータ分析スクリプトを作成してください",
        TaskType.CODE_GENERATION,
        priority=5,
        required_agents=[AgentRole.GENERATOR, AgentRole.VALIDATOR],
    )
    print(f"   タスクID: {task.task_id}\n")

    # 推奨エージェントを取得
    print("3️⃣  推奨エージェント:")
    recommendations = orchestrator.get_agent_recommendations(task)
    for rec in recommendations:
        print(f"   {rec['agent_id']}: スコア {rec['match_score']:.2f}")

    # 統計情報
    print("\n4️⃣  統計情報:")
    stats = orchestrator.get_execution_statistics()
    print(f"   総タスク数: {stats['total_tasks']}")
    print(f"   完了タスク数: {stats['completed_tasks']}")
