#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按最终时间轴（timeline.json）重写《分镜与口播稿》，保证文档、字幕、画面三者同步。"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "tts"))
from build_video import SCENES, CUES, ORIG_SCENES, ORIG_CUES, DURATION
from synth_voiceover import SPOKEN

VIS = {
    "s0": ("大字“12 万亿美元”从 0 数到 12；横线划开；金色“89%”数上来，注“（本文测算）”；底部衬线副题“工业 5.0：先搬的是利润池，不是产能”", "P21 标题；89% = 71/80，本文测算"),
    "s1": ("8 根资本开支柱依次长出（灰＝基线），金色增量 +2 → +33 跟着口播逐根冒出；括号标“增量 ≈ 80 万亿元 ≈ 12 万亿美元”；结尾一行“2030 年起六年拿走 89%”", "P21 图"),
    "s2": ("三组横条：工业 17.4% → 19.6% ▲（绿），基建 7.6% → 4.2% ▼、地产 3.3% → 3.0% ▼（红）；下方 GDP 拉动三根柱 0.0 / 0.3 / 0.5 依次升起", "P21 右图；P36 右图"),
    "s3": ("12 万亿美元拆账条逐段展开（基建 0.5／机器人 1.5／智能装备 3.0／软件 1.0／新产能 6.0），金色括号“改工厂 5.5”；随后两组大数：金色“7% → 17%”、“30% vs 15%”", "P22 瀑布图；P26；P25"),
    "s4": ("“−50.2%”数上来（卓越级工厂次品率）；三条工厂数量横条：基础级 >30,000 满宽、先进级 >1,200 一小截、卓越级 >230 一根金线", "P15；P8；<1% = 230/30,000，本文测算"),
    "s5": ("9 行国产化率哑铃图逐行出现：空心点（当前）→ 灰线 → 金色目标；半导体设备 13.5% → 30% 在最上", "P41 表；P15 图"),
    "s6": ("U 型曲线描线：0-1 利润最高 → 内卷最低 → 金色出海段修复企稳；“5% → 8%”工业企业利润率；三段条：易替代 40%／中度 32%／难替代 28%", "P34 示意图；P30；P39"),
    "s7": ("“37／7／1”，金色“46%”数上来；三组各两只：绿的谐波 118.4%、恒立液压 55.1%／兆易创新 91.5%、中国巨石 92.9%／阳光电源 160.8%、宁德时代 100.3%", "P46 表；中位数本文测算；分组本文归类"),
    "s8": ("衬线大字“别只盯 12 万亿美元的总量，盯利润池往哪搬。”；三行回顾；THE PORT 二维码＋“全球投行研报精选”；免责一行", "—"),
}


