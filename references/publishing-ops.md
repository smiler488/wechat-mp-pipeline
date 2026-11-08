# 发布运营手册（技术细节）

## publish.py 命令

```bash
python3 src/publish.py render  "articles/<稿>.md"   # 本地渲染预览 → previews/
python3 src/publish.py draft   "articles/<稿>.md"   # 推送草稿箱
python3 src/publish.py update  "articles/<稿>.md"   # 原地更新草稿（不传 --cover 沿用原封面）
python3 src/publish.py delete  ...                  # 删除草稿
python3 src/publish.py publish ...                  # 发布（不可逆，必须等良超明确确认）
python3 src/publish.py status / drafts / ip         # 状态 / 草稿列表 / 本机公网 IP
```

- 凭证在 `config.json`（勿外泄）；token 缓存在 `.token_cache.json`。
- **IP 白名单**：换网络后需重配，跑 `python3 src/publish.py ip` 取微信实际看到的 IP。
- 草稿列表终端中文乱码是 shell locale 问题，数据本身正常。
- 正文图片走 uploadimg 接口，不占素材库配额。
- mistune 会把中文图片文件名百分号编码进 src，publish.py 解析前已 unquote，中文文件名素材可正常用。

## 摘要长度红线（2026-11-08 推草稿 45004 实证）

- **触发**：【学术招聘】IGZ 宏条形码数据整理与生物信息学博后篇，`digest` 写了 145 字符 / 345 字节，
  `draft` 推送返回 `errcode=45004 description size out of limit`，正文图与双封面已上传但草稿没建成。
  只把摘要压到 108 字符 / 240 字节、其余字段一字不动，重推即成功。
- **规则**：front matter `digest` 一律 **≤120 字符且 ≤300 字节**（两个上限取更严者；微信官方口径为
  120 字，字节上限留保守余量）。摘要只写主题/单位、最关键数字（待遇或样本量）、截止日期，
  删掉「岗位卡片、申请条件逐条说明」这类目录式尾巴。
- **执行**：`scripts/selfcheck.py` 检查 18 在推草稿前 ✗ 阻断。`publish.py` 的 `make_digest` 只在摘要
  缺省时截前 54 字，显式写的摘要不截断，所以长度必须由写稿端控制。
- **存量稿**：已发布、已推草稿的文章不回改；新稿一律按此执行。

## 外链规则（2026-11-03 良超改版）

- **公众号正文禁止外链**。文末"阅读全文"入口走 `content_source_url`：front matter 写 `source_url: <链接>`，推送时由 publish.py 自动写入草稿"原文链接"。
- **文献学习类每篇必写 `source_url: <论文原文地址>`**（DOI 官方页统一 `https://doi.org/<DOI>`，arXiv 写 abs 页），渲染时自动在结尾固定块之后附 CTA「点击阅读全文，查看论文原文地址」（`templates/source_cta.html`）；**CTA 与"原文链接"必须同址**。
- 未确认 CC/OA 许可的论文**只挂原文地址，不分发 PDF**；PDF 托管渠道优先级仍为腾讯文档 > smiler488.com > GitHub Pages（仅供后台自动回复分发），正文不写获取引导语。
- 存量草稿补挂（只改原文链接与结尾 CTA，保留后台手工改动，不重渲染）：`python3 src/publish.py set-source <media_id> <论文原文地址>`。
- 其他栏目要挂外链时沿用同一 `source_url` 机制，但不附文献学习 CTA。

## 腾讯文档分发手册（2026-10-27 实测）

接口限制：**整文件导入 pre_import 上限约 10-20MB**（超了报 `320125 drivecgi Service Error`）；**文档附件单文件 ≤10MB**（超了报 `320154 attachment oversize`）。

大 PDF 标准做法（以 318 页招股书为例）：
1. 压缩：若图片占大头，先 `sips -Z 1600 -s format jpeg -s formatOptions 72` 降采样图片，再用 Playwright/Chrome 重新 print-to-pdf。
2. 拆分：用 pypdf 按页拆成 ≤9.5MB 的分册（拆分后校验每册大小，图片密集区可能不均）。
3. 建承载文档：tdoc_call `doc-mcp create_with_markdown`（base64_markdown 参数），写入文件说明 + 关键数据速览 + 原始出处。
4. 逐册挂载：`pre_insert_attachment` → curl PUT 到 upload_url → `insert_attachment`（layout_type=3 预览态，classify=3 文档，idx 取 `resolve_document_structure` 返回的最大 start_index；附件节点不出现在结构树中，顺序无法接口验证，文件名自带分册编号兜底）。
5. 开权限：`manage.set_privilege` policy=2（所有人可读）。
6. 分享链接格式：`<doc_url>?_fid=<file_id>`。

## 图片渲染与处理

- **SVG→PNG**：用 `scripts/svg2png.py`（跨平台：Playwright 默认浏览器 → 各平台缓存的 Chrome for Testing → 系统 Chrome 命令行，三级回退）。Chrome.app headless 在 macOS 自 2026-10-27 起不稳定（GPU FATAL / 沙盒拒绝清理临时文件），勿直接调用。Windows 首次使用若失败，先跑 `playwright install chromium`；Windows 系统 Chrome 命令行兜底：`& "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --screenshot=out.png --window-size=宽,高 in.svg`。
- **跨端同步**：本技能为项目级，随 OneDrive 工作区同步；新会话启动时才加载技能与记忆。换电脑后不生效时：① 确认 OneDrive 已同步 `.workbuddy/skills/`；② 开新会话；③ 提示词显式点名「用 wechat-mp-pipeline 技能」。
- **ImageGen 水印**：成品右下角有"AI生成"水印。发布前处理：检测差异像素定位 → 用干净背景邻近条带覆盖修补 → 四角复扫确认。
- SEC EDGAR 的 htm 主文件不含图片，整页图片是同目录独立 jpg，需全部下载（curl 要带 User-Agent）。EDGAR 页面容器带 `content-visibility:auto`，本地阅读前用 sed 移除，否则渲染空白。

## 发布档案

每次推送草稿/发布后，把标题、media_id、状态记入项目记忆 `.workbuddy/memory/MEMORY.md` 的发布档案表。
