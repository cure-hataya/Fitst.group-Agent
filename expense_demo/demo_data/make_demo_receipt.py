"""生成占位小票示例图（仅用于 demo，无真实 OCR 语义要求）。运行：python demo_data/make_demo_receipt.py"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def build() -> Path:
    width, height = 420, 620
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except OSError:
        font_title = ImageFont.load_default()
        font = font_title

    lines = [
        ("DEMO MART", font_title),
        ("------------------------", font),
        ("Milk       12.00", font),
        ("Bread       8.50", font),
        ("Coffee     25.00", font),
        ("------------------------", font),
        ("TOTAL      45.50", font_title),
        ("2026-11-12 14:30", font),
        ("Thank you!", font),
    ]
    y = 40
    for text, fnt in lines:
        draw.text((40, y), text, fill="black", font=fnt)
        y += 55

    out = Path(__file__).resolve().parent / "sample_receipt.png"
    img.save(out)
    return out


if __name__ == "__main__":
    path = build()
    print(f"saved: {path}")
