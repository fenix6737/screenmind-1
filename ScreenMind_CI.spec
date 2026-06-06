# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_all

# パス設定
current_dir = Path(os.getcwd())
build_dir = current_dir if current_dir.name == 'build' else current_dir / 'build'
project_root = build_dir.parent
src_path = project_root / 'src'

block_cipher = None

# PyQt6のすべての依存関係を強制的に収集
datas, binaries, hidden_imports = collect_all('PyQt6')

# その他の依存関係
hidden_imports += [
    'httpx',
    'PIL',
    'PIL.ImageGrab',
    'psutil',
    'numpy',
    'fastapi',
    'uvicorn',
    'keyboard',
    'logging',
    'asyncio',
    'json',
]
hidden_imports += collect_submodules('uvicorn')
hidden_imports += collect_submodules('fastapi')

# データファイルの追加
datas += [
    (str(build_dir / 'models_config.json'), '.'),
    (str(project_root / 'README.txt'), '.'),
]

# アイコン
icon_file = str(build_dir / 'screenmind.ico')
if not os.path.exists(icon_file):
    icon_file = None

a = Analysis(
    [str(build_dir / 'screenmind_lite.py')],
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
    debug=True, # デバッグ情報を表示するために一時的にTrue
    bootloader_ignore_signals=False,
    strip=False,
    upx=False, # UPXが原因で壊れることがあるため一時的にFalse
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # エラー内容を画面で見れるように一時的にTrue
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
