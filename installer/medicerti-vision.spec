# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

project_root = Path(".").resolve()
src_dir = project_root / "src"
dashboard_dir = src_dir / "dashboard"
models_dir = project_root / "models"
version_file = project_root / "version.json"

model_onnx = models_dir / "yolov8n-pose.onnx"
datas = [
    (str(version_file), "."),
]

if model_onnx.exists():
    datas.append((str(model_onnx), "models"))

dash_files = list(dashboard_dir.rglob("*"))
for f in dash_files:
    if f.is_file():
        rel = f.relative_to(project_root)
        datas.append((str(f), str(rel.parent)))

a = Analysis(
    [str(project_root / 'run.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'src.api.main',
        'src.api.models',
        'src.api.event_logger',
        'src.ingest.rtsp_reader',
        'src.detector.yolo_pose',
        'src.detector.fall_detector',
        'src.detector.geo_fence',
        'src.detector.stranger_detector',
        'src.detector.roi_tracker',
        'src.privacy.masker',
        'src.accreditation.report_gen',
        'src.discovery.camera_scanner',
        'src.updater.auto_updater',
        'src.notify.telegram_notifier',
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
        'onnxruntime',
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
        'notebook',
        'jupyter',
        'ultralytics',
        'torch',
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
