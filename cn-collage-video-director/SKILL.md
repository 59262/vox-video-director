---
name: cn-collage-video-director
description: Create short Chinese paper-collage explainer videos from a topic, including script, beat map, host image generation, image-to-video generation, motion effects, Chinese narration, captions, music, FFmpeg assembly, and visual QA. Use when the user asks for a 中文短视频、竖屏讲解、纸片拼贴视频、历史/科普视频, or wants a Vox Director-style workflow without Atlas Cloud or overseas API keys. Works with mainland host image/video plugins such as those in 豆包工作, prompt handoff, user-supplied assets, and local fallbacks.
---

# 中国拼贴视频导演

把一个主题变成可交付的中文纸片拼贴讲解视频。默认成片为 30 秒、9:16、6 个节拍。除非用户指定，不要求 Atlas Cloud、海外图像 API 或云端视频模型。

## 先选执行路线

按当前宿主能力自动选择，不要为了选择路线打断用户：

1. **宿主图片 + 视频插件**：在豆包工作等宿主中，先调用图片生成插件制作无字关键帧，再调用视频生成插件执行图生视频。这是首选路线。
2. **只有图片插件**：生成关键帧后，用本地镜头运动、纸片覆盖层和转场补齐动效。
3. **国内软件交接**：插件不能由当前会话直接调用时，同时输出 `image-prompts.md` 和 `video-prompts.md`，供用户在豆包、即梦或其他国内工具中批量生成。
4. **现成素材或本地预览**：整理用户素材，或制作清楚标注的占位预览，再用本地渲染器完成。

配音优先使用 Edge TTS；无网络或不可用时，接受用户提供的逐节拍音频。视频动效、字幕、音乐和合成在本地用 Pillow 与 FFmpeg 完成。具体路由见 [references/host-routing.md](references/host-routing.md)。

## 工作流程

### 1. 建立项目

在用户指定目录运行：

```bash
python scripts/init_project.py --output <目录> --topic "主题" --duration 30 --aspect 9:16
```

编辑生成的 `beats.json`。每个节拍只表达一个清楚的信息点，口播总字数通常控制在 90–120 个中文字符。使用事实性内容时核实年代、人物和因果关系。

### 2. 完成两个内容检查点

先展示并确认：

- **节拍图**：标题、旁白、时长和信息顺序。
- **风格样张**：只为第一个节拍生成一张图，确认纸张、色彩、构图和字体方向。

用户已经明确指定结构或风格时，视为已确认，不重复询问。

### 3. 制作关键帧与图生视频

每个节拍生成一张 9:16 或 16:9 的无字图片，保存为：

```text
keyframes/beat-01.png
keyframes/beat-02.png
...
```

图片提示词应包含：主体、时代/场景、分层纸片构图、配色、光线、纵横比和禁止项。避免让图片模型直接生成中文文字；标题和字幕由本地脚本叠加。

图片确认后，逐张交给视频生成插件。每段图生视频使用克制的分层运动：纸片轻微视差、主体稳定、背景缓慢推进、可动小元素短促运动。不要让人物五官漂移，不要让文字或物体凭空出现。生成结果保存为：

```text
generated-clips/beat-01.mp4
generated-clips/beat-02.mp4
...
```

本地渲染器会优先使用这些视频；缺少某段视频时才对该段关键帧应用推近、拉远或横移动效。详细规则见 [references/story-style-guide.md](references/story-style-guide.md)。

### 4. 检查本机环境并渲染

```bash
python scripts/check_env.py
python scripts/render_local.py --project <项目目录>
```

渲染器会生成：

- `final.mp4`：H.264/AAC 成片；
- `qa/contact-sheet.jpg`：均匀抽帧的质检图；
- `overlays/`、`clips/`、`audio/`：中间产物，便于局部重做。

如不使用 Edge TTS，将音频放到 `audio/narration/beat-01.mp3` 等位置并运行：

```bash
python scripts/render_local.py --project <项目目录> --skip-tts
```

### 5. 质检后交付

至少检查：

- 总时长、分辨率和声画同步；
- 中文标题/字幕是否超框、遮挡主体或出现乱码；
- 每个节拍是否有可见运动，图生视频是否出现结构漂移，镜头移动是否过快；
- 人声是否清楚，背景音乐是否在人声下自动压低；
- 首帧是否能在 1 秒内说明主题，结尾是否完整收束。

发现问题时只重做对应关键帧、口播或节拍，不要无理由重跑整个项目。

## 输出原则

- 所有中间文件保存在项目目录，避免依赖特定宿主的临时存储。
- 不声称已经在豆包、即梦等外部软件里完成操作，除非宿主确实提供了对应工具并成功执行。
- 不把 API 密钥写进配置、日志或 Skill 包。
- 用户只要预览时可使用 540×960；正式交付默认 1080×1920、25 fps。
- 配置字段和目录约定见 [references/project-schema.md](references/project-schema.md)。
