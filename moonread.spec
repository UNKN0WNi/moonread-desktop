# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 单文件打包配置：把 src/web 静态资源一起打进 exe。"""

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/web', 'web')],
    hiddenimports=['clr', 'pythonnet'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'PIL'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MoonRead',
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
    icon=None,
)
