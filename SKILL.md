---
name: wechat-mp-pipeline
description: smiler488 微信公众号的全流程生产线——从选题写稿、排版预览、封面设计（Wong 色板 + 创意总监 V2 规范）、PDF 外链托管（腾讯文档/smiler488.com），到推送草稿箱与发布确认。当任务涉及为 smiler488 公众号写稿、改稿、做封面、排版、生成预览、托管附件、推草稿或发布时自动加载。触发词：公众号、写稿、封面、排版、推草稿、发布、smiler488。
agent_created: true
---

# smiler488 公众号生产管线

## Overview

为良超的个人公众号 smiler488 生产文章的完整工作流。所有写作、视觉、排版、发布规范均已沉淀在 references/ 中，**严格按规范执行，不要凭通用知识自由发挥**。

## 工作区结构（路径均为本仓库内相对路径）

- `articles/` — Markdown 原稿（front matter 见下）
- `previews/` — 排版预览 HTML（`src/publish.py render` 生成）
- `assets/` — 封面（900×383）与正文配图
- `templates/ending_block.html` — 结尾固定块（渲染时自动附加）
- `src/publish.py` — 渲染/草稿/发布管线（render / draft / update / delete / publish / status / drafts / ip）
- `docs/文献解读类公众号SOP.md` — 文献学习栏目专项 SOP

## 文章 front matter 规范

```yaml
---
title: 标题
author: smiler488          # 固定署名，不要写"良超"
digest: 摘要（显示在分享卡片）
cover: ../assets/xxx_封面_900x383.png
source_url: <外链>          # 需要外链时用（正文禁外链，固定走【阅读原文】）
comment: 1
---
```

## 标准流水线（按序执行）

1. **写稿**：读 `references/writing-style.md`（文风铁律）。文献解读类另读 `docs/文献解读类公众号SOP.md`（五段式定稿）。
2. **排版预览**：`python3 src/publish.py render "articles/<稿>.md"` → previews/ 生成，present_files 交付审阅。
3. **封面**：读 `references/cover-design.md`（Wong 色板 + 创意视觉总监 V2 六阶段）。**防模板化铁律：只有文献学习栏目用固定格式，其余栏目每张封面必须重新提炼概念，且先查「封面案例档案」确认构图不重复**；概念必须对准文章核心母题而非单一数据点。SVG 手写后用 `scripts/svg2png.py` 渲染成 900×383 PNG，**先用 ViewImage 自检再交付**。
4. **外链托管**（需要时）：读 `references/publishing-ops.md` 的腾讯文档分发手册（单附件 ≤10MB，超限拆分册）。
5. **推草稿箱**：`python3 src/publish.py draft "articles/<稿>.md"`。
6. **发布**：publish 不可逆——**必须等良超明确确认后**才执行 `publish`。

## 渲染脚本

`python3 scripts/svg2png.py <in.svg> <out.png> [宽] [高]` — 用 Playwright + 本机缓存的 Chrome for Testing 渲染 SVG→PNG（Chrome.app headless 在本机不稳定，勿用）。ImageGen 生成的图需先去右下角"AI生成"水印（差异像素定位 + 邻近条带覆盖修补，见 publishing-ops.md）。
