#!/usr/bin/env python3
"""Create a portable collage-video project with a beat template."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ASPECTS = {"9:16": [1080, 1920], "16:9": [1920, 1080], "1:1": [1080, 1080]}


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text).strip("-").lower()
    return slug or "collage-video"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--duration", type=float, default=30)
    parser.add_argument("--aspect", choices=ASPECTS, default="9:16")
    parser.add_argument("--beats", type=int, default=6)
    args = parser.parse_args()
    if args.duration <= 0 or args.beats <= 0:
        parser.error("duration and beats must be positive")

    root = args.output.resolve()
    for name in ("keyframes", "generated-clips", "audio/narration", "overlays", "clips", "qa"):
        (root / name).mkdir(parents=True, exist_ok=True)
    beat_duration = round(args.duration / args.beats, 3)
    beats = []
    for idx in range(1, args.beats + 1):
        beats.append({
            "id": idx,
            "title": f"节拍 {idx}",
            "narration": "请填写这一段的中文旁白。",
            "duration": beat_duration,
            "image_prompt": "请填写无文字、无水印的纸片拼贴关键帧提示词。",
            "video_prompt": "请填写主体稳定、分层克制的图生视频动作提示词。",
            "motion": "zoom_in",
        })
    doc = {
        "project": slugify(root.name),
        "topic": args.topic,
        "language": "zh-CN",
        "aspect": args.aspect,
        "duration": args.duration,
        "resolution": ASPECTS[args.aspect],
        "fps": 25,
        "voice": {"provider": "edge-tts", "voice_id": "zh-CN-YunyangNeural", "rate": "+8%"},
        "beats": beats,
    }
    (root / "beats.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    prompts = [f"# {args.topic}：关键帧提示词\n"]
    for beat in beats:
        prompts.append(
            f"## beat-{beat['id']:02d} — {beat['title']}\n\n"
            f"用途：{args.aspect} 无字关键帧\n\n"
            f"提示词：{beat['image_prompt']}\n\n"
            "禁止项：文字、水印、Logo、畸形手、重复主体、照片边框\n\n"
            f"输出文件：keyframes/beat-{beat['id']:02d}.png\n"
        )
    (root / "image-prompts.md").write_text("\n".join(prompts), encoding="utf-8")
    video_prompts = [f"# {args.topic}：图生视频提示词\n"]
    for beat in beats:
        video_prompts.append(
            f"## beat-{beat['id']:02d} — {beat['title']}\n\n"
            f"输入：keyframes/beat-{beat['id']:02d}.png\n\n"
            f"时长：{beat['duration']} 秒\n\n"
            f"提示词：{beat['video_prompt']}\n\n"
            "禁止项：新增文字、主体变形、五官漂移、镜头旋转、闪烁、突然出现新物体\n\n"
            f"输出文件：generated-clips/beat-{beat['id']:02d}.mp4\n"
        )
    (root / "video-prompts.md").write_text("\n".join(video_prompts), encoding="utf-8")
    print(f"项目已创建：{root}")
    print("下一步：编辑 beats.json 和 image-prompts.md，然后将关键帧放入 keyframes/。")


if __name__ == "__main__":
    main()
