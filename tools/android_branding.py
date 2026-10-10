"""Generate small legacy launcher/splash assets with Pillow, no remote fonts."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / "android/app/src/main/res"
GREEN, LEAF, PAPER = "#295c45", "#ddecc2", "#f6f8f5"


def curve(p0, p1, p2, p3):
    return [tuple((1-t)**3*p0[i] + 3*(1-t)**2*t*p1[i] + 3*(1-t)*t*t*p2[i] + t**3*p3[i] for i in (0, 1)) for t in [n/50 for n in range(51)]]


def icon(size=432, foreground=False, round_=False):
    image = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    if not foreground:
        if round_:
            draw.ellipse((0, 0, 431, 431), fill=GREEN)
        else:
            draw.rounded_rectangle((0, 0, 431, 431), radius=98, fill=GREEN)
    scale = lambda points: [(x*4, y*4) for x, y in points]
    for points in [[(54, 79), (54, 48)], curve((54, 63), (30, 63), (31, 36), (31, 36)) + curve((31, 36), (31, 36), (56, 35), (54, 63)), curve((54, 49), (54, 28), (78, 28), (78, 28)) + curve((78, 28), (78, 28), (80, 52), (54, 56))]:
        draw.line(scale(points), fill=LEAF, width=18, joint="curve")
    return image.resize((size, size), Image.Resampling.LANCZOS)


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
