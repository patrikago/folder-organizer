# folder-organizer
Folder organizer for straight forward iphone photo transfers

## Build dependency: ffprobe.exe

`ffprobe.exe` is required by the PyInstaller build but is not included in this
repo (it's a large binary, ~98 MB). Before running `pyinstaller iPhonePhotoSorting.spec`:

1. Download the official FFmpeg Windows build from https://www.gyan.dev/ffmpeg/builds/ (or https://ffmpeg.org/download.html)
2. Extract the archive and copy `ffprobe.exe` from its `bin/` folder
3. Place it at `ffmpeg/ffprobe.exe` in this project's root

