import re, glob, os, json
from urllib.parse import quote

SITE = "https://therapywithroy.co.uk"

# ---------- 1. FAQPage schema + canonical + OG/Twitter tags on the homepage ----------
# The FAQ lives in tools/content/faq.json (also used by tools/build_pages.py), so the wording is kept in one place.
import html
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "faq.json"), encoding="utf-8") as f:
    _faq = json.load(f)
faqs = [(html.unescape(i["q"]), html.unescape(i["a"])) for i in _faq["items"]]
faq_schema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
        for q, a in faqs
    ],
}

with open("index.html", encoding="utf-8") as f:
    t = f.read()
orig = t

if 'rel="canonical"' not in t:
    t = t.replace(
        '<meta name="description" content="Online therapy with Roy Lam, MBACP: anxiety, depression, relationships, identity and life transitions. UK-based, available worldwide. Free consultation.">',
        '<meta name="description" content="Online therapy with Roy Lam, MBACP: anxiety, depression, relationships, identity and life transitions. UK-based, available worldwide. Free consultation.">\n'
        '  <link rel="canonical" href="' + SITE + '/" />\n'
        '  <meta property="og:type" content="website" />\n'
        '  <meta property="og:site_name" content="Therapy with Roy" />\n'
        '  <meta property="og:title" content="Online Therapy UK | Therapy with Roy | Roy Lam MBACP" />\n'
        '  <meta property="og:description" content="Online therapy with Roy Lam, MBACP registered counsellor. Support for anxiety, depression, relationships, identity and life transitions. UK-based, available worldwide. Book a free consultation." />\n'
        '  <meta property="og:url" content="' + SITE + '/" />\n'
        '  <meta property="og:image" content="' + SITE + '/roy-lam-online-therapist.jpg" />\n'
        '  <meta name="twitter:card" content="summary_large_image" />\n'
        '  <meta name="twitter:title" content="Online Therapy UK | Therapy with Roy | Roy Lam MBACP" />\n'
        '  <meta name="twitter:description" content="Online therapy with Roy Lam, MBACP registered counsellor. Support for anxiety, depression, relationships, identity and life transitions. UK-based, available worldwide." />\n'
        '  <meta name="twitter:image" content="' + SITE + '/roy-lam-online-therapist.jpg" />'
    )

if '"@type": "FAQPage"' not in t:
    marker = '  }\n  </script>'
    idx = t.find(marker)
    if idx != -1:
        insertion_point = idx + len(marker)
        faq_block = '\n  <script type="application/ld+json">\n' + json.dumps(faq_schema, indent=2) + '\n  </script>'
        t = t[:insertion_point] + faq_block + t[insertion_point:]
    else:
        print("WARNING: could not find insertion point for FAQ schema in index.html")

if t != orig:
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(t)
    print("updated: index.html (canonical, OG/Twitter tags, FAQPage schema)")
else:
    print("index.html: no changes made (already up to date?)")

# ---------- 2. OG/Twitter tags on blog index + every blog post ----------
def get(pattern, text, default=None):
    m = re.search(pattern, text, re.S)
    return m.group(1) if m else default

def add_og_tags(path, is_index=False):
    with open(path, encoding="utf-8") as f:
        t = f.read()
    orig = t
    if 'property="og:title"' in t:
        return False

    title = get(r'<title>(.*?)</title>', t, "Therapy with Roy")
    title = title.replace('"', "&quot;")
    desc = get(r'<meta name="description" content="(.*?)">', t, "")
    desc = desc.replace('"', "&quot;")
    canonical = get(r'<link rel="canonical" href="(.*?)"\s*/>', t) or (SITE + "/blog/")

    if is_index:
        image = SITE + "/roy-lam-online-therapist.jpg"
        og_type = "website"
    else:
        hero_src = get(r'<img src="([^"]*\.webp)"[^>]*class="blog-hero-img"', t)
        image = SITE + "/blog/" + quote(hero_src) if hero_src else SITE + "/roy-lam-online-therapist.jpg"
        og_type = "article"

    og_block = (
        f'\n  <meta property="og:type" content="{og_type}" />\n'
        f'  <meta property="og:site_name" content="Therapy with Roy" />\n'
        f'  <meta property="og:title" content="{title}" />\n'
        f'  <meta property="og:description" content="{desc}" />\n'
        f'  <meta property="og:url" content="{canonical}" />\n'
        f'  <meta property="og:image" content="{image}" />\n'
        f'  <meta name="twitter:card" content="summary_large_image" />\n'
        f'  <meta name="twitter:title" content="{title}" />\n'
        f'  <meta name="twitter:description" content="{desc}" />\n'
        f'  <meta name="twitter:image" content="{image}" />'
    )

    if 'rel="canonical"' in t:
        t = re.sub(r'(<link rel="canonical" href="[^"]*"\s*/>)', r'\1' + og_block, t, count=1)
    else:
        t = re.sub(r'(<meta name="description" content="[^"]*">)', r'\1' + og_block, t, count=1)

    if t != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(t)
        return True
    return False

