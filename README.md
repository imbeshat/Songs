# Code Wishes — Lyrics Typewriter Player

A small Python script that downloads a YouTube track locally (audio only), starts playback at a chosen offset, and displays synced lyrics with a typewriter effect. Playback and lyrics stay in sync even when you pause/resume, and you can nudge lyric timing live.

## Features
- Downloads audio via `yt-dlp` and converts to MP3 using a portable ffmpeg (`imageio-ffmpeg`).
- Starts playback at a specific timestamp (default 115s).
- Typewriter lyrics with real-time sync to the audio clock.
- Interactive controls in the terminal:
  - `p` pause
  - `r` resume
  - `s`/`q` stop
  - `[` make lyrics earlier by 0.25s
  - `]` make lyrics later by 0.25s
  - `o` print current lyric offset

## Requirements
- Python 3.11+
- A virtual environment is recommended

## Setup
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip yt-dlp imageio-ffmpeg pygame
```

## Run
```bash
.venv/bin/python wishes_code.py
```

The script downloads the song (ignored by git) to the project folder as `song.mp3` and then plays it. Lyrics appear in a typewriter style, synced to the music. Use `[` and `]` to fine‑tune lyric timing.

## Notes
- Media files like `song.mp3` are excluded via `.gitignore` so the repo stays lightweight.
- You can change the YouTube URL or the start time in `wishes_code.py`.
- If you want to include the audio in the repo, remove the relevant patterns from `.gitignore`.
