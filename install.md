# wechat-mp-pipeline 安装说明（给 AI 助手）

> 用户只需对 AI 助手说：
> `请根据 https://raw.githubusercontent.com/smiler488/wechat-mp-pipeline/main/install.md，安装 wechat-mp-pipeline。`

你是收到安装请求的 AI 助手。按下面的步骤把 Agent Skill `wechat-mp-pipeline` 装到本机，用默认值直接执行，不需要每一步都征求确认。只有一种情况要先问用户：目标目录已经存在、而且不是本仓库的 git 克隆（可能是用户自己改过的版本）。装完用一两句话告诉用户结果。

## 1. 确定安装目录

按当前运行的工具选择 skills 目录；如果目录还不存在就创建它：

| 工具 | 用户级 skills 目录 |
| --- | --- |
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| WorkBuddy / CodeBuddy | `~/.workbuddy/skills/` |
| Cursor | `~/.cursor/skills/` |
| Gemini CLI | `~/.gemini/skills/` |

- 用户说只在当前项目里用时，改用项目内的目录，例如 `<项目>/.claude/skills/`。
- Windows 上 `~` 指 `C:\Users\<用户名>`。
- 目标目录记为 `TARGET = <skills 目录>/wechat-mp-pipeline`。目录名必须是 `wechat-mp-pipeline`，和 SKILL.md 里的 `name` 一致。

## 2. 下载

**有 git 时（推荐，方便以后更新）**

```bash
git clone --depth 1 https://github.com/smiler488/wechat-mp-pipeline.git "$TARGET"
```

如果 `TARGET` 已经是本仓库的克隆，改为更新：

```bash
git -C "$TARGET" pull --ff-only
```

**没有 git，macOS / Linux：**

```bash
mkdir -p "$TARGET"
curl -fsSL https://codeload.github.com/smiler488/wechat-mp-pipeline/tar.gz/refs/heads/main \
  | tar -xz --strip-components=1 -C "$TARGET"
```

**没有 git，Windows PowerShell：**

```powershell
$Target = "$HOME\.claude\skills\wechat-mp-pipeline"   # 按第 1 步换成实际目录
$Zip = "$env:TEMP\wechat-mp-pipeline.zip"
Invoke-WebRequest https://codeload.github.com/smiler488/wechat-mp-pipeline/zip/refs/heads/main -OutFile $Zip
Expand-Archive $Zip -DestinationPath "$env:TEMP\wechat-mp-pipeline-src" -Force
New-Item -ItemType Directory -Force $Target | Out-Null
Copy-Item "$env:TEMP\wechat-mp-pipeline-src\wechat-mp-pipeline-main\*" $Target -Recurse -Force
```

## 3. 安装依赖

写稿和自检只需要 Python 3。需要渲染封面或信息图（SVG → PNG）时再装：

```bash
python3 -m pip install playwright
python3 -m playwright install chromium   # 本机已有 Chrome 时可以跳过
```

推送和发布用的 `src/publish.py` 属于 smiler488 公众号的工作区，不在本仓库里；没有它也能使用写作和封面规范。

## 4. 检查

- `TARGET/SKILL.md` 存在，开头的 frontmatter 里有 `name: wechat-mp-pipeline`。
- 这些文件也在：`references/writing-style.md`、`references/cover-design.md`、`references/publishing-ops.md`、`scripts/selfcheck.py`、`scripts/svg2png.py`。

缺文件就说明下载不完整，删掉 `TARGET` 后重新执行第 2 步。

## 5. 告诉用户

报告安装路径，并提醒用户：**新开一个会话（或重启工具）后 skill 才会生效**。

用法示例："用 wechat-mp-pipeline 帮我把这篇论文写成公众号稿"、"给这篇稿子做封面"、"推送前跑一下自检"。这个 skill 也有项目级用法：用户指定了公众号工作区时，在 `<工作区>/.workbuddy/skills/` 下也放一份。

## 网页版助手（没有本地文件系统）

跳过安装。把 https://raw.githubusercontent.com/smiler488/wechat-mp-pipeline/main/SKILL.md 和 references/writing-style.md 读进对话，按其中的规范写稿和改稿；封面渲染、自检脚本和推送需要在本机运行。

## 卸载

删除 `TARGET` 目录即可。

---

## English

Tell your assistant: `Install wechat-mp-pipeline following https://raw.githubusercontent.com/smiler488/wechat-mp-pipeline/main/install.md`

1. Pick the skills folder of the running tool (table above), e.g. `~/.claude/skills/`. Set `TARGET=<folder>/wechat-mp-pipeline`. The folder name must equal the `name` in SKILL.md.
2. `git clone --depth 1 https://github.com/smiler488/wechat-mp-pipeline.git "$TARGET"`. If it already exists as a clone, run `git -C "$TARGET" pull --ff-only` instead. Without git, use the curl or PowerShell commands above.

   Optional for covers: `python3 -m pip install playwright && python3 -m playwright install chromium`. The publishing script lives in the account workspace, not in this repository.
3. Check that `TARGET/SKILL.md` has `name: wechat-mp-pipeline` and that `references/writing-style.md`, `references/cover-design.md`, `references/publishing-ops.md`, `scripts/selfcheck.py`, `scripts/svg2png.py` exist.
4. Tell the user where it was installed and that a new session is needed. Example: "use wechat-mp-pipeline to turn this paper into an article".

Chat-only assistants: read SKILL.md and references/writing-style.md from the raw URLs; rendering, the checker and publishing need a local machine.

Uninstall: delete `TARGET`.
