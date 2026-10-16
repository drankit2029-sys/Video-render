import os
import re
import subprocess
from kokoro import KPipeline
import soundfile as sf

text = open("script.txt", encoding="utf-8").read().strip()
pipeline = KPipeline(lang_code="a")

# Split into short, natural phrases for professional subtitle timing.
# Break on sentence boundaries first, then on clause boundaries (, ; —),
# and only hard-chunk on word count as a last resort.
def split_phrases(text, max_words=8):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    phrases = []
    for s in sentences:
        clauses = [c.strip() for c in re.split(r"\s*(?:;|—|--)\s*|\s*,\s*", s) if c.strip()]
        # re-attach trailing punctuation stripped by the split
        for c in clauses:
            words = c.split()
            for i in range(0, len(words), max_words):
                # if cutting here would orphan a tiny remainder (<3 words),
                # extend this chunk to absorb it (at most max_words+2 words)
                if 0 < len(words) - (i + max_words) < 3:
                    phrases.append(" ".join(words[i:]))
                    break
                chunk = " ".join(words[i:i + max_words])
                if chunk:
                    phrases.append(chunk)
    return phrases

phrases = split_phrases(text, max_words=8)

segments = []
for idx, phrase in enumerate(phrases):
    gen = pipeline(phrase, voice="af_heart", speed=1.0, split_pattern=r"\n+")
    for j, (gs, ps, audio) in enumerate(gen):
        seg_path = f"seg_{idx}_{j}.wav"
        sf.write(seg_path, audio, 24000)
        duration = len(audio) / 24000.0
        segments.append((phrase, duration, seg_path))
        print(f"seg {idx}_{j}: {phrase[:50]}... ({duration:.2f}s)")

# Concatenate all segment WAVs into one voiceover WAV
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

def fmt(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

# Write VTT (clean, readable subtitles)
# NOTE: each cue ends 80ms early (except the last) so consecutive cues never
# stack on boundary frames.
with open("captions.vtt", "w", encoding="utf-8") as f:
    f.write("WEBVTT\n\n")
    t = 0.0
    for n, (sentence, duration, _) in enumerate(segments):
        if not sentence:
            t += duration
            continue
        start = fmt(t)
        end = fmt(t + duration - (0.0 if n == len(segments) - 1 else 0.08))
        f.write(f"{start} --> {end}\n")
        f.write(f"{sentence}\n\n")
        t += duration

# Write ASS for professional burn-in styling (crisp outline, bottom-center).
# Field order MUST match the Format line exactly (23 fields): Name, Fontname,
# Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold,
# Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle,
# Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding.
# Alignment=2 -> bottom-center, MarginV=180 keeps text clear of phone UI.
ass_style = (
    "Style: Default,Inter,54,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
    "-1,0,0,0,100,100,0,0,1,3,1,2,60,60,180,1\n"
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
    t = 0.0
    for n, (sentence, duration, _) in enumerate(segments):
        if not sentence:
            t += duration
            continue
        start = fmt(t)
        end = fmt(t + duration - (0.0 if n == len(segments) - 1 else 0.08))
        f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{sentence}\n")
        t += duration

print(f"Total duration: {t:.2f}s")
print("Generated voiceover.mp3, captions.vtt, captions.ass")

# Patch index.html timings so the composition always contains the full
# voiceover (+1s tail) instead of cutting the ending off.
import math

total = t
D = math.ceil(total + 1.0)
D3 = round(D - 10.0, 1)

with open("index.html", encoding="utf-8") as f:
    html = f.read()

html = re.sub(
    r'(data-composition-id="short-video"[^>]*?data-duration=")[\d.]+(")',
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
    r'(id="scene-3"[^>]*?data-start=")10(" data-duration=")[\d.]+(")',
    rf"\g<1>10\g<2>{D3}\g<3>",
    html,
    count=1,
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Patched index.html: composition={D}s, scene-3 duration={D3}s")
