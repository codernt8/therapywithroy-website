import re, glob, os, json
from urllib.parse import quote

SITE = "https://therapywithroy.co.uk"

# ---------- 1. FAQPage schema + canonical + OG/Twitter tags on the homepage ----------
faqs = [
    ("How does online therapy work?",
     "Sessions take place via Google Meet, a free, easy-to-use video platform. You'll receive a link before each session. All you need is a private space, a stable internet connection, and a device with a camera and microphone. Many clients find online therapy just as effective as in-person, with the added benefit of attending from the comfort of their own home."),
    ("What happens in the free consultation?",
     "The free consultation is an informal, no-obligation conversation lasting 15–30 minutes. We'll talk about what's brought you here, what you're hoping to get from therapy, and I'll answer any questions you have about how I work. It's also a chance for you to get a feel for whether we're the right fit. There's no pressure to proceed."),
    ("How many sessions will I need?",
     "Every person is different, and there's no fixed number of sessions. Some people find that a focused course of 6–12 sessions is enough to address a specific issue; others prefer longer-term support. We'll review how things are going together and you're free to end or pause at any time. There's no minimum commitment."),
    ("Is everything I share confidential?",
     "Yes. Everything you share is treated with the strictest confidence. The only exceptions are rare situations where there is a serious risk of harm to yourself or others. In those cases, I have a professional duty to act. I'll explain the full bounds of confidentiality before we begin working together."),
    ("What is your cancellation policy?",
     "Payment is taken at the time of booking. If you need to reschedule or cancel, please give at least 48 hours’ notice and you'll receive a full refund. Cancellations made within 48 hours of your appointment are non-refundable. This policy reflects the value of the time we've set aside together."),
    ("Do you work with clients outside the UK?",
     "Yes, I work with clients across the UK and internationally. Sessions are conducted entirely online, so location is no barrier. All fees are charged in GBP. All sessions run Monday to Friday, 9am–7pm GMT, so please factor this in when booking from a different time zone."),
    ("Are you a registered therapist?",
     "Yes. I am a registered member of the British Association for Counselling and Psychotherapy (BACP), membership number 397064. I hold a Master of Social Sciences in Counselling from the University of Hong Kong (2017) and practise in accordance with the BACP Ethical Framework for the Counselling Professions."),
]
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
    desc = get(r'<meta name="description" content="(.*?)">', t, "")
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