#!/usr/bin/env python3
"""
测试脚本：试着读你那个互联网可见的飞书文件夹。

用法：
    python3 test_folder.py
"""
import os
import sys

# 清掉代理（和 main.py 保持一致）
for _k in list(os.environ.keys()):
    if "proxy" in _k.lower():
        del os.environ[_k]
os.environ["NO_PROXY"] = "*"

from feishu_bot.config import Config
from feishu_bot.core.api_client import api_client
from feishu_bot.core.user_auth import user_token_manager

FOLDER_TOKEN = "NuMEfrhlQlar0rdowNdcFaGqnhb"


def main():
    print("=" * 60)
    print(f"目标文件夹: {FOLDER_TOKEN}")
    print(f"App ID:    {Config.APP_ID[:10]}..." if Config.APP_ID else "App ID:    ❌ 未配置")
    print(f"用户授权:   {'✅ 已授权' if user_token_manager.is_authorized else '❌ 未授权（请先跑 python3 main.py --auth）'}")
    print("=" * 60)

    if not Config.APP_ID or not Config.APP_SECRET:
        print("\n❌ 缺 FEISHU_APP_ID / FEISHU_APP_SECRET，请检查 .env")
        sys.exit(1)

    # ── 步骤 1：列出文件夹里的东西 ──
    print("\n[1/2] 列文件夹内容...")
    data = api_client.list_drive_files(FOLDER_TOKEN, page_size=20)

    if data.get("code") != 0:
        print(f"❌ 失败: code={data.get('code')}, msg={data.get('msg')}")
        print(f"   完整响应: {data}")
        print("\n💡 常见原因：")
        print("   - code=99991663 → token 无效或过期，重跑 --auth")
        print("   - code=1254030  → 没权限读这个文件夹")
        print("   - code=1061004  → folder_token 不对")
        sys.exit(1)

    files = data.get("data", {}).get("files", [])
    print(f"✅ 找到 {len(files)} 个项目：\n")
    for i, f in enumerate(files, 1):
        ftype = f.get("type", "?")
        name = f.get("name", "无名")
        print(f"  {i:2}. [{ftype:8}] {name}")
        print(f"      token: {f.get('token')}")

    if not files:
        print("⚠️  文件夹是空的，或者权限不到")
        return

    # ── 步骤 2：试着读一篇 doc 的正文 ──
    print("\n[2/2] 尝试读第一篇文档的正文（PDF 不能用此接口）...")
    doc = next((f for f in files if f.get("type") in ("doc", "docx")), None)
    if not doc:
        print("ℹ️  这个文件夹里没有 doc/docx 类型，只有 PDF 之类。")
        print("   PDF 需要走下载接口，不在本测试范围。")
        print("   但能列出文件，说明权限已经通了 ✅")
        return

    resp = api_client.get_document_raw_content(doc["token"])
    if resp.get("code") != 0:
        print(f"❌ 读正文失败: {resp.get('msg')}")
        return

    content = resp.get("data", {}).get("content", "")
    print(f"✅ 读取成功！")
    print(f"   文档名: {doc['name']}")
    print(f"   字数:   {len(content)}")
    print(f"\n   前 300 字预览：")
    print("   " + "─" * 50)
    print("   " + content[:300].replace("\n", "\n   "))
    print("   " + "─" * 50)


if __name__ == "__main__":
    main()
