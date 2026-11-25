"""DJ Bombchelle trial reels: website-first reels with a song from the private music library.

Two layouts, both 1080x1920, cover visible from frame 0:
  "site"  : hero cover + hook -> cover carousel ("every album, one place") -> big website end card
  "album" : one album cover + hook -> title + "hear it at djbombchellemusic.com" end card
A "now playing" line names the song for the whole reel.

Usage: python3 trial_dj.py trial.json out_dir
trial.json: {"reels": [{"id", "layout", "hero": cover path, "hook", "artist_label",
                        "carousel": [cover paths] (site), "title_line" (album),
                        "song": display name, "album_of_song": display name,
                        "audio": mp3 path, "audio_start": seconds}]}
"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "apexlit"))
sys.path.insert(0, HERE)
from render import text_block, tracked, ease  # noqa: E402
from render_dj import palette, glow_bg, shadow_paste, pf  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

FPS, W, H = 30, 1080, 1920
SITE = "DJBOMBCHELLEMUSIC.COM"
WHITE = (255, 255, 255)


def sq(path, size):
    return Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)


def now_playing(d, r, acc, a=1.0):
    y = 1590
    tracked(d, (0, y), "NOW PLAYING", pf("Medium", 26), acc[:3] + (int(230 * a),), track=6, align="center", width=W)
    line = f"{r['song']}  ·  {r['album_of_song']}"
    f = pf("Medium", 32)
    while d.textlength(line, font=f) > W - 160 and f.size > 22:
        f = pf("Medium", f.size - 2)
    d.text(((W - d.textlength(line, font=f)) / 2, y + 40), line, font=f, fill=WHITE + (int(220 * a),))


def end_card(im, d, r, acc, a, cover_small):
    shadow_paste(im, cover_small, ((W - cover_small.width) // 2, 330), radius=36)
    y = 330 + cover_small.height + 80
    tracked(d, (0, y), r.get("end_kicker", "HEAR IT ALL AT"), pf("Medium", 32), WHITE + (int(220 * a),),
            track=6, align="center", width=W)
    f = pf("Bold", 74)
    while d.textlength(SITE, font=f) > W - 100:
        f = pf("Bold", f.size - 2)
    d.text(((W - d.textlength(SITE, font=f)) / 2, y + 56), SITE, font=f, fill=acc[:3] + (int(255 * a),))
    sub = r.get("end_sub", "Every album, one place · Link in bio")
    text_block(d, (80, y + 170), sub, pf("Medium", 36), WHITE + (int(225 * a),), W - 160, align="center")


def render(r, out):
    hero = Image.open(r["hero"]).convert("RGB")
    bg, acc = palette(hero)
    base = glow_bg(hero, (W, H), bg)
    big = hero.resize((900, 900), Image.LANCZOS)
    small = hero.resize((560, 560), Image.LANCZOS)
    car = [sq(c, 720) for c in r.get("carousel", [])]
    site = r["layout"] == "site"
    total = 14.0 if site else 12.0
    t_end = 9.6 if site else 7.2

    def hook_layer(d, a, text, kicker):
        n = len(text.split("\n"))
        hy = 470 - n * 80
        tracked(d, (0, hy - 64), kicker, pf("Medium", 30), acc[:3] + (int(255 * a),), track=6, align="center", width=W)
        text_block(d, (70, hy), text, pf("Bold", 72), WHITE + (int(255 * a),), W - 140, align="center", spacing=1.12)

    def frame(t):
        im = base.copy()
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # text drawn here so alpha fades blend
        d = ImageDraw.Draw(layer)
        if t < (4.6 if site else t_end):
            # product first: hero cover + hook from frame 0
            seg = 4.6 if site else t_end
            z = 1.0 + 0.05 * (t / seg)
            cv = big.resize((round(900 * z), round(900 * z)), Image.BILINEAR)
            shadow_paste(im, cv, ((W - cv.width) // 2, 560 - (cv.height - 900) // 2), radius=46)
            a = 1 - ease((t - (seg - 0.4)) / 0.4)
            if not site and t >= 3.6:
                # album layout: swap hook for title line over the same shot
                b = ease((t - 3.6) / 0.35)
                c = ease((t - 3.95) / 0.4)
                if b < 1:
                    hook_layer(d, 1 - b, r["hook"], r["artist_label"])
                if c > 0:
                    hook_layer(d, c * a, r["title_line"], r["artist_label"])
            else:
                hook_layer(d, a, r["hook"], r["artist_label"])
        elif site and t < t_end:
            # carousel: covers slide in from the right, one every 1.25s
            s = t - 4.6
            a = ease(s / 0.4) * (1 - ease((s - 4.6) / 0.4))
            tracked(d, (0, 300), r.get("carousel_kicker", "DJ BOMBCHELLE & FRIENDS"), pf("Medium", 30),
                    acc[:3] + (int(255 * a),), track=6, align="center", width=W)
            text_block(d, (70, 350), r.get("carousel_line", "Every mood.\nOne site."), pf("Bold", 70),
                       WHITE + (int(255 * a),), W - 140, align="center", spacing=1.1)
            step = 1.25
            i = min(int(s / step), len(car) - 1)
            k = ease((s - i * step) / 0.45)
            y = 620
            if i > 0:
                prev = car[i - 1]
                shadow_paste(im, prev, (int((W - 720) / 2 - k * W), y), radius=40)
            cur = car[i]
            x = int((W - 720) / 2 + (1 - k) * W) if i > 0 or s > 0.0 else (W - 720) // 2
            if i == 0:
                x = (W - 720) // 2
            shadow_paste(im, cur, (x, y), radius=40)
        else:
            a = ease((t - t_end) / 0.5)
            end_card(im, d, r, acc, a, small)
        now_playing(d, r, acc)
        im.alpha_composite(layer)
        return im

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-ss", str(r.get("audio_start", 0)), "-t", str(total), "-i", r["audio"],
           "-filter:a", f"afade=t=in:st=0:d=0.6,afade=t=out:st={total - 1.5}:d=1.5", "-map", "0:v", "-map", "1:a",
           "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(int(total * FPS)):
        proc.stdin.write(frame(f / FPS).convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    only = sys.argv[3] if len(sys.argv) > 3 else None
    for r in spec["reels"]:
        if only and r["id"] != only:
            continue
        render(r, os.path.join(out_dir, f"{r['id']}.mp4"))
        print("done", r["id"])
