#!/usr/bin/env python3
"""Build helper: read covers/<slug>.svg accent, compute tint, patch article pages, render card PNGs.
Usage: python3 scripts/build.py [slug ...]   (no args = all articles)"""
import json, re, sys, math, subprocess, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent

# --- OKLCH helpers ---
def srgb_to_lin(c): c/=255; return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
def lin_to_srgb(c): c=max(0,min(1,c)); return round(255*(12.92*c if c<=0.0031308 else 1.055*c**(1/2.4)-0.055))
def rgb_to_oklch(r,g,b):
    r,g,b=map(srgb_to_lin,(r,g,b))
    l=(0.4122214708*r+0.5363325363*g+0.0514459929*b)**(1/3)
    m=(0.2119034982*r+0.6806995451*g+0.1073969566*b)**(1/3)
    s=(0.0883024619*r+0.2817188376*g+0.6299787005*b)**(1/3)
    L=0.2104542553*l+0.7936177850*m-0.0040720468*s
    A=1.9779984951*l-2.4285922050*m+0.4505937099*s
    B=0.0259040371*l+0.7827717662*m-0.8086757660*s
    return L, math.hypot(A,B), math.degrees(math.atan2(B,A))%360
def oklch_to_hex(L,C,H):
    A=C*math.cos(math.radians(H)); B=C*math.sin(math.radians(H))
    l=(L+0.3963377774*A+0.2158037573*B)**3
    m=(L-0.1055613458*A-0.0638541728*B)**3
    s=(L-0.0894841775*A-1.2914855480*B)**3
    r=4.0767416621*l-3.3077115913*m+0.2309699292*s
    g=-1.2684380046*l+2.6097574011*m-0.3413193965*s
    b=-0.0041960863*l-0.7034186147*m+1.7076147010*s
    return "#%02X%02X%02X"%tuple(lin_to_srgb(x) for x in (r,g,b))

def render_card(e):
    html=ROOT/"scripts"/"_card.html"
    html.write_text(f'''<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="../assets/style.css">
<style>html,body{{margin:0;background:#E6E6E6;width:1200px;height:630px;overflow:hidden}}
.c{{display:grid;grid-template-columns:1.15fr 1fr;height:630px}}.c img{{width:100%;height:100%;object-fit:cover}}
.t{{padding:48px;display:flex;flex-direction:column;justify-content:space-between;border-left:3px double #1B2B26}}
h1{{font-family:'Noto Serif SC',serif;font-weight:900;font-size:52px;line-height:1.2;margin:0}}
.en{{font-family:'Instrument Serif',serif;font-style:italic;font-size:26px;opacity:.75}}</style>
<div class="c"><img src="../{e["cover"]}"><div class="t"><div class="mono">读本 · {e["category"]}</div>
<div><h1>{e["title_zh"]}</h1><div class="en">{e["title_en"]}</div></div><div class="mono">{e["author"]}</div></div></div>''')
    out=ROOT/"cards"/f'{e["slug"]}.png'
    subprocess.run(["google-chrome","--headless=new","--no-sandbox","--hide-scrollbars","--allow-file-access-from-files",
        "--window-size=1200,630","--virtual-time-budget=6000",f"--screenshot={out}",html.as_uri()],
        check=True,stderr=subprocess.DEVNULL,stdout=subprocess.DEVNULL)
    html.unlink()

def patch_article(e):
    p=ROOT/"articles"/f'{e["slug"]}.html'; s=p.read_text()
    s=re.sub(r'<body[^>]*>', f'<body class="article" style="--tint:{e["tint"]}">' if e.get("tint") else '<body class="article">', s, count=1)
    fig=(f'<figure class="cover"><img src="../{e["cover"]}" alt="{e["title_en"]} 封面">'
         +(f'<figcaption class="credit mono">封面图来源：<a href="{e["source"]}">{e["cover_credit"]}</a></figcaption>' if e.get("cover_credit") else '')
         +'</figure>')
    if '<figure class="cover">' in s:
        s=re.sub(r'<figure class="cover">.*?</figure>', lambda m: fig, s, count=1, flags=re.S)
    else:
        s=re.sub(r'(<section class="opening">.*?)<img [^>]*>', lambda m: m.group(1)+fig, s, count=1, flags=re.S)
    p.write_text(s)

def main():
    data=json.loads((ROOT/"articles.json").read_text())
    want=set(sys.argv[1:])
    for e in data:
        if want and e["slug"] not in want: continue
        svg=ROOT/"covers"/f'{e["slug"]}.svg'
        if not svg.exists(): sys.exit(f"missing {svg}: draw it per the cover system in README")
        m=re.search(r'data-accent="(#[0-9A-Fa-f]{6})"', svg.read_text())
        if not m: sys.exit(f"{svg} needs data-accent=\"#RRGGBB\" on the root <svg>")
        acc=m.group(1).upper()
        _,C,H=rgb_to_oklch(*(int(acc[k:k+2],16) for k in (1,3,5)))
        e["cover"]=f'covers/{e["slug"]}.svg'; e["accent"]=acc
        e["tint"]=oklch_to_hex(0.93, min(0.014, C*0.15) if C>0.02 else 0.004, H)
        for k in ("cover_source_url","cover_credit","dominant"): e.pop(k,None)
        patch_article(e); render_card(e)
        print(e["slug"], acc, e["tint"])
    (ROOT/"articles.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
main()
