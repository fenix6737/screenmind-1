"""
ScreenMind - キャッシュ管理モジュール
AIの回答をキャッシュして、同じ質問への高速応答を実現する。
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class CacheEntry:
    """キャッシュエントリを表すクラス。"""

    def __init__(
        self,
        query_hash: str,
        response: str,
        model_id: str,
        image_hash: Optional[str] = None,
        ttl_seconds: int = 86400,  # デフォルト24時間
    ):
        self.query_hash = query_hash
        self.response = response
        self.model_id = model_id
        self.image_hash = image_hash
        self.created_at = datetime.now().isoformat()
        self.ttl_seconds = ttl_seconds
        self.hit_count = 0
        self.last_accessed = datetime.now().isoformat()

    def is_expired(self) -> bool:
        """キャッシュが有効期限切れかどうかを判定する。"""
        created = datetime.fromisoformat(self.created_at)
        expired_at = created + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expired_at

    def to_dict(self) -> Dict:
        """辞書に変換する。"""
        return {
            "query_hash": self.query_hash,
            "response": self.response,
            "model_id": self.model_id,
            "image_hash": self.image_hash,
            "created_at": self.created_at,
            "ttl_seconds": self.ttl_seconds,
            "hit_count": self.hit_count,
            "last_accessed": self.last_accessed,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "CacheEntry":
        """辞書から復元する。"""
        entry = cls(
            query_hash=data["query_hash"],
            response=data["response"],
            model_id=data["model_id"],
            image_hash=data.get("image_hash"),
            ttl_seconds=data.get("ttl_seconds", 86400),
        )
        entry.created_at = data.get("created_at", entry.created_at)
        entry.hit_count = data.get("hit_count", 0)
        entry.last_accessed = data.get("last_accessed", entry.last_accessed)
        return entry


class CacheManager:
    """
    AIの回答をキャッシュして、パフォーマンスを向上させるマネージャー。
    """

    def __init__(self, cache_dir: str = "cache", max_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self._cache: Dict[str, CacheEntry] = {}
        self._load_cache()

    def _get_cache_path(self) -> str:
        """キャッシュファイルのパスを取得する。"""
        os.makedirs(self.cache_dir, exist_ok=True)
        return os.path.join(self.cache_dir, "response_cache.json")

    def _load_cache(self):
        """ディスクからキャッシュを読み込む。"""
        cache_path = self._get_cache_path()
        if not os.path.exists(cache_path):
            logger.info("キャッシュファイルが見つかりません（初回実行）")
            return

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._cache = {
                key: CacheEntry.from_dict(entry)
                for key, entry in data.items()
            }
            logger.info("キャッシュを読み込み: %d エントリ", len(self._cache))
        except Exception as e:
            logger.error("キャッシュの読み込みに失敗: %s", e)

    def _save_cache(self):
        """ディスクにキャッシュを保存する。"""
        cache_path = self._get_cache_path()
        try:
            data = {key: entry.to_dict() for key, entry in self._cache.items()}
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("キャッシュを保存: %d エントリ", len(self._cache))
        except Exception as e:
            logger.error("キャッシュの保存に失敗: %s", e)

    def _compute_hash(self, text: str) -> str:
        """テキストのハッシュ値を計算する。"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _compute_image_hash(self, image_base64: str) -> str:
        """画像のハッシュ値を計算する。"""
        return hashlib.sha256(image_base64.encode("utf-8")).hexdigest()

    def _get_cache_key(
        self,
        query: str,
        model_id: str,
        image_hash: Optional[str] = None,
    ) -> str:
        """キャッシュキーを生成する。"""
        query_hash = self._compute_hash(query)
        key_parts = [query_hash, model_id]
        if image_hash:
            key_parts.append(image_hash)
        return "_".join(key_parts)

    def get(
        self,
        query: str,
        model_id: str,
        image_base64: Optional[str] = None,
    ) -> Optional[str]:
        """
        キャッシュからレスポンスを取得する。
        見つからない、または期限切れの場合は None を返す。
        """
        image_hash = None
        if image_base64:
            image_hash = self._compute_image_hash(image_base64)

        cache_key = self._get_cache_key(query, model_id, image_hash)

        if cache_key not in self._cache:
            logger.debug("キャッシュミス: %s", cache_key[:16])
            return None

        entry = self._cache[cache_key]

        if entry.is_expired():
            logger.debug("キャッシュ期限切れ: %s", cache_key[:16])
            del self._cache[cache_key]
            self._save_cache()
            return None

        # ヒット数を更新
        entry.hit_count += 1
        entry.last_accessed = datetime.now().isoformat()
        logger.info(
            "キャッシュヒット: %s (ヒット数: %d)",
            cache_key[:16],
            entry.hit_count,
        )
        return entry.response

    def set(
        self,
        query: str,
        response: str,
        model_id: str,
        image_base64: Optional[str] = None,
        ttl_seconds: int = 86400,
    ) -> bool:
        """
        レスポンスをキャッシュに保存する。
        """
        image_hash = None
        if image_base64:
            image_hash = self._compute_image_hash(image_base64)

        cache_key = self._get_cache_key(query, model_id, image_hash)

        try:
            entry = CacheEntry(
                query_hash=self._compute_hash(query),
                response=response,
                model_id=model_id,
                image_hash=image_hash,
                ttl_seconds=ttl_seconds,
            )
            self._cache[cache_key] = entry

            # サイズチェック
            self._evict_if_needed()
            self._save_cache()

            logger.debug("キャッシュに保存: %s", cache_key[:16])
            return True
        except Exception as e:
            logger.error("キャッシュの保存に失敗: %s", e)
            return False

    def _evict_if_needed(self):
        """キャッシュサイズが上限を超えた場合、古いエントリを削除する。"""
        cache_path = self._get_cache_path()
        if not os.path.exists(cache_path):
            return

        size_mb = os.path.getsize(cache_path) / (1024 * 1024)
        if size_mb > self.max_size_mb:
            logger.warning("キャッシュサイズが上限を超えています: %.1f MB", size_mb)

            # 期限切れエントリを削除
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]

            # それでも超えている場合は、アクセス頻度が低いエントリを削除
            if len(self._cache) > 100:
                sorted_entries = sorted(
                    self._cache.items(),
                    key=lambda x: x[1].hit_count,
                )
                for key, _ in sorted_entries[:50]:
                    del self._cache[key]

            logger.info("キャッシュをクリーンアップしました")

    def clear(self):
        """全キャッシュをクリアする。"""
        self._cache.clear()
        cache_path = self._get_cache_path()
        if os.path.exists(cache_path):
            os.remove(cache_path)
        logger.info("キャッシュをクリアしました")

    def get_statistics(self) -> Dict:
        """キャッシュの統計情報を取得する。"""
        total_entries = len(self._cache)
        total_hits = sum(entry.hit_count for entry in self._cache.values())
        expired_count = sum(
            1 for entry in self._cache.values()
            if entry.is_expired()
        )

        cache_path = self._get_cache_path()
        cache_size_mb = 0
        if os.path.exists(cache_path):
            cache_size_mb = os.path.getsize(cache_path) / (1024 * 1024)

        return {
            "total_entries": total_entries,
            "total_hits": total_hits,
            "expired_entries": expired_count,
            "cache_size_mb": cache_size_mb,
            "hit_rate": total_hits / max(total_entries, 1),
        }

    def get_top_cached_queries(self, limit: int = 10) -> List[Dict]:
        """最もアクセスされたキャッシュエントリを取得する。"""
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].hit_count,
            reverse=True,
        )
        return [
            {
                "query_hash": entry.query_hash,
                "model_id": entry.model_id,
                "hit_count": entry.hit_count,
                "created_at": entry.created_at,
            }
            for _, entry in sorted_entries[:limit]
        ]


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== キャッシュマネージャーのテスト ===\n")

    manager = CacheManager()

    # テスト1: キャッシュに保存
    print("1️⃣  キャッシュに保存")
    manager.set(
        query="Pythonで素数判定関数を書いてください",
        response="def is_prime(n):\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
        model_id="gemma-4-12b-iq4",
    )
    print("   ✅ 保存完了\n")

    # テスト2: キャッシュから取得
    print("2️⃣  キャッシュから取得（1回目）")
    result = manager.get(
        query="Pythonで素数判定関数を書いてください",
        model_id="gemma-4-12b-iq4",
    )
    if result:
        print(f"   ✅ キャッシュヒット: {result[:50]}...\n")
    else:
        print("   ❌ キャッシュミス\n")

    # テスト3: 統計情報
    print("3️⃣  統計情報")
    stats = manager.get_statistics()
    print(f"   総エントリ数: {stats['total_entries']}")
    print(f"   総ヒット数: {stats['total_hits']}")
    print(f"   キャッシュサイズ: {stats['cache_size_mb']:.2f} MB\n")

    # テスト4: トップキャッシュ
    print("4️⃣  トップキャッシュ")
    top = manager.get_top_cached_queries(5)
    for i, entry in enumerate(top, 1):
        print(f"   {i}. {entry['model_id']} - ヒット数: {entry['hit_count']}")
