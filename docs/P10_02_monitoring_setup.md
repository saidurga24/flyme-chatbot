# P10_02: Azure Application Insights - Monitoring Setup

## Overview

Azure Application Insights is used to monitor and analyze the FlyMe chatbot's activity in production. It provides real-time performance monitoring, custom event tracking, and alerting capabilities.

## Setup Instructions

### 1. Create Application Insights Resource

1. Go to the [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → Search for **Application Insights**
3. Fill in:
   - **Name**: `flyme-chatbot-insights`
   - **Resource Group**: Your project resource group
   - **Region**: Same as your Web App
   - **Workspace**: Create new or use existing Log Analytics workspace
4. Click **Review + Create** → **Create**

### 2. Get Connection Credentials

After creating the resource:
1. Go to the Application Insights resource
2. Under **Overview**, copy:
   - **Instrumentation Key**
   - **Connection String**
3. Add to your `.env` file:
   ```
   AppInsightsInstrumentationKey=YOUR_KEY
   AppInsightsConnectionString=YOUR_CONNECTION_STRING
   ```

### 3. Telemetry Events Tracked

The integration tracks the following custom events:

| Event Name | Description | Properties |
|------------|-------------|------------|
| `LuisIntent` | Every LUIS/CLU recognition | intent, score, text |
| `BotComprehensionFailure` | Failed understanding | user_text, error_type |
| `BookingCompleted` | Successful booking | origin, destination, dates, budget |
| `DialogCancelled` | User cancelled dialog | user_text |

### 4. Setting Up Alerts

#### Alert: Comprehension Failures

To create an alert when the chatbot fails to understand users repeatedly:

1. In Application Insights → **Alerts** → **New Alert Rule**
2. **Condition**: 
   - Signal: `Custom log search`
   - Query:
     ```kusto
     customEvents
     | where name == "BotComprehensionFailure"
     | summarize count() by bin(timestamp, 5m)
     | where count_ >= 3
     ```
   - Alert logic: Greater than **0**
   - Evaluation period: **5 minutes**
3. **Actions**: 
   - Create an Action Group
   - Add email notification to the team
4. **Alert Rule Name**: `FlyMe - High Comprehension Failure Rate`

#### Alert: Error Rate

```kusto
customEvents 
| where name == "TurnError"
| summarize ErrorCount = count() by bin(timestamp, 1h)
| where ErrorCount > 5
```

### 5. Dashboard Queries

#### Booking Success Rate
```kusto
customEvents
| where name in ("BookingCompleted", "DialogCancelled", "BotComprehensionFailure")
| summarize count() by name
| render piechart
```

#### Intent Distribution
```kusto
customEvents
| where name == "LuisIntent"
| extend intent = tostring(customDimensions.intent)
| summarize count() by intent
| render piechart
```

#### Daily Active Conversations
```kusto
customEvents
| where name == "LuisIntent"
| summarize DailyUsers = dcount(tostring(customDimensions.text)) by bin(timestamp, 1d)
| render timechart
```

## Architecture

```
Bot Application
    ↓ (opencensus-ext-azure)
Azure Application Insights
    ├── Live Metrics (real-time)
    ├── Custom Events (tracked events)
    ├── Exceptions (errors)
    ├── Analytics (KQL queries)
    └── Alerts (threshold-based)
```
