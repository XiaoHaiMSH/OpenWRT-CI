#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# 为软件源目录的每一层生成 index.html（Cloudflare Pages 不会自动生成目录列表）
# 用法：Index.py <软件源根目录>

import html
import os
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")

CSS = """
:root{--bg:#f6f7f9;--fg:#1b1f24;--dim:#66707a;--line:#dfe3e8;--acc:#0b6e8a;--box:#eceff3}
@media(prefers-color-scheme:dark){:root{--bg:#14181c;--fg:#d8dde2;--dim:#8b95a0;--line:#262d34;--acc:#5cc3de;--box:#1b2127}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,"Segoe UI","PingFang SC","Noto Sans SC",sans-serif}
main{max-width:860px;margin:0 auto;padding:20px 16px 48px}
h1{font-size:20px;margin:0 0 4px;overflow-wrap:anywhere}
p.sub{margin:0 0 16px;color:var(--dim)}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
a:focus-visible,input:focus-visible,button:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
pre{background:var(--box);border:1px solid var(--line);border-radius:6px;padding:12px;margin:0 0 8px;overflow-x:auto;font:13px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
button{font:inherit;background:none;color:var(--acc);border:1px solid var(--line);border-radius:6px;padding:4px 10px;cursor:pointer}
.cmd{margin:0 0 20px}
input{width:100%;font:inherit;color:var(--fg);background:var(--box);border:1px solid var(--line);border-radius:6px;padding:9px 12px;margin:0 0 8px}
ul{list-style:none;margin:0;padding:0}
li{display:flex;justify-content:space-between;gap:16px;padding:7px 2px;border-bottom:1px solid var(--line)}
li a{font:14px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-wrap:anywhere}
li span{color:var(--dim);white-space:nowrap;font-size:13px}
.n{color:var(--dim);font-size:13px;margin:8px 0 0}
"""

JS = """
const q=document.getElementById('q'),rows=[...document.querySelectorAll('li[data-n]')],cnt=document.getElementById('cnt');
if(q){q.addEventListener('input',()=>{const k=q.value.trim().toLowerCase();let n=0;
rows.forEach(r=>{const s=!k||r.dataset.n.includes(k);r.hidden=!s;if(s)n++});
cnt.textContent=k?('匹配 '+n+' 项'):''})}
document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',()=>{
const t=document.getElementById(b.dataset.copy).innerText;
navigator.clipboard.writeText(t).then(()=>{b.textContent='已复制';setTimeout(()=>b.textContent='复制',1500)})}));
document.querySelectorAll('[data-origin]').forEach(e=>{e.textContent=e.textContent.replace('{ORIGIN}',location.origin)});
"""


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def page(title, sub, body):
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head>
<body><main><h1>{html.escape(title)}</h1><p class="sub">{html.escape(sub)}</p>
{body}</main><script>{JS}</script></body></html>"""


def usage_block(rel):
    """根目录：给出每个含 packages.adb 的软件源的使用命令"""
    out = []
    for i, d in enumerate(sorted(os.listdir(ROOT))):
        if not os.path.isfile(os.path.join(ROOT, d, "packages.adb")):
            continue
        cmd = (
            f"echo '{{ORIGIN}}/{d}/packages.adb' > /etc/apk/repositories.d/customfeeds.list\n"
            f"apk update\napk add <包名>"
        )
        out.append(
            f'<h2 style="font-size:16px;margin:16px 0 8px">{html.escape(d)}</h2>'
            f'<pre id="c{i}" data-origin>{html.escape(cmd)}</pre>'
            f'<p class="cmd"><button data-copy="c{i}">复制</button></p>'
        )
    return "".join(out)


def build(path):
    rel = os.path.relpath(path, ROOT)
    is_root = rel == "."
    entries = sorted(os.listdir(path), key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
    entries = [e for e in entries if e != "index.html"]

    items, nfiles = [], 0
    if not is_root:
        items.append('<li><a href="../">../</a><span></span></li>')
    for e in entries:
        full = os.path.join(path, e)
        name = html.escape(e)
        if os.path.isdir(full):
            items.append(f'<li data-n="{name.lower()}"><a href="{name}/">{name}/</a><span></span></li>')
        else:
            nfiles += 1
            items.append(
                f'<li data-n="{name.lower()}"><a href="{name}">{name}</a><span>{human(os.path.getsize(full))}</span></li>'
            )

    title = "软件源" if is_root else "/" + rel.replace(os.sep, "/") + "/"
    sub = "OpenWrt 软件源，点击文件即可下载。" if is_root else f"{nfiles} 个文件"
    body = usage_block(rel) if is_root else ""
    if nfiles > 8:
        body += '<input id="q" type="search" placeholder="搜索文件名" aria-label="搜索文件名">'
        body += '<p class="n" id="cnt"></p>'
    body += "<ul>" + "".join(items) + "</ul>"

    with open(os.path.join(path, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(title, sub, body))


for cur, dirs, _ in os.walk(ROOT):
    build(cur)
print(f"index.html generated under {ROOT}")
