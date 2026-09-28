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
        d = f"{M}/sherpa-onnx-paraformer-zh-2024-03-09"            # 大模型，回听更准
        if not os.path.exists(d):
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


def pinyin_err(ref, hyp):
    """读音层面的错误率：(无声调拼音编辑距离 + 0.5×带声调) / 字数。同音字不算错。"""
    from pypinyin import lazy_pinyin, Style
    def ed(a, b):
        d = list(range(len(b) + 1))
        for i, x in enumerate(a, 1):
            p, d[0] = d[0], i
            for j, y in enumerate(b, 1):
                p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (x != y))
        return d[len(b)]
    r0, h0 = lazy_pinyin(norm(ref)), lazy_pinyin(norm(hyp))
    r1 = lazy_pinyin(norm(ref), style=Style.TONE3, neutral_tone_with_five=True)
    h1 = lazy_pinyin(norm(hyp), style=Style.TONE3, neutral_tone_with_five=True)
    return (ed(r0, h0) + 0.5 * ed(r1, h1)) / max(1, len(r0))


def aac_roundtrip(x, sr):
    """按成品同样的链路（响度归一 + AAC 128k）编码再解码，返回 16kHz 单声道，用于"成品听感"回听。"""
    import subprocess, imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    enc = subprocess.run([ff, "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-",
                          "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100", "-c:a", "aac", "-b:a", "128k", "-f", "adts", "-"],
                         input=np.asarray(x, dtype=np.float32).tobytes(), capture_output=True, check=True).stdout
    dec = subprocess.run([ff, "-loglevel", "error", "-f", "aac", "-i", "-", "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                         input=enc, capture_output=True, check=True).stdout
    return np.frombuffer(dec, dtype=np.float32)
