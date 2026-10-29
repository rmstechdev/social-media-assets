"""Render a 4:5 feed image and a 9:16 video for each post in content.json.

Usage: python3 render.py [content.json] [out_dir]
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = "/usr/share/fonts/truetype/google-fonts"
FPS = 30


def font(kind, size):
    if kind == "serif":
        f = ImageFont.truetype(f"{FONTS}/Lora-Variable.ttf", size)
        try:
            f.set_variation_by_name("Bold")
        except Exception:
            pass
        return f
    if kind == "serif-italic":
        f = ImageFont.truetype(f"{FONTS}/Lora-Italic-Variable.ttf", size)
        return f
    name = {"sans": "Poppins-Regular", "sans-med": "Poppins-Medium", "sans-bold": "Poppins-Bold"}[kind]
    return ImageFont.truetype(f"{FONTS}/{name}.ttf", size)


def hexc(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def wrap(draw, text, fnt, width):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            t = (cur + " " + w).strip()
            if draw.textlength(t, font=fnt) <= width:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text_block(draw, xy, text, fnt, fill, width, align="left", spacing=1.18):
    x, y = xy
    lh = int(fnt.size * spacing)
    for line in wrap(draw, text, fnt, width):
        w = draw.textlength(line, font=fnt)
        lx = x + (width - w) / 2 if align == "center" else x
        draw.text((lx, y), line, font=fnt, fill=fill)
        y += lh
    return y


def tracked(draw, xy, text, fnt, fill, track=4, align="left", width=0):
    total = sum(draw.textlength(c, font=fnt) for c in text) + track * (len(text) - 1)
    x, y = xy
    if align == "center":
        x = x + (width - total) / 2
    for c in text:
        draw.text((x, y), c, font=fnt, fill=fill)
        x += draw.textlength(c, font=fnt) + track


def shadowed(canvas, img, pos, radius=28, offset=(0, 18), opacity=150):
    sh = Image.new("RGBA", (img.width + radius * 4, img.height + radius * 4), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([radius * 2, radius * 2, radius * 2 + img.width, radius * 2 + img.height],
                                 fill=(0, 0, 0, opacity))
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    canvas.alpha_composite(sh, (pos[0] - radius * 2 + offset[0], pos[1] - radius * 2 + offset[1]))
    canvas.alpha_composite(img.convert("RGBA"), pos)


def cover_at_height(path, h):
    im = Image.open(os.path.join(HERE, path)).convert("RGB")
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def logo_plate(h=64):
    logo = Image.open(os.path.join(HERE, "covers/logo.webp")).convert("RGB")
    logo = logo.resize((round(logo.width * h / logo.height), h), Image.LANCZOS)
    pad = 14
    plate = Image.new("RGBA", (logo.width + pad * 2, logo.height + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, plate.width - 1, plate.height - 1], 12, fill=(255, 255, 255, 255))
    plate.paste(logo, (pad, pad))
    return plate


# ---------------- feed image 1080x1350 ----------------
def feed_image(p, out):
    W, H = 1080, 1350
    t = p["theme"]
    c = Image.new("RGBA", (W, H), hexc(t["bg"]))
    d = ImageDraw.Draw(c)
    M = 80
    tracked(d, (M, 76), p["imprint_label"], font("sans-med", 26), hexc(t["accent"]), track=5)
    if p.get("type") == "problem_solution":
        # Problem in the reader's words, then the answer in the accent colour.
        y = text_block(d, (M, 124), p["feed_problem"], font("serif", 64), hexc(t["fg"]), W - 2 * M)
        af = font("sans-med", 34)
        d.rectangle([M, y + 26, M + 44, y + 30], fill=hexc(t["accent"]))
        y = text_block(d, (M + 62, y + 4), p["feed_answer"], af, hexc(t["accent"]), W - 2 * M - 62, spacing=1.3)
    else:
        hook_font = font("serif", 66 if len(p["feed_hook"]) < 40 else 54)
        y = text_block(d, (M, 124), p["feed_hook"], hook_font, hexc(t["fg"]), W - 2 * M)

    cov = cover_at_height(p["cover"], 760)
    cx = (W - cov.width) // 2
    cy = max(y + 50, 360)
    if cy + cov.height > H - 150:
        cov = cover_at_height(p["cover"], H - 150 - cy)
        cx = (W - cov.width) // 2
    # colour panel behind the cover
    d.rectangle([0, cy + cov.height * 0.35, W, H], fill=hexc(t["panel"]))
    shadowed(c, cov, (cx, cy))

    plate = logo_plate(46)
    c.alpha_composite(plate, (M, H - plate.height - 40))
    url = "apexlitpublishinggroup.com"
    uf = font("sans-med", 26)
    d.text((W - M - d.textlength(url, font=uf), H - 40 - plate.height / 2 - 18), url, font=uf, fill=hexc(t.get("panel_fg", t["fg"])))
    c.convert("RGB").save(out, quality=92)


# ---------------- video 1080x1920 ----------------
def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def video(p, out):
    W, H = 1080, 1920
    t = p["theme"]
    v = p["video_frames"]
    bg = hexc(t["bg"])
    fg, acc = hexc(t["fg"]), hexc(t["accent"])
    big = cover_at_height(p["cover"], 1150)
    small = cover_at_height(p["cover"], 760)
    plate = logo_plate(60)
    SAFE_BOTTOM = 1520  # keep text above TikTok/Reels caption area

    def base():
        im = Image.new("RGBA", (W, H), bg)
        return im, ImageDraw.Draw(im)

    def seg_hook(s):
        im, d = base()
        a = ease(s / 0.6)
        dy = int(40 * (1 - a))
        tracked(d, (0, 520), p["imprint_label"], font("sans-med", 32), acc[:3] + (int(255 * a),),
                track=6, align="center", width=W)
        y = text_block(d, (90, 700 + dy), v["hook"], font("serif", 104), fg[:3] + (int(255 * a),), W - 180,
                       align="center")
        a2 = ease((s - 0.5) / 0.6)
        text_block(d, (110, y + 50), v["hook_sub"], font("sans", 46), acc[:3] + (int(255 * a2),), W - 220,
                   align="center", spacing=1.3)
        return im

    def seg_cover(s, dur):
        im, d = base()
        d.rectangle([0, 1040, W, H], fill=hexc(t["panel"]))
        z = 1.0 + 0.07 * (s / dur)
        cov = big.resize((round(big.width * z), round(big.height * z)), Image.BILINEAR)
        x = (W - cov.width) // 2
        y = 1060 - cov.height // 2 + 40
        shadowed(im, cov, (x, y), radius=34)
        return im

    def seg_points(s):
        im, d = base()
        d.rectangle([0, 0, W, 760], fill=hexc(t["panel"]))
        sm = small.resize((round(small.width * 0.85), round(small.height * 0.85)))
        shadowed(im, sm, ((W - sm.width) // 2, 150), radius=22)
        pf = font("serif", 70)
        y = 150 + round(small.height * 0.85) + 110
        for i, pt in enumerate(v["points"]):
            a = ease((s - 0.25 - i * 0.55) / 0.45)
            dx = int(60 * (1 - a))
            d.rectangle([110 + dx, y + 22, 128 + dx, y + 40], fill=acc[:3] + (int(255 * a),))
            d.text((160 + dx, y - 6), pt, font=pf, fill=fg[:3] + (int(255 * a),))
            y += 170
        return im

    def seg_cta(s):
        im, d = base()
        a = ease(s / 0.5)
        d.rectangle([0, 0, W, 820], fill=hexc(t["panel"]))
        sc = small
        shadowed(im, sc, ((W - sc.width) // 2, 150), radius=26)
        y = 150 + sc.height + 70
        y = text_block(d, (100, y), v["cta"], font("serif", 58), fg[:3] + (int(255 * a),), W - 200,
                       align="center", spacing=1.2)
        lf = font("sans-bold", 44)
        txt = "Link in bio"
        tw = d.textlength(txt, font=lf)
        bx0, by0 = (W - tw) / 2 - 44, y + 40
        d.rounded_rectangle([bx0, by0, bx0 + tw + 88, by0 + 96], 48, fill=acc[:3] + (int(255 * a),))
        d.text(((W - tw) / 2, by0 + 18), txt, font=lf, fill=bg[:3] + (int(255 * a),))
        py = min(by0 + 150, SAFE_BOTTOM - plate.height)
        im.alpha_composite(plate, ((W - plate.width) // 2, int(py)))
        return im

    def seg_problem(s):
        im, d = base()
        a = ease(s / 0.5)
        dy = int(30 * (1 - a))
        tracked(d, (0, 520), p["imprint_label"], font("sans-med", 32), acc[:3] + (int(255 * a),),
                track=6, align="center", width=W)
        text_block(d, (90, 690 + dy), v["problem"], font("serif", 100), fg[:3] + (int(255 * a),), W - 180,
                   align="center")
        return im

    def seg_why(s):
        im, d = base()
        a = ease(s / 0.5)
        d.rectangle([W // 2 - 40, 700, W // 2 + 40, 706], fill=acc[:3] + (int(255 * a),))
        text_block(d, (110, 780), v["why"], font("serif", 78), acc[:3] + (int(255 * a),), W - 220,
                   align="center", spacing=1.25)
        return im

    def seg_answer(s, dur):
        im = seg_cover(s, dur)
        d = ImageDraw.Draw(im)
        a = ease(s / 0.5)
        tracked(d, (0, 210), v.get("answer_label", "THE FIX"), font("sans-bold", 40), acc[:3] + (int(255 * a),),
                track=8, align="center", width=W)
        return im

    if p.get("type") == "problem_solution":
        segs = [(2.8, seg_problem), (2.4, seg_why), (3.6, lambda s: seg_answer(s, 3.6)),
                (3.2, seg_points), (3.0, seg_cta)]
    else:
        segs = [(3.0, lambda s: seg_hook(s)), (4.0, lambda s: seg_cover(s, 4.0)),
                (3.2, lambda s: seg_points(s)), (3.3, lambda s: seg_cta(s))]
    XF = 0.4
    total = sum(dur for dur, _ in segs)
    starts, acc_t = [], 0.0
    for dur, _ in segs:
        starts.append(acc_t)
        acc_t += dur

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out],
        stdin=subprocess.PIPE)
    for f in range(int(total * FPS)):
        tt = f / FPS
        i = max(k for k, st in enumerate(starts) if st <= tt)
        frame = segs[i][1](tt - starts[i])
        if i + 1 < len(segs) and tt > starts[i + 1] - XF:
            nxt = segs[i + 1][1](0)
            frame = Image.blend(frame, nxt, (tt - (starts[i + 1] - XF)) / XF)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "content.json")
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out")
    only = sys.argv[3] if len(sys.argv) > 3 else None
    os.makedirs(out_dir, exist_ok=True)
    for p in json.load(open(src))["posts"]:
        if only and p["id"] != only:
            continue
        feed_image(p, os.path.join(out_dir, f"{p['id']}-feed.jpg"))
        if only != "feed":
            video(p, os.path.join(out_dir, f"{p['id']}-reel.mp4"))
        print("done", p["id"])
