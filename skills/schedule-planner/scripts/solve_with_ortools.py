"""
solve_with_ortools.py - OR-Tools CP-SATによるスケジュール最適化

使用方法:
  python solve_with_ortools.py [--dir <project_dir>]

  --dir: YAMLが置かれたディレクトリ（デフォルト: スクリプトの親ディレクトリ）

出力: <dir>/outputs/schedule_result.yaml
"""
import sys
import os
import yaml
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

try:
    from ortools.sat.python import cp_model
except ImportError:
    print('ERROR: OR-Tools がインストールされていません。')
    print('  pip install ortools')
    sys.exit(1)

def load_yaml(path):
    with open(path, encoding='utf-8') as f:
        return yaml.safe_load(f)

def time_to_minutes(t):
    h, m = map(int, t.split(':'))
    return h * 60 + m

def minutes_to_time(m):
    return f'{m // 60:02d}:{m % 60:02d}'

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default=None)
    args = parser.parse_args()

    base = Path(args.dir) if args.dir else Path(__file__).parent.parent
    out_dir = base / 'outputs'
    out_dir.mkdir(exist_ok=True)

    settings = load_yaml(base / 'settings.yaml')
    members_data = load_yaml(base / 'members.yaml')
    constraints_data = load_yaml(base / 'constraints.yaml')
    schedule_data = load_yaml(base / 'schedule.yaml')

    members = {m['id']: m for m in members_data.get('members', [])}
    constraints = constraints_data.get('constraints', {})
    tasks = schedule_data.get('tasks', [])

    wh_global_start = time_to_minutes(settings.get('working_hours', {}).get('start', '09:00'))
    wh_global_end = time_to_minutes(settings.get('working_hours', {}).get('end', '18:00'))
    lb_start = time_to_minutes(settings.get('lunch_break', {}).get('start', '12:00'))
    lb_end = time_to_minutes(settings.get('lunch_break', {}).get('end', '13:00'))

    task_map = {t['id']: t for t in tasks}
    DAYS = ['mon', 'tue', 'wed', 'thu', 'fri']
    horizon = wh_global_end  # 最大時刻（分）

    model = cp_model.CpModel()
    results = []

    # タスク×曜日の組み合わせごとに変数を作成
    intervals = {}  # (task_id, day) -> (start_var, end_var, interval_var)

    for task in tasks:
        tid = task['id']
        duration = task['duration_min']
        assignee = task['assignee']
        weekdays = task.get('weekdays', DAYS)
        member = members.get(assignee, {})
        wh = member.get('working_hours', settings.get('working_hours', {}))
        wh_start = time_to_minutes(wh.get('start', '09:00'))
        wh_end = time_to_minutes(wh.get('end', '18:00'))

        for day in weekdays:
            start_var = model.NewIntVar(wh_start, wh_end - duration, f'start_{tid}_{day}')
            end_var = model.NewIntVar(wh_start + duration, wh_end, f'end_{tid}_{day}')
            interval_var = model.NewIntervalVar(start_var, duration, end_var, f'interval_{tid}_{day}')
            intervals[(tid, day)] = (start_var, end_var, interval_var)

            # 勤務時間内制約
            model.Add(start_var >= wh_start)
            model.Add(end_var <= wh_end)

            # 昼休み回避（enforce_lunch_break）
            if constraints.get('enforce_lunch_break'):
                before_lunch = model.NewBoolVar(f'before_lunch_{tid}_{day}')
                model.Add(end_var <= lb_start).OnlyEnforceIf(before_lunch)
                model.Add(start_var >= lb_end).OnlyEnforceIf(before_lunch.Not())

    # depends_on制約
    if constraints.get('dependency_must_finish'):
        for task in tasks:
            tid = task['id']
            weekdays = task.get('weekdays', DAYS)
            for dep_id in task.get('depends_on', []):
                dep_task = task_map.get(dep_id)
                if not dep_task:
                    continue
                dep_weekdays = dep_task.get('weekdays', DAYS)
                for day in weekdays:
                    if day in dep_weekdays and (tid, day) in intervals and (dep_id, day) in intervals:
                        _, dep_end, _ = intervals[(dep_id, day)]
                        start_var, _, _ = intervals[(tid, day)]
                        model.Add(start_var >= dep_end)

    # no_overlap制約（同担当者・同曜日）
    if constraints.get('no_overlap'):
        from collections import defaultdict
        assignee_day_intervals = defaultdict(list)
        for task in tasks:
            tid = task['id']
            assignee = task['assignee']
            weekdays = task.get('weekdays', DAYS)
            for day in weekdays:
                if (tid, day) in intervals:
                    _, _, interval_var = intervals[(tid, day)]
                    assignee_day_intervals[(assignee, day)].append(interval_var)

        for (assignee, day), ivars in assignee_day_intervals.items():
            if len(ivars) > 1:
                model.AddNoOverlap(ivars)

    # max_daily_minutes制約
    max_daily = constraints.get('max_daily_minutes', {})
    for assignee, limit in max_daily.items():
        for day in DAYS:
            assignee_tasks = [
                t for t in tasks
                if t['assignee'] == assignee and day in t.get('weekdays', DAYS)
                and (t['id'], day) in intervals
            ]
            if assignee_tasks:
                total_duration = sum(t['duration_min'] for t in assignee_tasks)
                if total_duration > limit:
                    print(f'警告: {assignee} の {day} 合計 {total_duration}分 > 上限 {limit}分（制約追加）')

    # 解を求める
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print('✅ 解が見つかりました')
        result_tasks = []
        for task in tasks:
            tid = task['id']
            weekdays = task.get('weekdays', DAYS)
            for day in weekdays:
                if (tid, day) in intervals:
                    start_var, end_var, _ = intervals[(tid, day)]
                    s = solver.Value(start_var)
                    e = solver.Value(end_var)
                    result_tasks.append({
                        'id': tid,
                        'name': task.get('name', tid),
                        'assignee': task['assignee'],
                        'weekday': day,
                        'start': minutes_to_time(s),
                        'end': minutes_to_time(e),
                    })

        out_path = out_dir / 'schedule_result.yaml'
        with open(out_path, 'w', encoding='utf-8') as f:
            yaml.dump({'tasks': result_tasks}, f, allow_unicode=True, default_flow_style=False)
        print(f'出力: {out_path}')
    else:
        print('❌ 解が見つかりませんでした。制約条件を確認してください。')
        sys.exit(1)

if __name__ == '__main__':
    main()
