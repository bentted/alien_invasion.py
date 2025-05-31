# ...existing PyInstaller spec file structure...
block_cipher = None

a = Analysis(
    [
        '/home/kali/Documents/GitHub/alien_invasion.py/alien_invasion/Alien_Invasion.py',
        '/home/kali/Documents/GitHub/alien_invasion.py/leaderboard_server.py'  # Include leaderboard server script
    ],
    pathex=['/home/kali/Documents/GitHub/alien_invasion.py/alien_invasion'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='alien_invasion_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='alien_invasion_server',
)
