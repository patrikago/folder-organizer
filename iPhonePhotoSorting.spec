from pathlib import Path

from version import __version__


project_dir = Path(SPECPATH)
ffprobe_path = project_dir / "ffmpeg" / "ffprobe.exe"
app_version = __version__


a = Analysis(
    [str(project_dir / "app.py")],
    pathex=[str(project_dir)],
    binaries=[(str(ffprobe_path), "ffmpeg")],
    datas=[
        (str(project_dir / "ui"), "ui"),
        (str(project_dir / "assets"), "assets")
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)


pyz = PYZ(a.pure)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="iPhonePhotoSorting",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="iPhonePhotoSorting"
)