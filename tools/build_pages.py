"""Build the service pages and keep the shared blocks in step.

Run from the repo root:  python tools/build_pages.py

What it does (all output is plain static HTML, committed to the repo):
  1. Writes the two service pages from tools/templates/service-page.html and
     tools/content/service-*.json.
  2. Stamps the shared FAQ block (from tools/content/faq.json) between the
     <!-- FAQ:START --> and <!-- FAQ:END --> markers in index.html and both service pages.
  3. Stamps the FAQPage JSON-LD in index.html (between <!-- FAQ-JSONLD:START/END -->).
  4. Stamps the three Acuity booking modals (tools/templates/modals.html) between the
     <!-- MODALS:START --> and <!-- MODALS:END --> markers in the same three pages.

Edit the FAQ in tools/content/faq.json only. The "Further reading" lists are slugs in the
service-*.json files; the cap of MAX_READING_POSTS is enforced here.
"""
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://therapywithroy.co.uk"
MAX_READING_POSTS = 4
SERVICE_CONTENT = ["service-couples.json", "service-anxiety.json"]


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(os.path.join(ROOT, path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load_json(path):
    return json.loads(read(path))


# ---------- Shared blocks ----------
def faq_section(faq):
    items = []
    for it in faq["items"]:
        items.append(
            '        <details class="faq-item">\n'
            f'          <summary><span class="faq-q">{it["q"]}</span><span class="faq-icon" aria-hidden="true">+</span></summary>\n'
            f'          <div class="faq-a"><div class="faq-a-inner"><p>{it["a"]}</p></div></div>\n'
            '        </details>'
        )
    return (
        '  <section id="faq" class="faq-section">\n'
        '    <div class="faq-inner">\n'
        f'      <h2 class="section-title">{faq["heading"]}</h2>\n'
        f'      <p class="faq-intro">{faq["intro"]}</p>\n'
        '      <div class="faq-body">\n'
        '        <div class="faq-controls">\n'
        '          <button type="button" id="faq-toggle" class="faq-toggle" hidden>Expand all</button>\n'
        '        </div>\n'
        + "\n".join(items) + "\n"
        '      </div>\n'
        '    </div>\n'
        '  </section>'
    )


def faq_jsonld(faq):
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": html.unescape(it["q"]),
             "acceptedAnswer": {"@type": "Answer", "text": html.unescape(it["a"])}}
            for it in faq["items"]
        ],
    }
    return '  <script type="application/ld+json">\n' + json.dumps(data, indent=2) + "\n  </script>"


def stamp(text, name, block, path):
    pat = re.compile(r"(<!-- " + name + r":START[^\n]*-->\n).*?(<!-- " + name + r":END -->)", re.S)
    if not pat.search(text):
        sys.exit(f"{path}: markers for {name} not found")
    return pat.sub(lambda m: m.group(1) + block + "\n" + m.group(2), text, count=1)


# ---------- Blog cards (read from blog/index.html) ----------
def blog_cards():
    t = read("blog/index.html")
    cards = {}
    for m in re.finditer(r'<a href="([^"]+)\.html" class="blog-card">(.*?)</a>', t, re.S):
        slug, body = m.group(1), m.group(2)
        img = re.search(r'<img src="([^"]+)" alt="([^"]*)"[^>]*class="blog-card-img"(?:\s+style="([^"]*)")?', body)
        cat = re.search(r'class="blog-card-cat">(.*?)</p>', body, re.S)
        title = re.search(r'class="blog-card-title">(.*?)</h2>', body, re.S)
        if not (img and cat and title):
            continue
        pos = re.search(r"object-position:\s*([^;]+)", img.group(3) or "")
        cards[slug] = {
            "alt": img.group(2),
            "position": pos.group(1).strip() if pos else None,
            "cat": cat.group(1).strip(),
            "title": title.group(1).strip(),
        }
    return cards


def reading_cards(cfg, cards):
    slugs = cfg["slugs"]
    if len(slugs) > MAX_READING_POSTS:
        sys.exit(f"Further reading is capped at {MAX_READING_POSTS} posts, got {len(slugs)}")
    if cfg["featured"] != slugs[0]:
        sys.exit("The featured post must be first in the reading list")
    out = []
    for slug in slugs:
        c = cards.get(slug)
        if not c:
            sys.exit(f"Blog post not found on blog/index.html: {slug}")
        href = f"/blog/{slug}"
        body = (
            '<span class="read-card-body">'
            f'<span class="read-cat">{c["cat"]}</span>'
            f'<span class="read-title">{c["title"]}</span>'
            '<span class="read-more">Read the article &rarr;</span></span>'
        )
        if slug == cfg["featured"]:
            fi = cfg["featured_image"]
            style = f' style="object-position: {c["position"]};"' if c["position"] else ""
            img = (f'<img src="{fi["src"]}" alt="{c["alt"]}" width="{fi["width"]}" height="{fi["height"]}" '
                   f'loading="lazy"{style} />')
            out.append(f'        <a class="read-card has-image" href="{href}">{img}{body}</a>')
        else:
            out.append(f'        <a class="read-card" href="{href}">{body}</a>')
    return "\n".join(out)