changed = []
if add_og_tags("blog/index.html", is_index=True):
    changed.append("blog/index.html")
for path in glob.glob("blog/*.html"):
    if os.path.basename(path) == "index.html":
        continue
    if add_og_tags(path, is_index=False):
        changed.append(path)
print(f"Updated {len(changed)} blog files:")
for c in changed:
    print(" -", c)

# ---------- 2b. Post schema (BlogPosting upgrade, BreadcrumbList) and blog index schema ----------
from urllib.parse import unquote

ROY_ID = SITE + "/#roy"
LD_RE = re.compile(r'(  <script type="application/ld\+json">\n)(.*?)(\n  </script>\n)', re.S)


def post_info(path):
    """Everything the schema needs from a post, read from the post itself."""
    with open(path, encoding="utf-8") as f:
        t = f.read()
    canonical = get(r'<link rel="canonical" href="([^"]*)"\s*/>', t)
    hero = get(r'<img src="([^"]*)"[^>]*class="blog-hero-img"', t)
    image = SITE + "/blog/" + quote(unquote(hero)) if hero else SITE + "/roy-lam-online-therapist.jpg"
    bp = None
    for m in LD_RE.finditer(t):
        try:
            d = json.loads(m.group(2))
        except Exception:
            continue
        if d.get("@type") == "BlogPosting":
            bp = d
            break
    return t, canonical, image, bp


def add_post_schema(path):
    t, canonical, image, bp = post_info(path)
    if not bp or not canonical:
        return False
    orig = t
    published = bp.get("datePublished")

    # BlogPosting: the fields Google and AI search look for
    bp.setdefault("dateModified", published)
    bp.setdefault("image", [image])
    bp.setdefault("mainEntityOfPage", {"@type": "WebPage", "@id": canonical})
    bp.setdefault("inLanguage", "en-GB")
    if isinstance(bp.get("author"), dict):
        bp["author"].setdefault("@id", ROY_ID)
    ordered = {k: bp[k] for k in ["@context", "@type", "headline", "description", "image", "author", "publisher",
                                  "datePublished", "dateModified", "mainEntityOfPage", "url", "inLanguage", "keywords"] if k in bp}
    ordered.update({k: v for k, v in bp.items() if k not in ordered})
    block = "  <script type=\"application/ld+json\">\n" + json.dumps(ordered, indent=2, ensure_ascii=False) + "\n  </script>\n"

    m = None
    for cand in LD_RE.finditer(t):
        try:
            if json.loads(cand.group(2)).get("@type") == "BlogPosting":
                m = cand
                break
        except Exception:
            pass
    t = t[:m.start()] + block + t[m.end():]

    # BreadcrumbList (the breadcrumb already shows on the page)
    if '"@type": "BreadcrumbList"' not in t:
        crumbs = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
                {"@type": "ListItem", "position": 3, "name": bp["headline"], "item": canonical},
            ],
        }
        crumb_block = "  <script type=\"application/ld+json\">\n" + json.dumps(crumbs, indent=2, ensure_ascii=False) + "\n  </script>\n"
        end = t.index(block) + len(block)
        t = t[:end] + crumb_block + t[end:]

    # Open Graph article times
    if 'property="article:published_time"' not in t and published:
        og_image = re.search(r'  <meta property="og:image" content="[^"]*" />\n', t)
        if og_image:
            extra = (f'  <meta property="article:published_time" content="{published}" />\n'
                     f'  <meta property="article:modified_time" content="{bp["dateModified"]}" />\n'
                     f'  <meta property="article:author" content="https://www.linkedin.com/in/roykylam" />\n')
            t = t[:og_image.end()] + extra + t[og_image.end():]

    if t != orig:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(t)
        return True
    return False


