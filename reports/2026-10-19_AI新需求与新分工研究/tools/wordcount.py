#!/usr/bin/env python3
"""统计 Markdown 正文字数。
用法：python3 wordcount.py <文件> [--stop "## 附录"]
- 汉字数：Unicode CJK 统一表意字符（不含标点、数字、字母）
- 中文字数（含标点）：汉字 + 中文标点，近似 Word“字数”中的中文部分
- 默认在遇到 --stop 标题（默认“# 附录”开头的一级/二级标题）后停止计数，参考文献与附录不计入正文。
"""
import re, sys, argparse
p = argparse.ArgumentParser()
p.add_argument('files', nargs='+')
p.add_argument('--stop', default=None, help='遇到以此开头的行即停止计数')
a = p.parse_args()
han = re.compile(r'[一-鿿㐀-䶿]')
cpunct = re.compile(r'[　-〿＀-￯—…“”‘’]')
tot_h = tot_p = 0
for f in a.files:
    h = pn = 0
    for line in open(f, encoding='utf-8'):
        if a.stop and line.startswith(a.stop):
            break
        h += len(han.findall(line)); pn += len(cpunct.findall(line))
    tot_h += h; tot_p += pn
    print(f"{f}\t汉字 {h}\t含中文标点 {h+pn}")
if len(a.files) > 1:
    print(f"合计\t汉字 {tot_h}\t含中文标点 {tot_h+tot_p}")
