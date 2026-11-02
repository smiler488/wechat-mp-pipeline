#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selfcheck.py — 公众号稿件自检（Loop 1 机械层）

把 writing-style.md 里可机械判定的规则跑一遍，输出分级报告。
目的：不靠记忆，靠脚本。同类错误第二次出现，就往下面的规则表里加一条。

用法:
    python3 scripts/selfcheck.py "articles/<稿>.md"
    python3 scripts/selfcheck.py "articles/<稿>.md" --strict   # 警告也当失败

输出:
    ✗ 必须改（阻断交付）  ⚠ 建议检查  ✓ 通过
退出码: 有 ✗ 返回 1；--strict 下有 ⚠ 也返回 1；否则 0。
"""

import argparse
import re
import struct
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============================================================================
# 规则表 —— 自进化的落点
#
# 良超每提一条「通用」建议（换个主题、换个栏目仍成立），除了改规范文字，
# 还要把可机械检查的部分加进这里。规则不进表 = 下次还会犯。
# ============================================================================

# 明显不需要括注的通用缩写（RGB/PDF 这类，同行一看就懂）
ABBREV_WHITELIST = {
    "PDF", "URL", "HTML", "CSS", "JSON", "CSV", "XML",
    "USA", "UK", "EU", "UN",
    "DNA", "RNA", "PCR",
    "CPU", "GPU", "RAM", "API", "GUI", "IDE",
    "RGB", "HSV", "JPG", "PNG", "SVG", "GIF", "MP4",
    "DOI", "ISBN", "GPS", "USB", "WIFI", "AI2",
    # 学术元数据（三件套里的字段，大同行都懂，不强制括注）
    "ISSN", "PMID", "JCR", "JIF", "ORCID", "SCI", "SSCI",
    # 常识性机构名
    "NASA", "NOAA", "USAID", "USDA", "WHO", "IPCC",
    # 文献元信息字段（三件套里的标识号，同行都懂）
    "PMCID", "PMC", "PMID", "IEEE", "GPT",
    # 许可协议标识（三件套里按「许可：CC BY 4.0」格式出现即可）
    "CC", "CC0", "BYNC",
}

# 高危行话：本身有日常含义，脱离定语读者必然按日常义理解
# 格式：(词, 该词在专业语境里衡量什么)
JARGON_DAILY_MEANING = [
    ("技巧", "skill：预报相对简单基准的判别能力，不是‘技术窍门’"),
    ("锐利度", "sharpness：预报概率偏离气候平均的程度"),
    ("距平", "相对多年平均的偏差"),
    ("命中率", "probability of detection，预报中的事件被报中的比例"),
    ("虚警", "false alarm，报了却没发生"),
    ("信噪比", "signal-to-noise ratio，有效信号与背景波动强度之比"),
    ("归一化", "把不同量纲的变量缩到同一范围（如 0-1）便于比较"),
    ("显著性", "统计上能否拒绝‘纯属偶然’的判断"),
    ("提前量", "lead time：预报发布到目标事件发生相隔多久"),
    ("物候", "作物出苗、抽穗、成熟等随季节出现的生长阶段及其时间"),
    ("掩膜", "mask：只保留研究区域、屏蔽其他区域的二值图层"),
    ("后报", "hindcast：用当时能拿到的资料把系统重跑一遍做检验"),
    ("同化", "把观测数据并入模型，校正模型状态"),
]

# 跨学科借词黑名单 —— 良超实证看不懂或语义不准的
CROSS_DOMAIN_BORROW = [
    ("下垫面", "气象术语，指大气与地表的交界面；农业叙事改用‘产区之间的差异’‘空间异质性’"),
    ("非均匀下垫面", "气象规范搭配；写农学文章时先问一句：这里真的在说大气-地表交换吗"),
]

# AI 腔套话（文风铁律）
AI_CLICHE = [
    "在当今时代", "在当今社会", "赋能", "抓手", "闭环", "打法",
    "值得注意的是", "综上所述", "众所周知", "显而易见", "不难看出",
    "先说结论", "说几点", "还有两处细节", "值得单独点名",
    "翻译成人话", "真正该看的", "这正是", "答案藏在",
    "如果你经历过", "现在你知道了",
]

# 会过期的时间锚点（改用 X 月 X 日）
EPHEMERAL_TIME = [
    r"昨天", r"前天", r"今天[早中晚凌]", r"今[早天晚]晨", r"今晚", r"刚刚", r"上周", r"上个月",
]

# 「三件事」关键词：数据集 / 代码位置 / 评估口径
DATA_HINTS = [
    r"10\.\d{4,9}/[^\s，。）)]+",          # DOI
    r"\b(FAOSTAT|SEDAC|GEOGLAM|ERA5|MODIS|Landsat|Sentinel|GLDAS|CHIRPS|WorldCensus)\b",
    r"(公开数据集|数据可公开|数据集|Data availability)",
]
CODE_HINTS = [
    r"github\.com/[\w\-.]+/[\w\-.]+",
    r"仓库\s*[：: ]?\s*[\w\-.]+/[\w\-.]+",      # 「GitHub 仓库 owner/repo」写法
    r"github\s*[：: ]\s*[\w\-.]+/[\w\-.]+",      # 「GitHub: owner/repo」写法
    r"\b(zenodo|figshare|Code availability|代码仓库|开源代码|代码开源)\b",
]
EVAL_HINTS = [
    r"\b(ROC|AUC|RMSE|MAE|R²|R2|NRMSE|accuracy|precision|recall|F1)\b",
    r"(交叉验证|留一法|hold-?out|显著性|置信区间|误差线)",
]

# 术语括注里最好带英文原词（规则 3）
EN_CHECK = re.compile(r"[A-Za-z]{3,}")

# 文献元信息标识号（三件套里的编号字段，整串跳过，不必括注）
META_PATTERNS = [
    re.compile(r"^PMC\d+$"),
    re.compile(r"^(PMID|PMCID|ISSN|ISBN|ORCID|DOI)$"),
    re.compile(r"^CC[0-9A-Z-]*$"),
]


def is_meta_token(tok: str) -> bool:
    return any(p.match(tok) for p in META_PATTERNS)


def strip_front_matter(text: str) -> str:
    """去掉 YAML front matter，避免误报。"""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def body_text(md: str) -> str:
    """转成近似纯文本，便于上下文判断（保留段落结构）。"""
    # 图片：保留图题文字参与扫描（规则 7 要求图题内术语同样括注），只去掉路径
    md = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)  # 链接
    md = re.sub(r"^#{1,6}\s*", "", md, flags=re.M)   # 标题符号
    md = md.replace("**", "").replace("*", "").replace("`", "")
    # 注意：不要删 > 和 | —— 前者是引用块、后者是表格，
    # 删了会把 "ROC>0.6" 变成 "ROC0.6"，反而制造假缩写。
    return md


def _gloss_after(text: str, pos: int, window: int = 32) -> bool:
    """词之后：本句结束前是否紧跟括注。覆盖「ROC（受试者工作特征…）」写法。"""
    seg = text[pos:pos + window].replace("\n", " ")
    stop = min([i for i in (seg.find("。"), seg.find("；")) if i != -1] or [len(seg)])
    seg = seg[:stop]
    m = re.search(r"[（(]", seg)
    if not m:
        return False
    return len(seg[m.end(): m.end() + 40].strip()) >= 4


def _gloss_before(text: str, start: int, window: int = 28) -> bool:
    """词之前：是否处在一个尚未闭合的括号里。覆盖「地球系统科学交叉学科中心（ESSIC）」写法。"""
    seg = text[max(0, start - window):start]
    p = max(seg.rfind("（"), seg.rfind("("))
    if p == -1:
        return False
    between = text[max(0, start - window) + p:start]
    return "）" not in between and ")" not in between


def has_gloss_near(text: str, start: int, end: int) -> bool:
    """某次出现是否带括注（前后两种写法都认）。"""
    return _gloss_after(text, end) or _gloss_before(text, start)


def main() -> int:
    ap = argparse.ArgumentParser(description="公众号稿件自检")
    ap.add_argument("path", help="Markdown 稿件路径")
    ap.add_argument("--strict", action="store_true", help="警告也视为失败")
    args = ap.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"✗ 文件不存在: {p}")
        return 1
    raw = p.read_text(encoding="utf-8")
    md = strip_front_matter(raw)
    body = body_text(md)

    blocks = []          # (级别, 标题, [条目])
    n_err = n_warn = 0

    def add(level: str, title: str, items):
        nonlocal n_err, n_warn
        blocks.append((level, title, items))
        if level == "✗":
            n_err += len(items) or 1
        elif level == "⚠":
            n_warn += len(items) or 1

    # --- 1. 署名与标题 ---
    if re.search(r"author:\s*良超", raw):
        add("✗", "署名错误：front matter 写了「良超」", ["author 必须为 smiler488"])

    m_title = re.search(r"^title:\s*(.+)$", raw, flags=re.M)
    if m_title:
        title = m_title.group(1).strip()
        # 2026-10-31 良超否题实证：禁用第一人称卖关子标题
        if re.search(r"^(我|我们).{0,12}?(才|终于)", title):
            add("✗", "标题用了第一人称卖关子式（被否过）",
                [f"当前：{title} → 主题前置、直给信息"])
        if title.startswith("【文献学习】"):
            # 栏目标题按「期刊缩写｜译名」格式生成，长度天然偏长，不报长度；
            # 改为校验格式是否正确。
            if "｜" not in title and "|" not in title:
                add("✗", "文献学习标题缺分隔符",
                    ["格式：【文献学习】 期刊缩写｜论文中文译名"])
        elif len(title) > 40:
            add("⚠", f"标题偏长（{len(title)} 字）", ["建议压到 30 字内，微信列表会截断"])

    # --- 2. 缩写首现括注 ---
    # 2026-11-02 修复：\b 在中文环境失效——Python 的 \w 含汉字，「群晖NAS（Network…」
    # 里 NAS 紧贴汉字，两侧都是 \w，\b 不成立，导致已括注的缩写被误报。
    # 改用显式 lookaround：只把「紧邻 ASCII 字母数字」的位置视为缩写边界，汉字不算。
    ABBR_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9-]{2,})(?![A-Za-z0-9])")
    seen, missing = set(), []
    for m in ABBR_RE.finditer(body):
        a = m.group(0)
        if a in ABBREV_WHITELIST or is_meta_token(a) or a in seen:
            continue
        seen.add(a)
        # 全文任意一次出现带括注即视为已解释（容忍「先出现、后解释」的写法）
        glossed = any(has_gloss_near(body, k.start(), k.end())
                      for k in ABBR_RE.finditer(body) if k.group(0) == a)
        if not glossed:
            ctx = body[max(0, m.start() - 12):m.end() + 24].replace("\n", " ").strip()
            missing.append(f"{a} 全文未括注 …{ctx}")
    if missing:
        add("✗", f"缩写首现未括注（{len(missing)} 处）", missing)
    else:
        add("✓", "缩写首现括注", [])

    # --- 3. 高危行话（有日常义）---
    jargon_hits = []
    for word, hint in JARGON_DAILY_MEANING:
        occurrences = list(re.finditer(re.escape(word), body))
        if not occurrences:
            continue
        glossed = any(has_gloss_near(body, m.start(), m.end()) for m in occurrences)
        if not glossed:
            jargon_hits.append(f"「{word}」{len(occurrences)} 处均未括注 → 应注：{hint}")
    if jargon_hits:
        add("✗", f"有日常义的专业词未括注（{len(jargon_hits)} 类）", jargon_hits)
    else:
        add("✓", "高危行话已括注", [])

    # --- 4. 跨学科借词 ---
    borrow_hits = []
    for word, hint in CROSS_DOMAIN_BORROW:
        for m in re.finditer(re.escape(word), body):
            borrow_hits.append(f"「{word}」出现在非本学科语境 → {hint}")
            break
    if borrow_hits:
        add("⚠", "疑似跨学科借词（确认本学科是否有更平常的说法）", borrow_hits)

    # --- 5. AI 腔套话 ---
    cliche_hits = sorted({c for c in AI_CLICHE if c in body})
    if cliche_hits:
        add("✗", "AI 腔套话", list(cliche_hits))
    else:
        add("✓", "无 AI 腔套话", [])

    # --- 6. 会过期的时间锚点 ---
    time_hits = sorted({t for t in EPHEMERAL_TIME if re.search(t, body)})
    if time_hits:
        add("⚠", "时间词会过期，改用「X 月 X 日」", list(time_hits))

    # --- 7. 长段落（>200 字）---
    long_paras = []
    for para in re.split(r"\n\s*\n", body):
        s = para.strip()
        if not s or s.startswith(("#", "!", "|", "-", ">", "参考文献")):
            continue
        if re.search(r"^\s*[-:|]{3,}\s*$", s, flags=re.M):
            continue          # markdown 表格分隔行，跳过整块
        # 阈值放宽到 260：文献学习类信息密度天然高，只抓真正过长的段落，
        # 否则警告泛滥会让这份报告失去可信度。
        if len(s) > 260:
            long_paras.append(f"{len(s)} 字：{s[:40]}…")
    if long_paras:
        add("⚠", "段落偏长（公众号宜 ≤4 行 / 约 120 字）", long_paras)

    # --- 8. 三件事：数据集 / 代码 / 评估口径（仅文献学习类强制）---
    # 资讯科普 / 工具教程 / 观点类文章没有可复现数据集，强制要求属误报。
    is_paper = bool(re.search(r"(文献信息|通讯作者|期刊信息|Data availability|Code availability)", body))
    missing_three = []
    for label, pats, tip in [
        ("数据集来源", DATA_HINTS, "需交代公开数据集名称或 DOI"),
        ("代码/数据位置", CODE_HINTS, "需交代仓库名或存档 DOI（正文禁外链，给标识符即可）"),
        ("评估口径", EVAL_HINTS, "需交代验证方式与指标"),
    ]:
        if not any(re.search(p, body) for p in pats):
            missing_three.append((label, tip))
    if missing_three:
        if is_paper:
            add("✗", "文献学习类缺「三件事」",
                [f"{l}：{t}" for l, t in missing_three])
        else:
            add("⚠", "非文献学习类，若涉及可复现数据建议补「三件事」",
                [f"{l}：{t}" for l, t in missing_three])
    else:
        add("✓", "数据集 / 代码 / 评估口径三件事齐全", [])

    # --- 9. 正文配图 ---
    n_img = len(re.findall(r"!\[[^\]]*\]\((?!http)", md))
    if n_img == 0:
        add("✗", "无正文配图（铁律：至少 1-2 张，封面不算）", ["在信息密度最高章节插入 SVG 信息图或原文图"])
    else:
        add("✓", f"正文配图 {n_img} 张", [])

    # --- 10. 封面：双封面存在性 + 尺寸（2026-11-02 V3 规范：缺方版视为未交付）---
    def png_size(path: Path):
        try:
            head = path.read_bytes()[:24]
            if head[:8] != b"\x89PNG\r\n\x1a\n":
                return None
            return struct.unpack(">II", head[16:24])
        except Exception:
            return None

    m_cover = re.search(r"^cover:\s*(\S+)\s*$", raw, flags=re.M)
    if not m_cover:
        add("✗", "front matter 缺 cover 字段", ["双封面为每篇必做"])
    else:
        cover_items = []
        cover_path = (p.parent / m_cover.group(1)).resolve()
        if not cover_path.exists():
            cover_items.append(f"横版封面文件不存在：{m_cover.group(1)}")
        else:
            sz = png_size(cover_path)
            if sz and sz != (900, 383):
                cover_items.append(
                    f"横版封面尺寸 {sz[0]}×{sz[1]}，应为 900×383（管线消费尺寸；1800×766 母版另行保留）")
        m_sq = re.search(r"^cover_square:\s*(\S+)\s*$", raw, flags=re.M)
        if m_sq:
            sq_path = (p.parent / m_sq.group(1)).resolve()
        else:
            sq_path = cover_path.with_name(
                cover_path.stem.replace("_封面_900x383", "_封面方形_1080x1080") + ".png")
        if not sq_path.exists():
            cover_items.append(f"缺方版封面（{sq_path.name}），缺方版视为未交付")
        else:
            sz = png_size(sq_path)
            if sz and sz != (1080, 1080):
                cover_items.append(f"方版封面尺寸 {sz[0]}×{sz[1]}，应为 1080×1080")
        if cover_items:
            add("✗", f"封面问题（{len(cover_items)} 项）", cover_items)
        else:
            add("✓", "封面双张齐（横版 900×383 + 方版 1080×1080）", [])

    # --- 输出 ---
    print("=" * 64)
    print(f"自检报告：{p.name}")
    print("=" * 64)
    for level, title, items in blocks:
        print(f"\n{level} {title}")
        for it in items:
            print(f"    · {it}")
    print("\n" + "-" * 64)
    verdict = "阻断：有必须改的项" if n_err else ("有警告，建议过一遍" if n_warn else "全部通过")
    print(f"结论：{verdict}   （✗ {n_err} / ⚠ {n_warn}）")
    print("-" * 64)

    if n_err:
        return 1
    if args.strict and n_warn:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
