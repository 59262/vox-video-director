# Vox Director

Vox Director 是一个 Agent Skill，将主题组织为分镜，再生成纸片拼贴关键帧、动效、旁白、配乐、字幕和最终 MP4。

## 组件

- `SKILL.md`：英文工作流。
- `SKILL.zh.md`：中文工作流。
- `AGENTS.md`：其他编码 Agent 的入口。
- `scripts/`：关键帧、视频、音频和 FFmpeg 合成脚本。
- `references/`：风格、分镜、模型和本地引擎说明。

## 运行要求

Python 3、Pillow、FFmpeg 和 FFprobe。云端生成服务需要按服务商文档配置运行时凭证；本地合成可以使用已有媒体。

## 工作流

分镜确认 → 风格试片 → 关键帧 → 视频片段 → 旁白/配乐 → FFmpeg 合成。

## 许可证

请阅读同目录 `LICENSE`。
