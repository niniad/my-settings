import sys
sys.stdout.reconfigure(encoding='utf-8')

from faster_whisper import WhisperModel

audio_path = r"C:\Users\ninni\projects\awi\tmp\test_audio.mp4"
output_dir = r"C:\Users\ninni\.claude\skills\transcribe-workspace\iteration-1\eval-2-script-content\without_skill\outputs"

# Load model (small for speed, supports Japanese)
model = WhisperModel("small", device="cpu", compute_type="int8")

# Transcribe
segments, info = model.transcribe(audio_path, beam_size=5)

print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")
print()

transcript_lines = []
for segment in segments:
    line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text.strip()}"
    print(line)
    transcript_lines.append(line)

# Save transcript
transcript_path = output_dir + r"\transcript.txt"
with open(transcript_path, "w", encoding="utf-8") as f:
    f.write(f"Detected language: {info.language} (probability: {info.language_probability:.2f})\n\n")
    f.write("\n".join(transcript_lines))

print(f"\nTranscript saved to: {transcript_path}")
