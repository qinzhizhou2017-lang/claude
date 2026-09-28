# -*- coding: utf-8 -*-
"""离线中文 TTS（sherpa-onnx）+ ASR 回听校验的公共函数。模型放在会话 scratchpad，不入库。"""
import os, re, numpy as np, sherpa_onnx
M = os.environ.get("TTS_MODELS", "/tmp/claude-0/-home-user-claude/6fcf16f6-0f09-5541-a0a7-00c21c93e840/scratchpad/tts")

def kokoro():
    d = f"{M}/kokoro-multi-lang-v1_1"
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=f"{d}/model.onnx", voices=f"{d}/voices.bin", tokens=f"{d}/tokens.txt",
                data_dir=f"{d}/espeak-ng-data", dict_dir=f"{d}/dict",
                lexicon=f"{d}/lexicon-us-en.txt,{d}/lexicon-zh.txt"),
            num_threads=4),
        rule_fsts=f"{d}/date-zh.fst,{d}/phone-zh.fst,{d}/number-zh.fst", max_num_sentences=1)
    return sherpa_onnx.OfflineTts(cfg)

def melo():
    d = f"{M}/vits-melo-tts-zh_en"
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=f"{d}/model.onnx", lexicon=f"{d}/lexicon.txt", tokens=f"{d}/tokens.txt", dict_dir=f"{d}/dict"),
            num_threads=4),
        rule_fsts=f"{d}/phone.fst,{d}/date.fst,{d}/number.fst,{d}/new_heteronym.fst", max_num_sentences=1)
    return sherpa_onnx.OfflineTts(cfg)

_asr = None
def asr(samples, sr):
    global _asr
    if _asr is None:
        d = f"{M}/sherpa-onnx-paraformer-zh-small-2024-03-09"
        _asr = sherpa_onnx.OfflineRecognizer.from_paraformer(paraformer=f"{d}/model.int8.onnx", tokens=f"{d}/tokens.txt", num_threads=4)
    s = _asr.create_stream(); s.accept_waveform(sr, np.asarray(samples, dtype=np.float32)); _asr.decode_stream(s)
    return s.result.text

def norm(t):
    return re.sub(r"[\s，。：；、？！,.:;?!“”\"'（）()／/—-]", "", t).lower()

def cer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = list(range(len(h) + 1))
    for i, rc in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hc in enumerate(h, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (rc != hc))
    return d[len(h)] / max(1, len(r))

def f0_median(x, sr):
    x = np.asarray(x, dtype=np.float64); n = int(0.04 * sr); hop = n // 2; out = []
    lo, hi = int(sr / 400), int(sr / 70)
    for i in range(0, len(x) - n, hop):
        fr = x[i:i + n] * np.hanning(n)
        if np.sqrt(np.mean(fr ** 2)) < 0.02: continue
        ac = np.correlate(fr, fr, "full")[n - 1:]
        if ac[0] <= 0: continue
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] / ac[0] > 0.45: out.append(sr / k)
    return float(np.median(out)) if out else 0.0
