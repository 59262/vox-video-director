# 项目结构与配置

```text
project/
├── beats.json
├── image-prompts.md
├── video-prompts.md
├── keyframes/
│   ├── beat-01.png
│   └── beat-02.png
├── generated-clips/
│   ├── beat-01.mp4
│   └── beat-02.mp4
├── audio/
│   ├── narration/
│   └── background-music.*
├── overlays/
├── clips/
├── qa/
└── final.mp4
```

`beats.json` 最小结构：

```json
{
  "project": "example",
  "topic": "主题",
  "language": "zh-CN",
  "aspect": "9:16",
  "duration": 30,
  "resolution": [1080, 1920],
  "fps": 25,
  "voice": {
    "provider": "edge-tts",
    "voice_id": "zh-CN-YunyangNeural",
    "rate": "+8%"
  },
  "beats": [
    {
      "id": 1,
      "title": "标题",
      "narration": "这一段的中文旁白。",
      "duration": 5,
      "image_prompt": "无字纸片拼贴关键帧提示词",
      "video_prompt": "克制的图生视频动作提示词",
      "motion": "zoom_in"
    }
  ]
}
```

支持 `9:16`、`16:9` 和 `1:1`。每个节拍必须有唯一正整数 `id`、标题、旁白与正数时长。所有节拍时长之和应等于顶层 `duration`；渲染器遇到小误差时以节拍总和为准并给出提示。

图片支持 PNG、JPG 和 WEBP，推荐 PNG。逐节拍旁白支持 MP3、M4A、WAV 和 AAC。若 `audio/background-music.*` 存在，优先使用用户音乐，否则生成简单的本地背景音。

图生视频片段使用 `generated-clips/beat-NN.mp4` 命名。渲染器优先采用片段；没有片段才读取同编号关键帧。`motion` 支持 `zoom_in`、`zoom_out`、`pan_left`、`pan_right` 和 `static`。
