"""
render_html.py - HTMLダッシュボード生成

使用方法:
  python render_html.py [--dir <project_dir>]

出力: <dir>/outputs/dashboard.html
"""
import sys
import yaml
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

DAYS = ['mon', 'tue', 'wed', 'thu', 'fri']
DAY_LABEL = {'mon': '月曜', 'tue': '火曜', 'wed': '水曜', 'thu': '木曜', 'fri': '金曜'}
COLORS = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948']

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
    settings = load_yaml(base / 'settings.yaml')

    members = {m['id']: m['name'] for m in members_data.get('members', [])}
    project_name = settings.get('project', {}).get('name', 'Team Schedule')
    tasks = result.get('tasks', [])

    assignees = list(members.keys()) if members else list({t['assignee'] for t in tasks})
    assignee_color = {a: COLORS[i % len(COLORS)] for i, a in enumerate(assignees)}

    # 曜日ごとのテーブル生成
    day_sections = ''
    used_days = [d for d in DAYS if any(t.get('weekday') == d for t in tasks)]

    for day in used_days:
        day_label = DAY_LABEL.get(day, day)
        day_tasks = sorted(
            [t for t in tasks if t.get('weekday') == day],
            key=lambda x: x['start']
        )
        rows = ''
        for t in day_tasks:
            assignee = t['assignee']
            member_name = members.get(assignee, assignee)
            color = assignee_color.get(assignee, '#999')
            rows += f'''
            <tr>
              <td style="color:{color};font-weight:bold">{member_name}</td>
              <td>{t.get("name", t["id"])}</td>
              <td>{t["start"]}</td>
              <td>{t["end"]}</td>
              <td>{_calc_duration(t["start"], t["end"])}分</td>
            </tr>'''
        day_sections += f'''
        <h2>{day_label}</h2>
        <table>
          <thead><tr><th>担当者</th><th>タスク</th><th>開始</th><th>終了</th><th>時間</th></tr></thead>
          <tbody>{rows}
          </tbody>
        </table>'''

    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{project_name}</title>
  <style>
    body {{ font-family: 'Hiragino Sans', 'Meiryo', sans-serif; margin: 2rem; background: #f9f9f9; }}
    h1 {{ color: #333; border-bottom: 3px solid #4e79a7; padding-bottom: 0.5rem; }}
    h2 {{ color: #555; margin-top: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1rem; }}
    th {{ background: #4e79a7; color: white; padding: 0.75rem 1rem; text-align: left; }}
    td {{ padding: 0.6rem 1rem; border-bottom: 1px solid #eee; }}
    tr:hover {{ background: #f0f7ff; }}
    .legend {{ display: flex; gap: 1rem; margin: 1rem 0; flex-wrap: wrap; }}
    .legend-item {{ display: flex; align-items: center; gap: 0.4rem; }}
    .legend-color {{ width: 16px; height: 16px; border-radius: 3px; }}
  </style>
</head>
<body>
  <h1>📅 {project_name}</h1>
  <div class="legend">
    {''.join(f'<div class="legend-item"><div class="legend-color" style="background:{assignee_color.get(a,"#999")}"></div><span>{members.get(a,a)}</span></div>' for a in assignees)}
  </div>
  {day_sections}
</body>
</html>'''

    out_path = out_dir / 'dashboard.html'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'✅ HTMLダッシュボード生成: {out_path}')

def _calc_duration(start, end):
    def to_m(t):
        h, m = map(int, t.split(':'))
        return h * 60 + m
    return to_m(end) - to_m(start)

if __name__ == '__main__':
    main()
