#!/usr/bin/env python3
"""
Build-Script für CO₂-Bilanzierer macOS App
Erstellt eine eigenständige .app im dist/ Ordner
"""

import subprocess
import sys
import os
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
        subprocess.run([sys.executable, "-m", "pip",
                       "install", "pyinstaller"], check=True)
        print("   ✓ PyInstaller installiert")

    # 2. Icon konvertieren (PNG -> ICNS)
    print("\n2. Konvertiere App-Icon...")
    icon_path = convert_icon()
    if icon_path:
        print(f"   ✓ Icon erstellt: {icon_path}")
    else:
        print("   ⚠ Icon konnte nicht erstellt werden (optional)")
    
    # 3. .spec Datei erstellen (falls nicht vorhanden)
    spec_file = Path("CO2-Bilanzierer.spec")
    if not spec_file.exists():
        print("\n3. Erstelle .spec Datei...")
        create_spec_file(icon_path)
        print("   ✓ .spec Datei erstellt")
    else:
        print("\n3. .spec Datei existiert bereits")
        # Spec-Datei aktualisieren um Icon hinzuzufügen
        if icon_path:
            update_spec_icon(spec_file, icon_path)

    # 4. App bauen
    print("\n4. Baue macOS App...")
    print("   (Dies kann einige Minuten dauern...)")

    result = subprocess.run([
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "CO2-Bilanzierer.spec"
    ], capture_output=False)

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✅ App erfolgreich erstellt!")
        print("=" * 60)
        print("\nSpeicherort: dist/CO₂-Bilanzierer.app")
        print("\nNächste Schritte:")
        print("1. Öffne den Finder")
        print("2. Navigiere zu: dist/CO₂-Bilanzierer.app")
        print("3. Ziehe die App in den Programme-Ordner")
        print("4. Optional: Erstelle Alias auf dem Desktop")
        print("\nStarten: Doppelklick auf die App!")
    else:
        print("\n❌ Fehler beim Erstellen der App")
        print("Prüfe die Fehlermeldungen oben.")
        sys.exit(1)


def convert_icon():
    """Konvertiert PNG zu ICNS für macOS"""
    png_path = Path('data/app_icon.png')
    icns_path = Path('data/app_icon.icns')
    
    if not png_path.exists():
        print(f"   ⚠ Icon nicht gefunden: {png_path}")
        return None
    
    try:
        # Temporäres iconset-Verzeichnis erstellen
        iconset_path = Path('data/app_icon.iconset')
        iconset_path.mkdir(exist_ok=True)
        
        # Verschiedene Größen für macOS generieren
        sizes = [
            (16, 'icon_16x16.png'),
            (32, 'icon_16x16@2x.png'),
            (32, 'icon_32x32.png'),
            (64, 'icon_32x32@2x.png'),
            (128, 'icon_128x128.png'),
            (256, 'icon_128x128@2x.png'),
            (256, 'icon_256x256.png'),
            (512, 'icon_256x256@2x.png'),
            (512, 'icon_512x512.png'),
            (1024, 'icon_512x512@2x.png'),
        ]
        
        for size, filename in sizes:
            output = iconset_path / filename
            subprocess.run([
                'sips',
                '-z', str(size), str(size),
                str(png_path),
                '--out', str(output)
            ], check=True, capture_output=True)
        
        # iconset zu icns konvertieren
        subprocess.run([
            'iconutil',
            '-c', 'icns',
            str(iconset_path),
            '-o', str(icns_path)
        ], check=True, capture_output=True)
        
        # Aufräumen
        import shutil
        shutil.rmtree(iconset_path)
        
        return str(icns_path)
        
    except Exception as e:
        print(f"   ⚠ Fehler bei Icon-Konvertierung: {e}")
        return None


def update_spec_icon(spec_file: Path, icon_path: str) -> None:
    """Aktualisiert Icon-Pfad in existierender .spec Datei"""
    try:
        content = spec_file.read_text(encoding='utf-8')
        # Icon-Zeile ersetzen
        content = content.replace(
            "icon=None,",
            f"icon='{icon_path}',"
        )
        spec_file.write_text(content, encoding='utf-8')
        print("   ✓ Icon-Pfad in .spec Datei aktualisiert")
    except Exception as e:
        print(f"   ⚠ Konnte .spec Datei nicht aktualisieren: {e}")


def create_spec_file(icon_path=None):
    """Erstellt PyInstaller .spec Datei"""
    
    # Icon-Wert für Spec-Datei
    icon_value = f"'{icon_path}'" if icon_path else "None"

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

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
    hooksconfig={{}},
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
    icon={icon_value},
    bundle_identifier='de.abc.co2bilanzierer',
    info_plist={{
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'CO₂-Bilanzierer',
        'CFBundleDisplayName': 'CO₂-Bilanzierer',
        'CFBundleVersion': '2.0',
        'CFBundleShortVersionString': '2.0',
    }},
)
'''

    with open("CO2-Bilanzierer.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)


if __name__ == "__main__":
    build_app()
