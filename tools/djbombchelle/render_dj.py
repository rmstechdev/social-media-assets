"""DJ Bombchelle / Slamdino / Resonant Theory renderer.

For each album: a 4:5 Instagram feed image and a 9:16 reel built around the album cover.
If a post has "audio" (path to an mp3/wav/m4a) the reel uses it (from "audio_start" seconds,
with fades); otherwise the reel is silent.

Usage: python3 render_dj.py content.json out
"""
import colorsys, json, os, subprocess, sys
sys.path.insert(0, os.environ.get("RENDER_PY_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apexlit")))
from render import hexc, text_block, tracked, ease  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

F = "/usr/share/fonts/truetype/google-fonts"
FPS = 30
W, H = 1080, 1920


def pf(kind, size):
    return ImageFont.truetype(f"{F}/Poppins-{kind}.ttf", size)


def palette(cover):
    """Dark background + one bright accent sampled from the cover itself."""
    small = cover.convert("RGB").resize((64, 64))
    q = small.quantize(colors=10, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[:30]
    counts = sorted(q.getcolors(), reverse=True)
    cols = [tuple(pal[i * 3:i * 3 + 3]) for _, i in counts]
    def hsv(c):
        return colorsys.rgb_to_hsv(*[x / 255 for x in c])
    accent = max(cols, key=lambda c: hsv(c)[1] * (hsv(c)[2] ** 1.5))
    h, s, v = hsv(accent)
    if v < 0.75:
        accent = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, min(s, 0.85), 0.9))
    h0, s0, _ = hsv(cols[0])
    bg = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h0, min(0.6, s0 + 0.1), 0.10))
    return bg + (255,), accent + (255,)


def glow_bg(cover, size, bg):
    """Blurred, darkened copy of the cover filling the frame."""
    w, h = size
    s = max(w / cover.width, h / cover.height)
    im = cover.convert("RGB").resize((round(cover.width * s), round(cover.height * s)), Image.BILINEAR)
    im = im.crop(((im.width - w) // 2, (im.height - h) // 2, (im.width - w) // 2 + w, (im.height - h) // 2 + h))
    im = im.filter(ImageFilter.GaussianBlur(60))
    im = ImageEnhance.Brightness(im).enhance(0.35)
    base = Image.new("RGB", size, bg[:3])
    return Image.blend(base, im, 0.75).convert("RGBA")


def shadow_paste(canvas, img, pos, radius=40, opacity=170):
    pad = radius * 3
    sh = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([pad, pad + 20, pad + img.width, pad + img.height + 20], fill=(0, 0, 0, opacity))
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    canvas.alpha_composite(sh, (pos[0] - pad, pos[1] - pad))
    canvas.alpha_composite(img.convert("RGBA"), pos)


def feed(p, out):
    cover = Image.open(p["cover"]).convert("RGB")
    bg, acc = palette(cover)
    FH = 1350
    c = glow_bg(cover, (W, FH), bg)
    d = ImageDraw.Draw(c)
    M = 72
    tracked(d, (M, 66), p["artist_label"], pf("Medium", 24), acc, track=4)
    y = text_block(d, (M, 106), p["feed_hook"], pf("Bold", 58), (255, 255, 255, 255), W - 2 * M, spacing=1.15)
    size = min(860, FH - (y + 40) - 130)
    cv = cover.resize((size, size), Image.LANCZOS)
    cy = y + 40
    shadow_paste(c, cv, ((W - size) // 2, cy))
    by = FH - 88
    f = pf("Bold", 30)
    t = p.get("feed_cta", "STREAM IT NOW")
    tracked(d, (M, by), t, f, acc, track=3)
    f2 = pf("Medium", 26)
    t2 = "Spotify · Apple Music"
    d.text((W - M - d.textlength(t2, font=f2), by + 2), t2, font=f2, fill=(255, 255, 255, 220))
    c.convert("RGB").save(out, quality=92)


def reel(p, out):
    cover = Image.open(p["cover"]).convert("RGB")
    bg, acc = palette(cover)
    base = glow_bg(cover, (W, H), bg)
    big = cover.resize((920, 920), Image.LANCZOS)
    v = p["video_frames"]
    white = (255, 255, 255)
    total = 12.0

    def frame(t):
        im = base.copy()
        d = ImageDraw.Draw(im)
        z = 1.0 + 0.06 * (t / total)
        cv = big.resize((round(920 * z), round(920 * z)), Image.BILINEAR)
        cy = 560 - (cv.height - 920) // 2
        shadow_paste(im, cv, ((W - cv.width) // 2, cy), radius=46)
        # hook (0–6s): above the cover
        a = ease(t / 0.6) * (1 - ease((t - 5.6) / 0.5))
        if a > 0:
            n = len(v["hook"].split("\n"))
            hy = 500 - n * 78
            tracked(d, (0, hy - 60), p["artist_label"], pf("Medium", 30), acc[:3] + (int(255 * a),), track=6,
                    align="center", width=W)
            text_block(d, (70, hy), v["hook"], pf("Bold", 70), white + (int(255 * a),), W - 140,
                       align="center", spacing=1.12)
        # title + stream line (6–12s)
        b = ease((t - 6.0) / 0.6)
        if b > 0:
            n2 = len(v["title_line"].split("\n"))
            text_block(d, (70, 500 - n2 * 72), v["title_line"], pf("Bold", 64), white + (int(255 * b),), W - 140,
                       align="center", spacing=1.1)
        cta_a = ease((t - 2.0) / 0.6)
        y = 560 + 920 + 90
        tracked(d, (0, y), v.get("cta", "STREAM IT NOW"), pf("Bold", 44), acc[:3] + (int(255 * cta_a),),
                track=6, align="center", width=W)
        text_block(d, (70, y + 70), "Spotify · Apple Music · Link in bio", pf("Medium", 36),
                   white + (int(220 * cta_a),), W - 140, align="center")
        return im

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    if p.get("audio"):
        st = float(p.get("audio_start", 0))
        cmd += ["-ss", str(st), "-t", str(total), "-i", p["audio"], "-filter:a",
                f"afade=t=in:st=0:d=0.8,afade=t=out:st={total - 1.2}:d=1.2", "-map", "0:v", "-map", "1:a"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(int(total * FPS)):
        proc.stdin.write(frame(f / FPS).convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()


if __name__ == "__main__":
    src = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "out"
    os.makedirs(out_dir, exist_ok=True)
    for p in json.load(open(src))["posts"]:
        feed(p, f"{out_dir}/{p['id']}-feed.jpg")
        if "--no-video" not in sys.argv:
            reel(p, f"{out_dir}/{p['id']}-reel.mp4")
        print("done", p["id"])
