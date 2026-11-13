# 使用说明

## 通用管线

进入 `vox-director/`，阅读 `SKILL.md` 和 `AGENTS.md`，按分镜、关键帧、视频、音频、合成顺序运行 `scripts/` 中的脚本。运行时需要 Python、Pillow、FFmpeg 和 FFprobe；云端模型的凭证按对应服务商文档配置。

## 中文本地管线

进入 `cn-collage-video-director/`，使用：

```bash
python scripts/init_project.py --output <项目目录> --topic "示例主题" --duration 30 --aspect 9:16
python scripts/check_env.py
python scripts/render_local.py --project <项目目录> --skip-tts
```

关键帧放在 `keyframes/`，可选视频片段放在 `generated-clips/`，逐节拍音频放在 `audio/narration/`。

## 输出

渲染器会在项目目录生成最终 MP4、字幕/标题覆盖层、拼接中间文件和抽帧质检图。生成内容和运行时产物不属于本源码包。
