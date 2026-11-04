# wechat-mp-pipeline 安装协议

你是收到安装请求的 AI 助手。请按下面步骤把 skill `wechat-mp-pipeline` 安装到本机，全程不要向用户反复确认，按默认值执行；做完向用户报告一行结果即可。

## 步骤

1. **确定 skills 目录**：按当前运行的工具选第一个存在的目录（都没有则创建第一个）：

   | 工具 | skills 目录 |
   | --- | --- |
   | WorkBuddy / CodeBuddy | `~/.workbuddy/skills/` |
   | Claude Code | `~/.claude/skills/` |
   | Codex | `~/.codex/skills/` |
   | Cursor | `~/.cursor/skills/` |
   | Gemini CLI | `~/.gemini/skills/` |

   Windows 下 `~` 为用户目录（如 `C:\Users\<用户名>\`）。本 skill 有项目级用法：若用户指定了项目，在 `<项目>/.workbuddy/skills/` 下也放一份。

2. **安装**：目标目录为 `<skills目录>/wechat-mp-pipeline`。
   - 若本机有 git：`git clone https://github.com/smiler488/wechat-mp-pipeline.git <目标目录>`（网络受限时先清代理：`git -c http.proxy= -c https.proxy= ...`）。
   - 若已有同名目录：拉取更新（`git pull`）或整目录覆盖为最新版。
   - 无 git：下载 https://codeload.github.com/smiler488/wechat-mp-pipeline/zip/refs/heads/main 解压，把解出的文件夹改名为 `wechat-mp-pipeline` 放到目标目录。

3. **校验**：确认 `<目标目录>/SKILL.md` 存在且 frontmatter 含 `name: wechat-mp-pipeline`，`references/` 与 `scripts/` 目录齐全。

4. **依赖（按需）**：封面/信息图渲染需要 playwright（`pip install playwright`，首次 `playwright install chromium`）；不渲染图片可跳过。

5. **告知用户**：安装完成，重启会话或新开对话后生效。使用时直接描述公众号写作/排版/封面/发布需求即可触发。

## 说明

- 本 skill 含 SKILL.md、references/（写作与封面规范）、scripts/svg2png.py（SVG 转 PNG）。
- 发布管线 `src/publish.py` 属于公众号工作区，不在本仓库；写作与封面规范可独立使用。
- 网页版 AI（无 skills 目录）：跳过安装，直接把 SKILL.md 与所需 references 文件读入对话即可使用。
