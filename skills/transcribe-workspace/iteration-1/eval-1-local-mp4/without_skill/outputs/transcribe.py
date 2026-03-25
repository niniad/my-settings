import sys
sys.stdout.reconfigure(encoding='utf-8')

from faster_whisper import WhisperModel
import os

input_file = r"C:\Users\ninni\projects\awi\tmp\test_audio.mp4"
wav_file = r"C:\Users\ninni\projects\awi\tmp\test_audio.wav"
output_dir = r"C:\Users\ninni\.claude\skills\transcribe-workspace\iteration-1\eval-1-local-mp4\without_skill\outputs"
output_file = os.path.join(output_dir, "transcript.txt")

# Step 1: Convert MP4 to WAV using ffmpeg (16kHz mono for Whisper)
print("Converting MP4 to WAV...")
import subprocess
subprocess.run([
    "ffmpeg", "-i", input_file,
    "-ar", "16000", "-ac", "1", "-f", "wav",
    wav_file, "-y"
], capture_output=True, check=True)
print("Conversion done.")

# Step 2: Load large-v2 model (best accuracy for Japanese)
print("Loading model: large-v2 ...")
model = WhisperModel("large-v2", device="cpu", compute_type="int8")

# Step 3: Transcribe with relaxed thresholds for short clips
print(f"Transcribing: {input_file}")
segments, info = model.transcribe(
    wav_file,
    beam_size=5,
    language="ja",
    vad_filter=False,
    condition_on_previous_text=False,
    temperature=0,
    no_speech_threshold=0.1,
    compression_ratio_threshold=10.0,
    log_prob_threshold=-2.0
)

print(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")

lines = []
lines.append(f"# 文字起こし結果")
lines.append(f"# ファイル: {input_file}")
lines.append(f"# モデル: large-v2")
lines.append(f"# 言語: {info.language} (確信度: {info.language_probability:.2f})")
lines.append("")

for segment in segments:
    line = f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text.strip()}"
    print(line)
    lines.append(line)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n保存完了: {output_file}")
