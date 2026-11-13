#!/usr/bin/env python3
"""Check the local runtime needed by cn-collage-video-director."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path


def find_ffmpeg(name: str) -> str | None:
    direct = shutil.which(name)
    if direct:
        return direct
    try:
        import ffmpeg  # type: ignore

        if hasattr(ffmpeg, "init"):
            ffmpeg.init()
        candidate = Path(ffmpeg.__file__).parent / "binaries" / "bin" / f"{name}.exe"
        if candidate.exists():
            return str(candidate)
    except Exception:
        pass
    return None


def find_font() -> str | None:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
    ]
    return next((str(path) for path in candidates if path.exists()), None)


def main() -> int:
    checks = {
        "Python >= 3.10": sys.version_info >= (3, 10),
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "FFmpeg": bool(find_ffmpeg("ffmpeg")),
        "FFprobe": bool(find_ffmpeg("ffprobe")),
        "中文字体": bool(find_font()),
    }
    optional = {"Edge TTS（可选）": bool(shutil.which("edge-tts"))}
    for label, ok in checks.items():
        print(f"[{'OK' if ok else 'MISSING'}] {label}")
    for label, ok in optional.items():
        print(f"[{'OK' if ok else 'OPTIONAL'}] {label}")
    if all(checks.values()):
        print("\n环境可用于本地渲染。")
        return 0
    print("\n请安装缺少项：pip install pillow ffmpeg-binaries edge-tts")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
