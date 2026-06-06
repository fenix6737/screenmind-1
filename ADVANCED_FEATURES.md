# 🚀 ScreenMind v2.0+ - 高度な機能ガイド

このドキュメントでは、Phase 3-4 で実装された高度な機能について説明します。

---

## 📋 目次

1. [レスポンスキャッシング](#レスポンスキャッシング)
2. [会話履歴の動的圧縮](#会話履歴の動的圧縮)
3. [詳細な分析・ログ機能](#詳細な分析ログ機能)
4. [Webダッシュボード](#webダッシュボード)
5. [統合使用例](#統合使用例)

---

## 🔄 レスポンスキャッシング

### 概要
AIの回答をキャッシュして、同じ質問への高速応答を実現します。

### 機能

| 機能 | 説明 |
|------|------|
| **自動キャッシュ** | 回答後、自動的にキャッシュに保存 |
| **キャッシュヒット** | 同じ質問が来たら、キャッシュから即座に返却 |
| **TTL管理** | デフォルト24時間で自動削除 |
| **サイズ管理** | 100MBを超えた場合、古いエントリを自動削除 |

### 使用方法

```python
from cache_manager import CacheManager

cache = CacheManager()

# キャッシュに保存
cache.set(
    query="Pythonで素数判定関数を書いてください",
    response="def is_prime(n): ...",
    model_id="gemma-4-12b-iq4",
    ttl_seconds=86400,  # 24時間
)

# キャッシュから取得
cached = cache.get(
    query="Pythonで素数判定関数を書いてください",
    model_id="gemma-4-12b-iq4",
)

# 統計情報
stats = cache.get_statistics()
print(f"キャッシュエントリ: {stats['total_entries']}")
print(f"ヒット率: {stats['hit_rate']:.1%}")
```

### パフォーマンス効果

- **キャッシュヒット時**: 応答時間 < 100ms
- **キャッシュミス時**: 通常の応答時間（数秒〜数十秒）
- **平均的な改善**: 30-50% の応答時間削減

---

## 📦 会話履歴の動的圧縮

### 概要
長い会話履歴を自動的に圧縮・要約して、コンテキストウィンドウを効率的に利用します。

### 機能

| 機能 | 説明 |
|------|------|
| **自動圧縮** | メッセージ数がしきい値を超えたら自動圧縮 |
| **トピック抽出** | 会話から主要なトピックを自動抽出 |
| **スマート要約** | 重要な情報を保持しながら圧縮 |
| **適応的管理** | モデルのコンテキストウィンドウに応じて自動調整 |

### 使用方法

```python
from history_compressor import AdaptiveHistoryManager

manager = AdaptiveHistoryManager(context_window_tokens=4096)

# 履歴を管理（自動圧縮）
messages = [
    {"role": "system", "content": "You are helpful..."},
    {"role": "user", "content": "質問1"},
    {"role": "assistant", "content": "回答1"},
    # ... 多数のメッセージ ...
]

managed = manager.manage_history(messages, system_prompt)
# 必要に応じて自動的に圧縮される

# 統計情報
stats = manager.compressor.get_compression_statistics()
print(f"圧縮回数: {stats['total_compressions']}")
print(f"平均圧縮率: {stats['avg_compression_ratio']:.1%}")
```

### 圧縮の仕組み

1. **判定**: メッセージ数が `max_history_messages` を超えたか確認
2. **抽出**: 古いメッセージから主要トピックを抽出
3. **要約**: トピックと重要な内容をサマリーに変換
4. **置換**: 古いメッセージをサマリーに置き換え

### トピック抽出の例

```
入力: 複数のプログラミング関連の会話
↓
抽出されたトピック: ["プログラミング", "データ分析", "セキュリティ"]
↓
サマリー: "[会話履歴サマリー] 元のメッセージ数: 20, 圧縮率: 50%..."
```

---

## 📊 詳細な分析・ログ機能

### 概要
ユーザーの利用パターン、モデル選択、パフォーマンスを詳細に分析します。

### イベント種別

| イベント | 説明 |
|---------|------|
| `request` | AIリクエスト（応答時間、トークン数、成功/失敗） |
| `model_selection` | モデル選択（自動/手動、理由） |
| `cache_hit` | キャッシュヒット |
| `history_compression` | 履歴圧縮 |

### 使用方法

```python
from analytics import AnalyticsCollector

collector = AnalyticsCollector()

# リクエストイベントを記録
collector.record_request(
    query="Pythonについて教えてください",
    model_id="gemma-4-12b-iq4",
    response_time_ms=1250.5,
    tokens=512,
    success=True,
)

# モデル選択イベントを記録
collector.record_model_selection(
    query="複雑な分析",
    selected_model_id="gemma-4-12b-iq4",
    candidate_models=["model1", "model2", "model3"],
    selection_reason="complex / analysis",
    is_auto=True,
)

# 統計情報を取得
stats = collector.get_statistics(hours=24)
print(f"総リクエスト: {stats['total_requests']}")
print(f"成功率: {stats['success_rate']:.1%}")
print(f"キャッシュヒット率: {stats['cache_hit_rate']:.1%}")

# モデル別パフォーマンス
perf = collector.get_model_performance("gemma-4-12b-iq4", hours=24)
print(f"リクエスト数: {perf['request_count']}")
print(f"平均応答時間: {perf['avg_response_time_ms']:.0f}ms")

# 利用パターン
patterns = collector.get_usage_patterns(hours=24)
print(f"平均クエリ長: {patterns['avg_query_length']:.0f} 文字")
print(f"P95応答時間: {patterns['response_time_percentiles']['p95']:.0f}ms")

# HTMLレポート生成
html_report = collector.generate_report(hours=24)
with open("report.html", "w", encoding="utf-8") as f:
    f.write(html_report)
```

### レポート機能

`generate_report()` メソッドで、以下を含むHTMLレポートを自動生成：

- 📊 総リクエスト数、成功率、平均応答時間
- 🤖 モデル別統計（リクエスト数、応答時間、トークン数）
- 📈 利用パターン（時間帯別、クエリ長分布）
- ⏱️ レスポンス時間のパーセンタイル（P50, P95, P99）

---

## 🌐 Webダッシュボード

### 概要
FastAPI を使用したリアルタイム統計・分析表示サーバー。

### 起動方法

```bash
# ダッシュボードサーバーを起動
python dashboard_server.py

# ブラウザで以下にアクセス
# http://localhost:8000
```

### API エンドポイント

#### 統計API

```
GET /api/statistics?hours=24
GET /api/model-performance/{model_id}?hours=24
GET /api/usage-patterns?hours=24
GET /api/events?event_type=request&limit=100
```

#### キャッシュAPI

```
GET /api/cache/statistics
GET /api/cache/top-queries?limit=10
POST /api/cache/clear
```

#### モデルAPI

```
GET /api/models
GET /api/models/statistics
```

#### レポートAPI

```
GET /api/report/html?hours=24
```

#### WebSocket

```
WS /ws/stats
```

リアルタイム統計をWebSocketで配信（5秒ごと）。

### ダッシュボード画面

ダッシュボードには以下の情報が表示されます：

- **概要カード**: 総リクエスト、成功率、平均応答時間、キャッシュヒット率
- **モデル別統計**: テーブル形式で各モデルのパフォーマンスを表示
- **キャッシュ情報**: エントリ数、サイズ、ヒット率

### カスタマイズ

ダッシュボードのHTMLは `dashboard_server.py` の `get_dashboard_html()` 関数で生成されます。

```python
# 例: 新しいメトリクスを追加
def get_dashboard_html() -> str:
    return """
    <!-- カスタムダッシュボードHTML -->
    """
```

---

## 🔗 統合使用例

### 例1: 完全なワークフロー

```python
from screenmind_v2 import ScreenMindWindow
from PyQt6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = ScreenMindWindow()

# 以下の処理が自動的に実行される：
# 1. ユーザーが質問を入力
# 2. キャッシュを確認 → ヒット時は即座に返却
# 3. キャッシュミス時：
#    a. 画面をキャプチャ
#    b. リクエストを分析
#    c. 最適なモデルを自動選択
#    d. AIに送信
#    e. 回答をキャッシュに保存
#    f. 履歴を圧縮（必要に応じて）
# 4. 全てのイベントを分析ログに記録

window.show()
sys.exit(app.exec())
```

### 例2: 分析結果の活用

```python
from analytics import AnalyticsCollector

collector = AnalyticsCollector()

# 過去24時間の統計
stats = collector.get_statistics(hours=24)

# 最も効率的なモデルを特定
best_model = max(
    stats['model_statistics'].items(),
    key=lambda x: x[1]['count'] / max(x[1]['avg_time'], 1)
)
print(f"最も効率的なモデル: {best_model[0]}")

# ピーク時間帯を特定
patterns = collector.get_usage_patterns(hours=24)
peak_hour = max(patterns['hourly_usage'].items(), key=lambda x: x[1])
print(f"ピーク時間帯: {peak_hour[0]}時")

# レポートを生成して保存
html = collector.generate_report(hours=24)
with open("daily_report.html", "w", encoding="utf-8") as f:
    f.write(html)
```

### 例3: ダッシュボード + デスクトップアプリ

```bash
# ターミナル1: ScreenMind デスクトップアプリを起動
python screenmind_v2.py

# ターミナル2: ダッシュボードサーバーを起動
python dashboard_server.py

# ブラウザで http://localhost:8000 を開く
# → リアルタイムでアプリの統計が表示される
```

---

## 📈 パフォーマンス最適化のベストプラクティス

### 1. キャッシュの活用

- **TTLを適切に設定**: 頻繁に変わる情報は短く、安定した情報は長く
- **定期的にクリーンアップ**: 古いエントリを削除してディスク容量を節約

```python
# 1時間ごとに古いキャッシュをクリーンアップ
cache.clear()  # または、期限切れエントリのみ削除
```

### 2. 履歴圧縮の活用

- **コンテキストウィンドウに合わせる**: モデルのコンテキストサイズに応じて圧縮比率を調整
- **重要な情報を保持**: トピック抽出で重要な会話内容を保持

```python
manager = AdaptiveHistoryManager(context_window_tokens=8192)  # より大きいウィンドウ
```

### 3. 分析ログの活用

- **定期的にレポート生成**: 日次/週次でパフォーマンスレポートを確認
- **ボトルネック特定**: 遅いモデルや失敗率の高いモデルを特定して改善

```python
# 週次レポート
weekly_stats = collector.get_statistics(hours=24*7)
if weekly_stats['success_rate'] < 0.95:
    print("⚠️ 成功率が低下しています")
```

---

## 🔧 トラブルシューティング

### キャッシュが機能しない

```
症状: キャッシュヒットが記録されない
原因: クエリやモデルIDが完全に一致していない
解決: 
  - クエリの前後の空白を確認
  - モデルIDのスペルを確認
  - キャッシュディレクトリの権限を確認
```

### 履歴圧縮が動作しない

```
症状: メッセージが圧縮されない
原因: メッセージ数がしきい値に達していない
解決:
  - max_history_messages を低くする
  - または、より多くのメッセージを蓄積
```

### ダッシュボードに接続できない

```
症状: http://localhost:8000 にアクセスできない
原因: サーバーが起動していない、またはポートが使用中
解決:
  - python dashboard_server.py を実行
  - ポート8000が使用中の場合: uvicorn.run(..., port=8001)
```

---

## 📚 参考資料

- `cache_manager.py`: キャッシュ管理の詳細実装
- `history_compressor.py`: 履歴圧縮アルゴリズム
- `analytics.py`: 分析・ログ機能の詳細
- `dashboard_server.py`: Webダッシュボードの実装

---

**ScreenMind v2.0+ — 高度な機能ガイド**
