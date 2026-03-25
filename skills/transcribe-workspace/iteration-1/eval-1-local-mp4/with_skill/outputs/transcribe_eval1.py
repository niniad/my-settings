import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from faster_whisper import WhisperModel

input_file = r"C:\Users\ninni\projects\awi\tmp\test_audio.mp4"
output_file = r"C:\Users\ninni\projects\awi\tmp\test_audio_トランスクリプト.txt"

print(f"文字起こし開始: {input_file}")
sys.stdout.flush()

model = WhisperModel("large-v3", device="cpu", compute_type="int8")
print("モデルロード完了")
sys.stdout.flush()

segments, info = model.transcribe(
    input_file,
    language="ja",
    beam_size=5,
    vad_filter=False,
)

print(f"検出言語: {info.language} (確率: {info.language_probability:.2f})")
print(f"総時間: {info.duration/60:.1f}分")
sys.stdout.flush()

# ヘッダー書き込み
with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"# 文字起こし: {os.path.basename(input_file)}\n")
    f.write(f"# 生成日: {__import__('datetime').date.today()}\n")
    f.write(f"# モデル: faster-whisper large-v3 (CPU/int8)\n")
    f.write(f"# 総時間: {info.duration/60:.1f}分\n")
    f.write("\n---\n\n")

count = 0
for segment in segments:
    start_min = int(segment.start // 60)
    start_sec = segment.start % 60
    end_min = int(segment.end // 60)
    end_sec = segment.end % 60
    timestamp = f"[{start_min:02d}:{start_sec:05.2f} --> {end_min:02d}:{end_sec:05.2f}]"
    line = f"{timestamp} {segment.text.strip()}"
    print(line)
    sys.stdout.flush()
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    count += 1
    if count % 50 == 0:
        print(f"--- {count}セグメント処理済み ---")
        sys.stdout.flush()

print(f"\n=== 完了: {count}セグメント ===")
print(f"出力: {output_file}")
