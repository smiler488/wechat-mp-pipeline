# wechat-mp-pipeline

smiler488 微信公众号生产管线（WorkBuddy Skill）——把一篇公众号文章的完整工作流沉淀为可自动触发的技能：选题写稿 → 排版预览 → 封面设计 → 外链托管 → 推送草稿 → 确认发布。

## 包含内容

| 文件 | 内容 |
|------|------|
| `SKILL.md` | 主流水线、front matter 规范、触发词 |
| `references/writing-style.md` | 文风铁律 + **去 AI 味七刀法**（实证沉淀）+ **术语/缩写首现必括注**（中文（原文全称，一句解释），有日常义的专业词必括）+ 排版基准（含配图铁律、大表格图片化） |
| `references/cover-design.md` | **创意视觉总监 V2 六阶段** + Wong（Okabe–Ito）色板 + 防模板化铁律 + 封面案例档案 |
| `references/publishing-ops.md` | publish.py 命令手册、腾讯文档大文件分发手册（10MB 附件上限拆分册）、渲染与跨端同步指引 |
| `scripts/svg2png.py` | SVG→PNG 跨平台渲染器（Playwright → Chrome for Testing → 系统 Chrome 三级回退） |

## 核心设计原则

- **去 AI 味**：砍导游式过渡句、元评论、自我标榜；口语化吐槽保留
- **封面**：一张封面一个核心概念，概念对准文章母题；Wong 色盲友好色板；只有「文献学习」栏目用固定格式，其余栏目禁止套模板
- **事实核查**：关键数字必须回到一手来源核实，媒体口径与原文冲突时以原文为准
- **术语首现必括注**：专业名词与缩写首现给 `中文（原文全称，一句解释）`，解释说明"衡量什么"，不只换同义词

## 多机使用注意（云同步环境）

本仓库的部署副本可能位于 OneDrive 等云同步目录内。多机编辑时 OneDrive 会生成 `*-<设备名>` 冲突副本（`.gitignore` 已屏蔽，不会提交）。**纪律：每台机器改完即 push；换机开工前先 pull。** 若 git 历史出现不可快进的同步异常，先备份工作区再处理，不要硬合并。

## 安装

1. 直接安装：在 WorkBuddy 中对 Agent 说「安装 GitHub 上的 skill：smiler488/wechat-mp-pipeline」
2. 手动安装：将本仓库内容复制到 `~/.workbuddy/skills/wechat-mp-pipeline/`（用户级，跨项目生效）或 `<项目>/.workbuddy/skills/wechat-mp-pipeline/`（项目级）
3. Release 附件提供打包好的 `wechat-mp-pipeline.zip`

## 依赖

- 封面/信息图渲染：`pip install playwright`（首次使用执行 `playwright install chromium`，或复用本机已有的 Chrome for Testing / 系统 Chrome）
- 发布管线 `src/publish.py` 属于 smiler488 公众号工作区（未包含在本仓库中）；写作与封面规范可独立使用

## License

MIT © smiler488
