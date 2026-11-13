# Vox 视频项目源码

这是一个面向 Agent 的 AI 视频制作源码集合，包含通用 Vox Director 管线和中文本地优先管线。包内只包含源码、Skill 工作流、参考架构、示例说明和必要许可证文件。

## 目录

- `vox-director/`：Python + FFmpeg + Pillow 的通用视频管线和 Agent Skill。
- `cn-collage-video-director/`：中文纸片拼贴视频的本地渲染 Skill。
- `docs/architecture.md`：组件关系和数据流。
- `docs/usage.md`：最小使用说明。

## 环境

Python 3.10+、Pillow、FFmpeg 和 FFprobe。云端生成路线还需要按服务商文档配置运行时凭证；本地路线可以使用宿主生成的关键帧、视频和音频。

## 基本流程

1. 用 `beats.json` 描述主题和节拍。
2. 生成或准备关键帧、视频片段和旁白。
3. 使用对应管线脚本完成字幕、动效、音频混合和 FFmpeg 合成。
4. 输出 MP4 和质检抽帧。

## 许可证

请阅读包内 `LICENSE`。媒体、字体、模型输出和外部服务内容不包含在此源码包中。
