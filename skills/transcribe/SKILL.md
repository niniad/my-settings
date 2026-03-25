---
name: transcribe
description: >
  MP4などの動画・音声ファイルやYouTube URLを日本語文字起こしするスキル。
  Faster-Whisper（ローカルLLM）を使ってタイムスタンプ付きトランスクリプトを生成する。
  「文字起こし」「トランスクリプト」「transcribe」と言われたとき、またはMP4ファイルパスや
  YouTube URLが与えられたときに必ず使うこと。「会議録を文字に起こして」「この動画の内容を
  テキスト化して」「YouTubeをダウンロードして文字起こし」なども含む。
---

# 文字起こしスキル（Faster-Whisper）

## 概要

ローカルのMP4ファイル または YouTube URL を受け取り、Faster-Whisper（large-v3モデル）で
日本語文字起こしを行い、タイムスタンプ付きテキストファイルを生成する。

**対応入力:**
- ローカルファイル（MP4, M4A, WAV, MP3など）
- YouTube URL（`youtube.com` または `youtu.be`）

---

## Step 1: 依存関係の確認とインストール

```bash
# faster-whisper（未インストールの場合のみ）
uv pip install faster-whisper

# yt-dlp（YouTube URLの場合のみ）
uv tool install yt-dlp
```

インストール済みか確認してから実行（`uv pip show faster-whisper` で確認可）。

---

## Step 2: YouTube URLの場合はダウンロード

YouTube URLが入力された場合、まず動画をダウンロードする。

```bash
# 保存先ディレクトリに移動してからダウンロード
cd "<保存先ディレクトリ>"
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" \
  -o "%(title)s.%(ext)s" "<YouTube URL>"
```

**注意事項:**
- 「No supported JavaScript runtime」警告は無視してOK（動作する）
- ファイル名はYouTubeのタイトルが自動設定される
- ダウンロード完了後、保存されたMP4パスを取得する

---

## Step 3: 文字起こしスクリプトを `tmp/` に作成して実行

### スクリプトテンプレート

```python
import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from faster_whisper import WhisperModel

input_file = r"<入力ファイルの絶対パス>"
output_file = r"<出力ファイルの絶対パス>"

print(f"文字起こし開始: {input_file}")
sys.stdout.flush()

model = WhisperModel("large-v3", device="cpu", compute_type="int8")
print("モデルロード完了")
sys.stdout.flush()

segments, info = model.transcribe(
    input_file,
    language="ja",
    beam_size=5,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500),
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
```

### 出力ファイルの命名規則

| 入力 | 出力先 |
|------|--------|
| `/path/to/会議録.mp4` | `/path/to/会議録_トランスクリプト.txt` |
| YouTube DL → `/path/to/タイトル.mp4` | `/path/to/タイトル_トランスクリプト.txt` |

出力は**入力ファイルと同じフォルダ**に保存する（`tmp/` ではなく元のフォルダ）。

### 実行（バックグラウンド）

スクリプトは `tmp/transcribe_<識別名>.py` として保存し、バックグラウンドで実行する。
ログは `tmp/transcribe_<識別名>_log.txt` に保存。

```bash
uv run python tmp/transcribe_<識別名>.py > tmp/transcribe_<識別名>_log.txt 2>&1
```

`run_in_background=true` で実行し、完了通知を待つ。

---

## Step 4: 完了後の処理

完了通知が届いたら出力ファイルを確認し、ユーザーに以下を報告する:
- 出力ファイルのパス
- 動画の総時間
- 最初の数行のプレビュー（内容の確認）

---

## 処理時間の目安（CPU only）

| 動画時間 | 処理時間（単独実行） |
|----------|---------------------|
| 〜30分 | 15〜30分 |
| 60分 | 30〜60分 |
| 102分 | 1〜2時間 |

- 初回実行時: モデル（large-v3, 約1.5GB）のダウンロードが発生（数分追加）
- 複数同時実行: 処理時間が倍増するため、可能なら1本ずつ推奨

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `faster-whisper not found` | `uv pip install faster-whisper` |
| `yt-dlp not found` | `uv tool install yt-dlp` |
| ファイル名が文字化け | ログファイルを確認（実際のファイルは正常なことが多い） |
| JS runtime警告 | 無視してOK（ダウンロードは動作する） |
