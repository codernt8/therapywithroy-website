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
        '<meta name="description" content="Online therapy with Roy Lam, MBACP registered counsellor. Support for anxiety, depression, relationships, identity and life transitions. UK-based, available worldwide. Book a free consultation.">',
        '<meta name="description" content="Online therapy with Roy Lam, MBACP registered counsellor. Support for anxiety, depression, relationships, identity and life transitions. UK-based, available worldwide. Book a free consultation.">\n'
        '  <link rel="canonical" href="' + SITE + '/" />\n'
        '  <meta property="og:type" content="website" />\n'
        '  <meta property="og:site_name" content="Therapy with Roy" />\n'
        '  <meta property="og:title" content="Online Therapy UK | Therapy with Roy | Roy Lam MBACP" />\n'
        '  <meta property="og:description" content="Online therapy with Roy Lam, MBACP registered counsellor. Support for anxiety, depression, relationships, identity and life transitions. UK-based, available worldwide. Book a free consultation." />\n'
        '  <meta property="og:url" content="' + SITE + '/" />\n'
        '  <meta property="og:image" content="' + SITE + '/roy%20pic.jpg" />\n'
        '  <meta name="twitter:card" content="summary_large_image" />\n'
        '  <meta name="twitter:title" content="Online Therapy UK | Therapy with Roy | Roy Lam MBACP" />\n'
        '  <meta name="twitter:description" content="Online therapy with Roy Lam, MBACP registered counsellor. Support for anxiety, depression, relationships, identity and life transitions. UK-based, available worldwide." />\n'
        '  <meta name="twitter:image" content="' + SITE + '/roy%20pic.jpg" />'
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
        image = SITE + "/roy%20pic.jpg"
        og_type = "website"
    else:
        hero_src = get(r'<img src="([^"]*\.webp)"[^>]*class="blog-hero-img"', t)
        image = SITE + "/blog/" + quote(hero_src) if hero_src else SITE + "/roy%20pic.jpg"
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

# ---------- 3. robots.txt + sitemap.xml ----------
urls = [(SITE + "/", None, "weekly", "1.0"), (SITE + "/blog/", None, "weekly", "0.8")]
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "content", "services.json"), encoding="utf-8") as f:
    for service in json.load(f):
        if os.path.exists(service["slug"] + ".html"):
            urls.append((SITE + "/" + service["slug"], None, "monthly", "0.9"))
for page, prio in [("privacy-policy.html", "0.3"), ("client-agreement.html", "0.3")]:
    if os.path.exists(page):
        urls.append((SITE + "/" + page, None, "yearly", prio))

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