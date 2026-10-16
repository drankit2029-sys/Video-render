import os
import re
import subprocess
from kokoro import KPipeline
import soundfile as sf

text = open("script.txt", encoding="utf-8").read().strip()
pipeline = KPipeline(lang_code="a")

# Split into sentences for finer subtitle granularity
sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

segments = []
for idx, sentence in enumerate(sentences):
    gen = pipeline(sentence, voice="af_heart", speed=1.0, split_pattern=r"\n+")
    for j, (gs, ps, audio) in enumerate(gen):
        seg_path = f"seg_{idx}_{j}.wav"
        sf.write(seg_path, audio, 24000)
        duration = len(audio) / 24000.0
        segments.append((sentence, duration, seg_path))
        print(f"seg {idx}_{j}: {sentence[:50]}... ({duration:.2f}s)")

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

# Write VTT subtitles
def fmt(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

with open("captions.vtt", "w", encoding="utf-8") as f:
    f.write("WEBVTT\n\n")
    t = 0.0
    for sentence, duration, _ in segments:
        if not sentence:
            t += duration
            continue
        start = fmt(t)
        end = fmt(t + duration)
        f.write(f"{start} --> {end}\n")
        f.write(f"{sentence}\n\n")
        t += duration

print(f"Total duration: {t:.2f}s")
print("Generated voiceover.mp3 and captions.vtt")
