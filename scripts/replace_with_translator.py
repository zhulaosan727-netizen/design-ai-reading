#!/usr/bin/env python3
"""Feed all articles.json source URLs into DSH 译文工坊, then replace site article bodies."""
from __future__ import annotations

import html as html_lib
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_JSON = ROOT / "articles.json"
OUT_ROOT = ROOT / "article-translations"
ARTICLES_DIR = ROOT / "articles"
FIGURES_DIR = ROOT / "figures"
API = "http://127.0.0.1:3080/article-translator/api"
CONCURRENCY = 2
POLL_SEC = 4
JOB_TIMEOUT = 60 * 25  # 25 min per article
STATE = OUT_ROOT / ".batch_state.json"
LOCK = threading.Lock()

NOTICE = (
    '<p class="notice">中文全文译文：由「译文工坊」根据英文原文自动翻译生成，'
    "供学习参考。结构与措辞以译文为准；想看原始论述，请点上方「阅读原文」。</p>"
)


def api(method: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={"content-type": "application/json", "accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except Exception:
            raise RuntimeError(f"HTTP {e.code}: {raw[:400]}") from e


def normalize_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    p = urlparse(u)
    host = (p.netloc or "").lower().removeprefix("www.")
    path = (p.path or "").rstrip("/")
    return f"{p.scheme.lower()}://{host}{path}"


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"jobs": {}, "packages": {}}


def save_state(st: dict) -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    with LOCK:
        STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n")


def discover_packages() -> dict[str, str]:
    """Map normalized source URL -> package directory name."""
    mapping: dict[str, str] = {}
    if not OUT_ROOT.exists():
        return mapping
    for d in OUT_ROOT.iterdir():
        if not d.is_dir():
            continue
        man = d / "manifest.json"
        if not man.exists():
            continue
        try:
            m = json.loads(man.read_text())
        except Exception:
            continue
        src = m.get("sourceUrl") or ""
        key = normalize_url(src)
        if key:
            mapping[key] = d.name
    return mapping


def host_label(url: str) -> str:
    host = urlparse(url).netloc.removeprefix("www.")
    # short display like existing pages
    parts = host.split(".")
    if len(parts) >= 2:
        return "/".join(parts[:2]) if parts[0] in {"blog", "www"} else host
    return host


def tags_line(entry: dict) -> str:
    tags = entry.get("tags") or []
    cat = entry.get("category") or ""
    bits = [cat] + [t for t in tags if t != cat]
    # existing pages mix category + tags; keep similar
    return " / ".join(bits) if bits else cat


def extract_body(zh_html: str) -> tuple[str, str]:
    """Return (body_html, script_html) from translator article.zh.html."""
    m = re.search(r"<main>(.*)</main>", zh_html, re.S)
    if not m:
        raise ValueError("article.zh.html missing <main>")
    body = m.group(1)
    body = re.sub(r'<div class="kicker">.*?</div>\s*', "", body, count=1, flags=re.S)
    body = re.sub(r"<h1>.*?</h1>\s*", "", body, count=1, flags=re.S)
    body = re.sub(r'<p class="byline">.*?</p>\s*', "", body, count=1, flags=re.S)
    body = re.sub(r'<img class="cover"[^>]*>\s*', "", body, count=1)
    body = re.sub(r'<nav class="toc">.*?</nav>\s*', "", body, count=1, flags=re.S)
    body = re.sub(r'<section class="terms">.*?</section>\s*', "", body, flags=re.S)
    body = re.sub(r"<footer>.*?</footer>\s*", "", body, flags=re.S)
    script_m = re.search(r"(<script>[\s\S]*?</script>)\s*</body>", zh_html)
    script = script_m.group(1) if script_m else ""
    return body.strip(), script


def build_toc(body: str) -> str:
    items = []
    for m in re.finditer(r"<h2([^>]*)>(.*?)</h2>", body, re.S):
        attrs, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        idm = re.search(r'id="([^"]+)"', attrs)
        hid = idm.group(1) if idm else None
        if hid:
            items.append(f'<li><a href="#{html_lib.escape(hid)}">{html_lib.escape(title)}</a></li>')
        else:
            items.append(f"<li>{html_lib.escape(title)}</li>")
    if not items:
        return ""
    return (
        '<nav class="toc"><div class="mono">本篇目录</div><ol>\n'
        + "".join(items)
        + "</ol></nav>\n"
    )


def rewrite_images(body: str, slug: str, pkg: Path) -> str:
    src_dir = pkg / "images"
    dest = FIGURES_DIR / slug
    if src_dir.exists():
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        for f in src_dir.iterdir():
            if f.is_file():
                shutil.copy2(f, dest / f.name)
        body = body.replace('src="images/', f'src="../figures/{slug}/')
        body = body.replace('href="images/', f'href="../figures/{slug}/')
        body = body.replace('data-poster="images/', f'data-poster="../figures/{slug}/')
        body = body.replace("src='images/", f"src='../figures/{slug}/")
    return body


def video_styles() -> str:
    return (
        "<style>"
        ".video-card{margin:1.8em 0}"
        ".video-frame{position:relative;display:block;width:100%;aspect-ratio:16/9;"
        "overflow:hidden;border:1px solid var(--rule);background:#CFCFCF;cursor:pointer}"
        ".video-frame img,.video-frame iframe,.video-frame video{position:absolute;inset:0;"
        "width:100%;height:100%;object-fit:cover;border:0;display:block}"
        ".video-play{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);"
        "width:56px;height:56px;border-radius:50%;background:#7A1E2B;color:#fff;"
        "display:flex;align-items:center;justify-content:center;font-size:22px}"
        ".video-card figcaption{margin-top:10px;font-size:14px;opacity:.8}"
        ".video-index{margin:2em 0;padding:16px 18px;border:1px solid var(--rule)}"
        "article.body figure img{width:100%;height:auto;display:block}"
        "article.body figcaption{margin-top:8px;font-size:14px;opacity:.75}"
        "</style>"
    )


def render_page(entry: dict, index: int, body: str, script: str) -> str:
    slug = entry["slug"]
    title_zh = entry["title_zh"]
    title_en = entry.get("title_en") or ""
    author = entry.get("author") or ""
    author_role = entry.get("author_role") or ""
    source = entry["source"]
    date = entry.get("date") or ""
    date_note = entry.get("date_note") or ""
    cover = entry.get("cover") or f"covers/{slug}.svg"
    tint = entry.get("tint") or "#E6E6E6"
    date_disp = date + (f"（{date_note}）" if date_note else "")
    tags = tags_line(entry)
    no = f"{index:02d}"
    host = host_label(source)
    toc = build_toc(body)
    meta_role = (
        f"<dt>署名</dt><dd>{html_lib.escape(author_role)}</dd>" if author_role else ""
    )
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>{html_lib.escape(title_zh)} · 读本</title><link rel="stylesheet" href="../assets/style.css">{video_styles()}</head><body class="article" style="--tint:{html_lib.escape(tint)}">
<section class="opening"><div class="t"><a class="mono" href="../index.html">← 读本 · 目录</a><div><div class="mono">No. {no} · {html_lib.escape(tags)}</div><h1>{html_lib.escape(title_zh)}</h1><div class="en">{html_lib.escape(title_en)}</div></div>
<dl class="meta mono"><dt>作者</dt><dd>{html_lib.escape(author)}</dd>{meta_role}<dt>日期</dt><dd>{html_lib.escape(date_disp)}</dd><dt>原文</dt><dd><a href="{html_lib.escape(source)}">{html_lib.escape(host)} ↗</a></dd></dl><a class="readorig" href="{html_lib.escape(source)}" target="_blank" rel="noopener">阅读原文 →</a></div>
<figure class="cover"><img src="../{html_lib.escape(cover)}" alt="{html_lib.escape(title_en)} 封面"></figure></section>
<article class="body">
{NOTICE}
{toc}
{body}
<p style="margin-top:3em"><a class="readorig" href="{html_lib.escape(source)}" target="_blank" rel="noopener">阅读原文 →</a></p>
</article>
<footer class="mono">原文 © {html_lib.escape(author or host)} · 本页为自动生成的中文译文，仅供学习参考</footer>
{script}
</body></html>
"""


def start_job(url: str) -> dict:
    return api(
        "POST",
        "/jobs",
        {"url": url, "downloadImages": True, "withOriginal": True},
    )


def wait_job(job_id: str) -> dict:
    started = time.time()
    while True:
        data = api("GET", f"/jobs/{urllib.request.quote(job_id, safe='')}")
        job = data.get("job") or {}
        status = job.get("status")
        if status in {"done", "failed", "cancelled", "error"}:
            return job
        if time.time() - started > JOB_TIMEOUT:
            try:
                api("POST", f"/jobs/{urllib.request.quote(job_id, safe='')}/cancel", {})
            except Exception:
                pass
            raise TimeoutError(f"job {job_id} timed out after {JOB_TIMEOUT}s")
        time.sleep(POLL_SEC)


def translate_one(slug: str, url: str, st: dict) -> tuple[str, str, str]:
    """Returns (slug, status, detail)."""
    key = normalize_url(url)
    packages = discover_packages()
    if key in packages:
        return slug, "cached", packages[key]

    # reuse in-memory state
    prev = st["jobs"].get(slug)
    if prev and prev.get("package"):
        pkg_path = OUT_ROOT / prev["package"]
        if (pkg_path / "article.zh.html").exists():
            return slug, "cached", prev["package"]
    if prev and prev.get("job_id") and prev.get("status") == "running":
        try:
            job = wait_job(prev["job_id"])
            if job.get("status") == "done":
                pkg = (job.get("result") or {}).get("relativeDirectory") or ""
                st["jobs"][slug] = {"job_id": prev["job_id"], "status": "done", "package": pkg, "url": url}
                save_state(st)
                return slug, "done", pkg
        except Exception as e:
            pass

    print(f"[start] {slug}", flush=True)
    data = start_job(url)
    if "error" in data and "job" not in data:
        err = data["error"]
        msg = err.get("message") if isinstance(err, dict) else str(err)
        st["jobs"][slug] = {"status": "failed", "error": msg, "url": url}
        save_state(st)
        return slug, "failed", msg
    job = data["job"]
    job_id = job["id"]
    st["jobs"][slug] = {"job_id": job_id, "status": "running", "url": url}
    save_state(st)
    try:
        job = wait_job(job_id)
    except Exception as e:
        st["jobs"][slug] = {"job_id": job_id, "status": "failed", "error": str(e), "url": url}
        save_state(st)
        return slug, "failed", str(e)
    if job.get("status") != "done":
        err = job.get("error") or {}
        msg = err.get("message") if isinstance(err, dict) else str(err or job.get("status"))
        st["jobs"][slug] = {"job_id": job_id, "status": "failed", "error": msg, "url": url}
        save_state(st)
        return slug, "failed", msg
    pkg = (job.get("result") or {}).get("relativeDirectory") or ""
    st["jobs"][slug] = {"job_id": job_id, "status": "done", "package": pkg, "url": url}
    save_state(st)
    print(f"[done]  {slug} -> {pkg}", flush=True)
    return slug, "done", pkg


def apply_packages(articles: list[dict], packages_by_url: dict[str, str]) -> dict:
    ok, fail = [], []
    for i, entry in enumerate(articles, 1):
        slug = entry["slug"]
        key = normalize_url(entry["source"])
        pkg_name = packages_by_url.get(key) or (load_state().get("jobs", {}).get(slug) or {}).get("package")
        if not pkg_name:
            fail.append((slug, "no package"))
            continue
        pkg = OUT_ROOT / pkg_name
        zh = pkg / "article.zh.html"
        if not zh.exists():
            fail.append((slug, f"missing {zh}"))
            continue
        try:
            body, script = extract_body(zh.read_text(encoding="utf-8"))
            body = rewrite_images(body, slug, pkg)
            page = render_page(entry, i, body, script)
            (ARTICLES_DIR / f"{slug}.html").write_text(page, encoding="utf-8")
            ok.append(slug)
            print(f"[write] {slug}", flush=True)
        except Exception as e:
            fail.append((slug, str(e)))
            print(f"[fail-write] {slug}: {e}", flush=True)
    return {"ok": ok, "fail": fail}


def main() -> int:
    health = api("GET", "/health")
    if not health.get("ok"):
        print("translator API not healthy:", health, file=sys.stderr)
        return 1
    articles = json.loads(ARTICLES_JSON.read_text(encoding="utf-8"))
    skipped = []
    todo = []
    for a in articles:
        src = a.get("source") or ""
        if not src.startswith("http"):
            skipped.append(a["slug"])
        else:
            todo.append(a)

    st = load_state()
    print(f"total={len(articles)} todo={len(todo)} skipped={len(skipped)}", flush=True)

    # Phase 1: translate
    results = {"cached": [], "done": [], "failed": []}
    # Prefer already-finished packages first
    existing = discover_packages()
    pending = []
    for a in todo:
        key = normalize_url(a["source"])
        if key in existing:
            results["cached"].append(a["slug"])
            st["jobs"][a["slug"]] = {
                "status": "done",
                "package": existing[key],
                "url": a["source"],
            }
        else:
            pending.append(a)
    save_state(st)
    print(f"already packaged={len(results['cached'])} pending={len(pending)}", flush=True)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(translate_one, a["slug"], a["source"], st): a for a in pending}
        for fut in as_completed(futs):
            slug, status, detail = fut.result()
            results.setdefault(status, []).append(slug if status != "failed" else f"{slug}: {detail}")
            print(f"[{status}] {slug} {detail}", flush=True)

    # Refresh package map
    packages = discover_packages()
    # Also map from state
    for slug, info in load_state().get("jobs", {}).items():
        if info.get("package") and info.get("url"):
            packages[normalize_url(info["url"])] = info["package"]

    applied = apply_packages(articles, packages)

    summary = {
        "total": len(articles),
        "skipped_no_url": skipped,
        "translate_cached": results.get("cached", []),
        "translate_done": results.get("done", []),
        "translate_failed": results.get("failed", []),
        "write_ok": applied["ok"],
        "write_fail": applied["fail"],
        "packages": packages,
    }
    (OUT_ROOT / ".batch_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps({
        "total": summary["total"],
        "skipped": len(skipped),
        "cached": len(summary["translate_cached"]),
        "newly_done": len(summary["translate_done"]),
        "translate_failed": summary["translate_failed"],
        "write_ok": len(summary["write_ok"]),
        "write_fail": summary["write_fail"],
    }, ensure_ascii=False, indent=2), flush=True)
    return 0 if not summary["write_fail"] and not summary["translate_failed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
