"""
ScreenMind - モデル設定管理モジュール
複数のLLMモデルを定義・管理し、JSON形式で永続化する。
"""

import json
import logging
import os
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """モデルの種類を定義する列挙型。"""
    CONVERSATION = "conversation"    # 会話・雑談用
    ANALYSIS = "analysis"            # 分析・思考用
    CODING = "coding"                # コード生成・デバッグ用
    FAST = "fast"                    # 高速応答・軽量用
    VISION = "vision"                # 画像解析・マルチモーダル用


class ModelProvider(Enum):
    """モデルの提供元を定義する列挙型。"""
    LOCAL_LLAMA = "local_llama"      # llama.cpp（ローカル）
    OPENAI = "openai"                # OpenAI API
    ANTHROPIC = "anthropic"          # Claude API
    GOOGLE = "google"                # Google Gemini API
    OLLAMA = "ollama"                # Ollama（ローカル）


@dataclass
class ModelConfig:
    """
    単一のLLMモデルの設定情報。
    """
    # 基本情報
    id: str                           # モデルの一意識別子（例: "gemma-4-12b"）
    name: str                         # 表示名（例: "Gemma 4 12B"）
    provider: ModelProvider           # 提供元
    model_type: ModelType             # モデルの用途
    description: str = ""             # 説明

    # 接続設定
    endpoint_url: str = ""            # API エンドポイント（例: http://localhost:8080/v1/chat/completions）
    api_key: Optional[str] = None     # APIキー（必要な場合）
    model_name: str = ""              # モデル名（APIに送信する名前）

    # パフォーマンス設定
    max_tokens: int = 1024            # 最大トークン数
    temperature: float = 0.7          # 温度（創造性）
    context_size: int = 4096          # コンテキストサイズ
    avg_tokens_per_second: float = 60.0  # 平均トークン/秒

    # リソース要件
    required_vram_gb: float = 8.0     # 必要VRAM（GB）
    is_multimodal: bool = False       # 画像解析対応か
    supports_streaming: bool = True   # ストリーミング対応か

    # 状態管理
    is_enabled: bool = True           # 有効か
    priority: int = 0                 # 優先度（高いほど優先）
    tags: List[str] = field(default_factory=list)  # タグ（検索用）

    # メトリクス（実行時に更新）
    success_count: int = 0            # 成功回数
    error_count: int = 0              # エラー回数
    total_tokens_used: int = 0        # 使用トークン総数
    last_used_at: Optional[str] = None  # 最後に使用した時刻

    def to_dict(self) -> Dict:
        """辞書に変換する。"""
        data = asdict(self)
        data['provider'] = self.provider.value
        data['model_type'] = self.model_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "ModelConfig":
        """辞書から復元する。"""
        data = data.copy()
        data['provider'] = ModelProvider(data['provider'])
        data['model_type'] = ModelType(data['model_type'])
        return cls(**data)

    @property
    def success_rate(self) -> float:
        """成功率を計算する（0.0〜1.0）。"""
        total = self.success_count + self.error_count
        if total == 0:
            return 1.0
        return self.success_count / total

    def __str__(self) -> str:
        return f"{self.name} ({self.provider.value})"


