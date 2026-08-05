# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# Collect package dependencies
datas = [
    ('assets', 'assets'),
    ('bin', 'bin'),
    ('styles', 'styles'),
]

hiddenimports = [
    'customtkinter',
    'tkinterdnd2',
    'py7zr',
    'rarfile',
    'zipfile',
    'tarfile',
    'zstandard',
    'cryptography',
    'queue',
    'concurrent.futures',
    'PIL',
    'zlib',
    'hashlib'
]

# Collect customtkinter and py7zr datas
ctk_datas, ctk_binaries, ctk_hidden = collect_all('customtkinter')
py7zr_datas, py7zr_binaries, py7zr_hidden = collect_all('py7zr')

datas.extend(ctk_datas)
datas.extend(py7zr_datas)
hiddenimports.extend(ctk_hidden)
hiddenimports.extend(py7zr_hidden)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=ctk_binaries + py7zr_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ArchiveTranscoderPro',
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
    icon='assets/icon.ico',
)
