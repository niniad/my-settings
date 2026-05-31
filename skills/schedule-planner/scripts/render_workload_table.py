"""
render_workload_table.py - 担当者×曜日の負荷テーブル生成

使用方法:
  python render_workload_table.py [--dir <project_dir>]

出力: <dir>/outputs/workload_table.md
"""
import sys
import yaml
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DAYS = ['mon', 'tue', 'wed', 'thu', 'fri']
DAY_LABEL = {'mon': '月', 'tue': '火', 'wed': '水', 'thu': '木', 'fri': '金'}

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
        print('ERROR: outputs/schedule_result.yaml が見つかりません。')
        sys.exit(1)

    result = load_yaml(result_path)
    members_data = load_yaml(base / 'members.yaml')
    constraints_data = load_yaml(base / 'constraints.yaml')

    members = {m['id']: m['name'] for m in members_data.get('members', [])}
    constraints = constraints_data.get('constraints', {})
    max_daily = constraints.get('max_daily_minutes', {})

    tasks = result.get('tasks', [])

    # 担当者×曜日の稼働分数を集計
    workload = defaultdict(lambda: defaultdict(int))
    task_details = defaultdict(lambda: defaultdict(list))

    for t in tasks:
        assignee = t['assignee']
        day = t.get('weekday', 'mon')
        duration = _calc_duration(t['start'], t['end'])
        workload[assignee][day] += duration
        task_details[assignee][day].append(t.get('name', t['id']))

    # テーブル生成
    lines = ['# 担当者別稼働テーブル', '']

    all_assignees = list(members.keys()) if members else list(workload.keys())

    # ヘッダー
    header = '| 担当者 | ' + ' | '.join(DAY_LABEL.get(d, d) for d in DAYS) + ' | 週計 |'
    separator = '|' + '---|' * (len(DAYS) + 2)
    lines.append(header)
    lines.append(separator)

    for assignee in all_assignees:
        name = members.get(assignee, assignee)
        limit = max_daily.get(assignee)
        row_vals = []
        week_total = 0
        for day in DAYS:
            mins = workload[assignee][day]
            week_total += mins
            cell = f'{mins}分'
            if limit and mins > limit:
                cell += ' ⚠️超過'
            elif limit and mins > 0:
                pct = int(mins / limit * 100)
                cell += f' ({pct}%)'
            row_vals.append(cell)
        row = f'| {name} | ' + ' | '.join(row_vals) + f' | {week_total}分 |'
        lines.append(row)

    lines.append('')

    # 上限との比較
    if max_daily:
        lines.append('## 上限設定')
        lines.append('')
        for assignee, limit in max_daily.items():
            name = members.get(assignee, assignee)
            lines.append(f'- **{name}**: 1日最大 {limit}分')
        lines.append('')

    # タスク内訳
    lines.append('## タスク内訳')
    lines.append('')
    for assignee in all_assignees:
        name = members.get(assignee, assignee)
        lines.append(f'### {name}')
        for day in DAYS:
            tlist = task_details[assignee][day]
            if tlist:
                day_label = DAY_LABEL.get(day, day)
                lines.append(f'- **{day_label}曜**: {", ".join(tlist)}（{workload[assignee][day]}分）')
        lines.append('')

    out_path = out_dir / 'workload_table.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'✅ 負荷テーブル生成: {out_path}')

def _calc_duration(start, end):
    def to_m(t):
        h, m = map(int, t.split(':'))
        return h * 60 + m
    return to_m(end) - to_m(start)

if __name__ == '__main__':
    main()
