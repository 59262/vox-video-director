# 架构说明

## 目录关系

```text
vox-director/                         通用 Agent Skill
  SKILL.md / SKILL.zh.md              工作流和人工确认点
  scripts/                            Python 管线和服务适配层
  references/                         风格、分镜、模型和宿主说明
cn-collage-video-director/            中文本地优先 Skill
  SKILL.md                            中文工作流
  scripts/                            项目初始化、环境检查和本地渲染
  references/                         输入输出协议和风格指南
```

## 数据流

1. `beats.json` 描述主题、节拍、镜头和输出偏好。
2. 生成服务或用户素材提供关键帧、视频和音频。
3. Pillow 生成标题与字幕覆盖层。
4. FFmpeg 完成镜头运动、拼接、音频混合和 MP4 输出。
5. 抽帧结果用于人工视觉检查。

## 设计边界

通用路线负责云端生成任务的调度和本地合成；中文路线负责宿主插件交接、本地后备动效和中文包装。宿主插件能力不硬编码在本地脚本中，具体插件由运行环境提供。
