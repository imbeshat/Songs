import os
import sys
import time
import json
import threading
import pygame
import yt_dlp
import imageio_ffmpeg


# ------------------ LOAD LYRICS FROM JSON ------------------
def load_lyrics(path="lyrics_kashish.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Convert into list of tuples: (time, text)
    return [(float(item["time"]), item["text"]) for item in data]


# ------------------ DOWNLOAD YOUTUBE AUDIO ------------------
def download_audio(url, output_name="song.mp3"):
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(os.getcwd(), "song.%(ext)s"),
        "prefer_ffmpeg": True,
        "ffmpeg_location": ffmpeg_exe,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }
        ],
        "postprocessor_args": ["-ar", "44100"],
    }

    print("Downloading audio...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Ensure mp3 exists
    if not os.path.exists(output_name):
        for f in os.listdir():
            if f.startswith("song.") and f.endswith(".mp3"):
                os.rename(f, output_name)
                break

    return os.path.join(os.getcwd(), output_name)


# ------------------ PLAYER SETUP ------------------
pause_flag = threading.Event()
stop_flag = threading.Event()
lyric_offset = 0.0


def input_controls():
    global lyric_offset
    while not stop_flag.is_set():
        try:
            cmd = input().strip().lower()
        except EOFError:
            break

        if cmd == "p":
            pygame.mixer.music.pause()
            pause_flag.set()
            print("Paused")

        elif cmd == "r":
            pygame.mixer.music.unpause()
            pause_flag.clear()
            print("Resumed")

        elif cmd == "[":
            lyric_offset -= 0.25
            print(f"Lyric offset: {lyric_offset:+.2f}s")

        elif cmd == "]":
            lyric_offset += 0.25
            print(f"Lyric offset: {lyric_offset:+.2f}s")

        elif cmd == "o":
            print(f"Lyric offset: {lyric_offset:+.2f}s")

        elif cmd in ("s", "q"):
            stop_flag.set()
            pygame.mixer.music.stop()
            print("Stopped")
            break


def show_lyrics(lyrics):
    idx = 0
    total = len(lyrics)
    line_started = False
    typed_idx = 0

    while idx < total and not stop_flag.is_set():
        if pause_flag.is_set():
            time.sleep(0.02)
            continue

        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0:
            time.sleep(0.02)
            continue

        pos = pos_ms / 1000.0
        cue_time, text = lyrics[idx]

        if not line_started:
            if pos + lyric_offset >= cue_time:
                # compute char speed
                if idx + 1 < total:
                    next_time = lyrics[idx + 1][0]
                    char_delay = max(0.03, (next_time - cue_time) / len(text))
                else:
                    char_delay = 0.12

                line_started = True
                start_time = pos + lyric_offset  # when typing begins
                typed_idx = 0
            else:
                time.sleep(0.01)
                continue

        elapsed = (pos + lyric_offset) - cue_time
        target = int(elapsed / char_delay) + 1
        target = min(target, len(text))

        while typed_idx < target and not stop_flag.is_set():
            sys.stdout.write(text[typed_idx])
            sys.stdout.flush()
            typed_idx += 1

        if typed_idx >= len(text):
            sys.stdout.write("\n")
            sys.stdout.flush()
            idx += 1
            line_started = False
        else:
            time.sleep(0.01)


# ------------------ MAIN ------------------
if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=Db_s0IdsbEc"

    # Load lyrics from JSON
    lyrics = load_lyrics("lyrics_kashish.json")

    # Download MP3 if missing
    if not os.path.exists("song.mp3"):
        download_audio(url)

    pygame.mixer.init(frequency=44100)
    pygame.mixer.music.load("song.mp3")

    pygame.mixer.music.play()

    threading.Thread(target=input_controls, daemon=True).start()
    threading.Thread(target=show_lyrics, args=(lyrics,), daemon=True).start()

    try:
        while pygame.mixer.music.get_busy() and not stop_flag.is_set():
            time.sleep(0.2)
    finally:
        stop_flag.set()
