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
import datetime
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
# --- 规则登记（非机械判定，人工在封面验收时执行）---
# 2026-11-04 良超反馈「你不应该强调五而忽略了我们的主角/主题」→ 封面主角锚定原则：
# 封面主视觉必须让文章主角/主题对象成为画面最大元素；计数与工具隐喻不得盖过主角。
# 缩略图一问：不看标题，能否一眼认出文章主角？答不出即返工。
# 规则本体：references/cover-design.md「防模板化铁律 · 主角锚定原则」。
# 2026-11-04 良超反馈「你公众号里面说的GitHub的仓库，你是不是没有创建呀？
# 以后记住说要有的仓库你要给我建好了呀」→ 承诺资源先建好：正文承诺即交付物，
# 写进稿的 GitHub 仓库/数据链接必须在推草稿前真实创建并可访问。
# 检查 11 逐个 HTTP 核验，404 阻断。规则本体：references/writing-style.md 三件事第 5 条。
# 2026-11-05 良超反馈（帽子全图谱一周 5000 阅读只涨几十粉）→ 转化设计四件套：
# 新稿默认带文首埋点/文末领取钩子/系列化/转发语（已发布文章不回改）。
# 检查 12 机械层只查「钩子存在性」（领取钩子或系列化至少一），⚠ 不阻断；
# 资产是否真的建好属人工核对。规则本体：references/writing-style.md「转化设计」节。
# 2026-11-06 良超反馈（新型研究型大学篇：筹建校联培研究生入学被写成"首批新生"）→
# 招生表述须落到培养类型与招生资格：研究生联培 ≠ 独立招本科生，筹建校不得笼统写招生。
# 检查 6.2 机械层扫「裸招生句」（含首批新生/开始招生等且同句无培养类型限定词），⚠ 不阻断。
# 规则本体：references/writing-style.md「事实核查」节。
# 2026-11-06 良超提供微信官方《如何让公众号文章获取更多搜索流量？丨搜一搜优化教程01》
# （微信搜一搜助手 2023-01-06）→ 搜一搜优化进规范：标题清晰不堆砌不过短、加粗标主旨句
# 但不过度、长文分段小标题、图为主稿配文字介绍、发布后确认声明原创（相同内容优先展示原创）。
# 检查 14 机械层查标题堆砌/过短、过度加粗、长文缺小标题、图主文辅。
# 规则本体：references/search-optimization.md。
# 2026-11-06 良超反馈「我们写公众号别写成工作报告，再出现xxx口径这样的表述了」→
# 报告腔「xxx 口径」（官方口径/公布口径/汇聚口径…）一律不写，直接陈述或写「据官方介绍」；
# 「500 米口径」望远镜专业名称豁免。检查 15 机械层扫「口径」，✗ 阻断。
# 规则本体：references/writing-style.md「文风」节。
# 2026-11-06 中国科技云篇草稿回流（闭环 C）：良超逐段改稿后总结「不要这样用那个破折号，
# 这样太AI了，也尽量不要用不是什么什么而是什么什么这样的句子，还有什么什么太重了」→
# 破折号插入语/「不是…而是」禁（检查 16 ✗）、量感渲染与报幕回指进词表（5.2/META_NARRATION），
# 惯用结尾模板同步改版（templates/ending_block.html）。规则本体：writing-style.md「去 AI 味句式」节。
# 2026-11-07 良超反馈（Skill 解剖图篇图注截图）→ 图注科研规范化：正文插图一律带图注，
# 格式「图编号 + 图标题 + 图中元素解释」，左对齐（渲染器自动补「图N」并加粗编号）；
# 同次定排版升级：正文 15px→16px、加 font-weight 500（对标量子位，公众号是视觉产品，
# 大龄科研读者多）。检查 17 机械层查 alt 空 ✗ / alt 无「：」⚠。
# 规则本体：references/writing-style.md「排版基准」节。
# 2026-11-08 良超反馈（农光互补篇：「为什么作者简介没先做成表格？skill 中没强调这一点吗？」）→
# 文献学习作者简介 = 作者表 + 合作史证据段，表格先行，禁 bullet 清单代替表格。
# 检查 8.2 机械层查「## 作者简介」节内 markdown 表格行（≥3 行），缺即 ✗ 阻断。
# 规则本体：docs/文献解读类公众号SOP.md §3 结构表 + §3.5②。
# 2026-11-08 推草稿实测（IGZ 学术招聘篇）：front matter digest 145 字符 / 345 字节 →
# 微信 draft/add 报 errcode=45004 "description size out of limit"，素材已上传但草稿没建成；
# 只把摘要压到 108 字符 / 240 字节，其余字段不动，重推成功。→ 摘要双上限：≤120 字符且
# ≤300 字节，超限 ✗ 阻断。检查 18 落点；规则本体：references/publishing-ops.md「摘要长度红线」节。
# 2026-11-08 良超反馈（农业院士版图篇：误列王二涛为院士、漏张启发等 5 位涉农院士）→
# 名单盘点类内容（院士/人才/高校/机构名单）必须逐人回官方名单页核验
# （两院：casad.cas.cn 学部名单 / cae.cn 院士名单），不得凭记忆或媒体转述。
# 检查 20 机械层：含「院士」且含名单/盘点/全景/版图类词 → ⚠ 提示逐人核验。
# 规则本体：references/writing-style.md「事实核查」节。
# 2026-11-08 良超反馈（当日学术招聘系列）：「标题要写名方向，文中要简要介绍下单位，
# 还有不要出现<第三方职业社交平台>」→ 三条栏目通用规则进检查 19（均 ✗ 阻断）：
# ① 标题必写方向词（词表 + 英文方向缩写）；② 正文必有单位简介句式或机构全称括注；
# ③ 全文禁第三方线索平台名称与「线索来自…」表述，旧「出处标注」条废止。存量稿不回改。
# 规则本体：references/writing-style.md「学术招聘栏目专属」节 + docs/学术招聘栏目SOP.md。
# 2026-11-08 良超反馈（种植空间配置篇发布前复核）：「再检查一下文中出现的参考文献是否正确，
# 并且所引用的内容是否正确。我们作为科研类的公众号不能错误的」→ 复核实证：Evers & Bastiaans 2016
# 的 DOI 正确但期刊名凭记忆写成 Plant Ecology，DOI 解析实为 Journal of Plant Research——
# DOI 对、期刊名错同样是引用事故。铁律：文内出处（作者/期刊/年份）以 DOI 解析题录为准，
# 引用内容逐条回一手原文核验后再推草稿。检查 21 机械层：① 每条 doi: 必须可解析（✗）；
# ② Crossref 有题录时比对期刊名与年份（不一致 ⚠）。规则本体：references/writing-style.md「事实核查」节。
ABBREV_WHITELIST = {
    "PDF", "URL", "HTML", "CSS", "JSON", "CSV", "XML",
    "USA", "UK", "EU", "UN",
    "DNA", "RNA", "PCR",
    "CPU", "GPU", "RAM", "API", "GUI", "IDE",
    "RGB", "HSV", "JPG", "PNG", "SVG", "GIF", "MP4",
    "DOI", "ISBN", "GPS", "USB", "WIFI", "AI2",
    # 学术元数据（三件套里的字段，大同行都懂，不强制括注）
    "ISSN", "PMID", "JCR", "JIF", "ORCID", "SCI", "SSCI",
    # 期刊分区标注（2026-11-02 三维表型综述篇：新锐分区官方标注「1 区 TOP」被误报）
    "TOP",
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

# 写稿时是未来、发布时已成过去的计划时间点 —— 2026-11-03 良超实证（双一流警示学科篇）
# 教育部 2022 年通知里「2023 年接受再评价」被照抄成将来时，发稿时（2026-11）已过期。
# 规律：引旧政策/旧名单的未来节点，必须锚定成历史（「按当时要求，原定 X 年……」）并补现状。
# 2026-11-04 修复误报（冠层颗粒物 AE 篇）：裸「拟」命中了「模拟」的拟——文献学习稿
# 几乎必有"大涡模拟/数值模拟"，旧式导致历史书目句（"2014 年 10 月刊出"）被误判将来时。
# 改为 (?<!模)拟，只认"拟于/拟聘"这类将来时用法；「待」同理由前视排除"等待/对待"。
# 2026-11-04 二次修复（JEM 虚拟 ALS 篇）：(?<!模)拟 仍漏过「虚拟」的拟，而"伪-前缀"
# 同形词是开放集（虚拟/拟合/拟南芥/拟态/比拟/拟人/拟除虫菊酯……），负面排除堵不住，
# 且误报会逼着重写好词（"虚拟森林"被改坏）。改为正向前瞻：只认「拟+将来动作」
# （拟于/拟建/拟聘/拟设/拟招/拟引进/拟录取/拟调/拟发行……），
# 模拟/虚拟/拟合/拟南芥等名词性同形词一律不再命中。漏报个别动词可往括号里补字。
# 2026-11-04 三次修复（Front. Plant Sci. Helios 篇）：正向前瞻仍误伤「模拟生理过程」
# 的「拟生」——"生"在拟招/拟招生前瞻集里。规律收口：拟表将来时的主语只能是人/机构，
# 不可能紧贴"模/虚"，加 (?<![模虚]) 前视排除即可，前瞻集不动。
STALE_FUTURE_MARK = r"(将|计划|预计|(?<![模虚])拟(?=[于建聘设招引任录用生开调发赴增出投收派立示荐报审评转授入向通在选补免停减\s\d])|(?<![等对])待|尚未|原定|定于|将于|未通过|通不过|不合格|再评价|接受[^。；\n]{0,6}评价|调出[^。；\n]{0,6}范围)"
TIME_ANCHOR = r"(截至(发稿|目前|今天)|目前|当时|当年|其后|此后|后来|现已|如今)"

# 元叙事标签句 —— 2026-11-02 良超改稿实证二（CVPR 万花筒篇，后台逐句删）
# 他删掉了：「我的判断是，…」「我的可执行下一步：」「这个方法对我的研究方向有直接的咬合点。」
# 「差距也要摆在桌面上：」「合作史的证据链很整齐。」「再往前，」「归纳成一句：…」「两处照录：」
# 规律：正文只留内容与判断本身，不留「我怎么得出这个判断 / 这一段要讲什么 / 这句话多重要」。
# 2026-11-04 实证三（学术造假审查篇，草稿箱回流）删掉了：
# 「这篇只谈手段：」「有人觉得…。规范文本不是这么写的。」「把责任拆开，是五层：」
# 「我给自己定的清单是这几条，也」「还有一条不在清单里但更根本：…制度立住了，…清单救不了系统性的问题。」
# 规律同上：报幕式开头、树靶子再打、结构自述、自指清单、口号式收束，一律删。
META_NARRATION = [
    r"我的(判断|看法|观点|结论|建议|下一步|计划|可执行)[^。；\n]{0,4}[：:是]",
    r"我给自己(定的|定下)",
    r"(这一|这篇|这个|该方法|这套方法)[^。；\n]{0,8}?对我的",
    r"^这篇(只)?(谈|讲|盘|说)[：:]",
    r"有人觉得[^。\n]{0,40}规范文本不是这么写的",
    r"把[^。；\n]{2,12}拆开[，,](是|成)",
    r"(还有一条|还有一点)(不在清单里)?但更根本",
    r"制度(立住|缺席)[，,]",
    r"(也|还)要摆在桌面上",
    r"(归纳成一句|一句话概括|概括起来说|总结一下)",
    r"(证据链很整齐|线索很清晰|值得单独说一句)",
    r"^(两处|三处|两点|三点|两点半)(照录|细节|提醒|补充)[：:]",
    r"^再往前[，,]",
    # 2026-11-06 中国科技云篇草稿回流：报幕与回指被整句删
    r"把[^。；\n]{2,12}摊开看",
    r"串起来[，,]",
    r"(典型)?流程是这样的[：:]",
    r"就是开头",
]

# 主观强度词降级 —— 同次实证：「最要命…有张力」→「最重要」；「都是便宜货」→「都很便宜」
OVERSTRONG = [
    ("最要命", "改中性：最重要 / 最关键"),
    ("便宜货", "改中性：很便宜 / 成本低"),
    ("致命", "确认是否夸张，宜改「关键」「主要」"),
    ("碾压", "禁用夸张对比"),
    ("完爆", "禁用夸张对比"),
    ("杀疯了", "禁用网络热词"),
    # 2026-11-06 中国科技云篇草稿回流：「最重的一个/最实用/惊艳」量感渲染被删
    ("太重了", "删量感渲染，直接陈述事实差异"),
    ("最重的一个", "删量感渲染，直接陈述事实差异"),
    ("惊艳", "改中性评价：各有取舍 / 完成度不一"),
    ("最实用", "删最高级：改「对 X 实用/直接」"),
]

# 小标题俏皮 / 带价值判断 —— 同次实证：「成绩单：与真值标签打平」→「算法评估」、
# 「老实话时间」→「限制」、「CVPR 是什么门槛」→「CVPR 是什么」。
# 文献学习栏目小标题只标内容域，不标观点、不玩梗。
CUTE_HEADING = ["老实话", "成绩单", "值不值", "凭什么", "有多香", "划算吗",
                "香不香", "真香", "翻车", "含金量", "到底行不行", "水有多深",
                "逐个过", "的家底"]

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
    r"\b(zenodo|figshare|Code availability)\b",
    # 2026-11-04 修正：中文词组不能用 \b 包裹（前字仍是 \w，永远匹配不上），
    # 改为直接子串匹配
    r"(代码仓库|开源代码|代码开源)",
]

