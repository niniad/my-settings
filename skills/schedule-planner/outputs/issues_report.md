# Issues Report

## 検出事項

- tanaka は data_collect の開始時刻 (09:30) が勤務開始時刻 (10:00) より前
  → data_collect の start を "10:00" に変更するか、tanaka の勤務時間を見直すことを推奨
- report_review は start が未定義のため、depends_on (data_collect) の終了後に自動配置される
  → OR-Tools最適化（optimize: true）を使用すると自動で最適時刻が割り当てられる
- tanaka の金曜は unavailable_days に指定されているが、割り当てタスクなし（問題なし）
