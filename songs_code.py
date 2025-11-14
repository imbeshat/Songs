import os
import sys
import time
import threading
import pygame
import yt_dlp
import imageio_ffmpeg

"""Download the song locally as song.mp3 and then play it."""

# ------------ DOWNLOAD SONG (yt-dlp + ffmpeg) ------------
url = "https://www.youtube.com/watch?v=8of5w7RgcTc"
target_mp3 = os.path.join(os.getcwd(), "song.mp3")

if os.path.exists(target_mp3):
    print("Audio already present:", target_mp3)
else:
    print("Downloading audio with yt-dlp...")
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
                "preferredquality": "192",
            }
        ],
        # ensure stable sample rate for pygame
        "postprocessor_args": ["-ar", "44100"],
        "quiet": False,
        "noprogress": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # After postprocessing, song.mp3 should exist
    if not os.path.exists(target_mp3):
        # Fallback: find any song.* and rename if needed
        for fname in os.listdir(os.getcwd()):
            if fname.startswith("song.") and fname.endswith(".mp3"):
                target_mp3 = os.path.join(os.getcwd(), fname)
                break
    print("Downloaded:", target_mp3)

# ------------ SETUP PYGAME ------------
pygame.mixer.init(frequency=44100)
pygame.mixer.music.load(target_mp3)

# Start playing from 0:00 → 0 seconds
start_time = 0
pygame.mixer.music.play(start=start_time)

# ------------ CONTROLS (pause/resume/stop) ------------
pause_flag = threading.Event()
stop_flag = threading.Event()

def input_controls():
    global lyric_offset
    #print("Controls: p=pause, r=resume, s/q=stop, [ / ] nudge lyrics, o=offset")
    while not stop_flag.is_set():
        try:
            cmd = input().strip().lower()
        except EOFError:
            break
        if cmd == "p":
            if not pause_flag.is_set():
                pygame.mixer.music.pause()
                pause_flag.set()
                print("Paused")
        elif cmd == "r":
            if pause_flag.is_set():
                pygame.mixer.music.unpause()
                pause_flag.clear()
                print("Resumed")
        elif cmd == "[":
            lyric_offset -= 0.25
            print(f"Lyric offset: {lyric_offset:+.2f}s (earlier)")
        elif cmd == "]":
            lyric_offset += 0.25
            print(f"Lyric offset: {lyric_offset:+.2f}s (later)")
        elif cmd == "o":
            print(f"Lyric offset: {lyric_offset:+.2f}s")
        elif cmd in ("s", "q"):
            stop_flag.set()
            pygame.mixer.music.stop()
            print("Stopped")
            break

ctrl_thread = threading.Thread(target=input_controls, daemon=True)
ctrl_thread.start()

# ------------ LYRICS WITH TIMING (absolute seconds from playback start) ------------
# The first element of each tuple is an ABSOLUTE timestamp (in seconds)
# measured from when playback starts, not a relative delay.
lyrics = [
    (17.6, "Pal Pal Jeena Muhal"),
    (20, "Mera Tere Bina"),
    (22, "Ye Sarey Nashe Bekaar"),
    (24.2, "Teri Ankhon Kay Siwa"),
    (26.8, "Ghar Nahi Jata Mein Bahar"),
    (29, "Rehta Tera Intazar"),
    (31.2, "Mere, Khwabon Mein Aa Na"),
    (33.5, "Karkay Sola Singhaar"),
    (35.8, "Mein Ab Kyu Hosh Mein Ata Ni"),
    (37.9, "Sukoon Ye Dil Kyu Pata Ni"),
    (40.1, "Kyu Toru Khud Say Jo Thay Wade Kay Ab Ye Ishaq Nibahana Nahi"),
    (44.8, "Mein Moru Tumsay Jo Ye Chehra Dubara Nazar Milana Nahi,"),
    (48.9, "Ye Duniya Janay Mera Dard Tujhe Ye Nazar Kyu Ata Nahi"),
    (53.9, "Soneya Yu Tera Sharmana Meri Jaan Na Lele"),
    (58.7, "Kaan Ke Peechy Zulf Chupana Meri Jan Kya Kehne"),
    (63, "Zalima Toba Tera Nakhra Iske War Kya Kehne"),
    (68.3, "Tham Kay Bethe Dil Ko Ghayal Kaheen Har Na Bethein"),
    (72.5, "Teri Nazrein Mujhsay Kya Kehti Hain"),
    (75.2, "Inme Wafa Bethi Hai"),
    (78, "Thori Thori Si Razi Thori Si Khafa Rehti Hein"),
    (81.7, "Log Hein Zalim Barey"),
    (84.4, "Inme Jafa Dekhi Hay"),
    (87, "Ye Duniya Teri Nahi Maine Tujmay Haya Dekhi Hay"),
    (91.4, "Jeena Muhal"),
    (93.2, "Mera Tere Bina"),
    (95, "Ye Sarey Nashe Bekaar"),
    (97.5, "Teri Ankhon Kay Siwa"),
    (99.8, "Ghar Nahi Jata Mein Bahar"),
    (102, "Rehta Tera Intazar"),
    (104, "Mere, Khwabon Mein Aa Na"),
    (106.5, "Karkay Sola Singhaar")
]

lyric_offset = 0.0  # allow fine-tuning in real time

def show_lyrics():
    # Typewriter effect synced to the audio clock
    idx = 0
    total = len(lyrics)
    line_started = False
    typed_idx = 0
    char_delay = 0.01  # default; recomputed per line based on available window

    while idx < total and not stop_flag.is_set():
        if pause_flag.is_set():
            time.sleep(0.02)
            continue

        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0:
            time.sleep(0.02)
            continue

        pos = pos_ms / 1000.0  # seconds since play() (doesn't advance while paused)
        cue_time, text = lyrics[idx]
        cue_time = float(cue_time)

        # Wait for cue
        if not line_started:
            if pos + lyric_offset >= cue_time:
                # Type so the last character lands exactly at the next cue.
                if idx + 1 < total:
                    next_cue = lyrics[idx + 1][0]
                    char_delay = max(0.03, (next_cue - cue_time) / max(len(text), 1))
                else:
                    # Last line: use a reasonable default
                    char_delay = 0.12

                line_started = True
                typed_idx = 0
                # Immediately render first character at cue
                # (the loop below will compute target based on elapsed)
            else:
                time.sleep(0.01)
                continue

        # How many characters should be visible by now?
        elapsed = (pos + lyric_offset) - cue_time
        target = int(elapsed / char_delay) + 1  # start typing at cue
        target = max(0, min(target, len(text)))

        # Print any missing characters
        while typed_idx < target and not stop_flag.is_set():
            sys.stdout.write(text[typed_idx])
            sys.stdout.flush()
            typed_idx += 1

        # If the line is complete, newline and advance
        if typed_idx >= len(text):
            sys.stdout.write("\n")
            sys.stdout.flush()
            idx += 1
            line_started = False
        else:
            time.sleep(0.01)

lyrics_thread = threading.Thread(target=show_lyrics, daemon=True)
lyrics_thread.start()

# Keep script running until song ends
try:
    while pygame.mixer.music.get_busy() and not stop_flag.is_set():
        time.sleep(0.2)
finally:
    stop_flag.set()
