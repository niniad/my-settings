"""
validate.py - schedule-planner YAML検証スクリプト

使用方法:
  python validate.py [--dir <project_dir>]

  --dir: schedule.yaml等が置かれたディレクトリ（デフォルト: スクリプトの親ディレクトリ）
"""
import sys
import os
import yaml
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

def load_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)

def time_to_minutes(t):
    h, m = map(int, t.split(':'))
    return h * 60 + m

def check_circular(task_id, deps_map, visited, stack):
    visited.add(task_id)
    stack.add(task_id)
    for dep in deps_map.get(task_id, []):
        if dep not in visited:
            if check_circular(dep, deps_map, visited, stack):
                return True
        elif dep in stack:
            return True
    stack.discard(task_id)
    return False

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default=None)
    args = parser.parse_args()

    base = Path(args.dir) if args.dir else Path(__file__).parent.parent
    errors = []
    warnings = []

    # YAMLファイル読み込み
    try:
        settings = load_yaml(base / 'settings.yaml')
    except Exception as e:
        errors.append(f'settings.yaml 読み込みエラー: {e}')
        settings = {}

    try:
        members_data = load_yaml(base / 'members.yaml')
        members = {m['id']: m for m in members_data.get('members', [])}
    except Exception as e:
        errors.append(f'members.yaml 読み込みエラー: {e}')
        members = {}

    try:
        constraints_data = load_yaml(base / 'constraints.yaml')
        constraints = constraints_data.get('constraints', {})
    except Exception as e:
        errors.append(f'constraints.yaml 読み込みエラー: {e}')
        constraints = {}

    try:
        schedule_data = load_yaml(base / 'schedule.yaml')
        tasks = schedule_data.get('tasks', [])
    except Exception as e:
        errors.append(f'schedule.yaml 読み込みエラー: {e}')
        tasks = []

    task_ids = {t['id'] for t in tasks if 'id' in t}
    deps_map = {}
    daily_minutes = defaultdict(lambda: defaultdict(int))

    for task in tasks:
        tid = task.get('id', '(id未定義)')

        # 必須フィールド確認
        for field in ['id', 'name', 'assignee', 'duration_min']:
            if field not in task:
                errors.append(f'タスク {tid}: 必須フィールド "{field}" が未定義')

        # 担当者存在確認
        assignee = task.get('assignee')
        if assignee and members and assignee not in members:
            errors.append(f'タスク {tid}: 担当者 "{assignee}" が members.yaml に存在しない')

        # depends_on 参照確認
        depends_on = task.get('depends_on', [])
        deps_map[tid] = depends_on
        for dep in depends_on:
            if dep not in task_ids:
                errors.append(f'タスク {tid}: depends_on "{dep}" が存在しないタスクIDを参照している')

        # 勤務時間・曜日制約との整合性
        if assignee and assignee in members:
            member = members[assignee]
            wh = member.get('working_hours', settings.get('working_hours', {}))
            wh_start = time_to_minutes(wh.get('start', '09:00'))
            wh_end = time_to_minutes(wh.get('end', '18:00'))

            task_start_str = task.get('start')
            duration = task.get('duration_min', 0)
            weekdays = task.get('weekdays', [])

            unavailable = set(member.get('unavailable_days', []))
            available = set(member.get('available_days', ['mon','tue','wed','thu','fri']))

            for wd in weekdays:
                if wd in unavailable:
                    errors.append(f'タスク {tid}: 担当者 {assignee} は {wd} が不在日')
                if member.get('available_days') and wd not in available:
                    errors.append(f'タスク {tid}: 担当者 {assignee} は {wd} が勤務対象外')

                if task_start_str:
                    t_start = time_to_minutes(task_start_str)
                    t_end = t_start + duration
                    if t_start < wh_start:
                        warnings.append(f'タスク {tid} ({wd}): 開始時刻 {task_start_str} が勤務開始前')
                    if t_end > wh_end:
                        warnings.append(f'タスク {tid} ({wd}): 終了時刻が勤務終了後')

                # max_daily_minutes 累計
                daily_minutes[assignee][wd] += duration

    # 循環依存チェック
    visited = set()
    for tid in task_ids:
        if tid not in visited:
            if check_circular(tid, deps_map, visited, set()):
                errors.append(f'循環依存が検出された（タスク {tid} 周辺）')

    # max_daily_minutes チェック
    max_daily = constraints.get('max_daily_minutes', {})
    for assignee, days in daily_minutes.items():
        limit = max_daily.get(assignee)
        if limit:
            for wd, total in days.items():
                if total > limit:
                    warnings.append(
                        f'{assignee} の {wd} 合計稼働: {total}分 > 上限 {limit}分'
                    )

    # 結果出力
    print('=' * 50)
    print('YAML検証結果')
    print('=' * 50)
    if errors:
        print(f'\n❌ エラー ({len(errors)}件):')
        for e in errors:
            print(f'  - {e}')
    else:
        print('\n✅ エラーなし')

    if warnings:
        print(f'\n⚠️  警告 ({len(warnings)}件):')
        for w in warnings:
            print(f'  - {w}')
    else:
        print('⚠️  警告なし')

    print()
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
