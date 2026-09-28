#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中文女声口播：统一语速合成 → 按语音重排字幕与分镜时间轴（总长仍 120 秒）→ 逐句 ASR 回听校验。
  python3 synth_voiceover.py plan   # 合成 + 写 video/timeline.json + 存逐句音频
  python3 synth_voiceover.py mix    # 画面重渲之后：把逐句音频按新时间轴混成音轨，与画面合并
引擎：Kokoro v1.1-zh（Apache-2.0），sid=9（女声；在 55 个中文女声里 ASR 回听错误率最低）。"""
import json, os, subprocess, sys, wave
import numpy as np, imageio_ffmpeg
HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.dirname(HERE); ROOT = os.path.dirname(VID)
sys.path.insert(0, VID)
from build_video import ORIG_SCENES, ORIG_CUES, DURATION   # 原始（无配音）时间轴
from ttslib import kokoro, asr, cer, pinyin_err, aac_roundtrip

FF = imageio_ffmpeg.get_ffmpeg_exe()
SID = 9
CLIPS = os.path.join(HERE, "clips")

# 读法版口播：数字、年份、百分比写成汉字，保证读法；与字幕逐条对应、意思逐字一致
# 多音字按词典查过：量词“只”词典读 zhǐ → 口播用同音“支”；“组装地”的“地”词典读 de → 用同音“第”（字幕不变）
SPOKEN = [
    "大摩测算：中国工业五点零，十年要多花十二万亿美元。",
    "但近九成的钱，要到二零三零年以后才花。",
    "分年看，二零二六到二七年只多出两万亿元，",
    "二零三四到三五年是三十三万亿元。",
    "原因是过剩产能还没消化，起步会慢。",
    "三条投资腿，只有工业往上：占GDP从百分之十七点四升到十九点六，",
    "而基建和地产都在降。",
    "对GDP的拉动是J曲线：头两年是零，后面才显现。",
    "钱花在哪？六万亿美元建新的产能，五点五万亿用来改造工厂。",
    "改造工厂有两个放大器：软件占设备投资的比重，从百分之七升到百分之十七；",
    "有工业五点零，机器人的年增速是百分之三十；没有，只有百分之十五。",
    "回报已被验证：卓越级智能工厂的次品率降了一半。",
    "但这样的工厂只有二百三十多家，不到基础级的百分之一。",
    "第二条线是卡脖子。",
    "锂电、光伏设备国产化率已达百分之九十七，半导体设备只有十三点五，目标三十。",
    "国产化率越低的环节，抬升空间越大。",
    "第三条线是利润和出海。",
    "大摩预计，工业利润率从百分之五修复到百分之八左右。",
    "关税改变的是组装第，不是产能：对美出口只有约四成容易被替代。",
    "落到股票，大摩列了四十五支，三十七支增持，上行空间中位数百分之四十六。",
    "比如改工厂的绿的谐波、卡脖子的兆易创新、出海的阳光电源。",
    "一句话：不要只盯总量，要盯利润池往哪搬。",
    "以上整理自大摩研报，不构成投资建议。",
]
assert len(SPOKEN) == len(ORIG_CUES)

LEAD0 = 0.35      # 片头第一句开口时间
GAP = 0.30        # 同一分镜内句间停顿
SCENE_GAP = 0.85  # 换分镜时的停顿（含 0.35s 画面淡入）
PRE = 0.45        # 分镜比它的第一句提前多久出现
HOLD = 0.25       # 字幕在句尾多留的时间
TAIL_MIN = 0.8    # 片尾至少留白


def scene_of(t):
    for k, (_, s, e, _) in enumerate(ORIG_SCENES):
        if s <= t < e:
            return k
    return len(ORIG_SCENES) - 1


def layout(durs):
    sc = [scene_of(s) for s, _, _ in ORIG_CUES]
    t = LEAD0; starts = []
    for i, d in enumerate(durs):
        if i > 0:
            t += SCENE_GAP if sc[i] != sc[i - 1] else GAP
        starts.append(t); t += d
    return sc, starts, t


def synth_all(tts, speed, pick=False):
    """pick=True：每句在 speed−0.08…+0.04 七档里各合成一次，取读音错误率最低的一版（同分取最接近 speed 的）。"""
    out = []
    for txt in SPOKEN:
        cands = []
        for sp in ([round(speed + d, 3) for d in (0, -0.02, -0.04, -0.06, -0.08, 0.02, 0.04)] if pick else (speed,)):
            a = tts.generate(txt, sid=SID, speed=sp)
            x = np.array(a.samples, dtype=np.float32)
            err = max(pinyin_err(txt, asr(x, a.sample_rate)),                       # 原始音频
                      pinyin_err(txt, asr(aac_roundtrip(x, a.sample_rate), 16000))) if pick else 0.0  # 成品编码后
            cands.append((err, abs(sp - speed), x, a.sample_rate))
        err, _, x, sr = min(cands, key=lambda c: (round(c[0], 4), c[1]))
        out.append((x, sr))
    return out


def plan():
    tts = kokoro()
    base = [len(x) / sr for x, sr in synth_all(tts, 1.0)]
    fixed = LEAD0 + GAP * len(base) + (SCENE_GAP - GAP) * (len(ORIG_SCENES) - 1) + TAIL_MIN
    speed = round(sum(base) / (DURATION - fixed), 3)
    for _ in range(4):                                   # 实测后微调，保证总长 ≤120s
        clips = synth_all(tts, speed, pick=True)
        durs = [len(x) / sr for x, sr in clips]
        sc, starts, end = layout(durs)
        if end + TAIL_MIN <= DURATION:
            break
        speed = round(speed * (end + TAIL_MIN) / DURATION + 0.005, 3)
    os.makedirs(CLIPS, exist_ok=True)
    report = []
    for i, ((x, sr), d, st) in enumerate(zip(clips, durs, starts)):
        with wave.open(os.path.join(CLIPS, f"{i+1:02d}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
        hyp = asr(x, sr)
        report.append(dict(i=i + 1, start=round(st, 2), dur=round(d, 2), cer=round(cer(SPOKEN[i], hyp), 3),
                           pyerr=round(pinyin_err(SPOKEN[i], hyp), 3), text=SPOKEN[i], asr=hyp))
    # 新字幕：开口即出，句尾多留 HOLD，不跨到下一句
    cues = []
    for i, (st, d) in enumerate(zip(starts, durs)):
        nxt = starts[i + 1] if i + 1 < len(starts) else DURATION
        cues.append([round(st - 0.05, 2), round(min(st + d + HOLD, nxt - 0.05), 2), ORIG_CUES[i][2]])
    # 新分镜：每个分镜在它的第一句前 PRE 秒出现
    first = {}
    for i, k in enumerate(sc):
        first.setdefault(k, starts[i])
    sstart = [0.0 if k == 0 else round(first[k] - PRE, 2) for k in range(len(ORIG_SCENES))]
    scenes = [[ORIG_SCENES[k][0], sstart[k], sstart[k + 1] if k + 1 < len(sstart) else DURATION, ORIG_SCENES[k][3]]
              for k in range(len(ORIG_SCENES))]
    json.dump(dict(engine="kokoro-multi-lang-v1_1", sid=SID, speed=speed, scenes=scenes, cues=cues,
                   voice_starts=[round(s, 3) for s in starts]),
              open(os.path.join(VID, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(report, open(os.path.join(HERE, "asr_report.json"), "w"), ensure_ascii=False, indent=1)
    tot = sum(len(r["text"]) for r in report)
    wcer = sum(r["cer"] * len(r["text"]) for r in report) / tot
    wpy = sum(r["pyerr"] * len(r["text"]) for r in report) / tot
    print(f"语速 x{speed}；语音总长 {sum(durs):.1f}s；末句结束 {end:.1f}s；平均 {tot/sum(durs):.1f} 字/秒；"
          f"逐句回听：字错误率 {wcer:.3f}，读音错误率 {wpy:.3f}")
    for r in report:
        flag = "  ←" if r["pyerr"] > 0.06 else ""
        print(f'{r["i"]:>2} @{r["start"]:>6}s {r["dur"]:>4}s 读音 {r["pyerr"]:.2f} 字 {r["cer"]:.2f}{flag}  {r["asr"]}')
    for s in scenes:
        print("分镜", s)


def mix():
    tl = json.load(open(os.path.join(VID, "timeline.json")))
    track = None; sr = None
    for i, st in enumerate(tl["voice_starts"]):
        with wave.open(os.path.join(CLIPS, f"{i+1:02d}.wav")) as w:
            sr = w.getframerate(); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32767
        if track is None:
            track = np.zeros(int(DURATION * sr), dtype=np.float32)
        a = int(st * sr); track[a:a + len(x)] += x[:max(0, len(track) - a)]
    wav = os.path.join(HERE, "voiceover.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
    src = os.path.join(ROOT, "大摩-工业5.0-2分钟视频.mp4")
    out = os.path.join(ROOT, "大摩-工业5.0-2分钟视频_女声配音.mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", src, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100", "-c:a", "aac", "-b:a", "128k", "-ac", "2",
                    "-t", str(DURATION), "-movflags", "+faststart", out], check=True)
    # 整轨回听：从成品里把音频解出来，整段识别，对照全部口播
    pcm = subprocess.run([FF, "-loglevel", "error", "-i", out, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         capture_output=True, check=True).stdout
    y = np.frombuffer(pcm, dtype=np.float32)
    rep = json.load(open(os.path.join(HERE, "asr_report.json"), encoding="utf-8"))
    tp = n = 0; bad = []
    for r, st in zip(rep, tl["voice_starts"]):              # 按每句实际开口与时长切段，避免串到下一句
        h = asr(y[int((st - 0.05) * 16000):int((st + r["dur"] + 0.15) * 16000)], 16000)
        e = pinyin_err(r["text"], h); tp += e * len(r["text"]); n += len(r["text"])
        if e > 0.05:
            bad.append((r["i"], round(e, 2), h))
    print(f"写出 {out}  {os.path.getsize(out)/1e6:.1f} MB；成品整轨逐句回听读音错误率 {tp/n:.3f}；>5% 的句：{bad}")
    json.dump(dict(final_pyerr=round(tp / n, 4), flagged=bad), open(os.path.join(HERE, "final_check.json"), "w"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    {"plan": plan, "mix": mix}[sys.argv[1]]()
