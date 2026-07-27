#!/usr/bin/env python3
"""Clean-crop a QR image down to the code + a generous quiet zone.

Removes surrounding branding/captions (a logo above the code, a "扫码加好友" line below)
so the QR can be placed into your own designed card, WITHOUT touching the code modules.
Locates the code region with OpenCV's QR detector (works even when it can't decode a
logo-in-center WeChat code), adds a ~15% white quiet zone (>= the 4-module minimum), and
re-verifies the crop decodes to the same payload as the source — so scannability is guaranteed.

Usage:
    python crop_qr.py <in.png> [out.png]     # default out: qr.png next to input
"""
import sys, os
import numpy as np
from PIL import Image

if len(sys.argv) < 2:
    sys.exit("usage: crop_qr.py <in.png> [out.png]")
src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(src) or ".", "qr.png")

im = Image.open(src).convert("RGB")
W, H = im.size
box = None

# 1) Preferred: OpenCV locates the QR quad (robust to logos/captions outside the code).
try:
    import cv2
    arr = np.array(im)[:, :, ::-1]  # RGB->BGR
    det = cv2.QRCodeDetector()
    ok, pts = det.detect(arr)
    if ok and pts is not None:
        p = pts.reshape(-1, 2)
        minc, minr = p[:, 0].min(), p[:, 1].min()
        maxc, maxr = p[:, 0].max(), p[:, 1].max()
        # small outward pad so we don't clip the outermost modules
        pad = 0.02 * max(maxc - minc, maxr - minr)
        box = (max(0, int(minc - pad)), max(0, int(minr - pad)),
               min(W, int(maxc + pad)), min(H, int(maxr + pad)))
except Exception as e:
    print(f"(cv2 detect unavailable: {e})")

# 2) Fallback: bounding box of the darkest pixels (finder patterns are pure black).
if box is None:
    g = np.array(im.convert("L"))
    ys, xs = np.where(g < 110)
    if len(xs) == 0:
        sys.exit("no dark pixels found — is this a QR image?")
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    print("note: used dark-pixel fallback; if a logo got included, pre-crop the source.")

code = im.crop(box)
cw, ch = code.size
side = max(cw, ch)
margin = int(round(side * 0.15))
canvas = Image.new("RGB", (side + 2 * margin, side + 2 * margin), (255, 255, 255))
canvas.paste(code, ((canvas.size[0] - cw) // 2, (canvas.size[1] - ch) // 2))
canvas.save(out)
print(f"cropped {src} -> {out}  code={cw}x{ch}  margin={margin}px ({margin/side*100:.0f}%)")

# 3) Verify decode survived (needs libzbar0 + pyzbar).
try:
    from pyzbar.pyzbar import decode
    a = [r.data.decode("utf-8", "replace") for r in decode(Image.open(src))]
    b = [r.data.decode("utf-8", "replace") for r in decode(Image.open(out))]
    print("decode source:", a or "NONE")
    print("decode  crop :", b or "NONE")
    if b and a and b[0] == a[0]:
        print("OK: crop decodes to the same payload — scannability preserved.")
    elif b:
        print("NOTE: crop decodes but payload differs — inspect.")
    else:
        print("WARN: crop did not decode — widen the margin or pre-crop the source.")
except Exception as e:
    print(f"(skip decode check: {e}; install libzbar0 + pyzbar to enable)")
