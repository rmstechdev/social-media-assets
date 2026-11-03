# PuzzleVybe inbox

Drop finished videos for PuzzleVybe puzzles in `clips/` (vertical MP4 works best).
`clips/clips.json` describes each clip: the puzzle(s) it shows, the post type and caption notes.
Clips without an entry are reviewed by the scheduled task, which identifies the puzzle from the frames and skips anything it cannot match.
When a clip is scheduled it is moved to `puzzlevybe/<date>/` and its entry gets status "posted".
