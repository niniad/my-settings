"""NocoDB backup with logarithmic retention.

Retention slots (max 9 files, ~3.6GB):
  Daily  : today, -1d, -2d          (3 files)
  Weekly : -7d, -14d, -21d          (3 files, ±2d tolerance)
  Monthly: -30d, -60d, -90d         (3 files, ±3d tolerance)

Runs daily via Task Scheduler. Each run:
  1. sqlite3 .backup to Google Drive
  2. Scan existing backups
  3. Keep files that fill a retention slot, delete the rest
"""

import subprocess
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = Path(r"C:\Users\ninni\nocodb\noco.db")
BACKUP_DIR = Path(r"G:\マイドライブ\backup\nocodb")
LOG_FILE = Path(r"C:\Users\ninni\nocodb\backup.log")

# Retention targets: (days_ago, tolerance_days)
RETENTION = [
    (0, 0), (1, 0), (2, 0),       # daily
    (7, 2), (14, 2), (21, 2),     # weekly
    (30, 3), (60, 3), (90, 3),    # monthly
]

FILENAME_RE = re.compile(r"^noco_?(?:backup_?)?(\d{8})(?:_(\d{4}))?\.db$")


def log(msg: str):
    line = f"[{datetime.now():%Y-%m-%d %H:%M}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def create_backup() -> Path | None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    dest = BACKUP_DIR / f"noco_{stamp}.db"
    result = subprocess.run(
        ["sqlite3", str(DB_PATH), f".backup '{dest}'"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and dest.exists():
        size_mb = dest.stat().st_size / (1024 * 1024)
        log(f"OK backup {dest.name} ({size_mb:.0f}MB)")
        return dest
    else:
        log(f"ERROR backup failed: {result.stderr.strip()}")
        return None


def parse_backup_date(name: str) -> datetime | None:
    m = FILENAME_RE.match(name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y%m%d")
    except ValueError:
        return None


def apply_retention():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Collect all backup files with their dates
    backups: list[tuple[Path, datetime]] = []
    orphans: list[Path] = []  # files without parseable date
    for f in BACKUP_DIR.glob("noco*.db"):
        dt = parse_backup_date(f.name)
        if dt:
            backups.append((f, dt))
        else:
            orphans.append(f)

    # Sort newest first (prefer newest when multiple match a slot)
    backups.sort(key=lambda x: x[1], reverse=True)

    # Assign files to retention slots
    keep: set[Path] = set()
    filled_slots: set[int] = set()

    for path, dt in backups:
        age = (today - dt).days
        for i, (target, tol) in enumerate(RETENTION):
            if i not in filled_slots and abs(age - target) <= tol:
                keep.add(path)
                filled_slots.add(i)
                break

    # Delete files not in any slot
    deleted = 0
    for path, dt in backups:
        if path not in keep:
            path.unlink()
            deleted += 1
    # Delete files without parseable dates (legacy naming)
    for path in orphans:
        path.unlink()
        deleted += 1

    log(f"Retention: {len(keep)} kept, {deleted} deleted, "
        f"{len(filled_slots)}/{len(RETENTION)} slots filled")


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = create_backup()
    if backup:
        apply_retention()


if __name__ == "__main__":
    main()
