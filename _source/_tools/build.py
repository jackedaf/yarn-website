"""Builds the real alcovecomputer.com site from this folder.

The pages here are also the Claude artifact preview, which adds its own
<!doctype>/<head>; the real site needs them in the file, plus its own
title, icons and link-preview tags. The source lives in the repo's _source folder
(GitHub Pages skips folders starting with _), and the site is built into the repo root.
Run from anywhere: python3 _source/_tools/build.py
"""
import hashlib, os, re, shutil, sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.dirname(SRC)  # the repo root, which GitHub Pages serves
SITE = "https://www.alcovecomputer.com"
PAGES = {
    "index.html": "Yarn: Journal to Unlock Apps",
    "terms.html": None, "privacy.html": None, "contact.html": None,
}
HEAD_EXTRA = """<link rel="icon" type="image/png" href="/img/icon-32.png">
<link rel="apple-touch-icon" href="/img/icon-180.png">
<meta property="og:site_name" content="Yarn">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}/img/share-wide.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The hand-drawn Yarn logo">
<meta property="og:video" content="{site}/img/share.mp4">
<meta property="og:video:secure_url" content="{site}/img/share.mp4">
<meta property="og:video:type" content="video/mp4">
<meta property="og:video:width" content="1200">
<meta property="og:video:height" content="630">
<meta property="og:url" content="{site}/{path}">
<link rel="canonical" href="{site}/{path}">
<meta name="twitter:card" content="summary_large_image">
"""


def fingerprint(name):
    """site.css -> site.<hash>.css: a new file name whenever it changes. GitHub's servers
    cache files for 10 minutes and ignore ?v= tags, so the version has to be in the name."""
    base, ext = os.path.splitext(name)
    return f"{base}.{hashlib.md5(open(os.path.join(SRC, name), 'rb').read()).hexdigest()[:8]}{ext}"

def clean_links(html):
    """Links on the live site use clean addresses (/privacy, not privacy.html)."""
    html = re.sub(r'href="/?index\.html(#[\w-]+)?"', lambda m: 'href="/' + (m.group(1) or '') + '"', html)
    html = re.sub(r'href="/?(privacy|terms|contact)\.html"', r'href="/\1"', html)
    return re.sub(r'(href|src)="(/?)(site\.css|site\.js)"', lambda m: f'{m.group(1)}="{m.group(2)}{fingerprint(m.group(3))}"', html)

os.makedirs(OUT, exist_ok=True)
used = set()
for page, new_title in PAGES.items():
    s = open(os.path.join(SRC, page)).read()
    if new_title:
        s = re.sub(r"<title>[^<]*</title>", f"<title>{new_title}</title>", s, count=1)
    if not s.lstrip().lower().startswith("<!doctype"):
        s = '<!doctype html>\n<html lang="en">\n' + s
    title = re.search(r"<title>([^<]*)</title>", s).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', s).group(1)
    path = "" if page == "index.html" else page[:-5]
    extra = HEAD_EXTRA.format(title=title, desc=desc, site=SITE, path=path)
    s = s.replace('<link rel="stylesheet" href="site.css">', extra + '<link rel="stylesheet" href="site.css">', 1)
    open(os.path.join(OUT, page), "w").write(clean_links(s))
    used |= set(re.findall(r"(img/[\w./-]+\.png)", s))

# Older versioned copies (and the plain names) are kept: a page cached in the last
# ten minutes still points at them.
for f in ("site.css", "site.js"):
    shutil.copy(os.path.join(SRC, f), os.path.join(OUT, f))
    shutil.copy(os.path.join(SRC, f), os.path.join(OUT, fingerprint(f)))
    used |= set(re.findall(r"(img/[\w./-]+\.png)", open(os.path.join(SRC, f)).read()))
# Frame sequences are listed in data-frames attributes.
for page in PAGES:
    for frames in re.findall(r'data-frames="([^"]+)"', open(os.path.join(SRC, page)).read()):
        used |= set(frames.split())

if os.path.isdir(os.path.join(OUT, "img")):
    shutil.rmtree(os.path.join(OUT, "img"))
GENERATED = {"img/icon-32.png", "img/icon-180.png", "img/share.png", "img/share-wide.png"}
for rel in sorted(used - GENERATED):
    dst = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(os.path.join(SRC, rel), dst)
for extra in ("icon-32.png", "icon-180.png", "share-wide.png", "share.mp4"):
    shutil.copy(os.path.join(SRC, "_tools", extra), os.path.join(OUT, "img", extra))
open(os.path.join(OUT, "404.html"), "w").write(clean_links(open(os.path.join(SRC, "_tools", "404.html")).read()))
# The CNAME file claims www.alcovecomputer.com for GitHub Pages. Only add it
# once the domain's DNS points at GitHub (pass --domain), or Pages redirects
# to a domain that still serves the old site.
if True:  # the domain is live, so the CNAME file always goes in
    shutil.copy(os.path.join(SRC, "_tools", "CNAME"), os.path.join(OUT, "CNAME"))
os.makedirs(os.path.join(OUT, "_drafts"), exist_ok=True)
shutil.copy(os.path.join(SRC, "_tools", "manifesto-2025.md"), os.path.join(OUT, "_drafts", "manifesto-2025.md"))
print(f"built {len(PAGES)} pages and {len(used)} images into {OUT}")
