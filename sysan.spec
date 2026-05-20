# Сборка ОСХ-Аналитик под Windows (single-folder).
# Результат: dist/OSH-Analitik/OSH-Analitik.exe
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = [
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtPrintSupport",
]
hiddenimports += collect_submodules("scipy")
hiddenimports += collect_submodules("sklearn")
hiddenimports += collect_submodules("matplotlib.backends")

datas = [
    ("app/resources/styles/dark.qss", "app/resources/styles"),
    ("app/resources/icons", "app/resources/icons"),
    ("samples", "samples"),
]

a = Analysis(
    ["app/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OSH-Analitik",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon="app/resources/icons/osh-analitik.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="OSH-Analitik",
)
