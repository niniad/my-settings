"""
render_mermaid.py - Mermaid Ganttチャート生成

使用方法:
  python render_mermaid.py [--dir <project_dir>]

出力: <dir>/outputs/gantt.md
"""
import sys
import yaml
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DAY_LABEL = {
    'mon': '月曜', 'tue': '火曜', 'wed': '水曜',
    'thu': '木曜', 'fri': '金曜', 'sat': '土曜', 'sun': '日曜'
}

def load_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default=None)
    args = parser.parse_args()

    base = Path(args.dir) if args.dir else Path(__file__).parent.parent
    out_dir = base / 'outputs'
    out_dir.mkdir(exist_ok=True)

    result_path = out_dir / 'schedule_result.yaml'
    if not result_path.exists():
        print('ERROR: outputs/schedule_result.yaml が見つかりません。先にスケジュールを生成してください。')
        sys.exit(1)

    result = load_yaml(result_path)
    members_data = load_yaml(base / 'members.yaml')
    members = {m['id']: m['name'] for m in members_data.get('members', [])}

    tasks = result.get('tasks', [])

    # 曜日ごとにチャートを生成
    day_tasks = defaultdict(list)
    for t in tasks:
        day_tasks[t.get('weekday', 'mon')].append(t)

    days_order = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    used_days = [d for d in days_order if d in day_tasks]

    lines = []

    for day in used_days:
        day_name = DAY_LABEL.get(day, day)
        lines.append(f'## {day_name}')
        lines.append('')
        lines.append('```mermaid')
        lines.append('gantt')
        lines.append(f'title {day_name}のスケジュール')
        lines.append('dateFormat HH:mm')
        lines.append('axisFormat %H:%M')
        lines.append('')

        # 担当者ごとにセクション
        assignee_tasks = defaultdict(list)
        for t in day_tasks[day]:
            assignee_tasks[t['assignee']].append(t)

        for assignee, atasks in assignee_tasks.items():
            member_name = members.get(assignee, assignee)
            lines.append(f'section {member_name}')
            for t in sorted(atasks, key=lambda x: x['start']):
                name = t.get('name', t['id'])
                start = t['start']
                duration = _calc_duration(t['start'], t['end'])
                lines.append(f'{name} :{start}, {duration}m')
            lines.append('')

        lines.append('```')
        lines.append('')

    out_path = out_dir / 'gantt.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'✅ Mermaid Gantt生成: {out_path}')

    # チャットへの直接表示用にも出力
    print('\n--- Ganttプレビュー（最初の曜日）---')
    if used_days:
        day = used_days[0]
        day_name = DAY_LABEL.get(day, day)
        print(f'\n**{day_name}**\n')
        print('```mermaid')
        print('gantt')
        print(f'title {day_name}のスケジュール')
        print('dateFormat HH:mm')
        print('axisFormat %H:%M')
        print()
        assignee_tasks = defaultdict(list)
        for t in day_tasks[day]:
            assignee_tasks[t['assignee']].append(t)
        for assignee, atasks in assignee_tasks.items():
            member_name = members.get(assignee, assignee)
            print(f'section {member_name}')
            for t in sorted(atasks, key=lambda x: x['start']):
                name = t.get('name', t['id'])
                start = t['start']
                duration = _calc_duration(t['start'], t['end'])
                print(f'{name} :{start}, {duration}m')
            print()
        print('```')

def _calc_duration(start, end):
    def to_m(t):
        h, m = map(int, t.split(':'))
        return h * 60 + m
    return to_m(end) - to_m(start)

if __name__ == '__main__':
    main()
