#!/usr/bin/env bash
# 云端会话（手机发起）一次性环境准备。Mac / Windows 本机不用跑。
# 容器每次会话都是新的，所以每个云端会话第一次用 scripts/ 之前跑一次；重复跑无副作用。
#
#   bash .claude/skills/yanbao-visual-digest-v3/云端/setup.sh
#
# 做四件事：
#  1. Python 依赖：pypdf / pypdfium2 / pillow / numpy（+ cffi，容器自带的 cryptography 缺它，pypdf 会导入失败）
#  2. 中文字体：Noto Sans / Serif CJK（容器默认只有文泉驿正黑，没有宋体）
#  3. fontconfig 别名：母本写的 PingFang SC / Songti SC 等 Mac 字体名 → Noto，母本一个字不用改
#  4. 把 Playwright 自带的 Chromium 挂到 PATH 上，render_pdf.py 不用传 --browser
set -u

echo "① Python 依赖"
pip install -q pypdf pypdfium2 pillow numpy cffi 2>&1 | grep -v "Running pip as the 'root' user" || true
python3 -c "import pypdf, pypdfium2, PIL, numpy" && echo "   ok" || echo "   ✗ Python 依赖没装好"

echo "② 中文字体"
if fc-list :lang=zh family | grep -q "Noto Serif CJK SC"; then
  echo "   已装"
else
  (apt-get install -y -q --no-install-recommends fonts-noto-cjk fonts-noto-cjk-extra >/dev/null 2>&1 \
    || { apt-get update -q >/dev/null 2>&1 && apt-get install -y -q --no-install-recommends fonts-noto-cjk fonts-noto-cjk-extra >/dev/null 2>&1; }) \
    && echo "   ok" || echo "   ✗ 装不上（网络策略？）——会退回文泉驿正黑，成品字体和 Mac 版不一致，交付时要说明"
fi

echo "③ 字体别名"
mkdir -p "$HOME/.config/fontconfig"
cat > "$HOME/.config/fontconfig/fonts.conf" <<'XML'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <alias binding="same"><family>PingFang SC</family><prefer><family>Noto Sans CJK SC</family></prefer></alias>
  <alias binding="same"><family>Hiragino Sans GB</family><prefer><family>Noto Sans CJK SC</family></prefer></alias>
  <alias binding="same"><family>Songti SC</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias binding="same"><family>STSong</family><prefer><family>Noto Serif CJK SC</family></prefer></alias>
  <alias binding="same"><family>SF Mono</family><prefer><family>DejaVu Sans Mono</family></prefer></alias>
  <alias binding="same"><family>Menlo</family><prefer><family>DejaVu Sans Mono</family></prefer></alias>
</fontconfig>
XML
fc-cache -f >/dev/null 2>&1
echo "   PingFang SC → $(fc-match -f '%{family[0]}' 'PingFang SC')｜Songti SC → $(fc-match -f '%{family[0]}' 'Songti SC')"

echo "④ Chromium"
if command -v chromium >/dev/null 2>&1; then
  echo "   已在 PATH：$(command -v chromium)"
elif [ -x /opt/pw-browsers/chromium ]; then
  ln -sf /opt/pw-browsers/chromium /usr/local/bin/chromium && echo "   ok → /usr/local/bin/chromium"
else
  echo "   ✗ 没找到 Chromium，render_pdf.py 需要 --browser 指定"
fi
