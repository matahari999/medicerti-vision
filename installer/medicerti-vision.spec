# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

src_dir = Path(__file__).parent / "src"
dashboard_dir = src_dir / "dashboard"
version_file = Path(__file__).parent / "version.json"

a = Analysis(
    ['run.py'],
    pathex=[str(Path(__file__).parent)],
    binaries=[],
    datas=[
        (str(dashboard_dir / "index.html"), "src/dashboard"),
        (str(version_file), "."),
    ],
    hiddenimports=[
        'src.api.main',
        'src.api.models',
        'src.api.event_logger',
        'src.ingest.rtsp_reader',
        'src.detector.pose_estimator',
        'src.detector.fall_detector',
        'src.detector.geo_fence',
        'src.privacy.masker',
        'src.accreditation.report_gen',
        'src.discovery.camera_scanner',
        'src.updater.auto_updater',
        'src.config.settings',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'mediapipe',
        'cv2',
        'numpy',
        'fastapi',
        'websockets',
        'pydantic',
        'sqlite3',
        'asyncio',
        'multipart',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'sympy',
        'PIL.ImageShow',
        'PIL.ImageQt',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='medicerti-vision',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    contents_directory='.',
)
