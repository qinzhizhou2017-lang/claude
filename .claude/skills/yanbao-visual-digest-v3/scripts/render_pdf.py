#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_pdf.py —— HTML → A4 PDF（跨平台无头浏览器，已修两个老坑）

修掉的坑：
  ①「退出码 0 但几十秒后才落盘」：老 render.py 进程一返回就判文件存在 → 误报 render FAILED，
    其实 PDF 是成功的。这里改成**轮询等文件大小连续两次不变**才算完。
  ②「并行渲染互相顶掉 + 残留浏览器进程」：每次渲染用独立临时 profile，结束后按 profile 路径清理。

⚠ 沙箱：在 Claude Code 里跑无头浏览器常被沙箱静默掐掉（退出码 0、无 stdout、不落文件）。
   这不是脚本坏了，也不是 --no-sandbox 的问题——用 dangerouslyDisableSandbox 跑本脚本。

用法：
    python3 render_pdf.py 成品.html 成品.pdf
    python3 render_pdf.py 成品.html 成品.pdf --wait 120 --budget 5000
    python3 render_pdf.py 成品.html --png 页.png --dpi 200      # 顺手出拼版图（走 pypdfium2）
"""
from __future__ import annotations
import argparse, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

CANDIDATES = [
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    # Windows
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    # Linux / PATH
    "google-chrome", "chromium", "chromium-browser", "microsoft-edge",
]


def find_browser(explicit: str | None) -> str:
    if explicit:
        return explicit
    for c in CANDIDATES:
        if os.path.sep in c or (len(c) > 2 and c[1] == ":"):
            if Path(c).exists():
                return c
        elif shutil.which(c):
            return shutil.which(c)
    sys.exit("找不到 Chrome/Edge/Chromium，用 --browser 指定绝对路径")


def wait_settled(path: Path, timeout: int, proc=None) -> bool:
    """等文件落盘：大小连续两次不变才算写完（浏览器会退出码 0 但几十秒后才写）。"""
    t0, last, stable = time.time(), -1, 0
    while time.time() - t0 < timeout:
        if path.exists():
            sz = path.stat().st_size
            if sz > 0 and sz == last:
                stable += 1
                if stable >= 2:
                    return True
            else:
                stable = 0
            last = sz
        # 浏览器已退出且文件还没影 → 多半被沙箱掐了，早点报出来别干等
        if proc is not None and proc.poll() is not None and not path.exists() \
                and time.time() - t0 > 8:
            return False
        time.sleep(1.0)
    return path.exists() and path.stat().st_size > 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("pdf", nargs="?")
    ap.add_argument("--browser")
    ap.add_argument("--wait", type=int, default=90, help="等落盘秒数，默认 90")
    ap.add_argument("--budget", type=int, default=4000, help="--virtual-time-budget，默认 4000ms")
    ap.add_argument("--png", help="额外导出拼版 PNG（每页一张，前缀）")
    ap.add_argument("--dpi", type=int, default=180)
    a = ap.parse_args()

    html = Path(a.html).resolve()
    if not html.exists():
        sys.exit(f"没有这个文件：{html}")
    pdf = Path(a.pdf).resolve() if a.pdf else html.with_suffix(".pdf")
    if pdf.exists():
        pdf.unlink()

    browser = find_browser(a.browser)
    profile = tempfile.mkdtemp(prefix="yanbao_profile_")
    cmd = [
        browser, "--headless=new", "--disable-gpu", "--no-sandbox",
        f"--user-data-dir={profile}",                 # 独立 profile：并行不互顶
        "--no-first-run", "--no-default-browser-check",
        f"--print-to-pdf={pdf}", "--print-to-pdf-no-header", "--no-pdf-header-footer",
        f"--virtual-time-budget={a.budget}",
        html.as_uri(),
    ]
    print(f"渲染器：{browser}\n输出：{pdf}")
    t0 = time.time()
    # headless Chrome 常常写完 PDF 也不退出，所以不等它退——盯文件，落盘了就收工。
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    ok = wait_settled(pdf, a.wait, proc)
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()                                 # 只杀自己起的那个，不误伤别的浏览器
    shutil.rmtree(profile, ignore_errors=True)          # 只清自己起的 profile
    if not ok:
        print("❌ 没有落盘。先确认是不是被沙箱掐了——用 dangerouslyDisableSandbox 重跑；"
              "不要急着改脚本。", file=sys.stderr)
        return 1
    print(f"✅ PDF 落盘 {pdf.stat().st_size/1024:.0f} KB，耗时 {time.time()-t0:.0f}s")

    if a.png:
        try:
            import pypdfium2 as pdfium
        except ImportError:
            print("导 PNG 需要 pypdfium2", file=sys.stderr)
            return 0
        doc = pdfium.PdfDocument(str(pdf))
        stem = Path(a.png)
        for i in range(len(doc)):
            out = stem.with_name(f"{stem.stem}{i+1:02d}{stem.suffix or '.png'}")
            doc[i].render(scale=a.dpi / 72).to_pil().save(out)
            print(f"  P{i+1} → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