# ---------- Fee cards (wording copied from the home page #services) ----------
FEES = [
    ("free", "Initial Consultation", "Free", "15&ndash;30 minutes &bull; Online via Google Meet",
     ["No obligation or commitment", "Discuss what&rsquo;s brought you here", "Ask questions about how I work",
      "Decide together if we&rsquo;re a good fit"]),
    ("individual", "Individual Therapy", "&pound;80", "50 minutes &bull; Online via Google Meet",
     ["Weekly or fortnightly sessions", "Tailored integrative approach", "Confidential &amp; non-judgemental",
      "Available Mon&ndash;Fri, 9am&ndash;7pm London time"]),
    ("couples", "Couples Therapy", "&pound;120", "50 minutes &bull; Online via Google Meet",
     ["For partners facing difficulties", "Communication &amp; conflict support", "Integrative, tailored approach",
      "Available Mon&ndash;Fri, 9am&ndash;7pm London time"]),
]


def fee_cards(featured):
    out = []
    for key, name, price, duration, feats in FEES:
        cls = "service-card featured" if key == featured else "service-card"
        lis = "\n".join(f"            <li>{f}</li>" for f in feats)
        out.append(
            f'        <div class="{cls}">\n'
            f'          <h3 class="service-name">{name}</h3>\n'
            f'          <p class="service-price">{price}</p>\n'
            f'          <p class="service-duration">{duration}</p>\n'
            f'          <ul class="service-features">\n{lis}\n          </ul>\n'
            f'          <button class="btn-book" data-modal="{key}">Book Now</button>\n'
            '        </div>'
        )
    return "\n".join(out)


# ---------- Service pages ----------
def build_service_page(cfg, template, favicon, cards, faq, modals):
    esc = lambda s: html.escape(s, quote=True)
    url = f'{SITE}/{cfg["slug"]}'
    crumb_plain = html.unescape(cfg["crumb"])
    breadcrumb = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": crumb_plain, "item": url},
        ],
    }, indent=2)

    h = cfg["hero"]
    p = cfg["problem"]
    book = cfg["book"]
    values = {
        "title": esc(cfg["title"]),
        "description": esc(cfg["description"]),
        "url": url,
        "og_image": SITE + "/roy%20pic.jpg",
        "favicon": favicon,
        "breadcrumb_jsonld": breadcrumb,
        "couples_current": ' aria-current="page"' if cfg["slug"] == "online-couples-therapy" else "",
        "anxiety_current": ' aria-current="page"' if cfg["slug"] == "online-anxiety-depression-therapy" else "",
        "crumb": cfg["crumb"],
        "hero_eyebrow": h["eyebrow"],
        "hero_h1": h["h1"],
        "hero_subtitle": h["subtitle"],
        "hero_badges": "\n".join(f'        <span class="hero-badge">{b}</span>' for b in h["badges"]),
        "problem_id": p["id"],
        "problem_label": p["label"],
        "problem_title": p["title"],
        "problem_paragraphs": "\n".join(f"          <p>{x}</p>" for x in p["paragraphs"]),
        "problem_tags": "\n".join(f'            <span class="approach-tag">{x}</span>' for x in p["tags"]),
        "problem_quote": p["quote"],
        "steps": "\n".join(
            f'        <div class="step">\n          <div class="step-number">0{i}</div>\n'
            f'          <h3>{s["title"]}</h3>\n          <p>{s["text"]}</p>\n        </div>'
            for i, s in enumerate(cfg["steps"], 1)),
        "approach_title": cfg["approach"]["title"],
        "approach_paragraphs": "\n".join(f"          <p>{x}</p>" for x in cfg["approach"]["paragraphs"]),
        "fee_cards": fee_cards(cfg["featured_fee"]),
        "reading_cards": reading_cards(cfg["reading"], cards),
        "book_title": book["title"],
        "book_price": book["price_value"],
        "book_price_label": book["price_label"],
        "also_href": book["also_href"],
        "also_label": book["also_label"],
        "book_support_note": (
            '        <p class="support-note">If you are in immediate distress, please contact the '
            '<a href="https://www.samaritans.org">Samaritans on 116 123</a>.</p>'
            if book["samaritans"] else ""),
    }
    page = template
    for k, v in values.items():
        page = page.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{\w+\}\}", page)
    if left:
        sys.exit(f"Unfilled placeholders in {cfg['slug']}: {left}")
    page = stamp(page, "FAQ", faq_section(faq), cfg["slug"])
    page = stamp(page, "MODALS", modals.rstrip("\n"), cfg["slug"])
    return page


def main():
    faq = load_json("tools/content/faq.json")
    modals = read("tools/templates/modals.html")
    template = read("tools/templates/service-page.html")
    index = read("index.html")
    favicon_lines = re.findall(r'^\s*<link rel="(?:icon|shortcut icon)"[^\n]*$', index, re.M)
    if len(favicon_lines) != 2:
        sys.exit("Could not find the two favicon links in index.html")
    favicon = "\n".join(favicon_lines)
    cards = blog_cards()

    for name in SERVICE_CONTENT:
        cfg = load_json("tools/content/" + name)
        write(cfg["slug"] + ".html", build_service_page(cfg, template, favicon, cards, faq, modals))
        print("wrote", cfg["slug"] + ".html")

    new_index = stamp(index, "FAQ", faq_section(faq), "index.html")
    new_index = stamp(new_index, "FAQ-JSONLD", faq_jsonld(faq), "index.html")
    new_index = stamp(new_index, "MODALS", modals.rstrip("\n"), "index.html")
    if new_index != index:
        write("index.html", new_index)
        print("updated index.html (FAQ, FAQ JSON-LD, modals)")
    else:
        print("index.html already up to date")


if __name__ == "__main__":
    main()
