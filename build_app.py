#!/usr/bin/env python3
"""
Build-Script für ABC-CO₂-Bilanzierer macOS App
Erstellt eine eigenständige .app im dist/ Ordner
"""

import subprocess
import sys
from pathlib import Path

def build_app():
    """Erstellt macOS .app mit PyInstaller"""
    
    print("=" * 60)
    print("CO₂-Bilanzierer - App Builder")
    print("=" * 60)
    
    # 1. PyInstaller installieren (falls nicht vorhanden)
    print("\n1. Prüfe PyInstaller...")
    try:
        import PyInstaller
        print("   ✓ PyInstaller bereits installiert")
    except ImportError:
        print("   → Installiere PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("   ✓ PyInstaller installiert")
    
    # 2. .spec Datei erstellen (falls nicht vorhanden)
    spec_file = Path("ABC-CO2-Bilanzierer.spec")
    if not spec_file.exists():
        print("\n2. Erstelle .spec Datei...")
        create_spec_file()
        print("   ✓ .spec Datei erstellt")
    else:
        print("\n2. .spec Datei existiert bereits")
    
    # 3. App bauen
    print("\n3. Baue macOS App...")
    print("   (Dies kann einige Minuten dauern...)")
    
    result = subprocess.run([
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "ABC-CO2-Bilanzierer.spec"
    ], capture_output=False)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ App erfolgreich erstellt!")
        print("=" * 60)
        print("\nSpeicherort: dist/ABC-CO₂-Bilanzierer.app")
        print("\nNächste Schritte:")
        print("1. Öffne den Finder")
        print("2. Navigiere zu: dist/ABC-CO₂-Bilanzierer.app")
        print("3. Ziehe die App in den Programme-Ordner")
        print("4. Optional: Erstelle Alias auf dem Desktop")
        print("\nStarten: Doppelklick auf die App!")
    else:
        print("\n❌ Fehler beim Erstellen der App")
        print("Prüfe die Fehlermeldungen oben.")
        sys.exit(1)

def create_spec_file():
    """Erstellt PyInstaller .spec Datei"""
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/OBD_Datenbank.csv', 'data'),
        ('services/pdf/Logos', 'services/pdf/Logos'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'customtkinter',
        'matplotlib',
        'numpy',
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
    name='ABC-CO₂-Bilanzierer',
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
    name='ABC-CO₂-Bilanzierer',
)

app = BUNDLE(
    coll,
    name='ABC-CO₂-Bilanzierer.app',
    icon=None,  # Optional: 'icon.icns' hinzufügen
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
'''
    
    with open("ABC-CO2-Bilanzierer.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)

if __name__ == "__main__":
    build_app()
