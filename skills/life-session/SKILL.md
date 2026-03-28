---
name: life-session
description: ライフセッション（ヒアリング・相談）の運用スキル。lifeプロジェクトから呼び出される。トリガー：「セッション開始」「スタート」「相談したい」「ヒアリング」。
---

# life-session スキル

ライフセッション（ヒアリング・相談）の運用手順。
`life` プロジェクトから呼び出される。

## トリガー

「セッション開始」「スタート」「相談したい」「ヒアリング」

## セッションモード

| モード | 起動条件 | 読み込むデータ |
|--------|---------|--------------|
| **ヒアリングモード** | 「スタート」等、特定テーマなし | profile-core.json のみ |
| **相談モード** | 「〜について相談したい」等 | profile-core.json + 関連ドメイン |

## セッション開始手順（2回目以降）

1. `docs/profile-core.json` を Read ツールで読み込む（**profile.json は読まない**）
2. Todoist @life タスクを `todoist_task_get` (filter: `#マイタスク & @life`) で取得し、優先タスクと進捗を把握する
3. **データリフレッシュ**（profile/Todoist読み込みと並行して実行可）:
   - **Chrome履歴**: `uv run --with requests python scripts/sync_chrome_history.py` を実行（自動同期）
   - **Googleカレンダー**: `gcal_list_events` MCPツールで過去2週間+今後2週間のイベントを取得（NocoDB更新不要、セッション中に直接利用）
   - **Gmail**: 社会的接触の分析が必要な場合のみ `gmail_search_messages` MCPツールで直近メールを取得（常時取得は不要）
   - **Apple Health / YouTube**: `sqlite3 "C:/Users/ninni/nocodb/noco.db" "SELECT MAX(date) FROM 'nc_mtf3___Appleヘルスケア';"` で最終同期日を確認。2週間以上古ければユーザーに通知（自動化は今後対応予定）
4. ユーザーの最初のメッセージからモードを判断:
   - **ヒアリング継続**: `open_questions` と `active_hypotheses` を確認し、未収集データを特定
   - **相談モード**: 下記「ドメインfacts取得コマンド」で関連ドメインのみ抽出してから応答
   - **データ分析**: NocoDB SQLite を直接クエリ（`data-sources.md` は読まない）
5. **分析結果と新たな仮説をユーザーに共有してから対話開始**

## ドメインfacts取得コマンド

相談テーマが明確になったら、以下のコマンドで該当ドメインのみ抽出する。
**profile.json 全体は読まない。**

```python
# 単一ドメインの取得
python3 -c "
import sys, json; sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('docs/profile.json', encoding='utf-8'))
print(json.dumps(d['domains']['DOMAIN_KEY'], ensure_ascii=False, indent=2))
"

# 複数ドメインの取得（例: 仕事・経済 + 意味・目的）
python3 -c "
import sys, json; sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('docs/profile.json', encoding='utf-8'))
for k in ['E_work_finance', 'G_meaning_purpose']:
    print(json.dumps(d['domains'][k], ensure_ascii=False, indent=2))
"
```

### ドメインキー一覧

| キー | 内容 | 主な相談テーマ |
|------|------|--------------|
| `A_mental_health` | 精神的健康・睡眠 | 体調、うつ、疲労 |
| `B_relationships` | 人間関係・夫婦・社会的接触 | 夫婦関係、孤立、友人 |
| `C_personality` | 性格・Big Five | 自己理解、強み |
| `D_physical_health` | 身体的健康・運動 | 健康診断、体のこと |
| `E_work_finance` | 仕事・収入・資産 | EC事業、キャリア、家計 |
| `F_time_structure` | 時間・生活構造・通勤 | 時間管理、余暇 |
| `G_meaning_purpose` | 意味・目的・将来ビジョン | 人生相談、将来、やりたいこと |
| `H_life_history` | 人生史・トラウマ・レジリエンス | 過去の経験 |
| `I_life_stage` | 年齢・ライフステージ | ライフイベント |
| `J_behavior_patterns` | 消費・デジタル行動・利他 | お金の使い方、習慣 |
| `K_environment` | 居住環境・自然 | 引越し、環境 |

## profile.json への fact 追加テンプレート

新しい事実を記録する場合は以下のフォーマットに従う:

```json
{
  "id": "fact_XXX",
  "content": "事実の内容",
  "source_grade": "A〜E",
  "confidence": 1-5,
  "source": "データソース",
  "date_recorded": "YYYY-MM-DD",
  "verification_notes": "裏付けの詳細"
}
```

信頼性格付けの詳細は `docs/admiralty-code.md` を Read して参照する。

## セッション終了手順

1. 新たに確認・発見した事実をすべて `docs/profile.json` に反映する
2. `open_questions`（未解決の問い）を更新する
3. `hypotheses`（仮説）を更新する
4. `meta.next_session_priorities` を更新する
5. **`uv run python scripts/generate_core.py` を実行して `profile-core.json` を再生成する**
6. プライベート（Life/Work/Finance）の完了アクションは NocoDB に記録（nocodb スキル経由）

> **EC状況確認**: EC事業のアクション管理・KPIレビューは `ec-analytics` スキルに委譲。
> EC関連の質問が出た場合は ec-analytics スキルを呼び出すこと。
