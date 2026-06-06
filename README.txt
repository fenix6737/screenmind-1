================================================================================
                        ScreenMind v4.1 (Clean Edition)
                    AI-Powered Workflow Platform
================================================================================

📦 プロジェクト構成
================================================================================

📂 screenmind/
  ├─ 📄 README.txt                 ← このファイル
  ├─ 📄 requirements.txt           ← Python 依存ライブラリ
  ├─ 📄 run.bat                    ← Windows 起動スクリプト
  ├─ 📄 run.sh                     ← macOS/Linux 起動スクリプト
  │
  ├─ 📁 src/                       ← ソースコード（21ファイル）
  │  ├─ screenmind_v2.py          ← メインアプリケーション
  │  ├─ ai_client.py              ← AI バックエンド通信
  │  ├─ capture.py                ← 画面キャプチャ機能
  │  ├─ model_manager.py          ← LLM 管理
  │  ├─ auto_switcher.py          ← 自動モデル切り替え
  │  ├─ cache_manager.py          ← レスポンスキャッシング
  │  ├─ history_compressor.py     ← 会話履歴圧縮
  │  ├─ analytics.py              ← 分析・ログ機能
  │  ├─ dashboard_v2.py           ← Web ダッシュボード
  │  ├─ agent_orchestrator.py     ← AI エージェント管理
  │  ├─ tool_engine.py            ← 外部ツール実行
  │  ├─ user_profile.py           ← ユーザープロファイル
  │  ├─ preference_learner.py     ← 好み学習エンジン
  │  ├─ ui_themes.py              ← UI テーマ管理
  │  ├─ keyboard_shortcuts.py     ← キーボード設定
  │  ├─ setup_wizard.py           ← セットアップウィザード
  │  ├─ watchdog.py               ← システムモニタリング
  │  ├─ recovery_manager.py       ← 自動リカバリー
  │  ├─ debug_logger.py           ← ログ・デバッグツール
  │  ├─ config.py                 ← 設定管理
  │  └─ model_config.py           ← モデル定義
  │
  ├─ 📁 docs/                      ← ドキュメント（7ファイル）
  │  ├─ README.md                 ← 基本的な使い方
  │  ├─ README_v2.md              ← 高度な機能
  │  ├─ ADVANCED_FEATURES.md      ← 詳細な機能説明
  │  ├─ INSTALLATION_GUIDE.md     ← インストール手順
  │  ├─ BUILD_INSTRUCTIONS.md     ← ビルド手順
  │  ├─ RELEASE_NOTES_v4.0.md     ← v4.0 新機能
  │  └─ STABILITY_REPORT.md       ← 安定性テストレポート
  │
  └─ 📁 build/                     ← ビルド・設定ファイル
     ├─ build_v2.py               ← EXE ビルドスクリプト
     ├─ create_installer.py       ← インストーラー作成
     ├─ screenmind.spec           ← PyInstaller 設定
     ├─ screenmind.ico            ← アプリアイコン
     ├─ models_config.json        ← LLM 設定
     └─ METADATA.json             ← メタデータ


🚀 クイックスタート
================================================================================

【方法 1】Python から直接実行
  1. Python 3.8+ をインストール
  2. 依存ライブラリをインストール
     $ pip install -r requirements.txt
  3. アプリを起動
     $ python src/screenmind_v2.py

【方法 2】起動スクリプトを使用
  Windows:  run.bat をダブルクリック
  macOS/Linux: bash run.sh を実行

【方法 3】EXE ファイルを生成してインストール
  1. build/ フォルダに移動
     $ cd build
  2. EXE をビルド
     $ python build_v2.py
  3. インストーラーを作成
     $ python create_installer.py
  4. 生成された installer/ フォルダから Install.vbs を実行


📋 システム要件
================================================================================

最小要件:
  - OS: Windows 7+, macOS 10.13+, Linux (Ubuntu 18.04+)
  - Python: 3.8 以上
  - メモリ: 2GB 以上
  - ディスク: 500MB 以上

推奨要件:
  - OS: Windows 10/11, macOS 12+, Ubuntu 22.04 LTS
  - Python: 3.10 以上
  - メモリ: 8GB 以上
  - ディスク: 1GB 以上
  - GPU: NVIDIA CUDA 対応（オプション）


🔧 主要機能
================================================================================

