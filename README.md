# wechat-mp-pipeline

English | [中文](README.zh-CN.md)

The production pipeline behind my WeChat official account (smiler488), written down as an Agent Skill: topic and draft, layout preview, cover design, hosting of attachments, pushing to the draft box, and publishing after confirmation. Most of the account is about crop science, plant phenotyping and AI for research. The rules are written in Chinese because the articles are.

I keep it public because parts of it are useful on their own: the writing rules for explaining field-specific terms to readers from neighbouring fields, the checklist against "AI-sounding" prose, the colour-blind-safe cover palette, and a script that checks a draft before it goes out.

## Contents

| File | What it is |
| --- | --- |
| `SKILL.md` | the pipeline, front-matter rules for articles, trigger phrases |
| `references/writing-style.md` | writing rules: feedback loop, tone, seven cuts against AI-sounding prose, the target reader (scientists from a neighbouring field), first-use glosses for every term and abbreviation, layout |
| `references/cover-design.md` | cover design process, the Wong (Okabe–Ito) palette, rules against template covers, an archive of past covers with the reasons behind them |
| `references/publishing-ops.md` | publishing commands, splitting large PDFs for Tencent Docs, rendering and sync notes |
| `scripts/selfcheck.py` | draft checker: unexplained abbreviations, jargon, AI phrases, byline, title, data/code/evaluation statements, figures, paragraph length. Exit code 1 when something must be fixed |
| `scripts/svg2png.py` | SVG → PNG for covers and figures, with fallbacks: Playwright, then Chrome for Testing, then system Chrome |
| `CHANGELOG.md` | why each rule exists: the feedback that triggered it, the file it changed, the commit |

## Install

Tell your assistant (WorkBuddy, Claude Code, Codex, …):

```text
Install wechat-mp-pipeline following https://raw.githubusercontent.com/smiler488/wechat-mp-pipeline/main/install.md
```

Or clone it into the skills folder of your tool, e.g. `~/.workbuddy/skills/wechat-mp-pipeline/` or `~/.claude/skills/wechat-mp-pipeline/`. `wechat-mp-pipeline.skill` is the same content as an importable package.

Covers and figures need Playwright: `pip install playwright`, then `playwright install chromium` once (or an existing Chrome). The publishing script `src/publish.py` belongs to my account workspace and is not part of this repository. The writing and cover rules work without it.

## Check a draft

```bash
python3 scripts/selfcheck.py articles/draft.md          # ✗ must fix, ⚠ worth a look
python3 scripts/selfcheck.py articles/draft.md --strict # warnings fail too
```

## Changes in this revision

- Removed a non-standard `agent_created` key from the SKILL.md front matter and added `license` and author metadata.
- Two diverging change logs (`CHANGELOG.md` and `references/CHANGELOG.md`) were merged into one.
- English README, a more robust `install.md` (several tools, no-git install, checks), and a rebuilt `.skill` package.

## License

MIT, see [LICENSE](LICENSE). Liangchao Deng (邓良超, smiler488).
