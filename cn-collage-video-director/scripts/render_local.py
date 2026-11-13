#!/usr/bin/env python3
"""Render a beats.json collage-video project with Pillow, Edge TTS and FFmpeg."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFilter, ImageFont


IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
AUDIO_EXTS = (".mp3", ".m4a", ".wav", ".aac", ".ogg")
VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv")
TEAL = (11, 73, 78, 255)
ORANGE = (229, 83, 31, 255)
CREAM = (247, 230, 196, 255)
INK = (24, 27, 26, 255)


def run(args: Iterable[str | Path], quiet: bool = False) -> None:
    cmd = [str(item) for item in args]
    if not quiet:
        print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def find_binary(name: str) -> str:
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
    raise RuntimeError(f"找不到 {name}。请安装 FFmpeg 或运行 pip install ffmpeg-binaries。")


def find_edge_tts() -> str | None:
    direct = shutil.which("edge-tts")
    if direct:
        return direct
    scripts = Path(sys.executable).parent / "Scripts" / "edge-tts.exe"
    return str(scripts) if scripts.exists() else None


def find_font(bold: bool = True) -> Path:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise RuntimeError("找不到中文字体。请安装 Microsoft YaHei 或 Noto Sans CJK。")


def find_numbered_file(folder: Path, index: int, extensions: tuple[str, ...]) -> Path | None:
    stem = f"beat-{index:02d}"
    return next((folder / f"{stem}{ext}" for ext in extensions if (folder / f"{stem}{ext}").exists()), None)


def probe_duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def validate(doc: dict) -> tuple[int, int, int, list[dict], float]:
    beats = doc.get("beats")
    if not isinstance(beats, list) or not beats:
        raise ValueError("beats.json 必须包含非空 beats 数组。")
    width, height = map(int, doc.get("resolution", (1080, 1920)))
    fps = int(doc.get("fps", 25))
    if min(width, height, fps) <= 0:
        raise ValueError("resolution 和 fps 必须为正数。")
    seen: set[int] = set()
    for beat in beats:
        idx = int(beat.get("id", 0))
        if idx <= 0 or idx in seen:
            raise ValueError("每个 beat.id 必须是唯一正整数。")
        seen.add(idx)
        beat["id"] = idx
        beat["title"] = str(beat.get("title", beat.get("title_cn", f"节拍 {idx}")))
        beat["narration"] = str(beat.get("narration", "")).strip()
        beat["duration"] = float(beat.get("duration", float(doc.get("duration", 30)) / len(beats)))
        if beat["duration"] <= 0 or not beat["narration"]:
            raise ValueError(f"beat-{idx:02d} 缺少旁白或有效时长。")
    total = sum(beat["duration"] for beat in beats)
    declared = float(doc.get("duration", total))
    if abs(total - declared) > 0.05:
        print(f"提示：顶层 duration={declared:.2f}s，与节拍合计 {total:.2f}s 不同；以节拍合计为准。")
    return width, height, fps, beats, total


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for char in text:
        if char == "\n":
            if current:
                lines.append(current)
            current = ""
            continue
        candidate = current + char
        if current and text_width(draw, candidate, font) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def fit_font(text: str, max_width: int, start: int, minimum: int, font_path: Path) -> ImageFont.FreeTypeFont:
    draw = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for size in range(start, minimum - 1, -2):
        font = ImageFont.truetype(str(font_path), size)
        if text_width(draw, text, font) <= max_width:
            return font
    return ImageFont.truetype(str(font_path), minimum)


def make_overlays(root: Path, beats: list[dict], width: int, height: int) -> tuple[Path, Path]:
    title_dir = root / "overlays" / "titles"
    caption_dir = root / "overlays" / "captions"
    title_dir.mkdir(parents=True, exist_ok=True)
    caption_dir.mkdir(parents=True, exist_ok=True)
    font_path = find_font(True)
    unit = min(width, height)
    for beat in beats:
        idx = beat["id"]
        title_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(title_layer)
        font = fit_font(beat["title"], int(width * 0.82), int(unit * 0.12), int(unit * 0.065), font_path)
        tw = text_width(draw, beat["title"], font)
        x, y = (width - tw) // 2, int(height * 0.06)
        shadow = Image.new("RGBA", title_layer.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.text((x + 8, y + 10), beat["title"], font=font, fill=(0, 0, 0, 145), stroke_width=5, stroke_fill=(0, 0, 0, 145))
        title_layer = Image.alpha_composite(title_layer, shadow.filter(ImageFilter.GaussianBlur(4)))
        draw = ImageDraw.Draw(title_layer)
        draw.text((x, y), beat["title"], font=font, fill=TEAL, stroke_width=max(2, unit // 360), stroke_fill=CREAM)
        draw.line((x, y + font.size + 12, x + tw, y + font.size + 12), fill=ORANGE, width=max(4, unit // 140))
        title_layer.save(title_dir / f"beat-{idx:02d}.png")

        caption_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(caption_layer)
        caption_font = ImageFont.truetype(str(font_path), max(24, int(unit * 0.045)))
        lines = wrap_text(draw, beat["narration"], caption_font, int(width * 0.82))
        line_height = int(caption_font.size * 1.4)
        box_height = line_height * len(lines) + int(unit * 0.035)
        margin = int(width * 0.05)
        bottom = int(height * 0.95)
        top = bottom - box_height
        draw.rounded_rectangle((margin, top, width - margin, bottom), radius=max(12, unit // 40), fill=(8, 42, 45, 220), outline=ORANGE, width=max(3, unit // 220))
        cy = top + int(unit * 0.015)
        for line in lines:
            lw = text_width(draw, line, caption_font)
            draw.text(((width - lw) / 2, cy), line, font=caption_font, fill=CREAM, stroke_width=1, stroke_fill=INK)
            cy += line_height
        caption_layer.save(caption_dir / f"beat-{idx:02d}.png")
    return title_dir, caption_dir


def tempo_chain(ratio: float) -> str:
    parts: list[float] = []
    while ratio > 2.0:
        parts.append(2.0)
        ratio /= 2.0
    while ratio < 0.5:
        parts.append(0.5)
        ratio /= 0.5
    parts.append(ratio)
    return ",".join(f"atempo={value:.5f}" for value in parts)


def make_narration(root: Path, doc: dict, beats: list[dict], ffmpeg: str, ffprobe: str, skip_tts: bool) -> list[Path]:
    narration_dir = root / "audio" / "narration"
    raw_dir = root / "audio" / "raw"
    narration_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    edge_tts = find_edge_tts()
    voice = doc.get("voice", {})
    results: list[Path] = []
    for beat in beats:
        idx, target = beat["id"], beat["duration"]
        existing = find_numbered_file(narration_dir, idx, AUDIO_EXTS)
        if existing and existing.suffix.lower() != ".m4a":
            source = existing
        elif existing:
            source = existing
        elif skip_tts:
            raise FileNotFoundError(f"缺少 audio/narration/beat-{idx:02d}.*")
        else:
            if not edge_tts:
                raise RuntimeError("找不到 edge-tts。可安装 edge-tts，或提供逐节拍音频后使用 --skip-tts。")
            source = raw_dir / f"beat-{idx:02d}.mp3"
            run([edge_tts, "--voice", voice.get("voice_id", "zh-CN-YunyangNeural"), "--rate", voice.get("rate", "+8%"), "--text", beat["narration"], "--write-media", source])
        output = narration_dir / f"normalized-{idx:02d}.m4a"
        source_duration = probe_duration(ffprobe, source)
        spoken_target = max(0.5, target - 0.28)
        ratio = source_duration / spoken_target
        audio_filter = f"{tempo_chain(ratio)},apad,atrim=0:{target:.3f}"
        run([ffmpeg, "-y", "-loglevel", "error", "-i", source, "-af", audio_filter, "-c:a", "aac", "-b:a", "160k", output])
        results.append(output)
    return results


def synth_music(output: Path, seconds: float, sample_rate: int = 22050) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    total_samples = int(seconds * sample_rate)
    roots = (73.42, 87.31, 65.41, 98.0)
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            root = roots[int(t // 5) % len(roots)]
            pad = math.sin(2 * math.pi * root * t) + 0.45 * math.sin(2 * math.pi * root * 1.5 * t + 0.4)
            pulse = math.sin(2 * math.pi * root * 2 * t) * math.exp(-(t % 0.5) * 12)
            fade = max(0.0, min(1.0, t, (seconds - t) / 1.5))
            value = max(-1.0, min(1.0, fade * (0.09 * pad + 0.035 * pulse)))
            frames.extend(struct.pack("<h", int(value * 32767)))
        wav.writeframes(frames)


def image_motion_filter(motion: str, width: int, height: int, fps: int, frames: int) -> str:
    motion = motion.lower()
    if motion == "zoom_out":
        zoom, x, y = "if(eq(on,1),1.09,max(zoom-0.00075,1.0))", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "pan_left":
        zoom, x, y = "1.08", "max(0,(iw-iw/zoom)*(1-on/%d))" % max(1, frames - 1), "ih/2-(ih/zoom/2)"
    elif motion == "pan_right":
        zoom, x, y = "1.08", "min(iw-iw/zoom,(iw-iw/zoom)*on/%d)" % max(1, frames - 1), "ih/2-(ih/zoom/2)"
    elif motion == "static":
        zoom, x, y = "1.0", "0", "0"
    else:
        zoom, x, y = "min(zoom+0.00075,1.09)", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    return f"zoompan=z='{zoom}':d={frames}:x='{x}':y='{y}':s={width}x{height}:fps={fps}"


def render_clips(root: Path, beats: list[dict], width: int, height: int, fps: int, ffmpeg: str, title_dir: Path, caption_dir: Path) -> list[Path]:
    clip_dir = root / "clips"
    clip_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    for beat in beats:
        idx, seconds = beat["id"], beat["duration"]
        generated_video = find_numbered_file(root / "generated-clips", idx, VIDEO_EXTS)
        image = find_numbered_file(root / "keyframes", idx, IMAGE_EXTS)
        if not generated_video and not image:
            raise FileNotFoundError(f"缺少 generated-clips/beat-{idx:02d}.mp4 或 keyframes/beat-{idx:02d}.png")
        output = clip_dir / f"beat-{idx:02d}.mp4"
        frames = max(1, round(seconds * fps))
        if generated_video:
            source_args: list[str | Path] = ["-stream_loop", "-1", "-i", generated_video]
            base_filter = (
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},fps={fps},trim=duration={seconds:.3f},setpts=PTS-STARTPTS[base]"
            )
            print(f"beat-{idx:02d}: 使用图生视频片段 {generated_video.name}")
        else:
            scaled_w, scaled_h = math.ceil(width * 1.16 / 2) * 2, math.ceil(height * 1.16 / 2) * 2
            source_args = ["-loop", "1", "-i", image]
            motion_filter = image_motion_filter(str(beat.get("motion", "zoom_in")), width, height, fps, frames)
            base_filter = (
                f"[0:v]scale={scaled_w}:{scaled_h}:force_original_aspect_ratio=increase,"
                f"crop={scaled_w}:{scaled_h},{motion_filter}[base]"
            )
            print(f"beat-{idx:02d}: 无图生视频片段，使用本地 {beat.get('motion', 'zoom_in')} 动效")
        filters = base_filter + (
            f";[base][1:v]overlay=0:0:enable='lt(t,{seconds * 0.58:.3f})'[titled];"
            "[titled][2:v]overlay=0:0[v]"
        )
        run([ffmpeg, "-y", "-loglevel", "error", *source_args, "-loop", "1", "-i", title_dir / f"beat-{idx:02d}.png", "-loop", "1", "-i", caption_dir / f"beat-{idx:02d}.png", "-filter_complex", filters, "-map", "[v]", "-t", f"{seconds:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", output])
        clips.append(output)
    return clips


def concat_files(ffmpeg: str, files: list[Path], list_file: Path, output: Path, audio: bool = False) -> None:
    list_file.write_text("".join(f"file '{path.resolve().as_posix()}'\n" for path in files), encoding="utf-8")
    codec_args = ["-c:a", "aac", "-b:a", "160k"] if audio else ["-c", "copy"]
    run([ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", list_file, *codec_args, output])


def choose_music(root: Path, total: float) -> Path:
    audio_dir = root / "audio"
    for ext in AUDIO_EXTS:
        candidate = audio_dir / f"background-music{ext}"
        if candidate.exists():
            return candidate
    output = audio_dir / "procedural-score.wav"
    synth_music(output, total)
    return output


def mix_final(root: Path, body: Path, narration: Path, music: Path, total: float, ffmpeg: str) -> Path:
    output = root / "final.mp4"
    filters = (
        f"[1:a]apad,atrim=0:{total:.3f},asplit=2[narrA][narrB];"
        f"[2:a]atrim=0:{total:.3f},volume=0.34,afade=t=in:st=0:d=0.8,afade=t=out:st={max(0.0, total - 1.5):.3f}:d=1.5[bg];"
        "[bg][narrA]sidechaincompress=threshold=0.025:ratio=9:attack=8:release=280[ducked];"
        f"[narrB][ducked]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.95,atrim=0:{total:.3f}[audio]"
    )
    run([ffmpeg, "-y", "-loglevel", "error", "-i", body, "-i", narration, "-i", music, "-filter_complex", filters, "-map", "0:v", "-map", "[audio]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", output])
    return output


def make_contact_sheet(root: Path, final: Path, beats: list[dict], width: int, height: int, ffmpeg: str) -> Path:
    qa = root / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    times, cursor = [], 0.0
    for beat in beats:
        times.append(cursor + beat["duration"] / 2)
        cursor += beat["duration"]
    frames: list[Image.Image] = []
    thumb_w = 270
    thumb_h = max(1, round(thumb_w * height / width))
    for idx, second in enumerate(times, 1):
        frame = qa / f"frame-{idx:02d}.jpg"
        run([ffmpeg, "-y", "-loglevel", "error", "-ss", f"{second:.3f}", "-i", final, "-vf", f"scale={thumb_w}:{thumb_h}", "-frames:v", "1", frame], quiet=True)
        frames.append(Image.open(frame).convert("RGB"))
    cols = min(3, len(frames))
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGB", (thumb_w * cols, thumb_h * rows), (20, 20, 20))
    for idx, frame in enumerate(frames):
        sheet.paste(frame, ((idx % cols) * thumb_w, (idx // cols) * thumb_h))
    output = qa / "contact-sheet.jpg"
    sheet.save(output, quality=90)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--skip-tts", action="store_true", help="Use existing audio/narration/beat-NN audio files")
    args = parser.parse_args()
    root = args.project.resolve()
    config = root / "beats.json"
    if not config.exists():
        raise FileNotFoundError(config)
    doc = json.loads(config.read_text(encoding="utf-8"))
    width, height, fps, beats, total = validate(doc)
    ffmpeg, ffprobe = find_binary("ffmpeg"), find_binary("ffprobe")
    title_dir, caption_dir = make_overlays(root, beats, width, height)
    narration_files = make_narration(root, doc, beats, ffmpeg, ffprobe, args.skip_tts)
    clips = render_clips(root, beats, width, height, fps, ffmpeg, title_dir, caption_dir)
    body = root / "clips" / "body-silent.mp4"
    concat_files(ffmpeg, clips, root / "clips" / "video-concat.txt", body)
    narration = root / "audio" / "narration-track.m4a"
    concat_files(ffmpeg, narration_files, root / "audio" / "narration-concat.txt", narration, audio=True)
    final = mix_final(root, body, narration, choose_music(root, total), total, ffmpeg)
    sheet = make_contact_sheet(root, final, beats, width, height, ffmpeg)
    print(f"FINAL={final}")
    print(f"DURATION={probe_duration(ffprobe, final):.3f}")
    print(f"QA={sheet}")


if __name__ == "__main__":
    main()
