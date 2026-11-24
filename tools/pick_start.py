"""Pick a good start point for a short reel soundtrack.

Finds the loudest stretch of `length` seconds (usually the hook or drop) in the first 3 minutes
of a track, skipping the first 8 seconds of intro. Prints the start time in whole seconds.

usage: python3 tools/pick_start.py TRACK.mp3 [length_seconds]
"""
import subprocess, sys
import numpy as np

path = sys.argv[1]
length = float(sys.argv[2]) if len(sys.argv) > 2 else 14
SR = 8000
raw = subprocess.run(["ffmpeg", "-v", "error", "-t", "180", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
sec = len(x) // SR
if sec <= length + 8:
    print(0)
    sys.exit()
rms = np.array([np.sqrt(np.mean(x[i * SR:(i + 1) * SR] ** 2)) for i in range(sec)])
L = int(length)
best = max(range(8, sec - L + 1), key=lambda s: rms[s:s + L].mean())
print(best)
