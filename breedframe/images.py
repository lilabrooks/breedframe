import hashlib
import io
import warnings
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from .config import MAX_UPLOAD

Image.MAX_IMAGE_PIXELS = 20_000_000


def normalize_image(raw: bytes) -> tuple[bytes, dict]:
    if not raw or len(raw) > MAX_UPLOAD:
        raise ValueError("Choose a JPEG, PNG or WebP smaller than 12 MiB.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(raw)) as im:
                if im.format not in {"JPEG", "PNG", "WEBP"} or getattr(im, "n_frames", 1) != 1:
                    raise ValueError("Use a single-frame JPEG, PNG or WebP.")
                if im.width * im.height > Image.MAX_IMAGE_PIXELS:
                    raise ValueError("Image exceeds 20 megapixels.")
                im = ImageOps.exif_transpose(im).convert("RGB")
                im.load()
                output = io.BytesIO()
                # A fresh image drops all EXIF and other metadata.
                clean = Image.frombytes("RGB", im.size, im.tobytes())
                clean.save(output, format="PNG")
                pixels_hash = hashlib.sha256(im.tobytes() + str(im.size).encode()).hexdigest()
                return output.getvalue(), dict(width=im.width, height=im.height, sha256=pixels_hash)
        except (OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            raise ValueError("Image cannot be safely decoded.") from exc


def inspect_image(path: Path) -> dict:
    with Image.open(path) as im:
        width, height = im.size
        im.thumbnail((512, 512))
        a = np.asarray(im.convert("L"), dtype=np.float32)
    laplacian = a[:-2, 1:-1] + a[2:, 1:-1] + a[1:-1, :-2] + a[1:-1, 2:] - 4 * a[1:-1, 1:-1]
    detail = float(laplacian.var()) if laplacian.size else 0.0
    mean = float(a.mean())
    flags = []
    if min(width, height) < 160:
        flags.append("low_resolution")
    if mean < 35 or mean > 225:
        flags.append("exposure")
    if detail < 25:
        flags.append("low_detail")
    return dict(
        width=width,
        height=height,
        mean_luminance=round(mean, 2),
        laplacian_variance=round(detail, 2),
        quality_flags=flags,
        diagnostic_note="Heuristic pixel diagnostics, not calibrated quality or dog detection.",
    )