# 正文提到的 GitHub 仓库标识（owner/repo），检查 11 逐个 HTTP 核验存在性。
# 捕获组只认 ASCII，避免「仓库数据的 C/N 分项」这类中文串误命中。
REPO_PATTERNS = [
    r"github\.com/([A-Za-z0-9][A-Za-z0-9\-.]*/[A-Za-z0-9][A-Za-z0-9\-.]*)",
    r"仓库\s*[：: ]?\s*([A-Za-z0-9][A-Za-z0-9\-.]*/[A-Za-z0-9][A-Za-z0-9\-.]*)",
    r"[Gg]it[Hh]ub\s*[：: ]\s*([A-Za-z0-9][A-Za-z0-9\-.]*/[A-Za-z0-9][A-Za-z0-9\-.]*)",
]
EVAL_HINTS = [
    r"\b(ROC|AUC|RMSE|MAE|R²|R2|NRMSE|accuracy|precision|recall|F1)\b",
    r"(交叉验证|留一法|hold-?out|显著性|置信区间|误差线)",
    # 2026-11-02 实证：CV/图形学论文（万花筒雕刻 CVPR 2023 篇）的评估信号是
    # 真值网格与消融实验，不出现 ROC/RMSE 类指标，旧表导致「评估口径」误报阻断
    r"(真值|ground[ -]?truth|消融|ablation|参照网格)",
    # 2026-11-04 实证：机理/理论类论文（JFM 冠层湍流相干结构篇）的验证信号是
    # 标度律复核与实测波形定性对照，没有 ML 类指标，同样补进表避免误报
    r"(定性(对照|对比|验证|一致)|定量(复核|对比|验证)|标度|scaling)",
]

