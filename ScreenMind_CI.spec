# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

# パス設定
current_dir = Path(os.getcwd())
build_dir = current_dir if current_dir.name == 'build' else current_dir / 'build'
project_root = build_dir.parent
src_path = project_root / 'src'

block_cipher = None

# 主要ライブラリの依存関係を完全に収集（データ、バイナリ、インポートすべて）
packages_to_collect = ['PyQt6', 'httpx', 'PIL', 'fastapi', 'uvicorn', 'keyboard', 'psutil', 'numpy']
datas = []
binaries = []
hidden_imports = []

for pkg in packages_to_collect:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hidden_imports += h

# 追加のデータファイル
datas += [
    (str(build_dir / 'models_config.json'), '.'),
    (str(project_root / 'README.txt'), '.'),
]

# アイコン
icon_file = str(build_dir / 'screenmind.ico')
if not os.path.exists(icon_file):
    icon_file = None

a = Analysis(
    [str(build_dir / 'startup_check.py')],
    pathex=[str(src_path), str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ScreenMind',
    debug=True, # エラー特定のためTrue
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, # 安定性のためFalse
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # エラー画面を出すためTrue
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# macOS用バンドル設定
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='ScreenMind.app',
        icon=icon_file,
        bundle_identifier='com.manus.screenmind',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',
            'NSAppleEventsUsageDescription': 'ScreenMind requires permission to capture the screen.',
        },
    )
