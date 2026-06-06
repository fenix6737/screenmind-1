# ScreenMind v4.1 - GitHub 自動ビルド導入ガイド

このプロジェクトには、Windows、macOS、Linux 用の実行ファイルを自動的に作成する **GitHub Actions** が設定されています。

## 🚀 実行ファイル（EXE/APP）の作成手順

1.  **GitHub リポジトリを作成**:
    GitHub で [New repository] を作成します。Public でも Private でも構いません。

2.  **全ファイルをアップロード (Push)**:
    この ZIP を解凍して出てきたすべてのファイルを、作成したリポジトリにアップロードします。
    ※ `.github` フォルダを忘れずに含めてください。

3.  **[Actions] タブを確認**:
    リポジトリ画面上部の **[Actions]** をクリックします。
    `ScreenMind Continuous Build` という名前のワークフローが動いているはずです。

4.  **ビルド完了を待つ**:
    黄色い丸が緑色のチェックマーク（✅）に変わるまで待ちます（通常 3〜5 分）。

5.  **Artifacts からダウンロード**:
    完了したジョブ（一番上のリスト）をクリックして詳細画面を開きます。
    画面を一番下までスクロールすると **[Artifacts]** という項目があります。
    *   **Windows**: `ScreenMind-Windows` をクリックしてダウンロード。
    *   **macOS**: `ScreenMind-macOS` をクリックしてダウンロード。

6.  **ZIP を解凍して実行**:
    ダウンロードした ZIP を解凍すると、中に `ScreenMind.exe` (Windows) または `ScreenMind.app` (Mac) が入っています！

## 📂 構成ファイル
*   `.github/workflows/build.yml`: ビルド手順の定義
*   `build/ScreenMind_CI.spec`: PyInstaller の詳細設定
*   `build/screenmind_lite.py`: ビルド用エントリーポイント

---
この仕組みにより、開発環境（Python）を持っていない一般ユーザーでも、自分の PC に合ったファイルをダウンロードしてダブルクリックするだけで ScreenMind を使い始めることができます。