def mmss(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def main():
    tl = json.load(open(os.path.join(HERE, "timeline.json"), encoding="utf-8"))
    rep = json.load(open(os.path.join(HERE, "tts", "asr_report.json"), encoding="utf-8"))
    tot = sum(len(r["text"]) for r in rep)
    wpy = sum(r["pyerr"] * len(r["text"]) for r in rep) / tot
    chars = sum(len(c[2].replace(" ", "")) for c in CUES)
    L = []
    L.append("# 大摩 · 工业 5.0 · 2 分钟竖屏视频：分镜与口播稿\n")
    L.append("- 成品（中文女声配音）：`大摩-工业5.0-2分钟视频_女声配音.mp4`（1080×1920，30fps，2:00，H.264＋AAC，字幕已烧录）")
    L.append("- 无配音版：`大摩-工业5.0-2分钟视频.mp4`（同一时间轴，静音音轨，给剪映换配音用）")
    L.append("- 字幕：`大摩-工业5.0-2分钟视频_字幕.srt`（23 条，与画面字幕、配音逐句对齐）")
    L.append(f"- 口播：{chars} 字；配音语速 x{tl['speed']}（约 {tot / sum(r['dur'] for r in rep):.1f} 字/秒）")
    L.append("- 素材来源：6 页精华版里已核对过的数字；每个数的原报告页码写在 `video/stage.html` 的 `<!--src-->` 注释里")
    L.append("- 重做：`python3 video/tts/synth_voiceover.py plan` → `python3 video/build_video.py` → `python3 video/render_video.py` → `python3 video/tts/synth_voiceover.py mix` → `python3 video/gen_storyboard.py`\n")
    L.append("## 配音\n")
    L.append("- 引擎：Kokoro v1.1-zh（Apache-2.0，可商用），离线合成（sherpa-onnx），女声 #9。")
    L.append("- 选声：55 个中文女声各读同一段测试句，用语音识别回听；#9 字错误率最低（1.3%），平均音高 212Hz，属中音区女声。")
    L.append(f"- 回听校验：每句在 7 档语速里各合成一次，取读音错误率最低的一版；全片按拼音比对的读音错误率 {wpy:.1%}"
             "（同音字不算错；剩下的主要是公司名“绿的谐波”“兆易创新”和声调被识别器听偏）。**我没法亲耳听，发布前请过一遍。**")
    L.append("- 多音字按词典逐个查过，口播稿里做了三处同音替换（字幕不变）：量词“只”→“支”（词典读 zhǐ）、“组装地”的“地”→“第”（词典读 de）、“头两年为零”改成“头两年是零”（“为”词典读 wèi）。")
    L.append("- 为了让配音不赶，字幕／口播比无配音版删了约 20 字（数字一个没动），字幕和分镜时间轴按语音重排，总长仍是 2:00。\n")
    L.append("## 分镜\n")
    L.append("| # | 时间 | 画面 | 口播／字幕 | 数字出处 |")
    L.append("|---|---|---|---|---|")
    for k, (sid, s, e, lab) in enumerate(SCENES):
        os_, oe = ORIG_SCENES[k][1], ORIG_SCENES[k][2]
        lines = [c[2] for c, oc in zip(CUES, ORIG_CUES) if os_ <= oc[0] < oe]
        vis, src = VIS[sid]
        L.append(f"| {k+1:02d} {lab} | {mmss(s)}–{mmss(e)} | {vis} | {'／'.join(lines)} | {src} |")
    L.append("\n## 逐句时间与回听结果\n")
    L.append("| # | 开口 | 时长 | 口播（读法版） | 识别回听 | 读音错误率 |")
    L.append("|---|---|---|---|---|---|")
    for r in rep:
        L.append(f"| {r['i']} | {r['start']}s | {r['dur']}s | {r['text']} | {r['asr']} | {r['pyerr']:.2f} |")
    L.append("\n## 换配音（剪映）\n")
    L.append("1. 用无配音版 MP4 → 文本 → 导入字幕 → 选 `_字幕.srt`，把字幕轨隐藏（画面里已有烧录字幕）。")
    L.append("2. 选中全部字幕 → 朗读 → 换成喜欢的音色。时间轴已按语速 5 字/秒左右排好，一般不用再调。")
    L.append("3. 背景音乐压到 −20dB 左右，别盖过人声。\n")
    L.append("## 画面规范\n")
    L.append("- 竖屏安全区：正文在 y=150–1310，字幕带 y≈1334–1480，来源行 y≈1516；y>1560 留白给平台的标题、点赞栏。")
    L.append("- 配色与 PDF 一致：墨色＋金色强调；涨绿跌红只用在“三条腿”的真实升降上。顶部金色进度条随时间走满，右上角是分镜序号。")
    L.append("- 结尾二维码显示 260px，没有验证过能不能扫（微信个人号码会过期）。\n")
    L.append("## 合规提示\n")
    L.append("- 画面与口播都写明“整理自大摩研报，不构成投资建议”；89%、<1%、46% 标了“本文测算”，股票分组标了“本文归类”。")
    L.append("- 个股只出现评级与目标价上行空间，不出现股价与目标价（原表币种列有误）。")
    L.append("- 若发布渠道对荐股类内容有额外要求（如持牌主体、风险揭示位置），以渠道规则为准。")
    open(os.path.join(ROOT, "大摩-工业5.0-2分钟视频_分镜与口播稿.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("分镜稿已按时间轴重写")


if __name__ == "__main__":
    main()
