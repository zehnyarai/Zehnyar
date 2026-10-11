"""Generate small legacy launcher/splash assets with Pillow, no remote fonts."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / "android/app/src/main/res"
PAPER = "#f7faf8"
BRAND = Path(__file__).resolve().parents[1] / "public/icon-512.png"


def icon(size=432, foreground=False, round_=False):
    # The same reference leaf/circle is used in web, launcher and splash.
    with Image.open(BRAND) as source:
        mark = source.convert("RGBA")
    if not foreground:
        return mark.resize((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    safe_size = round(size * 2 / 3)
    mark = mark.resize((safe_size, safe_size), Image.Resampling.LANCZOS)
    inset = (size - safe_size) // 2
    canvas.paste(mark, (inset, inset), mark)
    return canvas


for folder, size in [("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)]:
    directory = ROOT / f"mipmap-{folder}"
    icon(size).save(directory / "ic_launcher.png", optimize=True)
    icon(size, round_=True).save(directory / "ic_launcher_round.png", optimize=True)
    icon(round(size*2.25), foreground=True).save(directory / "ic_launcher_foreground.png", optimize=True)
for file in ROOT.glob("drawable*/splash.png"):
    with Image.open(file) as original:
        size = original.size
    canvas = Image.new("RGB", size, PAPER)
    mark_size = max(60, min(220, round(min(size)*.23)))
    mark = icon(mark_size)
    canvas.paste(mark, ((size[0]-mark_size)//2, (size[1]-mark_size)//2), mark)
    canvas.save(file, optimize=True)
