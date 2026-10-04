# 父母学葡语 · 莫桑比克生活葡语（离线 PWA）

给父母用的葡萄牙语学习手册：203 条中葡对照学习卡（14 章 + 地名按省分组），
内置 pt-PT（欧洲葡语）神经网络语音，可添加到 iPhone 主屏幕、完全离线使用。

- 语音引擎（两套内置，页面内可切换）：
  - 声音一：Google Translate TTS（`tl=pt-PT`，欧洲葡语口音女声，`tools/gen_audio.py`）
  - 声音二：macOS `say` 的 Reed（苹果葡语合成（巴西口音），与 iPhone 上的 Reed 同源，
    `tools/gen_audio_reed.py`，本地生成）
  - 备选升级：edge-tts（Azure 神经网络 pt-PT：Fernanda/Duarte，质量最好），
    但本网络连通性极不稳定（2026-10-04 当天两次尝试，除偶发单次成功外全部被拒），
    `tools/gen_audio_azure.py` 带重试，网络畅通时跑完再 `build_html.py` 即可整批替换。
- 慢读按钮 = 同一音频 0.78 倍速重放（保音高）。
- 机器合成音不是莫桑比克真人录音；将来拿到真人录音后可整批替换。

## 目录结构

```
index.html            最终交付页（音频已 base64 内嵌，单文件自包含）
sw.js                 Service Worker（离线缓存）
manifest.webmanifest  PWA 清单
icon-*.png            主屏幕图标
entries.json          从 v5 提取的 203 条词条（id / section / pt）
tools/extract.py      从 v5 HTML 提取词条 → entries.json
tools/gen_audio.py    声音一：Google TTS (tl=pt-PT) → audio/main/*.mp3
tools/gen_audio_joana.py  声音二：macOS say Joana (pt-PT) → audio/joana/*.m4a
tools/gen_audio_azure.py  备选：edge-tts Azure 神经声音（网络畅通时用）
tools/make_icons.py   生成图标
tools/style.css       设计系统（make_src 会嵌入）
tools/make_src.py     v5 + 新样式/页眉/最终文案 → src/handbook.html
tools/app.js          页面主脚本（内置音频 + 系统声音双通道）
tools/build_html.py   总装：src + 内嵌字体 + 音频 + app.js → index.html
audio/                原始音频（未入库，可随时重新生成）
```

源文件：`/Users/kevinchen/Downloads/Mozambique_Portuguese_v5_SelectableVoices.html`（v5，203 条）。

## 重新构建

```bash
cd parents-pt-app
.venv/bin/python tools/extract.py     # 仅当源 HTML 变化时
.venv/bin/python tools/gen_audio.py   # 生成/补齐音频（增量，已有文件会跳过）
.venv/bin/python tools/build_html.py  # 总装出 index.html
```

## 更新线上版本

1. 重新构建出新的 `index.html`；
2. 修改 `sw.js` 里的 `CACHE` 版本号（`pt-handbook-v1` → `v2`）；
3. 提交并推送：

```bash
git add -A && git commit -m "update content" && git push
```

GitHub Pages 会在一两分钟内更新；父母手机联网打开一次后自动取到新版。

## 父母 iPhone 安装步骤（一次性）

1. 在有 WiFi 处，用 **Safari** 打开网站链接，等页面完全加载；
2. 点两三条"听读"确认有声音；
3. Safari 底部"分享"按钮 →"添加到主屏幕"；
4. 建议当场开飞行模式，点开主屏幕图标再听一条，确认离线可用。

之后无网络也能正常使用；图标被误删时，重新打开链接再"添加到主屏幕"即可。
