"""Fetch or verify the curated photo set without running either model."""

import argparse
import hashlib
import html
import json
import shutil
import time
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/photo-set-v2"
OUTPUT = ROOT / "data/photo-set-v2"


def prepare(check_only=False):
    manifest = json.loads((EVIDENCE / "manifest.json").read_text())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for row in manifest["images"]:
        path = ROOT / row["path"]
        if not path.exists():
            if check_only:
                raise FileNotFoundError(path)
            request = urllib.request.Request(
                row["download_url"], headers={"User-Agent": "BreedFrame-photo-set/0.1"}
            )
            # HTTP errors stop the download, including rate limits. Reruns retain verified files.
            with urllib.request.urlopen(request, timeout=45) as response:
                data = response.read(row["bytes"] + 1)
            if hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError(f"Upstream bytes changed for {row['id']}; review before updating.")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            time.sleep(2)
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"Checksum mismatch: {path}")
        with Image.open(path) as image:
            image.load()
            if image.size != (row["width"], row["height"]):
                raise ValueError(f"Dimensions changed: {path}")

    cards = []
    escape = html.escape
    sheet = Image.new("RGB", (1200, 245 * ((len(manifest["images"]) + 3) // 4)), "#ecebe5")
    draw = ImageDraw.Draw(sheet)
    for index, row in enumerate(manifest["images"]):
        case = next(case for case in manifest["cases"] if row["id"] in case["photo_ids"])
        caption = f"{row['creator']} · {row['license']} · {row['download_variant']}"
        cards.append(
            f'<article><a href="images/{escape(row["id"])}.jpg">'
            f'<img src="images/{escape(row["id"])}.jpg" alt="{escape(row["visual_review"])}"></a>'
            f'<h2>{escape(row["id"])}</h2><p class="meta">{escape(case["split"])}</p>'
            f'<p>{escape(row["visual_review"])}</p><p class="meta">{escape(caption)}</p>'
            f'<a href="{escape(row["source_revision_url"])}">Source and reuse terms</a></article>'
        )
        with Image.open(ROOT / row["path"]) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((290, 215))
            x, y = (index % 4) * 300, (index // 4) * 245
            sheet.paste(image, (x + (300 - image.width) // 2, y + (215 - image.height) // 2))
            draw.text((x + 8, y + 222), row["id"], fill="black")
    sheet.save(OUTPUT / "contact-sheet.jpg")
    (OUTPUT / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>BreedFrame photo set</title><style>"
        "body{font:16px system-ui;background:#f5f3ec;color:#223c32;margin:32px auto;max-width:1200px;padding:0 20px}"
        "main{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}"
        "article{background:white;border:1px solid #ddd;padding:16px;border-radius:12px}"
        "img{width:100%;height:220px;object-fit:contain;background:#eeede8}"
        "h2{font-size:19px}.meta{font-size:13px;color:#555}a{color:#276148}"
        "</style><h1>BreedFrame photo set</h1>"
        "<p>20 photographs · 13 cases · 7 same-dog pairs. Selected without model predictions.</p>"
        "<p>Documentary breed labels; ancestry unverified. Archive-heavy convenience sample. "
        "Pairs can be months or years apart. Individual image licenses apply.</p>"
        '<p><a href="manifest.json">Case manifest</a> · '
        '<a href="attribution.md">Full attribution</a></p><main>' + "".join(cards) + "</main></html>"
    )
    for name in ("manifest.json", "attribution.md"):
        shutil.copyfile(EVIDENCE / name, OUTPUT / name)
    print(f"Verified {len(manifest['images'])} images. Gallery: {OUTPUT / 'index.html'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Verify local images; no network.")
    prepare(parser.parse_args().check_only)
