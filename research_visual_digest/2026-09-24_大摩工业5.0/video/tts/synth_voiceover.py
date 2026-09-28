#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按字幕时间轴合成中文女声口播，逐句 ASR 回听校验，混成 120 秒音轨并与画面合并。
用法：python3 synth_voiceover.py <engine> <sid> [base_speed]   engine = kokoro | melo"""
import json, os, subprocess, sys, wave
import numpy as np, imageio_ffmpeg
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from build_video import CUES, DURATION      # 与画面字幕同一份时间轴
from ttslib import kokoro, melo, asr, cer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FF = imageio_ffmpeg.get_ffmpeg_exe()

# 读法版口播：数字、年份、百分比改写成汉字，保证 TTS 读法；与 CUES 一一对应、意思逐字一致
SPOKEN = [
    "大摩最新测算：未来十年，中国要为工业五点零多花十二万亿美元。",
    "但近九成，要到二零三零年后才花。",
    "分年看，二零二六到二七年只多出两万亿元，",
    "二零三四到三五年是三十三万亿元。",
    "原因是过剩产能还没消化，起步会慢。",
    "三条投资腿里，只有工业往上：占GDP从百分之十七点四升到百分之十九点六，",
    "基建和地产都在降。",
    "对GDP的拉动是J曲线：头两年为零，后面才显现。",
    "钱花在哪？六万亿美元建新产能，五点五万亿改造工厂。",
    "改工厂有两个放大器：工业软件占设备投资的比重从百分之七升到百分之十七；",
    "机器人市场年增速：有工业五点零是百分之三十，没有只有百分之十五。",
    "回报已被验证：卓越级智能工厂的次品率降了一半。",
    "但这样的工厂只有二百三十多家，不到基础级的百分之一。",
    "第二条线是卡脖子。",
    "锂电、光伏设备国产化率已达百分之九十七，半导体设备只有百分之十三点五，目标百分之三十。",
    "国产化率越低的环节，抬升空间越大。",
    "第三条线是利润和出海。",
    "大摩预计，工业利润率从百分之五修复到百分之八。",
    "关税改变的是组装地，不是产能：中国对美出口只有约四成容易被替代。",
    "落到股票，大摩列了四十五只，三十七只增持，上行空间中位数百分之四十六。",
    "比如改工厂的绿的谐波、卡脖子的兆易创新、出海的阳光电源。",
    "一句话：别只盯总量，要盯利润池往哪搬。",
    "以上整理自大摩研报，不构成投资建议。",
]
assert len(SPOKEN) == len(CUES)

LEAD = 0.08          # 字幕出现后多久开口
TAIL = 0.12          # 句尾到下一条字幕至少留的空
MAX_SPEED = 1.25


def main(engine, sid, base):
    tts = kokoro() if engine == "kokoro" else melo()
    sr = None; track = None; report = []
    for i, ((s, e, sub), text) in enumerate(zip(CUES, SPOKEN)):
        nxt = CUES[i + 1][0] if i + 1 < len(CUES) else DURATION
        slot = nxt - s - LEAD - TAIL
        speed = base
        a = tts.generate(text, sid=sid, speed=speed); x = np.array(a.samples, dtype=np.float32)
        sr = a.sample_rate; d = len(x) / sr
        if d > slot:                                   # 超时就提速重合成（有上限）
            speed = min(MAX_SPEED, base * d / slot * 1.02)
            a = tts.generate(text, sid=sid, speed=speed); x = np.array(a.samples, dtype=np.float32); d = len(x) / sr
        if track is None:
            track = np.zeros(int(DURATION * sr) + sr, dtype=np.float32)
        st = int((s + LEAD) * sr)
        track[st:st + len(x)] += x
        hyp = asr(x, sr)
        report.append(dict(i=i + 1, start=s, dur=round(d, 2), slot=round(slot, 2), speed=round(speed, 2),
                           overflow=round(max(0.0, d - slot), 2), cer=round(cer(text, hyp), 3), text=text, asr=hyp))
    track = track[:int(DURATION * sr)]
    peak = float(np.max(np.abs(track))) or 1.0
    track = (track / peak * 0.89).astype(np.float32)
    wav = os.path.join(HERE, "voiceover_raw.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())
    json.dump(report, open(os.path.join(HERE, "asr_report.json"), "w"), ensure_ascii=False, indent=1)
    # 响度归一（短视频常用 -16 LUFS）后与画面合并；画面流直接拷贝
    src = os.path.join(ROOT, "大摩-工业5.0-2分钟视频.mp4")
    out = os.path.join(ROOT, "大摩-工业5.0-2分钟视频_女声配音.mp4")
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", src, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100",
                    "-c:a", "aac", "-b:a", "128k", "-ac", "2", "-t", str(DURATION), "-movflags", "+faststart", out], check=True)
    tot = sum(len(r["text"]) for r in report)
    wcer = sum(r["cer"] * len(r["text"]) for r in report) / tot
    print(f"写出 {out}  {os.path.getsize(out)/1e6:.1f} MB")
    print(f"逐句回听：加权 CER {wcer:.3f}；提速句 {sum(r['speed'] > base for r in report)} 条；仍超时 {sum(r['overflow'] > 0 for r in report)} 条")
    for r in report:
        flag = "  ←" if r["cer"] > 0.08 or r["overflow"] > 0 else ""
        print(f'{r["i"]:>2} {r["dur"]:>5}s/{r["slot"]:>5}s x{r["speed"]} CER {r["cer"]:.2f}{flag}  {r["asr"]}')


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
