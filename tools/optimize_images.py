import os, re, glob
from urllib.parse import unquote
from PIL import Image

# ---- 1. Resize + convert to WebP ----
targets = [
    ("BACP Logo - 397064.png", 400, 85, "BACP Logo - 397064.webp"),
    ("micke-lindstrom-I3GuNBeDerI-unsplash.jpg", 1920, 78, "micke-lindstrom-I3GuNBeDerI-unsplash.webp"),
]
blog_images_raw = [
    "images/Couple%20on%20Sofa.png","images/Male.png","images/attachment-styles-and-relationships-main.png",
    "images/burnout-group.png","images/family-estrangement-and-mental-health-alt1.png","images/grief-lgbtq-community.png",
    "images/lgbtq-mental-health-alt1.png","images/men-asking-for-help.png","images/moving-abroad-expat-mental-health-alt2.png",
    "images/nhs-mental-health-funding-what-it-means-for-you-alt1.png","images/perfectionism-and-anxiety-main.png",
    "images/social-anxiety-what-it-really-is-and-how-therapy-helps-main.png","images/trauma-and-the-body-alt1.png",
    "images/uk-mental-health-act-what-it-means-for-you-main.png","images/why-sleep-and-mental-health-are-connected-alt1.png",
    "images/why-talking-to-friends-isnt-enough.png","images/why-you-cant-stop-doomscrolling.png","images/will-ai-take-my-job.png",
    "images/you-are-not-lazy-you-are-depleted.png",
]
for enc in blog_images_raw:
    real = "blog/" + unquote(enc)
    webp = real.rsplit(".", 1)[0] + ".webp"
    targets.append((real, 1400, 78, webp))

results = []
for src, maxw, quality, dest in targets:
    if not os.path.exists(src):
        results.append((src, None, None, "MISSING")); continue
    orig_size = os.path.getsize(src)
    im = Image.open(src)
    if im.mode in ("P", "CMYK"):
        im = im.convert("RGB")
    w, h = im.size
    if w > maxw:
        im = im.resize((maxw, int(h * (maxw / w))), Image.LANCZOS)
    im = im.convert("RGB")
    im.save(dest, "WEBP", quality=quality, method=6)
    results.append((src, orig_size, os.path.getsize(dest), "OK"))

print(f"{'file':<70}{'orig KB':>10}{'new KB':>10}")
total_o, total_n = 0, 0
for src, o, n, status in results:
    if status != "OK":
        print(f"{src:<70}{status:>10}"); continue
    total_o += o; total_n += n
    print(f"{src:<70}{o/1024:>9.0f}K{n/1024:>9.0f}K")
print(f"\nTOTAL: {total_o/1024/1024:.1f}MB -> {total_n/1024/1024:.1f}MB\n")

# ---- 2. Update HTML references ----
mapping = {os.path.basename(src) if not src.startswith("blog/") else "images/" + os.path.basename(src): os.path.basename(dest) if not dest.startswith("blog/") else "images/" + os.path.basename(dest) for src, _, _, dest in targets if isinstance(dest, str)}
# build explicit mapping using original (unquoted) relative refs as they appear in HTML src=""
html_mapping = {
    "micke-lindstrom-I3GuNBeDerI-unsplash.jpg": "micke-lindstrom-I3GuNBeDerI-unsplash.webp",
    "/BACP Logo - 397064.png": "/BACP Logo - 397064.webp",
}
for enc in blog_images_raw:
    html_mapping[enc] = enc.rsplit(".", 1)[0] + ".webp"

def replace_srcs(text):
    for old, new in html_mapping.items():
        text = text.replace(f'src="{old}"', f'src="{new}"')
    return text

def process(path, extra=None):
    with open(path, encoding="utf-8") as f:
        t = f.read()
    orig = t
    t = replace_srcs(t)
    if extra:
        t = extra(t)
    if t != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(t)
        print("updated:", path)

process("index.html", lambda t: t.replace(
    'style="width:100%;height:100%;object-fit:cover;" />',
    'style="width:100%;height:100%;object-fit:cover;" fetchpriority="high" />', 1))
process("footer.html", lambda t: t.replace(
    'alt="BACP Registered Member logo - Roy Lam membership number 397064" />',
    'alt="BACP Registered Member logo - Roy Lam membership number 397064" loading="lazy" />'))

def add_lazy(m):
    tag = m.group(0)
    return tag if "loading=" in tag else tag[:-2] + ' loading="lazy" />'
process("blog/index.html", lambda t: re.sub(r'<img[^>]*class="blog-card-img"[^>]*/>', add_lazy, t))

for path in glob.glob("blog/*.html"):
    if path != "blog/index.html".replace("/", os.sep) and os.path.basename(path) != "index.html":
        process(path)

# ---- 3. Delete superseded originals ----
for src, _, _, dest in targets:
    if os.path.exists(dest) and os.path.exists(src):
        os.remove(src)
        print("removed:", src)

print("\nDone.")