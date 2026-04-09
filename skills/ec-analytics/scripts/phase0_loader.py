# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, subprocess, urllib.request, urllib.parse

def get_token():
    result = subprocess.run(
        ['powershell.exe', '-Command',
         "& 'C:\\Users\\ninni\\AppData\\Local\\Google\\Cloud SDK\\google-cloud-sdk\\bin\\gcloud.cmd' secrets versions access latest --secret=NOCODB_API_TOKEN --project=main-project-477501"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

token = get_token()
base_url = "http://localhost:8080/api/v1"
headers = {"xc-token": token, "Content-Type": "application/json"}

def noco_get(path, params):
    url = base_url + path + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# EC_Data_Insights (mf8dwtphhlqflkn) - Status=有効
insights = noco_get("/db/data/noco/pbvdkr5cvkj4n2e/mf8dwtphhlqflkn", {
    "where": "(Status,eq,有効)",
    "limit": "50"
})
print("=== EC_Data_Insights (Status=有効) ===")
for r in insights.get('list', []):
    print(f"[{r.get('Category','')}] {r.get('Title','')} ({r.get('Date','')})")
    if r.get('Summary'):
        print(f"  {r.get('Summary','')[:150]}")

print()

# PDCA_Actions (m81djzj3lg2n0u9) - Category=EC, Status≠完了,中止
actions = noco_get("/db/data/noco/pbvdkr5cvkj4n2e/m81djzj3lg2n0u9", {
    "where": "(Category,eq,EC)~and(Status,neq,完了)~and(Status,neq,中止)",
    "limit": "50"
})
print("=== PDCA_Actions (EC・進行中) ===")
for r in actions.get('list', []):
    print(f"[{r.get('Status','')}] {r.get('Title','')} (期日:{r.get('DueDate','')})")
    if r.get('Detail'):
        print(f"  {r.get('Detail','')[:150]}")