class ModelConfigManager:
    """
    複数のモデル設定を管理するクラス。
    JSON形式で設定を保存・ロードする。
    """

    def __init__(self, config_file: str = "models_config.json"):
        self.config_file = config_file
        self.models: Dict[str, ModelConfig] = {}
        self._load_or_create_default()

    def _load_or_create_default(self):
        """設定ファイルをロード、なければデフォルト設定を作成する。"""
        if os.path.exists(self.config_file):
            self.load_from_file()
        else:
            self._create_default_models()
            self.save_to_file()

    def _create_default_models(self):
        """デフォルトモデル設定を作成する。"""
        default_models = [
            # Gemma 4 12B (ローカル・マルチモーダル)
            ModelConfig(
                id="gemma-4-12b-iq4",
                name="Gemma 4 12B (IQ4)",
                provider=ModelProvider.LOCAL_LLAMA,
                model_type=ModelType.VISION,
                description="画像解析対応・バランス型",
                endpoint_url="http://localhost:8080/v1/chat/completions",
                model_name="gemma-4-12b-iq4_xs",
                max_tokens=2048,
                context_size=4096,
                avg_tokens_per_second=60.0,
                required_vram_gb=8.0,
                is_multimodal=True,
                priority=100,
                tags=["local", "multimodal", "balanced"],
            ),
            # Mistral 7B (ローカル・軽量)
            ModelConfig(
                id="mistral-7b",
                name="Mistral 7B",
                provider=ModelProvider.LOCAL_LLAMA,
                model_type=ModelType.FAST,
                description="高速応答・軽量",
                endpoint_url="http://localhost:8080/v1/chat/completions",
                model_name="mistral-7b-instruct",
                max_tokens=1024,
                context_size=8192,
                avg_tokens_per_second=100.0,
                required_vram_gb=4.0,
                is_multimodal=False,
                priority=80,
                tags=["local", "fast", "lightweight"],
            ),
            # Llama 2 13B (ローカル・高性能)
            ModelConfig(
                id="llama2-13b",
                name="Llama 2 13B",
                provider=ModelProvider.LOCAL_LLAMA,
                model_type=ModelType.ANALYSIS,
                description="詳細分析・思考用",
                endpoint_url="http://localhost:8080/v1/chat/completions",
                model_name="llama-2-13b-chat",
                max_tokens=2048,
                context_size=4096,
                avg_tokens_per_second=50.0,
                required_vram_gb=12.0,
                is_multimodal=False,
                priority=90,
                tags=["local", "analysis", "powerful"],
            ),
            # OpenAI GPT-4 (リモート)
            ModelConfig(
                id="gpt-4",
                name="GPT-4",
                provider=ModelProvider.OPENAI,
                model_type=ModelType.ANALYSIS,
                description="高精度分析（クラウド）",
                endpoint_url="https://api.openai.com/v1/chat/completions",
                api_key=os.getenv("OPENAI_API_KEY", ""),
                model_name="gpt-4",
                max_tokens=2048,
                context_size=8192,
                avg_tokens_per_second=40.0,
                required_vram_gb=0.0,
                is_multimodal=True,
                is_enabled=bool(os.getenv("OPENAI_API_KEY")),
                priority=110,
                tags=["remote", "powerful", "multimodal"],
            ),
        ]

        for model in default_models:
            self.add_model(model)

    def add_model(self, model: ModelConfig) -> bool:
        """モデルを追加する。"""
        if model.id in self.models:
            logger.warning("モデル %s は既に存在します", model.id)
            return False
        self.models[model.id] = model
        logger.info("モデルを追加: %s", model.id)
        return True

    def remove_model(self, model_id: str) -> bool:
        """モデルを削除する。"""
        if model_id not in self.models:
            logger.warning("モデル %s は見つかりません", model_id)
            return False
        del self.models[model_id]
        logger.info("モデルを削除: %s", model_id)
        return True

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """IDでモデルを取得する。"""
        return self.models.get(model_id)

    def get_models_by_type(self, model_type: ModelType) -> List[ModelConfig]:
        """用途別にモデルを取得する。"""
        return [m for m in self.models.values() if m.model_type == model_type]

    def get_enabled_models(self) -> List[ModelConfig]:
        """有効なモデルのみを取得する。"""
        return [m for m in self.models.values() if m.is_enabled]

    def get_multimodal_models(self) -> List[ModelConfig]:
        """画像解析対応モデルを取得する。"""
        return [m for m in self.models.values() if m.is_multimodal and m.is_enabled]

    def get_fastest_model(self) -> Optional[ModelConfig]:
        """最速のモデルを取得する。"""
        enabled = self.get_enabled_models()
        if not enabled:
            return None
        return max(enabled, key=lambda m: m.avg_tokens_per_second)

    def get_best_model_for_type(self, model_type: ModelType) -> Optional[ModelConfig]:
        """用途に最適なモデルを取得する（優先度順）。"""
        candidates = [
            m for m in self.models.values()
            if m.model_type == model_type and m.is_enabled
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda m: m.priority)

    def update_model_metrics(
        self,
        model_id: str,
        success: bool,
        tokens_used: int = 0,
        timestamp: Optional[str] = None,
    ):
        """モデルの使用メトリクスを更新する。"""
        model = self.get_model(model_id)
        if not model:
            return

        if success:
            model.success_count += 1
        else:
            model.error_count += 1

        model.total_tokens_used += tokens_used
        if timestamp:
            model.last_used_at = timestamp

    def save_to_file(self) -> bool:
        """設定をJSONファイルに保存する。"""
        try:
            data = {
                "models": {
                    model_id: model.to_dict()
                    for model_id, model in self.models.items()
                }
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("モデル設定を保存: %s", self.config_file)
            return True
        except Exception as e:
            logger.error("モデル設定の保存に失敗: %s", e)
            return False

    def load_from_file(self) -> bool:
        """JSONファイルから設定をロードする。"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.models.clear()
            for model_id, model_data in data.get("models", {}).items():
                model = ModelConfig.from_dict(model_data)
                self.models[model_id] = model
            logger.info("モデル設定をロード: %s (%d個)", self.config_file, len(self.models))
            return True
        except Exception as e:
            logger.error("モデル設定のロードに失敗: %s", e)
            return False

    def get_summary(self) -> Dict:
        """設定の概要を取得する。"""
        enabled = self.get_enabled_models()
        return {
            "total_models": len(self.models),
            "enabled_models": len(enabled),
            "multimodal_models": len(self.get_multimodal_models()),
            "models": [
                {
                    "id": m.id,
                    "name": m.name,
                    "type": m.model_type.value,
                    "provider": m.provider.value,
                    "enabled": m.is_enabled,
                    "success_rate": m.success_rate,
                }
                for m in self.models.values()
            ],
        }


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== モデル設定マネージャーのテスト ===\n")

    # マネージャーを初期化
    manager = ModelConfigManager()

    # 概要を表示
    summary = manager.get_summary()
    print(f"総モデル数: {summary['total_models']}")
    print(f"有効なモデル: {summary['enabled_models']}")
    print(f"マルチモーダル対応: {summary['multimodal_models']}\n")

    # モデル一覧
    print("=== 登録されているモデル ===")
    for model in manager.get_enabled_models():
        print(f"  {model.name} ({model.provider.value})")
        print(f"    用途: {model.model_type.value}")
        print(f"    速度: {model.avg_tokens_per_second} tok/s")
        print(f"    マルチモーダル: {model.is_multimodal}\n")

    # 最速モデルを取得
    fastest = manager.get_fastest_model()
    if fastest:
        print(f"最速モデル: {fastest.name} ({fastest.avg_tokens_per_second} tok/s)")

    # 用途別に最適なモデルを取得
    print("\n=== 用途別の最適モデル ===")
    for model_type in ModelType:
        best = manager.get_best_model_for_type(model_type)
        if best:
            print(f"  {model_type.value}: {best.name}")

    # メトリクスを更新
    print("\n=== メトリクス更新テスト ===")
    manager.update_model_metrics("gemma-4-12b-iq4", success=True, tokens_used=512)
    manager.update_model_metrics("gemma-4-12b-iq4", success=True, tokens_used=256)
    manager.update_model_metrics("mistral-7b", success=False, tokens_used=0)

    model = manager.get_model("gemma-4-12b-iq4")
    print(f"Gemma 4 成功率: {model.success_rate:.1%}")

    # 設定を保存
    manager.save_to_file()
    print("\n設定を保存しました")
