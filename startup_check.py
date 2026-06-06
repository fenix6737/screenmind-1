import sys
import traceback

def check_dependencies():
    print("--- ScreenMind 依存関係チェック開始 ---")
    dependencies = [
        ('PyQt6.QtWidgets', 'PyQt6'),
        ('PIL.Image', 'Pillow'),
        ('httpx', 'httpx'),
        ('keyboard', 'keyboard'),
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('psutil', 'psutil'),
        ('numpy', 'numpy'),
    ]
    
    missing = []
    for module_name, pkg_name in dependencies:
        try:
            __import__(module_name)
            print(f"✅ {pkg_name} は正常にロードされました")
        except ImportError as e:
            print(f"❌ {pkg_name} が見つかりません: {e}")
            missing.append(pkg_name)
        except Exception as e:
            print(f"❌ {pkg_name} のロード中にエラーが発生しました: {e}")
            missing.append(pkg_name)
            
    if missing:
        print("\n以下のライブラリが不足しています。ビルド設定を確認してください:")
        for pkg in missing:
            print(f" - {pkg}")
        return False
    
    print("\n--- すべての依存関係が正常です。アプリケーションを起動します... ---\n")
    return True

if __name__ == "__main__":
    try:
        if check_dependencies():
            # 本来のアプリを起動
            from screenmind_lite import main
            main()
        else:
            input("\nエラーが発生しました。何かキーを押して終了してください...")
            sys.exit(1)
    except Exception:
        print("\n致命的なエラーが発生しました:")
        traceback.print_exc()
        input("\n何かキーを押して終了してください...")
        sys.exit(1)
