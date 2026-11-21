#!/usr/bin/env python3
"""
Static site builder for ALIR Cat & Dog Shelter.

    python build.py            # builds into ./dist
    python build.py --watch    # rebuilds when anything in ./src changes

Content the shelter edits lives in src/content/ (through the editor at /admin):
    settings.json      phone numbers, email, bank and PayPal details, urgent banner
    cases/*.json       rescue cases
    gallery/*.json     shelter photos
    press/*.json       news articles (one is featured)
    clippings/*.json   press clippings wall
    team/*.json        committee and caretakers

Pages live in src/pages/*.html. Each page starts with a front-matter comment:

    <!--
    title: Page title
    description: Meta description
    nav: about            (which menu item is current; optional)
    og_image: https://... (optional)
    -->

Inside a page you can use these tokens:
    {{setting:email}}                 any value from settings.json
    {{cases:banban,trinie}}           rescue case cards
    {{cases:all}}                     every case, newest first
    {{pile:banban,trinie,tigger}}     the decorative hero stack (3 cards)
    {{gallery}}                       shelter photos
    {{press:featured}}                the featured article
    {{press:cards}}                   the other articles
    {{clippings}}                     the press clippings wall
    {{team}}                          the team grid
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
CONTENT = SRC / "content"

# Set this to the live domain once you have one, e.g. "https://alirshelter.org/".
# Leave empty to omit canonical / og:url tags.
SITE_URL = ""

DEFAULT_OG = ("https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEje_fwO66EnL269U9h4x3a4wEA_3gP1z7bgT8g2gW1a5dbYrPQHGMENeymzMuZlKl3PvBfA1NVc7GertdJLKeouzufY0CfCnoFaewud6djB7ix222-MPGpKojScp-w9Ar_i58Aaz78ccFWR/s1200/FB_IMG_1623589010546.jpg")
NAV_KEYS = ("about", "rescues", "shelter", "press", "donate")

esc = lambda s: html.escape(str(s), quote=True)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def month_year(iso: str) -> str:
    return date.fromisoformat(iso).strftime("%b %Y")


def sized(url: str, size: int) -> str:
    """Blogger URLs carry their size in the path (/s1600/). Swap it for a thumbnail size.
    Other URLs (uploads) are returned unchanged."""
    return re.sub(r"/(s\d+|w\d+-h\d+)/", f"/s{size}/", url, count=1)


def load_folder(name: str) -> list[dict]:
    """Every JSON file in src/content/<name>/, keyed by its file name (without .json)."""
    items = []
    for f in sorted((CONTENT / name).glob("*.json")):
        d = json.loads(read(f))
        d["_id"] = f.stem
        items.append(d)
    return items


def load_settings() -> dict:
    s = json.loads(read(CONTENT / "settings.json"))
    # Ready-made variant the donate page needs (the copy button uses digits only)
    s["bank_account_digits"] = re.sub(r"\D", "", s.get("bank_account_number", ""))
    return s


# ---------- Components ----------

def case_card(c: dict, *, decorative: bool = False) -> str:
    img = c["img"]
    photo_url = lambda size: img.format(size=size) if "{size}" in img else img
    alt = "" if decorative else (c.get("alt") or f'{c["name"]}, {c["species"].lower()}')
    lazy = "" if decorative else 'loading="lazy" '
    photo = (
        f'<div class="case-photo"><img src="{esc(photo_url(640))}" '
        f'srcset="{esc(photo_url(480))} 480w, {esc(photo_url(800))} 800w" '
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

    link_text = "Read the appeal" if c["_id"] == "appeal" else f'Read {c["name"]}’s story'
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
    photos = load_folder("gallery")
    total = len(photos)
    out = []
    for i, p in enumerate(photos, 1):
        full = p["photo"]
        thumb = sized(full, 500)
        out.append(
            f'<button type="button" data-full="{esc(full)}" aria-label="Open photo {i} of {total}">'
            f'<img src="{esc(thumb)}" alt="Rescued animals at the ALIR shelter, photo {i} of {total}" '
            f'loading="lazy" decoding="async"></button>'
        )
    return '<div class="gallery">\n          ' + "\n          ".join(out) + "\n        </div>"


def press_meta(a: dict) -> str:
    return " · ".join(x for x in (a.get("year", ""), a.get("language", "")) if x)


def render_press_featured() -> str:
    feats = [a for a in load_folder("press") if a.get("featured")]
    if not feats:
        return ""
    a = feats[0]
    return f'''<a class="press-feature" href="{esc(a["url"])}" rel="noopener">
          <figure class="press-feature-figure">
            <img class="press-feature-img" src="{esc(a["image"])}" width="800" height="451" alt="{esc(a.get("alt", ""))}" loading="lazy" decoding="async">
            <figcaption>{esc(a.get("caption", ""))}</figcaption>
          </figure>
          <div class="press-feature-body">
            <span class="press-outlet">{esc(a["outlet"])}</span>
            <h2>{esc(a["title"])}</h2>
            <p>{esc(a["description"])}</p>
            <span class="press-more">Read the article</span>
          </div>
        </a>'''


def render_press_cards() -> str:
    items = sorted((a for a in load_folder("press") if not a.get("featured")), key=lambda a: a.get("order", 0))
    lis = []
    for a in items:
        malay = a.get("language") == "Malay"
        lang_attr = ' lang="ms"' if malay else ""
        href_lang = ' hreflang="ms"' if malay else ""
        meta = press_meta(a)
        meta_html = f'<span class="press-meta">{esc(meta)}</span>' if meta else ""
        lis.append(
            f'<li>\n            <a class="press-card" href="{esc(a["url"])}" rel="noopener"{href_lang}>\n'
            f'              <span class="press-outlet">{esc(a["outlet"])}</span>\n'
            f'              <h3{lang_attr}>{esc(a["title"])}</h3>\n'
            f'              <p>{esc(a["description"])}</p>\n'
            f'              {meta_html}\n'
            f'              <span class="press-more">Read the article</span>\n'
            f'            </a>\n          </li>'
        )
    return "\n          ".join(lis)


def render_clippings() -> str:
    clips = load_folder("clippings")
    total = len(clips)
    out = []
    for i, c in enumerate(clips, 1):
        full = c["photo"]
        out.append(
            f'<button type="button" data-full="{esc(full)}" aria-label="Open press clipping {i} of {total}">'
            f'<img src="{esc(sized(full, 640))}" alt="Press clipping {i} of {total} about ALIR" '
            f'loading="lazy" decoding="async"></button>'
        )
    return '<div class="gallery">\n          ' + "\n          ".join(out) + "\n        </div>"


def render_team() -> str:
    people = sorted(load_folder("team"), key=lambda p: p.get("order", 0))
    figs = []
    for p in people:
        cls = ' class="lead-role"' if p.get("featured") else ""
        figs.append(
            f'<figure{cls}><img src="{esc(p["photo"])}" alt="{esc(p["name"])}, {esc(p["role"])}" '
            f'loading="lazy" decoding="async">'
            f'<figcaption><strong>{esc(p["name"])}</strong><span>{esc(p["role"])}</span></figcaption></figure>'
        )
    return "\n          ".join(figs)


def org_schema(settings: dict) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "AnimalShelter",
        "name": "ALIR Cat & Dog Shelter",
        "alternateName": settings["bank_account_name"],
        "description": "Independent no-kill cat and dog shelter in Sabah, Malaysia, rescuing injured, abandoned and abused animals since 2009.",
        "foundingDate": "2009",
        "email": settings["email"],
        "telephone": "+" + settings["whatsapp_number"],
        "areaServed": "Sabah, Malaysia",
        "address": {"@type": "PostalAddress", "addressRegion": "Sabah", "addressCountry": "MY"},
        "image": DEFAULT_OG,
        "sameAs": ["https://alirsabah.blogspot.com/"],
    }
    if SITE_URL:
        data["url"] = SITE_URL
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


# ---------- Build ----------

def fill_settings(text: str, settings: dict) -> str:
    """Replace {{setting:key}} with the value from settings.json.
    Bank account number and WhatsApp display use non-breaking spaces so they don't wrap."""
    def value(key: str) -> str:
        if key not in settings:
            raise ValueError(f"unknown setting: {key}")
        v = str(settings[key])
        if key in ("bank_account_number", "whatsapp_display"):
            v = v.replace(" ", "&nbsp;")
        return v
    return re.sub(r"\{\{setting:(\w+)\}\}", lambda m: value(m.group(1)), text)


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
    settings = load_settings()
    head, header, footer = (fill_settings(read(SRC / "partials" / f), settings) for f in ("head.html", "header.html", "footer.html"))
    cases = {c["_id"]: c for c in load_folder("cases")}

    # Empty dist/ rather than deleting it, so a dev server or open folder holding it doesn't break the build.
    DIST.mkdir(exist_ok=True)
    for item in DIST.iterdir():
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    shutil.copytree(SRC / "assets", DIST / "assets")
    # The editor (Decap CMS) lives at /admin
    shutil.copytree(SRC / "admin", DIST / "admin")

    for page in sorted((SRC / "pages").glob("*.html")):
        meta, body = parse_page(fill_settings(read(page), settings))
        path = "" if page.name == "index.html" else page.name

        body = re.sub(r"\{\{cases:([^}]+)\}\}", lambda m: render_cases(m.group(1), cases), body)
        body = re.sub(r"\{\{pile:([^}]+)\}\}", lambda m: render_pile(m.group(1), cases), body)
        body = body.replace("{{gallery}}", render_gallery() if "{{gallery}}" in body else "")
        body = body.replace("{{press:featured}}", render_press_featured())
        body = body.replace("{{press:cards}}", render_press_cards())
        body = body.replace("{{clippings}}", render_clippings())
        body = body.replace("{{team}}", render_team())

        h = head
        if not SITE_URL:
            h = re.sub(r'\s*<link rel="canonical"[^>]*>', "", h)
            h = re.sub(r'\s*<meta property="og:url"[^>]*>', "", h)
        h = (h.replace("{{title}}", meta["title"])
              .replace("{{description}}", meta["description"])
              .replace("{{og_image}}", meta.get("og_image", DEFAULT_OG))
              .replace("{{site_url}}", SITE_URL)
              .replace("{{path}}", path)
              .replace("{{schema}}", org_schema(settings) if page.name == "index.html" else ""))

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
