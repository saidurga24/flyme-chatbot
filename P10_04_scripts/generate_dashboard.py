import subprocess
import json
import os

APP_ID = "431443fa-1b40-4334-ac69-6e8916ed7202"

def query_az(kql):
    cmd = f'az monitor app-insights query --app {APP_ID} --analytics-query "{kql}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error running AZ CLI:", result.stderr)
        return []
    
    try:
        data = json.loads(result.stdout)
        return data['tables'][0]['rows']
    except Exception as e:
        print("Failed to parse JSON:", e)
        return []

print("Fetching Intent Distribution...")
intents = query_az('''
traces 
| extend intent = tostring(parse_json(tostring(customDimensions)).intent) 
| where isnotempty(intent) 
| summarize count() by intent
''')

print("Fetching Event types...")
events = query_az('''
traces 
| extend message = tostring(message)
| where message startswith 'Event:' 
| summarize count() by message
''')

print("Fetching Exception Events...")
errors = query_az('''
traces 
| extend message = tostring(message)
| where message startswith 'Exception:'
| summarize count() by message
''')

dashboard_path = os.path.join(os.path.dirname(__file__), "../P10_02_monitoring_tool/Automated_Dashboard.md")

with open(dashboard_path, "w") as f:
    f.write("# Production Monitoring Dashboard\n\n")
    f.write("> This dashboard was automatically generated using Azure Application Insights telemetry data.\n\n")
    
    f.write("## 1. Intent Distribution (CLU)\n")
    f.write("This table shows how frequently users are hitting specific intents.\n\n")
    f.write("| Intent | Count |\n|---|---|\n")
    if intents:
        for row in intents:
            f.write(f"| {row[0] or 'Unknown'} | {row[1]} |\n")
    else:
        f.write("| (No data yet) | 0 |\n")
        
    f.write("\n## 2. Event Analytics\n")
    f.write("This table tracks successful bookings vs generic dialog events.\n\n")
    f.write("| Event | Count |\n|---|---|\n")
    if events:
        for row in events:
            f.write(f"| {row[0]} | {row[1]} |\n")
    else:
        f.write("| (No data yet) | 0 |\n")

    f.write("\n## 3. Error Rates\n")
    f.write("Tracks Python errors or Azure Cognitive Service failures.\n\n")
    f.write("| Error Message | Occurrences |\n|---|---|\n")
    if errors:
        for row in errors:
            f.write(f"| `{row[0]}` | {row[1]} |\n")
    else:
        f.write("| No Errors Detected | 0 |\n")
        
print("Dashboard generated successfully at: " + dashboard_path)
