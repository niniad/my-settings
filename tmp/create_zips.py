import sys
sys.stdout.reconfigure(encoding='utf-8')
import zipfile
import os
from pathlib import Path

skills_dir = Path("C:/Users/ninni/projects/my-settings/skills")
dist_dir = Path("C:/Users/ninni/projects/my-settings/dist")
dist_dir.mkdir(exist_ok=True)

skip = set()  # 全スキルを対象にする

created = []
skipped = []

for skill_dir in sorted(skills_dir.iterdir()):
    if not skill_dir.is_dir():
        continue
    name = skill_dir.name
    if name in skip:
        skipped.append(name)
        continue

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        skipped.append(name)
        continue

    zip_path = dist_dir / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in skill_dir.rglob("*"):
            if file.is_file():
                arcname = Path(name) / file.relative_to(skill_dir)
                zf.write(file, arcname)

    size_kb = zip_path.stat().st_size // 1024
    print(f"  OK: {name}.zip ({size_kb} KB)")
    created.append(name)

print(f"\n計 {len(created)} 件作成, {len(skipped)} 件スキップ: {skipped}")