✅ 複数 LLM 対応
   - ローカルモデル: Gemma 4, Mistral 7B, Llama 2
   - クラウドモデル: OpenAI GPT-4, GPT-3.5

✅ 自動モデル切り替え
   - リクエスト内容を分析して最適なモデルを自動選択
   - 手動選択も可能

✅ 高度なキャッシング
   - レスポンスキャッシング（100ms 以下の高速応答）
   - 会話履歴の動的圧縮

✅ Web ダッシュボード
   - リアルタイム統計表示
   - パフォーマンス分析
   - エラー監視

✅ 自動リカバリー
   - システム異常の自動検出
   - 自動復旧機能
   - 詳細なログ記録

✅ UI/UX 強化
   - ダークモード対応
   - 拡張ショートカット（13個）
   - セットアップウィザード


📚 ドキュメント
================================================================================

初心者向け:
  → docs/README.md
  → docs/INSTALLATION_GUIDE.md

開発者向け:
  → docs/BUILD_INSTRUCTIONS.md
  → docs/ADVANCED_FEATURES.md

詳細情報:
  → docs/STABILITY_REPORT.md
  → docs/RELEASE_NOTES_v4.0.md


🔗 重要なリンク
================================================================================

ビルド手順:
  build/ フォルダの build_v2.py を実照
  詳細は docs/BUILD_INSTRUCTIONS.md を参照

インストーラー作成:
  build/ フォルダの create_installer.py を実行
  詳細は docs/INSTALLATION_GUIDE.md を参照

Web ダッシュボード:
  起動後、ブラウザで http://localhost:8000 にアクセス


💡 トラブルシューティング
================================================================================

起動しない:
  → logs/screenmind.log を確認
  → docs/INSTALLATION_GUIDE.md の「トラブルシューティング」を参照

パフォーマンスが低い:
  → Web ダッシュボード (http://localhost:8000) でモニタリング
  → docs/STABILITY_REPORT.md を参照

その他の問題:
  → docs/ フォルダのドキュメントを検索
  → ログファイルでエラーを確認


📞 サポート
================================================================================

問題が発生した場合:
  1. ログファイルを確認
     - Windows: %APPDATA%\ScreenMind\logs\
     - macOS: ~/Library/Application Support/ScreenMind/logs/
     - Linux: ~/.config/ScreenMind/logs/

  2. ドキュメントを参照
     - docs/ フォルダ内のマニュアルを確認

  3. エラーレポートをエクスポート
     - 設定 → 診断 → エラーレポートをエクスポート


🎯 ファイル構成の説明
================================================================================

src/ (ソースコード)
  - screenmind_v2.py: メインアプリケーション（PyQt6 GUI）
  - ai_client.py: AI バックエンド通信（httpx）
  - capture.py: 画面キャプチャ（PIL）
  - model_*.py: LLM 管理・自動切り替え
  - cache_manager.py: レスポンスキャッシング
  - dashboard_v2.py: Web ダッシュボード（FastAPI）
  - その他: 補助機能モジュール

docs/ (ドキュメント)
  - README.md: 基本的な使い方
  - INSTALLATION_GUIDE.md: インストール手順
  - BUILD_INSTRUCTIONS.md: ビルド・配布手順
  - ADVANCED_FEATURES.md: 高度な機能説明
  - STABILITY_REPORT.md: テスト結果・安定性情報
  - その他: 機能説明・リリースノート

build/ (ビルド・設定)
  - build_v2.py: PyInstaller を使用した EXE ビルド
  - create_installer.py: インストーラーパッケージ作成
  - screenmind.spec: PyInstaller ビルド設定
  - screenmind.ico: アプリケーションアイコン
  - models_config.json: LLM 設定ファイル
  - METADATA.json: メタデータ


✨ 今後のアップデート予定
================================================================================

v4.2 (Performance):
  - ストリーミング処理の導入
  - 適応的タイムアウト機能

v4.3 (Scalability):
  - 共有メモリの活用
  - 分散キャッシュ対応

v4.4 (Enterprise):
  - ユーザー権限管理
  - 監査ログ機能


================================================================================
                    ScreenMind v4.1 - Happy Computing! 🧠✨
================================================================================

バージョン: 4.1 (Installable Edition)
最終更新: 2026年6月6日
ライセンス: MIT

© 2026 ScreenMind Team
