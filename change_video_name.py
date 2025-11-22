# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# 修复 <video src=...> 中的路径与文件名：
# - 将所有反斜杠 '\' 统一为 '/'
# - 将文件名中的空格(含 &nbsp;, %20, 非断行空格)替换为下划线
# - 删除文件名末尾的 -数字（例如 foo-4.mp4 -> foo.mp4）
# - 支持 src 用单/双引号，支持 URL 编码与 HTML 实体
# """
#
# import re
# import sys
# import html
# import urllib.parse
# from pathlib import PurePosixPath
#
# def fix_src_value(src_raw):
#     # 1) 先解 HTML 实体（如 &nbsp; -> 非断行空格）
#     s = html.unescape(src_raw)
#
#     # 2) 再做 URL 解码（%20 -> 空格 等）
#     s = urllib.parse.unquote(s)
#
#     # 3) 统一分隔符为 '/'（把所有 '\' 换成 '/'）
#     s = s.replace("\\", "/")
#
#     # 4) 把连续的空白（普通空格、\u00A0 等）统一为普通空格
#     s = re.sub(r'[\u00A0\s]+', ' ', s)
#
#     # 5) 切分路径与文件名（保留中间路径）
#     parts = s.split('/')
#     if len(parts) == 0:
#         return s
#     path_parts = parts[:-1]
#     filename = parts[-1]
#
#     # 6) 删除 filename 末尾的 -数字（紧邻扩展名前，如 -4.mp4）
#     filename = re.sub(r'-\d+(?=\.[^.]+$)', '', filename)
#
#     # 7) 空格 -> 下划线（对 filename 生效）
#     filename = filename.replace(' ', '_')
#
#     # 8) 重新拼接（用 '/' 作为分隔）
#     if path_parts:
#         new_src = "/".join(path_parts) + "/" + filename
#     else:
#         new_src = filename
#
#     return new_src
#
# def fix_html_file(html_path, output_path=None):
#     with open(html_path, 'r', encoding='utf-8') as f:
#         html_text = f.read()
#
#     # 匹配 <video ... src="..."> 或 src='...'（非贪婪）
#     pattern = re.compile(r'(<video\b[^>]*?\ssrc=)(["\'])(.*?)\2', flags=re.IGNORECASE | re.DOTALL)
#
#     changed = []
#     def repl(m):
#         prefix = m.group(1)
#         quote = m.group(2)
#         src_raw = m.group(3)
#
#         new_src = fix_src_value(src_raw)
#
#         if new_src != src_raw:
#             changed.append((src_raw, new_src))
#         return f"{prefix}{quote}{new_src}{quote}"
#
#     new_html = pattern.sub(repl, html_text)
#
#     if output_path is None:
#         output_path = html_path
#
#     with open(output_path, 'w', encoding='utf-8') as f:
#         f.write(new_html)
#
#     print(f"处理完成：{len(changed)} 处可能被修改（只列出实际变更的前 20 条）")
#     for old, new in changed[:20]:
#         print("  ", old, "  ->  ", new)
#
# if __name__ == "__main__":
#     # if len(sys.argv) < 2:
#     #     print("用法: python fix_video_src.py your_file.html [output.html]")
#     #     sys.exit(1)
#     # inp = sys.argv[1]
#     # out = sys.argv[2] if len(sys.argv) >= 3 else None
#     fix_html_file('index.html', 'index.html')

import re
import os
import html
import urllib.parse
from pathlib import Path


# =====================================================
#        文件名修复函数（HTML 和 磁盘文件都复用）
# =====================================================
def fix_filename(name: str) -> str:
    # 解 HTML & URL 编码
    name = html.unescape(name)
    name = urllib.parse.unquote(name)

    # 统一空白字符（包括 &nbsp; 和 \u00A0）
    name = re.sub(r'[\u00A0\s]+', ' ', name)

    # 删除末尾 -数字（如 -4.mp4）
    name = re.sub(r'-\d+(?=\.[^.]+$)', '', name)

    # 空格替换为下划线
    name = name.replace(" ", "_")

    return name


# =====================================================
#                   处理 HTML
# =====================================================
def fix_html(html_path, output_path=None):
    with open(html_path, "r", encoding="utf-8") as f:
        html_text = f.read()

    pattern = re.compile(r'(<video[^>]*?src=)(["\'])(.*?)(\2)', re.IGNORECASE | re.DOTALL)

    modified = []

    def repl(m):
        prefix, quote, src, _ = m.groups()

        # 统一分隔符
        src = src.replace("\\", "/")

        # 分离路径/文件名
        parts = src.split("/")
        filename = parts[-1]
        path = "/".join(parts[:-1])

        new_filename = fix_filename(filename)

        new_src = (path + "/" + new_filename) if path else new_filename

        if new_src != src:
            modified.append((src, new_src))

        return f'{prefix}{quote}{new_src}{quote}'

    new_html = pattern.sub(repl, html_text)

    if output_path is None:
        output_path = html_path

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"[HTML] 修改完成，共处理 {len(modified)} 条 video src：")
    for old, new in modified[:20]:
        print("   ", old, "→", new)
    if len(modified) > 20:
        print("   ...")

    return modified  # 用于视频文件匹配


# =====================================================
#           重命名磁盘中的视频文件
# =====================================================
def fix_video_files(directories):
    print("\n[Video] 开始处理视频文件…")

    for folder in directories:
        p = Path(folder)
        if not p.exists():
            print(f"文件夹不存在，跳过：{folder}")
            continue

        for file in p.rglob("*.mp4"):
            old_name = file.name
            new_name = fix_filename(old_name)

            if new_name != old_name:
                new_path = file.with_name(new_name)

                try:
                    file.rename(new_path)
                    print(f"  {old_name}  →  {new_name}")
                except Exception as e:
                    print(f"  重命名失败 {old_name}: {e}")

    print("[Video] 视频文件全部处理完成。")


# =====================================================
#                     主函数执行
# =====================================================
def process_all(html_file):
    # 1. 修改 HTML 文件
    # fix_html(html_file)

    # 2. 修改视频文件名（static, VELR-1, VELR-2）
    video_dirs = ["static", "VELR-1", "VELR-2"]
    fix_video_files(video_dirs)


# ======================== 使用 ========================
process_all("index.html")
