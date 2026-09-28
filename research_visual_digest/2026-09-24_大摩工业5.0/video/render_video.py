#!/usr/bin/env python3
"""逐帧渲染 stage.html → H.264 MP4。4 路并行分段，最后无损拼接并加静音音轨（平台兼容）。"""
import os, subprocess, sys, pathlib, time
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = pathlib.Path(__file__).resolve().parent
FPS, DUR, W, H = 30, 120.0, 1080, 1920
N = int(DUR * FPS)

def worker(k, n):
    from playwright.sync_api import sync_playwright
    a, b = k * N // n, (k + 1) * N // n
    seg = HERE / f"seg_{k}.mp4"
    enc = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "image2pipe", "-vcodec", "mjpeg", "-framerate", str(FPS),
                            "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                            "-r", str(FPS), str(seg)], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pg = br.new_page(viewport={"width": W, "height": H})
        pg.goto(f"file://{HERE/'stage.html'}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        for i in range(a, b):
            pg.evaluate(f"renderAt({i / FPS})")
            enc.stdin.write(pg.screenshot(type="jpeg", quality=95))
        br.close()
    enc.stdin.close(); enc.wait()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        worker(int(sys.argv[2]), int(sys.argv[3])); sys.exit(0)
    n = 4; t0 = time.time()
    procs = [subprocess.Popen([sys.executable, __file__, "--worker", str(k), str(n)]) for k in range(n)]
    rc = [p.wait() for p in procs]
    assert all(r == 0 for r in rc), rc
    lst = HERE / "segs.txt"
    lst.write_text("".join(f"file 'seg_{k}.mp4'\n" for k in range(n)))
    out = HERE.parent / "大摩-工业5.0-2分钟视频.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-shortest",
                    "-movflags", "+faststart", str(out)], check=True)
    for k in range(n): (HERE / f"seg_{k}.mp4").unlink()
    lst.unlink()
    print("写出", out, f"{out.stat().st_size/1e6:.1f} MB，耗时 {time.time()-t0:.0f}s")
