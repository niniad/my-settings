"""
render_dependency_graph.py - タスク依存関係グラフ（Mermaid graph LR）生成

使用方法:
  python render_dependency_graph.py [--dir <project_dir>]

出力: <dir>/outputs/dependency_graph.md
"""
import sys
import yaml
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

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

    schedule_data = load_yaml(base / 'schedule.yaml')
    tasks = schedule_data.get('tasks', [])

    lines = ['# タスク依存関係グラフ', '', '```mermaid', 'graph LR']

    # ノード定義
    for task in tasks:
        tid = task['id']
        name = task.get('name', tid)
        assignee = task.get('assignee', '')
        lines.append(f'  {tid}["{name}<br/>担当: {assignee}"]')

    lines.append('')

    # エッジ定義
    has_deps = False
    for task in tasks:
        tid = task['id']
        for dep in task.get('depends_on', []):
            lines.append(f'  {dep} --> {tid}')
            has_deps = True

    if not has_deps:
        lines.append('  %% 依存関係なし')

    lines.append('```')
    lines.append('')

    out_path = out_dir / 'dependency_graph.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'✅ 依存関係グラフ生成: {out_path}')

if __name__ == '__main__':
    main()