def blog_index_schema():
    posts = []
    for path in glob.glob("blog/*.html"):
        if os.path.basename(path) == "index.html":
            continue
        t, canonical, image, bp = post_info(path)
        if bp and canonical:
            posts.append({"@type": "BlogPosting", "@id": canonical + "#post", "headline": bp["headline"], "url": canonical,
                          "datePublished": bp.get("datePublished"), "image": image,
                          "author": {"@type": "Person", "@id": ROY_ID, "name": "Roy Lam"}})
    posts.sort(key=lambda p: p["datePublished"] or "", reverse=True)
    with open("blog/index.html", encoding="utf-8") as f:
        bt = f.read()
    desc = get(r'<meta name="description" content="(.*?)">', bt, "")
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Blog", "@id": SITE + "/blog/#blog", "name": "Therapy with Roy Blog", "description": desc,
             "url": SITE + "/blog/", "inLanguage": "en-GB",
             "publisher": {"@type": "Organization", "name": "Therapy with Roy", "url": SITE},
             "author": {"@type": "Person", "@id": ROY_ID, "name": "Roy Lam", "url": SITE},
             "blogPost": posts},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"}]},
        ],
    }
    block = "  <script type=\"application/ld+json\">\n" + json.dumps(graph, indent=2, ensure_ascii=False) + "\n  </script>\n"
    existing = LD_RE.search(bt)
    if existing and '"@type": "Blog"' in existing.group(2):
        new = bt[:existing.start()] + block + bt[existing.end():]
    elif "</head>" in bt:
        new = bt.replace("</head>", block + "</head>", 1)
    else:
        return False
    if new != bt:
        with open("blog/index.html", "w", encoding="utf-8", newline="") as f:
            f.write(new)
        return True
    return False


schema_changed = [p for p in sorted(glob.glob("blog/*.html")) if os.path.basename(p) != "index.html" and add_post_schema(p)]
print(f"Post schema updated on {len(schema_changed)} posts")
print("Blog index schema updated" if blog_index_schema() else "Blog index schema already up to date")

# ---------- 3. robots.txt + sitemap.xml ----------

def file_lastmod(path):
    """Date a page last changed: today if it has uncommitted edits, otherwise its last commit date."""
    import datetime
    import subprocess
    dirty = subprocess.run(["git", "status", "--porcelain", "--", path], capture_output=True, text=True).stdout.strip()
    if dirty:
        return datetime.date.today().isoformat()
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", path], capture_output=True, text=True).stdout.strip()
    return out or None

urls = [(SITE + "/", file_lastmod("index.html"), "weekly", "1.0"), (SITE + "/blog/", file_lastmod("blog/index.html"), "weekly", "0.8")]
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "services.json"), encoding="utf-8") as f:
    for service in json.load(f):
        if os.path.exists(service["slug"] + ".html"):
            urls.append((SITE + "/" + service["slug"], file_lastmod(service["slug"] + ".html"), "monthly", "0.9"))
for page, prio in [("privacy-policy", "0.3"), ("client-agreement", "0.3")]:
    if os.path.exists(page + ".html"):
        urls.append((SITE + "/" + page, file_lastmod(page + ".html"), "yearly", prio))

for path in sorted(glob.glob("blog/*.html")):
    if os.path.basename(path) == "index.html":
        continue
    with open(path, encoding="utf-8") as f:
        t = f.read()
    canonical = get(r'<link rel="canonical" href="([^"]*)"\s*/>', t)
    if not canonical:
        continue
    lastmod = None
    ldjson_match = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', t, re.S)
    if ldjson_match:
        try:
            data = json.loads(ldjson_match.group(1))
            lastmod = data.get("dateModified") or data.get("datePublished")
        except Exception:
            pass
    urls.append((canonical, lastmod, "monthly", "0.6"))

lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for loc, lastmod, changefreq, priority in urls:
    lines.append('  <url>')
    lines.append(f'    <loc>{loc}</loc>')
    if lastmod:
        lines.append(f'    <lastmod>{lastmod}</lastmod>')
    lines.append(f'    <changefreq>{changefreq}</changefreq>')
    lines.append(f'    <priority>{priority}</priority>')
    lines.append('  </url>')
lines.append('</urlset>')
with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"sitemap.xml written with {len(urls)} URLs")

with open("robots.txt", "w", encoding="utf-8") as f:
    f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
print("robots.txt written")

print("\nDone.")