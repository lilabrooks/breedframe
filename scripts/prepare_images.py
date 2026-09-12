"""Fetch attributed fixtures. No evaluation output is consulted by this script."""

import hashlib
import json
from pathlib import Path
import httpx
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "beagle": (
        "Beagle_600.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/5/55/Beagle_600.jpg",
        "sannse",
        "CC BY-SA 3.0",
        "https://creativecommons.org/licenses/by-sa/3.0/",
    ),
    "golden": (
        "Golden_Retriever_Carlos_(10581910556).jpg",
        None,
        "Dirk Vorderstraße",
        "CC BY 2.0",
        "https://creativecommons.org/licenses/by/2.0/",
    ),
    "pug": ("Pug_600.jpg", None, "sannse", "CC BY-SA 3.0", "https://creativecommons.org/licenses/by-sa/3.0/"),
}


def main():
    for split in ("demo", "evaluation"):
        (ROOT / "data" / split).mkdir(parents=True, exist_ok=True)
    provenance = []
    with httpx.Client(
        follow_redirects=True,
        timeout=60,
        headers={"User-Agent": "BreedFrame/0.1 local educational evaluation"},
    ) as client:
        for key, (name, url, author, license_name, license_url) in SOURCES.items():
            digest = hashlib.md5(name.encode()).hexdigest()
            url = url or f"https://upload.wikimedia.org/wikipedia/commons/{digest[0]}/{digest[:2]}/{name}"
            split = "demo" if key == "beagle" else "evaluation"
            target = ROOT / "data" / split / f"{key}.jpg"
            if not target.exists():
                response = client.get(url)
                response.raise_for_status()
                target.write_bytes(response.content)
            provenance.append(
                dict(
                    id=key,
                    path=str(target.relative_to(ROOT)),
                    source=f"https://commons.wikimedia.org/wiki/File:{name}",
                    url=url,
                    author=author,
                    license=license_name,
                    license_url=license_url,
                    sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                    changes="Original downloaded bytes",
                )
            )
    for split, key in (("demo", "beagle"), ("evaluation", "golden")):
        with Image.open(ROOT / "data" / split / f"{key}.jpg") as im:
            im.convert("RGB").resize((48, 32)).save(ROOT / "data" / split / f"{key}-tiny.png")
    Image.new("RGB", (640, 480), (8, 8, 8)).save(ROOT / "data/evaluation/dark.png")
    im = Image.new("RGB", (640, 480), "white")
    from PIL import ImageDraw

    draw = ImageDraw.Draw(im)
    for y in range(0, 480, 40):
        for x in range(0, 640, 40):
            if (x // 40 + y // 40) % 2:
                draw.rectangle((x, y, x + 39, y + 39), fill="black")
    im.save(ROOT / "data/evaluation/checker.png")
    (ROOT / "docs/evidence/image-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


if __name__ == "__main__":
    main()
