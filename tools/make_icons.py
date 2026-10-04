#!/usr/bin/env python3
"""Generate PWA/apple-touch icons: dark green square with the character 葡."""
import pathlib

from PIL import Image, ImageDraw, ImageFont

BASE = pathlib.Path(__file__).resolve().parent.parent
GREEN = (22, 59, 52)
WHITE = (255, 255, 255)
FONTS = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
]


def load_font(size):
    for path in FONTS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    raise SystemExit("no usable CJK font found")


def draw_icon(size, char_ratio, out):
    img = Image.new("RGB", (size, size), GREEN)
    d = ImageDraw.Draw(img)
    font = load_font(int(size * char_ratio))
    bbox = d.textbbox((0, 0), "葡", font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), "葡", font=font, fill=WHITE)
    img.save(out)
    print(f"wrote {out} ({size}x{size})")


if __name__ == "__main__":
    draw_icon(180, 0.52, BASE / "icon-180.png")
    draw_icon(192, 0.52, BASE / "icon-192.png")
    draw_icon(512, 0.52, BASE / "icon-512.png")
    draw_icon(512, 0.40, BASE / "icon-512-maskable.png")