# 术语括注里最好带英文原词（规则 3）
EN_CHECK = re.compile(r"[A-Za-z]{3,}")

# 文献元信息标识号（三件套里的编号字段，整串跳过，不必括注）
META_PATTERNS = [
    re.compile(r"^PMC\d+$"),
    re.compile(r"^(PMID|PMCID|ISSN|ISBN|ORCID|DOI|PII)$"),   # 2026-11-02 补 PII（出版社文章编号，与 PMCID 同类）
    re.compile(r"^S\d{9,}[0-9X]?$"),                          # PII 值本体，如 S2590346226000556 / S277237552500930X（带校验位）
    re.compile(r"^CC[0-9A-Z-]*$"),
    # 2026-11-10 修复误报（辐射传输模型科普篇）：期刊页码（如 RSE 增刊页 S56、JGR 页 H123）
    # 形如单字母+数字，被当成未括注缩写——页码是定位号不是行文缩写，整串跳过
    re.compile(r"^[A-Z]\d{2,4}$"),
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
        # 2026-11-05 良超原话「还有别写第xx期」——标题不带期号，直接给主题
        if re.search(r"第\s*\d+\s*期", title):
            add("✗", "标题带期号（2026-11-05 良超定：别写第 xx 期）",
                ["去掉「第 N 期」，直接给主题"])
        if title.startswith("【文献学习】"):
            # 栏目标题按「期刊缩写｜译名」格式生成，长度天然偏长，不报长度；
            # 改为校验格式是否正确。
            if "｜" not in title and "|" not in title:
                add("✗", "文献学习标题缺分隔符",
                    ["格式：【文献学习】 期刊缩写｜论文中文译名"])
            # 2026-11-03 良超定：文献学习必挂论文原文地址（推送时写入"原文链接"，
            # 并自动附结尾 CTA「点击阅读全文，查看论文原文地址」）
            if not re.search(r"^source_url:\s*https?://\S+\s*$", raw, flags=re.M):
                add("✗", "文献学习稿 front matter 缺 source_url（论文原文地址）",
                    ["写 https://doi.org/<DOI> 或 arXiv abs 页；只挂原文地址，不分发 PDF"])
        elif len(title) > 40:
            add("⚠", f"标题偏长（{len(title)} 字）", ["建议压到 30 字内，微信列表会截断"])

    # --- 2. 缩写首现括注 ---
    # 2026-11-02 修复：\b 在中文环境失效——Python 的 \w 含汉字，「群晖NAS（Network…」
    # 里 NAS 紧贴汉字，两侧都是 \w，\b 不成立，导致已括注的缩写被误报。
    # 改用显式 lookaround：只把「紧邻 ASCII 字母数字」的位置视为缩写边界，汉字不算。
    # 2026-11-02 修复（AI 表型综述篇）：GitHub 仓库标识 owner/repo 里的全大写段
    # （如 IA-E-Col/PlantSAM 的 IA-E）被误报为未括注缩写——仓库路径是标识符不是行文
    # 缩写，且 CODE_HINTS 恰恰要求写 owner/repo，两条规则打架。扫描前先把仓库标识挖掉。
    body_abbr = re.sub(r"(?:github\.com/|仓库\s*[：: ]?\s*)[\w\-.]+/[\w\-.]+(?:/[\w\-.]+)?", " ", body)
    # 2026-11-04 修复误报（UE5Sim CVPRW 篇）：DOI 字符串里的全大写段（如
    # 10.1109/CVPRW63382.2024.00557 的 CVPRW63382）被当成裸缩写——DOI 是标识符
    # 不是行文缩写（与 owner/repo 同理）。扫描前把 DOI 整串挖掉。
    # 注意顺序：必须在 github 行之后对 body_abbr 挖（曾有一版写在前面又被 body 重赋值冲掉）。
    # 2026-11-10 修复漏挖（辐射传输模型科普篇）：旧字符集不含尖括号/分号/加号/百分号，
    # AMS 风格 DOI（10.1175/1520-0469(1980)037<0630:TSATRT>2.0.CO;2）只挖掉一半，
    # 剩下的 TSATRT 被当成裸缩写。DOI 后缀可含任意可见字符，扩字符集整体挖掉。
    body_abbr = re.sub(r"10\.\d{4,9}/[A-Za-z0-9._\-/:()<>=;+%]+", " ", body_abbr)
    ABBR_RE = re.compile(r"(?<![A-Za-z0-9])([A-Z][A-Z0-9-]{2,})(?![A-Za-z0-9])")
    seen, missing = set(), []
    for m in ABBR_RE.finditer(body_abbr):
        a = m.group(0)
        if a in ABBREV_WHITELIST or is_meta_token(a) or a in seen:
            continue
        seen.add(a)
        # 全文任意一次出现带括注即视为已解释（容忍「先出现、后解释」的写法）
        glossed = any(has_gloss_near(body_abbr, k.start(), k.end())
                      for k in ABBR_RE.finditer(body_abbr) if k.group(0) == a)
        if not glossed:
            ctx = body_abbr[max(0, m.start() - 12):m.end() + 24].replace("\n", " ").strip()
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

    # --- 5.1 元叙事标签句（2026-11-02 良超改稿实证二）---
    meta_hits = []
    for pat in META_NARRATION:
        for m in re.finditer(pat, body, flags=re.M):
            line = body[max(0, m.start() - 6):m.end() + 26].replace("\n", " ").strip()
            meta_hits.append(f"命中 {pat} …{line}")
            break
    if meta_hits:
        add("✗", "元叙事标签句（良超 2026-11-02 全部删掉，直接陈述即可）", meta_hits)
    else:
        add("✓", "无元叙事标签句", [])

    # --- 5.2 主观强度词 ---
    strong_hits = [f"「{w}」→ {tip}" for w, tip in OVERSTRONG if w in body]
    if strong_hits:
        add("⚠", "主观强度词降级", strong_hits)

    # --- 5.3 小标题俏皮 / 带价值判断 ---
    cute_hits = []
    for line in md.splitlines():
        s = line.strip()
        if not s.startswith("#"):
            continue
        h = s.lstrip("#").strip()
        for w in CUTE_HEADING:
            if w in h:
                cute_hits.append(f"「{h}」含「{w}」→ 用中性信息词（如「算法评估」「限制」）")
                break
    if cute_hits:
        add("⚠", "小标题偏俏皮/带判断（文献学习栏目宜中性化）", cute_hits)

    # --- 5.4 高亮使用量（==…==）---
    # 同次实证：全文 3 处米色高亮被全部去掉。强调改用句子本身或加粗。
    hl = re.findall(r"==[^=\n]+==", md)
    if len(hl) > 1:
        add("⚠", f"米色高亮用了 {len(hl)} 处（良超实证：全文 ≤1 处，优先不用）",
            [f"{h[:36]}…" for h in hl[:5]])

    # --- 6. 会过期的时间锚点 ---
    time_hits = sorted({t for t in EPHEMERAL_TIME if re.search(t, body)})
    if time_hits:
        add("⚠", "时间词会过期，改用「X 月 X 日」", list(time_hits))

    # --- 6.1 写稿时是未来、发布时已过去的时间点（2026-11-03 双一流警示学科篇实证）---
    cur_year = datetime.date.today().year
    stale_hits = []
    for para in re.split(r"\n\s*\n", body):
        if re.search(TIME_ANCHOR, para):
            continue          # 同段已锚定时态（按当时/截至发稿），不算过期
        for m in re.finditer(r"(20\d{2})\s*年", para):
            if int(m.group(1)) >= cur_year:
                continue
            end = para.find("。", m.end())
            sent = para[m.start(): end if end != -1 else len(para)]
            if re.search(STALE_FUTURE_MARK, sent):
                stale_hits.append(f"「{m.group(1)} 年」仍是将来时写法 …{sent[:44]}")
                break
    if stale_hits:
        add("⚠", "旧文的未来时间点如今已过去：锚定成历史并补现状", stale_hits)

    # --- 6.2 招生表述未落到培养类型（2026-11-06 新型研究型大学篇实证）---
    # 裸招生句 = 含「首批新生/开始招生…」且同句无培养类型限定词。
    # 联培研究生入学写成"迎来首批新生"会被误读为学校已独立招本科生。
    ENROLL_BARE = re.compile(r"首批新生|迎来新生|新生入学|新生报到|开始招生|启动招生|首届招生|首批招生")
    ENROLL_QUAL = re.compile(r"联培|联合培养|本科|博士|硕士|研究生|独立招|直博|保送")
    enroll_hits = []
    for para in re.split(r"\n\s*\n", body):
        for sent in re.split(r"[。；！？\n]", para):
            if ENROLL_BARE.search(sent) and not ENROLL_QUAL.search(sent):
                enroll_hits.append(f"…{sent.strip()[:52]}…")
    if enroll_hits:
        add("⚠", "招生表述未落到培养类型（联培研究生 ≠ 独立招本科生；筹建校不得笼统写'首批新生'）",
            enroll_hits[:5])

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
    # 2026-11-04 修复误报：原触发词含「通讯作者」，一篇讲通讯作者责任的
    # 资讯文被误判成文献学习类。改用五段式小标题/文献元信息作标记。
    is_paper = bool(re.search(r"(论文简介|期刊简介|文献信息|期刊信息|Data availability|Code availability)", body))
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

    # --- 8.2 作者简介表格先行（仅文献学习五段式强制；2026-11-08 良超反馈）---
    # 作者简介 = 作者表 + 合作史证据段，表必须先行；bullet 清单代替表格 = ✗。
    # 表头固定「作者 | 单位 | 角色证据」。多作者按单位归组行亦合规（≥3 行含表头与分隔行）。
    m_auth = re.search(r"(?m)^##\s*作者简介", md)
    if m_auth:
        sec = md[m_auth.end():]
        m_next = re.search(r"(?m)^##\s", sec)
        if m_next:
            sec = sec[:m_next.start()]
        trows = [ln for ln in sec.splitlines() if ln.strip().startswith("|")]
        if len(trows) < 3:
            add("✗", "作者简介缺作者表（五段式：作者表 + 合作史证据段，表先行；表头「作者 | 单位 | 角色证据」）",
                ["把作者、单位、角色证据整理成 markdown 表格置于该节开头，合作史叙事段放表后"])
        else:
            add("✓", "作者简介表格先行", [])

    # --- 9. 正文配图（2026-11-03 良超升级：公众号是类似 PPT 的视觉产品不是文本产品——每个主要章节至少一图）---
    # 2026-11-05 良超定（学术招聘稿实证，原话「如果我没给你图片你以后还是别截图插入了吧」）：
    # 招聘类配图只用两类——良超本人给的图片 + 岗位速览 SVG 信息图；官方页截图等"自己截图
    # 凑数"一律禁止，没给图就文字稿。故招聘类不适用 ≥3 张密度下限，有 1 张信息图即通过；
    # 其余栏目视觉密度铁律不变。机械层查不了"图是谁给的"，归人工层按此条核。
    is_recruit = bool(m_title and "学术招聘" in m_title.group(1))
    # 2026-11-10 良超反馈「写太多了，只要说怎么用，不要讲原理」→ 短工具/产品安利稿
    # （front matter 标 short_form: 1）不适用 ≥3 图的视觉密度下限，有 1 张「怎么用」图即通过。
    # 篇幅与原理词由检查 22 卡住。规则本体：references/writing-style.md「工具/产品安利稿专属」节。
    is_short = bool(re.search(r"^short_form:\s*1\s*$", raw, flags=re.M))
    min_img = 1 if (is_short or is_recruit) else 3
    n_img = len(re.findall(r"!\[[^\]]*\]\((?!http)", md))
    n_sec = len(re.findall(r"(?m)^##\s", md))
    if n_img == 0:
        add("✗", "无正文配图（铁律：至少 1-2 张，封面不算）", ["在信息密度最高章节插入 SVG 信息图或原文图"])
    elif not is_paper and n_img < min_img:
        add("✗", f"正文配图仅 {n_img} 张（视觉密度铁律：非文献学习类全文 ≥{min_img} 张，每主要章节一图）",
            ["按章节补信息图：流程、对比、结构、时间轴都可图化；表格优先图片化"])
    elif not is_short and not is_recruit and n_img < n_sec:
        add("⚠", f"正文 {n_sec} 个章节仅 {n_img} 张图（公众号是视觉产品，建议每主要章节一图）", [])
    else:
        add("✓", f"正文配图 {n_img} 张 / {n_sec} 章节", [])

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

    # --- 11. 正文承诺的 GitHub 仓库必须真实存在（2026-11-04 良超反馈）---
    # 正文承诺即交付物：链接是死的等于骗读者。写进稿的仓库必须先建好、再写稿。
    import urllib.request
    import urllib.error
    repos = set()
    scan = md.replace("`", "")
    for pat in REPO_PATTERNS:
        for m in re.finditer(pat, scan):
            # 2026-11-10 修复（辐射传输模型科普篇）：「开源仓库 github.com/owner/repo」写法下
            # 仓库 pattern 会捕到「github.com/owner」并拼出 https://github.com/github.com/owner
            # （404 误报）；捕获值自带 github.com/ 前缀时先剥掉再拆 owner/repo。
            val = re.sub(r"^(?:https?://)?(?:www\.)?github\.com/", "", m.group(1).rstrip("."))
            owner, _, repo = val.partition("/")
            if len(owner) >= 2 and len(repo) >= 2:
                repos.add(f"{owner}/{repo}")
    if repos:
        repo_ok, repo_bad, repo_unknown = [], [], []
        for r in sorted(repos):
            try:
                req = urllib.request.Request(
                    f"https://github.com/{r}", method="HEAD",
                    headers={"User-Agent": "Mozilla/5.0 (selfcheck)"})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    code = resp.status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception:
                repo_unknown.append(f"{r}（断网/超时，未能核验）")
                continue
            if code == 200:
                repo_ok.append(r)
            else:
                repo_bad.append(f"{r} → HTTP {code}：先建仓再写稿（gh repo create …）")
        if repo_bad:
            add("✗", "正文承诺的 GitHub 仓库不可访问（承诺资源先建好，再写进稿）", repo_bad)
        elif repo_unknown:
            add("⚠", "未能联网核验正文承诺的仓库", repo_unknown + ["推草稿前人工逐个打开确认"])
        else:
            add("✓", f"正文承诺的 {len(repo_ok)} 个 GitHub 仓库均存在", repo_ok)

    # --- 12. 运营话术禁用（2026-11-05 良超否决转化设计四件套，当日早间规则反转）---
    # 良超原话（看完【学术招聘】第 1 期样稿）：「这样的设计，以后公众号还是别有这部分了，
    # 还有别写第xx期」。文首埋点/文末领取钩子/栏目自介/下期预告/场景化转发语一律不写，
    # 正文只留内容与免责声明。原「转化钩子存在性」（当日早间立）反向为禁用检测——
    # 同日两次改主意以最新为准，旧规则作废。
    OPS_PATTERNS = [
        (r"回复\s*[【\[][^】\]]+[】\]]\s*领取", "文末领取钩子"),
        (r"领取《|免费领取", "领取钩子"),
        (r"建议收藏", "文首收藏埋点"),
        (r"下期预告|下期[:：]", "下期预告"),
        (r"新(开|设)(的)?(一个)?栏目", "栏目自介"),
        (r"转给正在", "场景化转发语"),
    ]
    ops_hits = []
    for pat, label in OPS_PATTERNS:
        m = re.search(pat, md)
        if m:
            ops_hits.append(f"{label} …{m.group(0)[:30]}")
    if ops_hits:
        add("✗", "出现运营话术（2026-11-05 良超定：埋点/领取钩子/栏目自介/下期预告/转发语一律不写）",
            ops_hits)
    else:
        add("✓", "无运营话术", [])

    # --- 13. 学术招聘类专项（2026-11-05 良超定：新开【学术招聘】栏目）---
    # 招聘信息的可信度红线是"来源官方 + 时效"：第三方平台帖子只是线索，每岗位须倒查官方页；
    # 无来源不发（✗），截止日期缺失读者没法安排申请（⚠，滚动招聘写明即可）。
    # 规则本体：references/writing-style.md「学术招聘栏目专属」节；完整 SOP docs/学术招聘栏目SOP.md。
    if is_recruit:
        has_url = re.search(r"https?://\S+", md)
        has_deadline = re.search(r"截止|招满为止|滚动招聘", md)
        if not has_url:
            add("✗", "学术招聘稿无来源官方链接（可信度红线：查不到官方源的岗位不发）",
                ["每岗位给官方岗位页 URL（可复制文本）；front matter 写 source_url=本期最重要岗位官方页"])
        if not has_deadline:
            add("⚠", "学术招聘稿未见截止日期", ["每岗位标 `截止 YYYY-MM-DD`；滚动招聘写明「滚动招聘（招满为止）」"])
        if not re.search(r"以官方页面为准", md):
            add("⚠", "学术招聘稿缺固定免责声明",
                ["文末加：信息以官方页面为准，岗位可能随时调整或提前招满。"])

    # --- 14. 搜一搜可检索性（2026-11-06 学习微信官方《搜一搜优化教程01》）---
    # 官方标准：标题清晰简洁直接（不堆砌关键词/符号、不过短缺关键信息）；加粗标出主旨句
    # 但不过度加粗；长文分段 + 小标题；图/资源为主的稿子必须配文字介绍（搜索引擎读不懂纯图）。
    # 「发布后确认声明原创」属发布环节人工步骤，不在此查。
    # 规则本体：references/search-optimization.md。
    if m_title:
        t = m_title.group(1).strip()
        core = re.sub(r"^【[^】]*】\s*", "", t)          # 去栏目前缀再判信息量
        if len(core) < 8:
            add("⚠", "标题过短、缺关键信息（官方反例：『我的周记』式）",
                [f"去栏目前缀后仅 {len(core)} 字：{t}"])
        t_sym = re.sub(r"(?<!｜)｜(?!｜)", "", t)  # 栏目标题「期刊缩写｜译名」的单个｜是格式分隔符不算堆砌（2026-11-08 修误报：「Sci.｜」会被判堆砌）
        sym = re.search(r"[。，！？,.!?;；:：、/\\|｜]{2,}", t_sym)
        if sym:
            add("⚠", "标题符号堆砌（官方反例：堆砌无意义符号）", [f"…{sym.group(0)}…"])
        gram_hits = []
        for n, thr in ((3, 3), (2, 4)):
            cnt = {}
            for i in range(len(core) - n + 1):
                g = core[i:i + n]
                if re.fullmatch(r"[\u4e00-\u9fffA-Za-z0-9]{%d}" % n, g):
                    cnt[g] = cnt.get(g, 0) + 1
            gram_hits += [f"「{g}」×{c}" for g, c in sorted(cnt.items()) if c >= thr]
        if gram_hits:
            add("⚠", "标题疑似堆砌关键词（官方反例：重复关键词凑排位）", gram_hits[:5])

    bolds = re.findall(r"\*\*([^*\n]{1,80})\*\*", md)
    bold_chars = sum(len(b) for b in bolds)
    if len(bolds) > 15 or (body and bold_chars > 0.12 * len(body)):
        add("⚠", f"加粗 {len(bolds)} 处偏多（官方：过多重点反而让搜索引擎抓不到重点）",
            ["每节至多 1-2 处加粗主旨句，其余去粗"])

    n_head = len(re.findall(r"(?m)^#{2,4}\s", md))
    n_chars = len(re.sub(r"\s", "", body))
    if n_chars > 1200 and n_head < 2:
        add("⚠", f"正文 {n_chars} 字但小标题仅 {n_head} 个（官方：分段+小标题利于用户定位与搜索引擎理解）",
            ["按逻辑分段并补 ##/### 小标题（写法照「小标题中性化」铁律）"])
    if n_img >= 4 and n_chars < 600:
        add("⚠", f"图 {n_img} 张但文字仅 {n_chars} 字（官方：图/资源为主的稿子须配文字介绍，否则难被搜索召回）",
            ["给图配文字介绍；图是内容的一部分，但不能替代文字"])

    # --- 15. 报告腔词（2026-11-06 良超反馈：公众号别写成工作报告）---
    # 良超原话：「我们写公众号别写成工作报告，再出现xxx口径这样的表述了」。
    # 「官方口径/公布口径/汇聚口径/资源口径」这类"xxx口径"是汇报语体，一律不写；
    # 数字直接给，需要限定来源时写「据官方介绍」。豁免：数字+米口径（望远镜专业名称，
    # 如"500 米口径球面射电望远镜"）。规则本体：references/writing-style.md「文风」节。
    body_wo_aperture = re.sub(r"\d+\s*米口径", "", body)
    kou_hits = []
    for m in re.finditer(r"口径", body_wo_aperture):
        line = body_wo_aperture[max(0, m.start() - 12):m.end() + 12].replace("\n", " ").strip()
        kou_hits.append(f"…{line}…")
    if kou_hits:
        add("✗", "报告腔「xxx 口径」（2026-11-06 良超定：别写成工作报告；直接陈述或写「据官方介绍」，"
                 "「500 米口径」类专业名称除外）", kou_hits[:5])
    else:
        add("✓", "无报告腔「口径」", [])

    # --- 16. AI 句式：破折号插入语 / 「不是…而是」（2026-11-06 中国科技云篇草稿回流实证）---
    # 良超改完草稿总结：「以后不要这样用那个破折号，这样太AI了，也尽量不要用不是什么什么
    # 而是什么什么这样的句子，还有什么什么太重了，这些都太AI了」。
    # ① 插入语式双破折号（——……——）✗ 禁；②「不是 X，(而)是 Y」对比句 ✗ 禁；
    # ③ 单破折号补充解释（X——Y）少用，≥3 处 ⚠；④ 否定式树靶子句（不是……。）⚠ 提醒。
    # 规则本体：references/writing-style.md「去 AI 味句式」节。
    db_insert = re.findall(r"——[^—\n]{2,40}——", body)
    em_total = len(re.findall(r"(?<!—)——(?!—)", body))
    bi_contrast = re.findall(r"不是[^。，；\n]{1,30}[，,](而)?是", body)
    neg_target = re.findall(r"不是[^。\n]{2,25}。", body)
    ai_x, ai_w = [], []
    ai_x += [f"插入语式双破折号 …{s[:40]}…" for s in db_insert[:3]]
    ai_x += [f"「不是…，是…」对比句 …{s[:40]}…" for s in bi_contrast[:3]]
    if em_total >= 3:
        ai_w.append(f"单破折号 {em_total} 处偏多（至多 1-2 处，改独立句或冒号）")
    ai_w += [f"否定式树靶子句 …{s[:40]}…" for s in neg_target[:3]]
    if ai_x:
        add("✗", "AI 句式（2026-11-06 良超定：破折号插入语 / 「不是…而是」太 AI，禁）", ai_x)
    if ai_w:
        add("⚠", "句式提醒（单破折号偏多 / 否定式树靶子，宜改正面直陈）", ai_w)
    if not ai_x and not ai_w:
        add("✓", "无破折号插入语与「不是…而是」句式", [])

    # --- 17. 图注科研规范（2026-11-07 良超定）---
    # 正文插图一律带图注：图编号（渲染器自动补「图N」，alt 里不用写）+ 图标题 +
    # 图中元素解释，左对齐。写法：图片 alt 按「标题：元素解释」撰写。
    # alt 为空 ✗ 阻断；alt 非空但无「：」⚠（多半只有标题、缺元素解释）。
    img_alts = re.findall(r"!\[([^\]]*)\]\((?!http)[^)]*\)", md)
    cap_x, cap_w = [], []
    for i, a in enumerate(img_alts, 1):
        a = a.strip()
        if not a:
            cap_x.append(f"第 {i} 张图 alt 为空（缺图注）→ 按「标题：元素解释」补写")
        elif "：" not in a and ":" not in a:
            cap_w.append(f"第 {i} 张图图注无「：」→ 应为「图标题：图中元素解释」两段式 …{a[:30]}")
    if cap_x:
        add("✗", "正文图片缺图注（2026-11-07 良超定：科研规范图注 = 图编号+图标题+元素解释）", cap_x)
    if cap_w:
        add("⚠", "图注结构建议两段式「标题：元素解释」", cap_w)
    if img_alts and not cap_x and not cap_w:
        add("✓", f"图注规范（{len(img_alts)} 张图均有「标题：元素解释」图注）", [])

    # --- 18. 摘要长度红线（2026-11-08 推草稿 45004 实证）---
    # 微信 draft/add 的 digest 超限报 errcode=45004 "description size out of limit"，
    # 图文素材已经上传但草稿建不成，只能靠写稿端控制长度。存量稿不回改。
    m_digest = re.search(r"^digest:\s*(.+)$", raw, flags=re.M)
    if m_digest:
        dg = m_digest.group(1).strip()
        dg_bytes = len(dg.encode("utf-8"))
        if len(dg) > 120 or dg_bytes > 300:
            add("✗", f"摘要超限（{len(dg)} 字符 / {dg_bytes} 字节）：推草稿会报 45004",
                ["压到 ≤120 字符且 ≤300 字节；只留主题、关键数字与截止日期，删「逐条说明」类目录式尾巴"])
        else:
            add("✓", f"摘要长度合规（{len(dg)} 字符 / {dg_bytes} 字节）", [])

    # --- 19. 学术招聘三项新规（2026-11-08 良超反馈）---
    # ① 标题必须写明方向：中文方向词表 + 常见英文方向缩写，均无命中即 ✗；
    # ② 正文要有单位简介：描述性句式或「机构英文全称 + 中文解释」括注至少一处；
    # ③ 全文（含 front matter / 图注）不出现第三方线索平台名称与中文同义称呼。
    # 存量稿不回改。规则本体：references/writing-style.md「学术招聘栏目专属」节 +
    # docs/学术招聘栏目SOP.md §1 / §3 / §4 / §9。
    if is_recruit:
        core_title = re.sub(r"^【[^】]*】\s*", "", m_title.group(1).strip()) if m_title else ""
        direction_cn = ("育种|遗传|基因组|生物信息|数据科学|人工智能|机器学习|深度学习|机器人|"
                        "表型|遥感|光合|作物|土壤|园艺|植物病理|精准农业|农业|环境|气候|生态|"
                        "计算|统计|自动化|微生物|食品|神经|材料|物理|化学|数学|经济|教育|"
                        "视觉|图像|光谱|激光|传感|无人机|建模|模拟|算法|水文|气象|海洋|"
                        "林业|畜牧|兽医|水产|昆虫|病害|病毒|线虫|蛋白|代谢|细胞|发育|进化|"
                        "制造|控制|优化|工程|科学")
        direction_en = r"(?<![A-Za-z])(AI|ML|DL|CV|NLP|CSE|CS|ECE|GIS|UAV|LLM|HPC|GWAS|CRISPR|QTL)(?![A-Za-z])"
        has_direction = bool(re.search(direction_cn, core_title)
                             or re.search(direction_en, core_title, flags=re.I))
        unit_marks = r"(下设|隶属|成立于|建于|创办于|位于|该校|该院|公立|私立|研究型|赠地|分校|校区|规模第|由.{0,12}设立)"
        unit_gloss = r"（[A-Za-z][A-Za-z.,&'’\- ]{4,90}，[^）]{4,90}）"
        has_unit = bool(re.search(unit_marks, body) or re.search(unit_gloss, body))
        platform_hits = re.findall(r"linked\s*in|领英", raw, flags=re.I)
        r19 = []
        if not has_direction:
            r19.append(f"标题未写明方向 → {core_title[:40]}；补研究方向或岗位方向词（如「土豆育种」「生物信息学」）")
        if not has_unit:
            r19.append("正文缺单位简介 → 开头用 1-2 句写机构性质、学院定位、与方向相关的积累")
        if platform_hits:
            r19.append(f"出现第三方线索平台字样 {len(platform_hits)} 处 → 删掉平台名与「线索来自…」表述，只给官方岗位页 URL")
        if r19:
            add("✗", "学术招聘三项新规（2026-11-08 良超定：标题写方向 / 单位简介 / 信源只给官方页）", r19)
        else:
            add("✓", "学术招聘三项新规（标题方向 / 单位简介 / 官方信源）", [])

    # --- 20. 名单盘点类核验提醒（2026-11-08 农业院士版图篇实证：凭记忆列名单误列王二涛、漏 5 人）---
    # 触发：正文含「院士/长江学者/杰青」等头衔词且含「名单/盘点/全景/版图/图谱」类词
    # → ⚠ 提示逐人回官方名单页核验。名单对错是发布级事实错误，脚本报不出对错，只报义务。
    # 规则本体：references/writing-style.md「事实核查」节。
    title_words = re.findall(r"院士|长江学者|杰出青年|优青|双一流", body)
    roster_words = re.findall(r"名单|盘点|全景|版图|图谱|全名单|一览", body)
    if title_words and roster_words:
        add("⚠", "名单盘点类内容：逐人回官方名单页核验（两院 casad.cas.cn / cae.cn，高校/机构官网），不得凭记忆或媒体转述",
            ["2026-11-08 实证：凭记忆列涉农院士名单，误列王二涛（非院士）、漏张启发等 5 人；发布后属事实事故"])
    elif title_words:
        add("✓", "涉头衔表述，非名单盘点类", [])

    # --- 21. 文献出处逐条 DOI 核验（2026-11-08 良超反馈：科研类公众号引用不能错）---
    # 复核实证：Evers & Bastiaans 2016 期刊名凭记忆写成 Plant Ecology，DOI 解析实为
    # Journal of Plant Research（s10265 = J Plant Res）——DOI 对、期刊名错也是引用事故。
    # 铁律：文内出处的作者/期刊/年份以 DOI 解析题录为准，引用内容逐条回一手原文核验。
    # 机械层两查：① 每个 doi: 能否解析（404/410 ✗）；② Crossref 有题录时比对期刊名与年份（⚠）。
    # 规则本体：references/writing-style.md「事实核查」节。
    # 2026-11-10 修复（辐射传输模型科普篇）：旧式捕获组不含成对括号，经典 DOI
    # （10.1016/0034-4257(90)90100-Z）在括号处被截断成假 DOI（检查 21 报✗）。
    # 改为吞到空白/中文标点为止，再剔尾：分号后接中文视为句末分隔；
    # 右括号仅在不成对时剥掉（DOI 内部成对括号不动）。
    def _clean_doi(raw: str) -> str:
        d = re.split(r"[；;](?=[\u4e00-\u9fff])", raw, maxsplit=1)[0]
        d = d.rstrip(".,;;，；。`")
        while d.endswith(")") and d.count(")") > d.count("("):
            d = d[:-1]
        return d

    dois = sorted({_clean_doi(m.group(1)) for m in
                   re.finditer(r"doi:\s*(10\.[0-9]{4,9}/[^\s，。,）`]+)", md, flags=re.I)})
    if dois:
        import json as _json
        # 中文刊英文名对照（Crossref 题录只给英文刊名；稿内写中文刊名时经此比对）
        JOURNAL_ALIASES = {
            "作物学报": "actaagronomicasinica",
            "中国农业大学学报": "journalofchinaagriculturaluniversity",
            "中国棉花": "chinacotton",
        }
        # 已知 DOI 不进 DOI 基金会国际库的中文期刊前缀（期刊官网标注亦如此，降级⚠但要求卷期页码）
        CHN_UNREG_PREFIXES = ("10.11963/",)

        def _norm(s):
            return re.sub(r"[^a-z0-9\u4e00-\u9fff]", "", s.lower())

        doi_ok, doi_bad, doi_chn, doi_unknown, meta_warn = [], [], [], [], []
        chunks = re.split(r"[；;]", md)   # 出处括注定位：按分号切块，避开卷期里的括号
        for d in dois:
            chunk = next((c for c in chunks if d.lower() in c.lower()), "")
            # ① 注册机构查询（doiRA）：RA 存在=已注册（Crossref/ISTIC/mEDRA 等）；
            #    "DOI does not exist" 是笔误/未注册的可靠判别（假 DOI 实测同样返回不存在）
            try:
                req = urllib.request.Request(
                    f"https://doi.org/doiRA/{d}",
                    headers={"User-Agent": "Mozilla/5.0 (selfcheck)"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    ra = (_json.load(resp) or [{}])[0]
            except Exception:
                doi_unknown.append(f"{d}（断网/超时，未能核验）")
                continue
            if ra.get("RA"):
                doi_ok.append(f"{d}（{ra['RA']} 注册）")
                # ② Crossref 题录比对期刊名与年份（ISTIC 等不在 Crossref 的查不到即跳过）
                try:
                    req = urllib.request.Request(
                        f"https://api.crossref.org/works/{d}",
                        headers={"User-Agent": "Mozilla/5.0 (selfcheck)"})
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        msg = _json.load(resp).get("message", {})
                    container = (msg.get("container-title") or [""])[0]
                    py = (msg.get("published-print")
                          or msg.get("published-online") or {}) \
                            .get("date-parts", [[None]])[0][0]
                    # 2026-11-10 修复（辐射传输模型科普篇）：同一分块里可能先撞上作者-年份括注
                    # （如「（Pinty et al., 2001）」），错把它当期刊名报题录不一致——
                    # 优先选年份与 DOI 题录一致的括注，取不到再退回首个
                    cands = re.findall(r"[（(]([^，,（）()]+)[，,]\s*(\d{4})", chunk)
                    pick = next((x for x in cands if py and x[1] == str(py)),
                                cands[0] if cands else None)
                    if pick and container:
                        jn, yr = pick[0].strip(), pick[1]
                        jn_cjk = bool(re.search(r"[\u4e00-\u9fff]", jn))
                        ct_cjk = bool(re.search(r"[\u4e00-\u9fff]", container))
                        cmp_jn = JOURNAL_ALIASES.get(jn)
                        if cmp_jn or jn_cjk == ct_cjk:
                            probe = cmp_jn or jn
                            if (_norm(probe) not in _norm(container)
                                    and _norm(container) not in _norm(probe)):
                                meta_warn.append(
                                    f"{d}：稿内期刊名「{jn}」≠ DOI 题录「{container}」，以题录为准")
                        if py and str(py) != yr:
                            meta_warn.append(f"{d}：稿内年份 {yr} ≠ DOI 题录 {py}")
                except Exception:
                    pass
            elif d.startswith(CHN_UNREG_PREFIXES):
                if not re.search(r"\d+\(\d+\)|\d+\s*[：:]\s*\d+\s*[-–]\s*\d+", chunk):
                    doi_bad.append(f"{d}：未注册 DOI 且出处缺卷期页码——读者无法定位，补「卷(期)：起止页」")
                else:
                    doi_chn.append(f"{d}（已知该刊 DOI 不进国际库、官网标注亦如此；出处带卷期页码可定位）")
            else:
                doi_bad.append(f"{d}：DOI 基金会无注册记录——疑似笔误，回原文核对")
        if doi_bad:
            add("✗", "文献 DOI 无效或出处不可定位（引用错误是发布级事故）", doi_bad)
        else:
            add("✓", f"文献 DOI 核验通过（{len(dois)} 条）", doi_ok)
        if doi_chn:
            add("⚠", "DOI 未进国际库但可定位（推草稿前到期刊官网终核题录）", doi_chn)
        if doi_unknown:
            add("⚠", "未能联网核验 DOI", doi_unknown + ["推草稿前逐条打开 https://doi.org/<DOI> 确认"])
        if meta_warn:
            add("⚠", "出处题录与 DOI 解析不一致（期刊名/年份以 DOI 题录为准）", meta_warn)

    # --- 22. 短工具/产品安利稿（2026-11-10 良超反馈：「你写的太多了，只要说怎么用就行了
    #          不要讲原理，说明这个 skill 能解决实验室安全考试就行」）---
    # 通用规则：安利类稿件只回答「能解决什么 + 怎么用」，不写实现原理、页面机制、站点细节、
    # 包结构、踩坑记录；篇幅压到一屏能读完。front matter 标 short_form: 1 时启用，存量稿不回改。
    # 规则本体：references/writing-style.md「工具/产品安利稿专属」节。
    if is_short:
        n_chars = len(re.sub(r"\s+", "", body))
        impl_words = (r"div\.scroll|window\.scrollTo|DOM|references/|scripts/|parse_exam\.py|"
                      r"SKILL\.md|选择器|轮询|滚动事件|计时器|后端同步|硬红线|placeholder|"
                      r"mouse\.wheel|reload|代码结构|实现原理")
        hits = sorted(set(re.findall(impl_words, body, flags=re.I)))
        has_install = bool(re.search(r"请根据\s*https?://|安装\s*@|install", body, flags=re.I))
        states_goal = bool(re.search(r"考试|准入|任务|流程", body)
                           and re.search(r"替你|交给|帮你|它会|全包|包办", body))
        r22 = []
        if n_chars > 900:
            r22.append(f"正文 {n_chars} 字符（含图注）超过短稿上限 900 → 安利稿写成了说明书，删原理与展开段")
        if hits:
            r22.append(f"出现实现原理/机制词 {hits} → 读者只要用法，删掉或移进技能包文档")
        if not has_install:
            r22.append("没有可照抄的安装/使用命令 → 补一句发给 AI 的安装提示词")
        if not states_goal:
            r22.append("没点明能解决什么 → 开头一句话写清它替读者做完哪件事")
        if n_sec > 3:
            r22.append(f"{n_sec} 个小标题过多 → 短稿只留「能做什么」与「怎么用」两节")
        if r22:
            add("✗", "短工具/产品安利稿（只讲用法与能解决什么，不讲原理）", r22)
        else:
            add("✓", f"短工具安利稿（{n_chars} 字符 / {n_sec} 节 / {n_img} 图，零原理词，安装命令齐）", [])

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
