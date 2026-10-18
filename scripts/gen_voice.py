import math
import re
import subprocess
from faster_whisper import WhisperModel

text = open("script.txt", encoding="utf-8").read().strip()

# Use the same edge-tts voice as the workflow so audio and captions stay in sync.
subprocess.run(
    ["edge-tts", "--voice", "en-US-ChristopherNeural", "--rate=+8%",
     "--file", "script.txt",
     "--write-media", "voiceover.mp3"],
    check=True,
)

# faster-whisper needs 16kHz mono; feed an ndarray to avoid its PyAV file decoder
# (breaks across av library versions).
subprocess.run(
    ["ffmpeg", "-y", "-i", "voiceover.mp3", "-ar", "16000", "-ac", "1",
     "voiceover_16k.wav"],
    check=True,
)

import soundfile as sf  # noqa: E402

audio16k, _sr = sf.read("voiceover_16k.wav", dtype="float32")
if audio16k.ndim > 1:
    audio16k = audio16k.mean(axis=1)

model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
segments, info = model.transcribe(audio16k, word_timestamps=True, vad_filter=True)

words = []
for seg in segments:
    for w in (seg.words or []):
        token = w.word.strip()
        if token:
            words.append((token, float(w.start), float(w.end)))

total = float(info.duration)
print(f"audio duration: {total:.2f}s, words: {len(words)}")


def fmt_ms(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


# ASS spec requires centiseconds (h:mm:ss.cc); millisecond timestamps make
# libass ignore cue end times, which stacks every subtitle on screen.
def fmt_ass(seconds):
    cs_total = int(round(seconds * 100))
    h = cs_total // 360000
    m = (cs_total % 360000) // 6000
    s = (cs_total % 6000) // 100
    cs = cs_total % 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


# One word at a time: each word shows from its own start until the next word
# begins, so cues never overlap and never leave a gap.
cues = []
for i, (token, start, end) in enumerate(words):
    stop = words[i + 1][1] if i + 1 < len(words) else total
    if stop <= start:
        stop = start + 0.2
    cues.append((token, start, stop))

with open("captions.vtt", "w", encoding="utf-8") as f:
    f.write("WEBVTT\n\n")
    for token, start, stop in cues:
        f.write(f"{fmt_ms(start)} --> {fmt_ms(stop)}\n{token}\n\n")

# 23 fields, in exactly the order of the Format line below.
ass_style = (
    "Style: Default,Montserrat,54,&H00FFFFFF,&H000000FF,&H00101413,&H80000000,"
    "-1,0,0,0,100,100,0,0,1,3,1,2,70,70,170,1\n"
)
with open("captions.ass", "w", encoding="utf-8") as f:
    f.write("[Script Info]\n")
    f.write("Title: Subtitles\n")
    f.write("ScriptType: v4.00+\n")
    f.write("WrapStyle: 0\n")
    f.write("ScaledBorderAndShadow: yes\n")
    f.write("YCbCr Matrix: TV.601\n")
    f.write("PlayResX: 1080\n")
    f.write("PlayResY: 1920\n")
    f.write("\n[V4+ Styles]\n")
    f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
    f.write(ass_style)
    f.write("\n[Events]\n")
    f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    for token, start, stop in cues:
        f.write(f"Dialogue: 0,{fmt_ass(start)},{fmt_ass(stop)},Default,,0,0,0,,{token}\n")

print(f"Generated voiceover.mp3, captions.vtt, captions.ass ({len(cues)} word cues)")

# Keep the composition long enough to hold the whole voiceover.
D = math.ceil(total + 1.0)
with open("index.html", encoding="utf-8") as f:
    html = f.read()
html = re.sub(
    r'(data-composition-id="indian-ocean-short"[^>]*?data-duration=")[\d.]+(")',
    rf"\g<1>{D}\g<2>", html, count=1)
html = re.sub(
    r'(<audio id="voiceover"[^>]*?data-duration=")[\d.]+(")',
    rf"\g<1>{D}\g<2>", html, count=1)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print(f"Patched index.html composition duration -> {D}s")