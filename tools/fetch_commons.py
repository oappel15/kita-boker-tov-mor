#!/usr/bin/env python3
"""Download a free image from Wikimedia Commons into assets/img/<edition-date>/ and print the
JSON "image" block (credit + licence) to paste into the edition file.
Usage: python3 tools/fetch_commons.py 2026-10-15 my-slug "File:Some image.jpg"
Search ideas: https://commons.wikimedia.org/w/index.php?search=...&title=Special:MediaSearch
Allowed licences only: Public domain, CC0, CC BY, CC BY-SA, KOGL Type 1, NASA/ESA public, "Attribution"."""
import sys, os, io, re, json, urllib.request, urllib.parse
UA = {"User-Agent": "KitaLessonBot/1.0 (https://github.com/oappel15; educational)"}
OK = re.compile(r"public domain|^pd|cc0|cc by|cc-by|kogl type 1|attribution", re.I)
date, slug, title = sys.argv[1], sys.argv[2], sys.argv[3]
u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(dict(action="query", titles=title, prop="imageinfo", iiprop="url|extmetadata", iiurlwidth=1000, format="json"))
p = list(json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA)))["query"]["pages"].values())[0]
if "imageinfo" not in p: sys.exit("not found: " + title)
ii = p["imageinfo"][0]; m = ii["extmetadata"]
g = lambda k: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.get(k, {}).get("value", ""))).strip()
lic = g("LicenseShortName")
if not OK.search(lic): sys.exit(f"licence not allowed: {lic}")
raw = urllib.request.urlopen(urllib.request.Request(ii.get("thumburl") or ii["url"], headers=UA)).read()
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(root, "assets/img", date), exist_ok=True)
rel = f"assets/img/{date}/{slug}.jpg"
try:
    from PIL import Image
    im = Image.open(io.BytesIO(raw)).convert("RGB"); im.thumbnail((1000, 1000))
    im.save(os.path.join(root, rel), "JPEG", quality=80, optimize=True, progressive=True)
except ImportError:
    open(os.path.join(root, rel), "wb").write(raw)
print(json.dumps({"src": rel, "alt": "TODO: תיאור קצר של התמונה", "caption": "TODO: כיתוב (לציין ״תמונת המחשה״ אם לא מהאירוע)",
                  "credit": g("Artist") or g("Credit"), "license": lic, "license_url": m.get("LicenseUrl", {}).get("value", ""),
                  "source_url": ii["descriptionurl"]}, ensure_ascii=False, indent=1))
