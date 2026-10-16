import math
import re
import subprocess
from kokoro import KPipeline
import soundfile as sf
from faster_whisper import WhisperModel

VOICE = "am_adam"  # Kokoro American male voice

text = open("script.txt", encoding="utf-8").read().strip()
pipeline = KPipeline(lang_code="a")

# --- 1. Synthesize voiceover with Kokoro (male voice), one chunk per sentence
sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

segments = []
for idx, sentence in enumerate(sentences):
    gen = pipeline(sentence, voice=VOICE, speed=1.0, split_pattern=r"\n+")
    for j, (gs, ps, audio) in enumerate(gen):
        seg_path = f"seg_{idx}_{j}.wav"
        sf.write(seg_path, audio, 24000)
        duration = len(audio) / 24000.0
        segments.append((sentence, duration, seg_path))
        print(f"seg {idx}_{j}: {sentence[:50]}... ({duration:.2f}s)")

with open("seg_list.txt", "w") as f:
    for _, _, path in segments:
        f.write(f"file '{path}'\n")

subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "seg_list.txt",
     "-c", "copy", "voiceover.wav"],
    check=True,
)
subprocess.run(
    ["ffmpeg", "-y", "-i", "voiceover.wav", "-codec:a", "libmp3lame",
     "-qscale:a", "2", "voiceover.mp3"],
    check=True,
)

# --- 2. Word-level timestamps via faster-whisper STT on the rendered voiceover.
# NOTE: decoded to a 16kHz mono array with ffmpeg/soundfile and passed as an
# ndarray on purpose — faster-whisper's PyAV-based file decoder breaks across
# av library versions, while the ndarray path needs no av at all.
subprocess.run(
    ["ffmpeg", "-y", "-i", "voiceover.wav", "-ar", "16000", "-ac", "1",
     "voiceover_16k.wav"],
    check=True,
)
audio16k, _sr = sf.read("voiceover_16k.wav", dtype="float32")
if audio16k.ndim > 1:
    audio16k = audio16k.mean(axis=1)

model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
whisper_segments, info = model.transcribe(
    audio16k, word_timestamps=True, vad_filter=True
)
words = []
for seg in whisper_segments:
    for w in (seg.words or []):
        token = w.word.strip()
        if token:
            words.append((token, float(w.start), float(w.end)))

total = float(info.duration)
print(f"audio duration: {total:.2f}s, words: {len(words)}")

# --- 3. One-word-at-a-time subtitles (trendy word-pop style).
# Each word shows from its start until the next word starts (no gaps/overlaps).
cues = []
for i, (token, start, end) in enumerate(words):
    cue_end = words[i + 1][1] if i + 1 < len(words) else total
    if cue_end <= start:
        cue_end = start + 0.2
    cues.append((token, start, cue_end))


def fmt_ms(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


# ASS spec requires centiseconds (h:mm:ss.cc)
def fmt_ass(seconds):
    total_cs = int(round(seconds * 100))
    h = total_cs // 360000
    m = (total_cs % 360000) // 6000
    s = (total_cs % 6000) // 100
    cs = total_cs % 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


with open("captions.vtt", "w", encoding="utf-8") as f:
    f.write("WEBVTT\n\n")
    for token, start, end in cues:
        f.write(f"{fmt_ms(start)} --> {fmt_ms(end)}\n")
        f.write(f"{token}\n\n")

# Field order MUST match the Format line exactly (23 fields).
ass_style = (
    "Style: Default,Inter,68,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
    "-1,0,0,0,100,100,0,0,1,3,1,2,60,60,200,1\n"
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
    for token, start, end in cues:
        f.write(f"Dialogue: 0,{fmt_ass(start)},{fmt_ass(end)},Default,,0,0,0,,{token}\n")

print("Generated voiceover.mp3, captions.vtt, captions.ass")

# --- 4. Patch index.html timings so the composition contains the full voiceover
D = math.ceil(total + 1.0)
D5 = round(D - 11.8, 1)

with open("index.html", encoding="utf-8") as f:
    html = f.read()

html = re.sub(
    r'(data-composition-id="apple-liquid-glass"[^>]*?data-duration=")[\d.]+(")',
    rf"\g<1>{D}\g<2>",
    html,
    count=1,
)
html = re.sub(
    r'(<audio id="voiceover"[^>]*?data-duration=")[\d.]+(")',
    rf"\g<1>{D}\g<2>",
    html,
    count=1,
)
html = re.sub(
    r'(id="scene-5"[^>]*?data-start=")11\.8(" data-duration=")[\d.]+(")',
    rf"\g<1>11.8\g<2>{D5}\g<3>",
    html,
    count=1,
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Patched index.html: composition={D}s, scene-5 duration={D5}s")
