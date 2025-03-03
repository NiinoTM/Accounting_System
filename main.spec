# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('ar_ap', 'ar_ap'), ('backups', 'backups'), ('build', 'build'), ('cashflow', 'cashflow'), ('credentials', 'credentials'), ('data', 'data'), ('dist', 'dist'), ('fixed_assets', 'fixed_assets'), ('main.build', 'main.build'), ('main.dist', 'main.dist'), ('main.onefile-build', 'main.onefile-build'), ('menu', 'menu'), ('recurring_transactions', 'recurring_transactions'), ('reports', 'reports'), ('utils', 'utils')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Niino\\Desktop\\Accounting_System\\data\\base.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
