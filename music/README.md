# Music for reels

Make one folder per album, named exactly like the album on djbombchellemusic.com, and put that album's MP3s inside:

```
music/
  Better Days/
    01 Sunrise.mp3
    02 Keep Going.mp3
  Velvet Vibes/
    Slow Burn.mp3
```

- Song file names become the track titles in captions. Leading track numbers like "01 " or "01. " are ignored.
- Use MP3s. GitHub's website takes files up to 25 MB each and up to 100 files per upload.
- Loose files named `Album Title - Track Title.mp3` directly in this folder also work.

How the scheduled tasks use these files:

- **ApexLit and PuzzleVybe reels** use them as background music, rotating so the same song isn't used back to back. The caption credits the song and links to djbombchellemusic.com.
- **DJ Bombchelle**: an album with songs here is posted as a reel with its own music instead of a still image.
- Each reel plays about 12 to 15 seconds, starting at the loudest part of the song (usually the hook or the drop).

Optional settings go in `tracks.json`, keyed by the file's path inside this folder:

```json
{
  "Better Days/01 Sunrise.mp3": {"start": 42},
  "Velvet Vibes/Slow Burn.mp3": {"background": false}
}
```

- `start`: second to start from, if you want a specific part of the song
- `background`: set to `false` for songs that shouldn't play under book or puzzle posts (for example, tracks with explicit lyrics)
