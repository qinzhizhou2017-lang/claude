import time, json, numpy as np
from ttslib import kokoro, melo, asr, cer, f0_median
TXT = "锂电、光伏设备国产化率已达百分之九十七，半导体设备只有百分之十三点五。三条投资腿里，只有工业往上：占GDP从百分之十七点四升到百分之十九点六。卡脖子的环节，抬升空间越大。"
res = []
t = melo(); a = t.generate(TXT, sid=0, speed=1.0); x = np.array(a.samples)
res.append(dict(v="melo-0", cer=cer(TXT, asr(x, a.sample_rate)), f0=f0_median(x, a.sample_rate), dur=len(x)/a.sample_rate))
k = kokoro(); print("kokoro speakers:", k.num_speakers)
for sid in range(k.num_speakers):
    a = k.generate(TXT, sid=sid, speed=1.0); x = np.array(a.samples)
    res.append(dict(v=f"kokoro-{sid}", cer=cer(TXT, asr(x, a.sample_rate)), f0=f0_median(x, a.sample_rate), dur=len(x)/a.sample_rate))
json.dump(res, open("eval.json", "w"), ensure_ascii=False, indent=0)
fem = sorted([r for r in res if r["f0"] > 165], key=lambda r: (r["cer"], -r["f0"]))
print("女声（F0>165Hz）按识别错误率排序：")
for r in fem[:15]: print(f'{r["v"]:>10}  CER {r["cer"]:.3f}  F0 {r["f0"]:.0f}Hz  时长 {r["dur"]:.1f}s')
print("全部", len(res), "；女声", len(fem))
