# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['H:\\Fast memory\\Projects\\Py scripts\\Self illuminated background oriented Schlieren\\RayTracingApp GUI\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('H:\\Fast memory\\Projects\\Py scripts\\Self illuminated background oriented Schlieren\\RayTracingApp GUI\\resources\\icon.ico', 'resources')],
    hiddenimports=['PyQt5.QtWebEngineWidgets', 'numpy', 'scipy', 'scipy.stats', 'scipy.stats._distn_infrastructure', 'scipy.stats._continuous_distns', 'scipy.stats._discrete_distns', 'scipy.interpolate', 'pandas', 'matplotlib', 'multiprocessing'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RayTracingBOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
