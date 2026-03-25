import sys
sys.stdout.reconfigure(encoding='utf-8')

from faster_whisper import WhisperModel
import os

# Input file
input_path = r"C:\Users\ninni\projects\awi\docs\松林社長\松林社長 年頭メッセージ（2026年1月）.mp4"

# Output file: same folder as the MP4, same base name with .txt extension
output_path = r"C:\Users\ninni\projects\awi\docs\松林社長\松林社長 年頭メッセージ（2026年1月）.txt"

# Load model (large-v2 for best Japanese accuracy)
model = WhisperModel("large-v2", device="cpu", compute_type="int8")

print(f"Transcribing: {input_path}")
print(f"Output will be saved to: {output_path}")

# Transcribe
segments, info = model.transcribe(
    input_path,
    language="ja",
    beam_size=5,
)

print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")

# Write output
with open(output_path, "w", encoding="utf-8") as f:
    for segment in segments:
        line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}"
        print(line)
        f.write(line + "\n")

print(f"\nDone. Transcript saved to: {output_path}")
