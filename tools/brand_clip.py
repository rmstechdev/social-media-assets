"""Burn a brand's website onto a ready-made video (e.g. an inbox clip) so every creative shows it.

A small pill with the site sits near the top for the whole clip, and a larger one sits in the
lower third for the last 3 seconds. Audio is copied unchanged.

usage: python3 tools/brand_clip.py IN.mp4 OUT.mp4 apexlitpublishinggroup.com [--fg #fbfaf8 --bg #36060d]
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

F = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"


def hexc(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def pill_png(text, size, fg, bg, path):
    f = ImageFont.truetype(F, size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw = d0.textlength(text, font=f)
    padx, pady = int(size * 0.9), int(size * 0.45)
    w, h = int(tw + 2 * padx), int(size * 1.25 + 2 * pady)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=bg)
    d.text((padx, pady - size * 0.08), text, font=f, fill=fg)
    im.save(path)


def main():
    a = sys.argv[1:]
    src, dst, site = a[0], a[1], a[2]
    fg = a[a.index("--fg") + 1] if "--fg" in a else "#ffffff"
    bg = a[a.index("--bg") + 1] if "--bg" in a else "#000000"
    info = json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
         "-of", "json", src]))
    W, H = info["streams"][0]["width"], info["streams"][0]["height"]
    dur = float(info["format"]["duration"])
    tmp = tempfile.mkdtemp()
    small, big = os.path.join(tmp, "s.png"), os.path.join(tmp, "b.png")
    pill_png(site, round(W * 0.032), hexc(fg), hexc(bg, 200), small)
    pill_png(site, round(W * 0.05), hexc(bg), hexc(fg, 235), big)
    t0 = max(0.0, dur - 3.0)
    top = round(H * 0.075)
    low = round(H * 0.66)
    fc = (f"[1:v]format=rgba[s];[2:v]format=rgba,fade=t=in:st={t0}:d=0.4:alpha=1[b];"
          f"[0:v][s]overlay=(W-w)/2:{top}[v1];[v1][b]overlay=(W-w)/2:{low}:enable='gte(t,{t0})'[v]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-loop", "1", "-i", small, "-loop", "1", "-i", big,
           "-filter_complex", fc, "-map", "[v]", "-map", "0:a?", "-t", str(dur), "-c:v", "libx264",
           "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", dst]
    subprocess.check_call(cmd)
    print("branded", dst, f"{W}x{H}", round(dur, 2), "s")


if __name__ == "__main__":
    main()
