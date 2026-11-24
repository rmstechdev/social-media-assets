# Music for reels

Upload MP3 files here (GitHub's website takes files up to 25 MB, so use MP3 rather than WAV).

**Name each file `Album Title - Track Title.mp3`**, using the album name as it appears on djbombchellemusic.com.
For example: `Better Days - Sunrise.mp3` or `LoFi Code Sessions - Night Shift.mp3`.

How the scheduled tasks use these files:

- **ApexLit and PuzzleVybe reels** use them as background music, rotating so the same song isn't used back to back. The caption credits the song and links to djbombchellemusic.com.
- **DJ Bombchelle reels**: when an album has a song here, that album is posted as a reel with its own music instead of a still image.
- Each reel plays about 12 to 15 seconds, starting at the loudest part of the song (usually the hook or the drop).

Optional settings go in `tracks.json`, keyed by file name:

```json
{
  "Better Days - Sunrise.mp3": {"start": 42, "background": true},
  "Velvet Vibes - Slow Burn.mp3": {"background": false}
}
```

- `start`: second to start from, if you want a specific part of the song
- `background`: set to `false` for songs that shouldn't play under book or puzzle posts (for example, tracks with explicit lyrics)
