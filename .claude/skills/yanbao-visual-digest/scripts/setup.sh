#!/usr/bin/env bash
# One-time tooling for the 研报可视化 skill.
# Installs: PDF text/image extraction (pymupdf), image + QR decode libs, and 思源 CJK fonts.
# Inter + Fraunces are bundled in ../assets/fonts/ — no download needed.
set -u
echo "[setup] python libs..."
pip install --quiet pymupdf pillow pyzbar >/dev/null 2>&1 || pip install pymupdf pillow pyzbar

echo "[setup] system fonts + zbar (needs apt; ok if it warns)..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null 2>&1 || true
# --no-install-recommends avoids a transient broken transitive dep pulling the whole install down
apt-get install -y --no-install-recommends fonts-noto-cjk libzbar0 >/dev/null 2>&1 \
  || { apt-get update -qq >/dev/null 2>&1; apt-get install -y --no-install-recommends fonts-noto-cjk libzbar0 >/dev/null 2>&1; } \
  || echo "[setup] WARN: apt install partially failed — 思源字体或 zbar 可能缺失，可重试或改用系统已有 CJK 字体"
apt-get install -y --no-install-recommends fonts-noto-cjk-extra >/dev/null 2>&1 || true

echo "[setup] CJK fonts present:"; fc-list 2>/dev/null | grep -ci "noto.*cjk" || true
echo "[setup] done."
