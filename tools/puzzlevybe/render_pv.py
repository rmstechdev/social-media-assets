"""PuzzleVybe renderer: 3-slide Instagram carousel (1080x1350) + 9:16 video per puzzle.

Usage: python3 render_pv.py content.json out
Reuses drawing helpers from the ApexLit render.py (set RENDER_PY_DIR or keep it next to this file).
"""
import json, os, subprocess, sys
sys.path.insert(0, os.environ.get("RENDER_PY_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apexlit")))
from render import hexc, wrap, text_block, tracked, shadowed, ease  # noqa: E402
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F = "/usr/share/fonts/truetype/google-fonts"
FPS = 30
# Brand colours sampled from the PuzzleVybe shop banner.
T = {"bg": "#0e2530", "panel": "#127a73", "fg": "#ffffff", "accent": "#ffc93c", "pink": "#ef3b6e",
     "teal": "#1fb3a6", "mat": "#fbf8f2"}


def pf(kind, size):
    return ImageFont.truetype(f"{F}/Poppins-{kind}.ttf", size)


def load(path):
    return Image.open(os.path.join(HERE, path)).convert("RGB")


def fit_w(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def framed(art, w, mat=26, edge=6):
    """Artwork in a thin dark frame with a cream mat, like a finished, framed puzzle."""
    a = fit_w(art, w - 2 * (mat + edge))
    fr = Image.new("RGBA", (w, a.height + 2 * (mat + edge)), hexc("#1b1b1f"))
    ImageDraw.Draw(fr).rectangle([edge, edge, fr.width - edge - 1, fr.height - edge - 1], fill=hexc(T["mat"]))
    fr.paste(a, (edge + mat, edge + mat))
    return fr


def stripes(d, W, y=0, h=14):
    for i, c in enumerate([T["teal"], T["pink"], T["accent"]]):
        d.rectangle([i * W // 3, y, (i + 1) * W // 3, y + h], fill=hexc(c))


def pill(d, x, y, text, fnt, bgc, fgc, pad=(28, 14), align="left", width=0):
    tw = d.textlength(text, font=fnt)
    w, h = tw + 2 * pad[0], fnt.size + 2 * pad[1] + 4
    if align == "center":
        x = x + (width - w) / 2
    d.rounded_rectangle([x, y, x + w, y + h], h / 2, fill=bgc)
    d.text((x + pad[0], y + pad[1] - 2), text, font=fnt, fill=fgc)
    return x, y, x + w, y + h


def wordmark(d, x, y, size, color, align="left", width=0):
    f = pf("Bold", size)
    t = "PuzzleVybe"
    if align == "center":
        x = x + (width - d.textlength(t, font=f)) / 2
    d.text((x, y), t, font=f, fill=color)


# ---------------- carousel ----------------
def slide1(p, sale, out):
    W, H, M = 1080, 1350, 72
    c = Image.new("RGBA", (W, H), hexc(T["bg"]))
    d = ImageDraw.Draw(c)
    stripes(d, W)
    tracked(d, (M, 70), p["imprint_label"], pf("Medium", 26), hexc(T["teal"]), track=4)
    if p["type"] == "problem_solution":
        y = text_block(d, (M, 112), p["feed_problem"], pf("Bold", 62), hexc(T["fg"]), W - 2 * M, spacing=1.15)
        d.rectangle([M, y + 22, M + 40, y + 27], fill=hexc(T["accent"]))
        y = text_block(d, (M + 58, y + 2), p["feed_answer"], pf("Medium", 34), hexc(T["accent"]), W - 2 * M - 58,
                       spacing=1.3)
    else:
        y = text_block(d, (M, 112), p["feed_hook"], pf("Bold", 62), hexc(T["fg"]), W - 2 * M, spacing=1.15)
    fr = framed(load(p["art"]), W - 2 * M + 20)
    fy = int(y + max(44, (H - 160 - y - fr.height) / 2))
    d.rectangle([0, fy + fr.height * 0.45, W, H], fill=hexc(T["panel"]))
    shadowed(c, fr, ((W - fr.width) // 2, fy), radius=26)
    by = H - 118
    pill(d, M, by, sale["label"], pf("Bold", 28), hexc(T["pink"]), hexc("#ffffff"))
    f2, f3 = pf("Bold", 36), pf("Regular", 26)
    was = p.get("price_was", "")
    px = W - M - d.textlength(p["price"], font=f2)
    d.text((px, by + 2), p["price"], font=f2, fill=hexc(T["fg"]))
    sub = (f"was {was}  ·  " if was else "") + "free shipping"
    d.text((W - M - d.textlength(sub, font=f3), by + 48), sub, font=f3, fill=hexc(T["fg"]))
    c.convert("RGB").save(out, quality=92)


def photo_slide(photo, caption, sub, out):
    W, H = 1080, 1350
    c = Image.new("RGBA", (W, H), hexc(T["bg"]))
    ph = load(photo).resize((W, W), Image.LANCZOS)
    c.paste(ph, (0, 0))
    d = ImageDraw.Draw(c)
    stripes(d, W, y=W, h=10)
    text_block(d, (72, W + 50), caption, pf("Bold", 44), hexc(T["fg"]), W - 144, spacing=1.2)
    tracked(d, (72, H - 70), sub, pf("Medium", 24), hexc(T["accent"]), track=4)
    c.convert("RGB").save(out, quality=92)


# ---------------- video ----------------
def video(p, sale, out):
    W, H = 1080, 1920
    v = p["video_frames"]
    bg, fg, acc = hexc(T["bg"]), hexc(T["fg"]), hexc(T["accent"])
    art = load(p["art"])
    hands = load(p["hands"]).resize((W, W), Image.LANCZOS)
    fr_big = framed(art, 1000)
    fr_small = framed(art, 860)

    def base():
        im = Image.new("RGBA", (W, H), bg)
        d = ImageDraw.Draw(im)
        stripes(d, W, h=16)
        return im, d

    def big_text(text, sub=None, label=True):
        def seg(s):
            im, d = base()
            a = ease(s / 0.5)
            dy = int(30 * (1 - a))
            if label:
                tracked(d, (0, 500), p["imprint_label"], pf("Medium", 32), hexc(T["teal"])[:3] + (int(255 * a),),
                        track=6, align="center", width=W)
            y = text_block(d, (80, 640 + dy), text, pf("Bold", 104), fg[:3] + (int(255 * a),), W - 160,
                           align="center", spacing=1.1)
            if sub:
                a2 = ease((s - 0.5) / 0.5)
                text_block(d, (110, y + 50), sub, pf("Regular", 46), acc[:3] + (int(255 * a2),), W - 220,
                           align="center", spacing=1.3)
            return im
        return seg

    def seg_why(s):
        im, d = base()
        a = ease(s / 0.5)
        d.rectangle([W // 2 - 40, 700, W // 2 + 40, 707], fill=hexc(T["pink"])[:3] + (int(255 * a),))
        text_block(d, (100, 780), v["why"], pf("Bold", 76), acc[:3] + (int(255 * a),), W - 200,
                   align="center", spacing=1.2)
        return im

    def seg_hands(s, dur):
        im, d = base()
        z = 1.0 + 0.10 * (s / dur)
        ph = hands.resize((round(W * z), round(W * z)), Image.BILINEAR)
        off = (ph.width - W) // 2
        im.paste(ph.crop((off, off, off + W, off + W)), (0, 420))
        label = v.get("answer_label", "PIECE BY PIECE")
        tracked(d, (0, 230), label, pf("Bold", 40), acc, track=8, align="center", width=W)
        text_block(d, (60, 290), p["title"], pf("Bold", 70), fg, W - 120, align="center")
        return im

    def seg_art(s):
        im, d = base()
        d.rectangle([0, 0, W, 760], fill=hexc(T["panel"]))
        z = 1.0 + 0.04 * min(1, s / 3.2)
        fr = fr_big.resize((round(fr_big.width * z), round(fr_big.height * z)), Image.BILINEAR)
        shadowed(im, fr, ((W - fr.width) // 2, 200), radius=30)
        y = 200 + fr_big.height + 120
        for i, pt in enumerate(v["points"]):
            a = ease((s - 0.3 - i * 0.5) / 0.45)
            dx = int(60 * (1 - a))
            col = [T["teal"], T["pink"], T["accent"]][i % 3]
            d.rounded_rectangle([110 + dx, y + 20, 134 + dx, y + 44], 6, fill=hexc(col)[:3] + (int(255 * a),))
            d.text((165 + dx, y - 4), pt, font=pf("Medium", 60), fill=fg[:3] + (int(255 * a),))
            y += 130
        return im

    def seg_cta(s):
        im, d = base()
        a = ease(s / 0.5)
        d.rectangle([0, 0, W, 700], fill=hexc(T["panel"]))
        shadowed(im, fr_small, ((W - fr_small.width) // 2, 180), radius=26)
        y = 180 + fr_small.height + 70
        text_block(d, (80, y), v["cta"], pf("Bold", 72), fg[:3] + (int(255 * a),), W - 160, align="center")
        y += 110
        pill(d, 0, y, sale["label"], pf("Bold", 40), hexc(T["pink"])[:3] + (int(255 * a),),
             (255, 255, 255, int(255 * a)), align="center", width=W)
        y += 120
        pill(d, 0, y, "Link in bio", pf("Bold", 44), acc[:3] + (int(255 * a),), bg[:3] + (int(255 * a),),
             pad=(44, 18), align="center", width=W)
        wordmark(d, 0, y + 150, 46, fg[:3] + (int(255 * a),), align="center", width=W)
        return im

    if p["type"] == "problem_solution":
        segs = [(2.8, big_text(v["problem"])), (2.3, seg_why), (3.4, lambda s: seg_hands(s, 3.4)),
                (3.4, seg_art), (3.4, seg_cta)]
    else:
        segs = [(3.0, big_text(v["hook"], v.get("hook_sub"))), (3.4, lambda s: seg_hands(s, 3.4)),
                (3.4, seg_art), (3.4, seg_cta)]
    XF = 0.4
    starts, t0 = [], 0.0
    for dur, _ in segs:
        starts.append(t0)
        t0 += dur
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for f in range(int(t0 * FPS)):
        tt = f / FPS
        i = max(k for k, st in enumerate(starts) if st <= tt)
        frame = segs[i][1](tt - starts[i])
        if i + 1 < len(segs) and tt > starts[i + 1] - XF:
            frame = Image.blend(frame, segs[i + 1][1](0), (tt - (starts[i + 1] - XF)) / XF)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()


def render_post(p, sale, out_dir, with_video=True):
    slide1(p, sale, f"{out_dir}/{p['id']}-1.jpg")
    photo_slide(p["hands"], p["slide2"], "PIECE BY PIECE", f"{out_dir}/{p['id']}-2.jpg")
    photo_slide(p["table"], p["slide3"], "FROM PUZZLE TO WALL ART", f"{out_dir}/{p['id']}-3.jpg")
    if with_video:
        video(p, sale, f"{out_dir}/{p['id']}-reel.mp4")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "content.json")
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out")
    os.makedirs(out_dir, exist_ok=True)
    data = json.load(open(src))
    for p in data["posts"]:
        render_post(p, data["sale"], out_dir, with_video="--no-video" not in sys.argv)
        print("done", p["id"])
