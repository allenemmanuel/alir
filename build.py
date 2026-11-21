#!/usr/bin/env python3
"""
Static site builder for ALIR Cat & Dog Shelter.

    python build.py            # builds into ./dist
    python build.py --watch    # rebuilds when anything in ./src changes

Pages live in src/pages/*.html. Each page starts with a front-matter comment:

    <!--
    title: Page title
    description: Meta description
    nav: about            (which menu item is current; optional)
    og_image: https://... (optional)
    -->

Inside a page you can use these tokens:
    {{cases:banban,trinie}}   rescue case cards from src/data/cases.json
    {{cases:all}}             every case, newest first
    {{pile:banban,trinie,tigger}}  the decorative hero stack (3 cards)
    {{gallery}}               shelter photos from src/data/gallery.txt
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DIST = ROOT / "dist"

# Set this to the live domain once you have one, e.g. "https://alirshelter.org/".
# Leave empty to omit canonical / og:url tags.
SITE_URL = ""

DEFAULT_OG = ("https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEje_fwO66EnL269U9h4x3a4wEA_3gP1z7bgT8g2gW1a5dbYrPQHGMENeymzMuZlKl3PvBfA1NVc7GertdJLKeouzufY0CfCnoFaewud6djB7ix222-MPGpKojScp-w9Ar_i58Aaz78ccFWR/s1200/FB_IMG_1623589010546.jpg")
BLOGGER_IMG = "https://blogger.googleusercontent.com/img/b/R29vZ2xl/"
NAV_KEYS = ("about", "rescues", "shelter", "press", "donate")

esc = lambda s: html.escape(str(s), quote=True)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def month_year(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%b %Y")


# ---------- Components ----------

def case_card(c: dict, *, decorative: bool = False) -> str:
    img = c["img"]
    alt = "" if decorative else (c.get("alt") or f'{c["name"]}, {c["species"].lower()}')
    lazy = "" if decorative else 'loading="lazy" '
    photo = (
        f'<div class="case-photo"><img src="{esc(img.format(size=640))}" '
        f'srcset="{esc(img.format(size=480))} 480w, {esc(img.format(size=800))} 800w" '
        f'sizes="(max-width: 640px) 92vw, (max-width: 980px) 46vw, 380px" '
        f'width="640" height="480" alt="{esc(alt)}" '
        f'{lazy}decoding="async">'
        f'<span class="id-tag">{esc(c["species"])}</span></div>'
    )
    status = f'<span class="status status-{esc(c["status"])}">{esc(c["status_label"])}</span>'

    if decorative:
        return (
            f'<div class="case-card">{photo}<div class="case-body">'
            f'<div class="case-head"><p class="case-name">{esc(c["name"])}</p>{status}</div>'
            f'<dl><dt>Found</dt><dd>{esc(c["found"])}</dd><dt>Vet bill</dt><dd>{esc(c["bill"])}</dd></dl>'
            f'</div></div>'
        )

    link_text = "Read the appeal" if c["id"] == "appeal" else f'Read {c["name"]}\u2019s story'
    return f'''<a class="case-card" href="{esc(c["url"])}" rel="noopener">
            {photo}
            <div class="case-body">
              <div class="case-head"><h3>{esc(c["name"])}</h3>{status}</div>
              <dl>
                <dt>Found</dt><dd>{esc(c["found"])}</dd>
                <dt>Condition</dt><dd>{esc(c["condition"])}</dd>
                <dt>Vet bill</dt><dd>{esc(c["bill"])}</dd>
                <dt>Date</dt><dd><time datetime="{esc(c["date"])}">{month_year(c["date"])}</time></dd>
              </dl>
              <p class="case-text">{esc(c["text"])}</p>
              <span class="case-link">{esc(link_text)}</span>
            </div>
          </a>'''


def render_cases(ids: str, cases: dict[str, dict]) -> str:
    if ids.strip() == "all":
        chosen = sorted(cases.values(), key=lambda c: c["date"], reverse=True)
    else:
        chosen = [cases[i.strip()] for i in ids.split(",")]
    cards = "\n          ".join(case_card(c) for c in chosen)
    return f'<div class="case-grid">\n          {cards}\n        </div>'


def render_pile(ids: str, cases: dict[str, dict]) -> str:
    cards = "".join(case_card(cases[i.strip()], decorative=True) for i in ids.split(","))
    return f'<div class="pile" aria-hidden="true">{cards}</div>'


def render_gallery() -> str:
    lines = [l.strip() for l in read(SRC / "data" / "gallery.txt").splitlines() if l.strip()]
    total = len(lines)
    out = []
    for i, line in enumerate(lines, 1):
        name, key = line.split("|")
        thumb = f"{BLOGGER_IMG}{key}/s500/{name}"
        full = f"{BLOGGER_IMG}{key}/s1600/{name}"
        out.append(
            f'<button type="button" data-full="{esc(full)}" aria-label="Open photo {i} of {total}">'
            f'<img src="{esc(thumb)}" alt="Rescued animals at the ALIR shelter, photo {i} of {total}" '
            f'loading="lazy" decoding="async"></button>'
        )
    return '<div class="gallery">\n          ' + "\n          ".join(out) + "\n        </div>"


def org_schema() -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "AnimalShelter",
        "name": "ALIR Cat & Dog Shelter",
        "alternateName": "Pertubuhan Pencinta dan Penyelamat Haiwan Sabah",
        "description": "Independent no-kill cat and dog shelter in Sabah, Malaysia, rescuing injured, abandoned and abused animals since 2009.",
        "foundingDate": "2009",
        "email": "alir.sabah@gmail.com",
        "telephone": "+60168420421",
        "areaServed": "Sabah, Malaysia",
        "address": {"@type": "PostalAddress", "addressRegion": "Sabah", "addressCountry": "MY"},
        "image": DEFAULT_OG,
        "sameAs": ["https://alirsabah.blogspot.com/"],
    }
    if SITE_URL:
        data["url"] = SITE_URL
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


# ---------- Build ----------

def parse_page(text: str) -> tuple[dict, str]:
    m = re.match(r"\s*<!--(.*?)-->\s*", text, re.S)
    if not m:
        raise ValueError("page is missing its front-matter comment")
    meta = {}
    for line in m.group(1).strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def build() -> None:
    head, header, footer = (read(SRC / "partials" / f) for f in ("head.html", "header.html", "footer.html"))
    cases = {c["id"]: c for c in json.loads(read(SRC / "data" / "cases.json"))}

    # Empty dist/ rather than deleting it, so a dev server or open folder holding it doesn't break the build.
    DIST.mkdir(exist_ok=True)
    for item in DIST.iterdir():
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    shutil.copytree(SRC / "assets", DIST / "assets")

    for page in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse_page(read(page))
        path = "" if page.name == "index.html" else page.name

        body = re.sub(r"\{\{cases:([^}]+)\}\}", lambda m: render_cases(m.group(1), cases), body)
        body = re.sub(r"\{\{pile:([^}]+)\}\}", lambda m: render_pile(m.group(1), cases), body)
        body = body.replace("{{gallery}}", render_gallery() if "{{gallery}}" in body else "")

        h = head
        if not SITE_URL:
            h = re.sub(r'\s*<link rel="canonical"[^>]*>', "", h)
            h = re.sub(r'\s*<meta property="og:url"[^>]*>', "", h)
        h = (h.replace("{{title}}", meta["title"])
              .replace("{{description}}", meta["description"])
              .replace("{{og_image}}", meta.get("og_image", DEFAULT_OG))
              .replace("{{site_url}}", SITE_URL)
              .replace("{{path}}", path)
              .replace("{{schema}}", org_schema() if page.name == "index.html" else ""))

        hd = header
        for key in NAV_KEYS:
            hd = hd.replace(f"{{{{cur:{key}}}}}", ' aria-current="page"' if meta.get("nav") == key else "")

        out = h + hd + body.rstrip() + "\n" + footer
        leftover = re.findall(r"\{\{[^}]+\}\}", out)
        if leftover:
            raise ValueError(f"{page.name}: unresolved tokens {leftover}")
        (DIST / page.name).write_text(out, encoding="utf-8")
        print(f"  built {page.name}")


def watch() -> None:
    def snapshot():
        return {p: p.stat().st_mtime for p in SRC.rglob("*") if p.is_file()}
    last = snapshot()
    print("Watching src/ for changes (Ctrl+C to stop)")
    while True:
        time.sleep(0.5)
        now = snapshot()
        if now != last:
            last = now
            try:
                build()
            except Exception as e:  # keep watching after a typo
                print(f"  build failed: {e}")


if __name__ == "__main__":
    build()
    print(f"Done: {DIST}")
    if "--watch" in sys.argv:
        watch()
