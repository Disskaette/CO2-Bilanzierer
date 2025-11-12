# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/OBD_Datenbank.csv', 'data'),
        ('data/ABC_Entwurfstafeln_Oekobilanzierung_2024-12.pdf', 'data'),
        ('services/pdf/Logos', 'services/pdf/Logos'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'customtkinter',
        'matplotlib',
        'numpy',
        'openpyxl',
        'openpyxl.cell._writer',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib',
    ],
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
    [],
    exclude_binaries=True,
    name='CO₂-Bilanzierer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Kein Terminal-Fenster
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CO₂-Bilanzierer',
)

app = BUNDLE(
    coll,
    name='CO₂-Bilanzierer.app',
    icon='data/app_icon.icns',  # Optional: 'icon.icns' hinzufügen
    bundle_identifier='de.abc.co2bilanzierer',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'CO₂-Bilanzierer',
        'CFBundleDisplayName': 'CO₂-Bilanzierer',
        'CFBundleVersion': '2.0',
        'CFBundleShortVersionString': '2.0',
    },
)
