# P10_03: Performance Monitoring Methodology

## 1. Model Evaluation Criteria

The FlyMe chatbot's LUIS/CLU model is evaluated using the following metrics:

### Intent Classification Metrics
| Metric | Description | Target |
|--------|-------------|--------|
| **Precision** | Correct predictions / Total predictions per intent | ≥ 0.85 |
| **Recall** | Correct predictions / Total actual cases per intent | ≥ 0.85 |
| **F1 Score** | Harmonic mean of precision and recall | ≥ 0.85 |
| **Accuracy** | Overall correct intent classifications | ≥ 0.90 |

### Entity Extraction Metrics
| Metric | Description | Target |
|--------|-------------|--------|
| **Entity Precision** | Correctly extracted entities / Total extracted | ≥ 0.80 |
| **Entity Recall** | Correctly extracted entities / Total expected | ≥ 0.80 |
| **Entity F1** | Harmonic mean per entity type | ≥ 0.80 |

### Production Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| **Comprehension Rate** | % of user messages understood | < 80% triggers alert |
| **Booking Completion Rate** | % of started bookings completed | < 50% triggers review |
| **Average Dialog Length** | Mean number of turns per booking | > 10 triggers review |
| **Error Rate** | Bot errors per hour | > 5 triggers alert |

## 2. Production Evaluation Mechanism

```
┌──────────────────────────────────────────────────────────────┐
│                    PRODUCTION MONITORING                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  User Message ──→ LUIS/CLU ──→ Bot Response                 │
│       │                │              │                      │
│       ▼                ▼              ▼                      │
│  ┌─────────┐    ┌──────────┐   ┌──────────┐                │
│  │ Log Raw  │    │ Log      │   │ Log Bot  │                │
│  │ Input    │    │ Intent & │   │ Response │                │
│  │          │    │ Entities │   │          │                │
│  └────┬─────┘    └────┬─────┘   └────┬─────┘                │
│       │               │              │                       │
│       └───────────┬───┘──────────────┘                       │
│                   ▼                                          │
│         ┌─────────────────┐                                  │
│         │  Application    │                                  │
│         │  Insights       │                                  │
│         └────────┬────────┘                                  │
│                  ▼                                           │
│    ┌──────────────────────────┐                              │
│    │     Analytics Engine      │                              │
│    ├──────────────────────────┤                              │
│    │ • Real-time dashboard    │                              │
│    │ • KQL custom queries     │                              │
│    │ • Threshold monitoring   │                              │
│    └─────────┬───────────────┘                              │
│              ▼                                               │
│    ┌──────────────────────────┐                              │
│    │      Alert System         │                              │
│    ├──────────────────────────┤                              │
│    │ • Email notifications    │                              │
│    │ • Slack/Teams webhooks   │                              │
│    │ • Auto-escalation        │                              │
│    └──────────────────────────┘                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow
1. **Collection**: Every user interaction is logged with intent, entities, confidence score, and bot response
2. **Storage**: Data is stored in Application Insights / Log Analytics workspace
3. **Analysis**: KQL queries compute metrics on windows of 5min, 1h, 1d
4. **Alerting**: Threshold breaches trigger notifications to the team

## 3. Model Retraining Procedures

### When to Retrain

| Trigger | Condition | Action |
|---------|-----------|--------|
| **Performance Drop** | F1 Score drops below 0.80 for any intent | Schedule retraining |
| **Comprehension Rate** | Falls below 80% over 24h | Investigate + retrain |
| **New Patterns** | Users express new intents consistently | Add intents + retrain |
| **Scheduled** | Every 2 weeks | Evaluate; retrain if needed |
| **Alert** | 3+ comprehension failures in 5 minutes | Review labeled data |

### Retraining Process

```
Step 1: Data Collection
├── Export last 2 weeks of conversation logs from App Insights
├── Filter for comprehension failures and low-confidence predictions
└── Sample successful interactions for balanced dataset

Step 2: Data Labeling
├── Review failed utterances manually
├── Correct intent labels where wrong
├── Add missing entity annotations
└── Add new utterances for underrepresented intents

Step 3: Model Training
├── Run prepare_training_data.py with updated data
├── Upload to LUIS/CLU
├── Train new model version
└── Evaluate on held-out test set

Step 4: Model Evaluation
├── Compare new model vs. current model metrics
├── If F1 improved by ≥ 2%, proceed to deployment
├── If F1 decreased, investigate and iterate
└── A/B test with shadow traffic if possible

Step 5: Deployment
├── Publish new model version to staging slot
├── Run integration tests against staging
├── Swap staging → production
└── Monitor closely for first 24 hours with tighter alert thresholds

Step 6: Post-Deployment
├── Monitor comprehension rate for 48 hours
├── Compare booking completion rate vs. previous period
├── If regressions detected, rollback to previous model
└── Document changes in model version changelog
```

### Retraining Frequency

| Scenario | Frequency |
|----------|-----------|
| **Routine evaluation** | Every 2 weeks |
| **Full retraining** | Monthly or when triggered |
| **Emergency retraining** | Within 24h of critical alert |
| **Model version review** | Quarterly (with stakeholders) |

## 4. Offline Evaluation Workflow

The `training/evaluate_model.py` script supports automated offline evaluation:

```bash
# 1. Prepare test data from production logs
python training/prepare_training_data.py

# 2. Run evaluation
python training/evaluate_model.py

# 3. Review results
cat training/evaluation_results.json
```

Output includes per-intent and per-entity precision, recall, and F1 scores that can be compared against the established thresholds.

## 5. Continuous Improvement Loop

```
Monitor → Detect → Analyze → Retrain → Evaluate → Deploy → Monitor
```

This creates a virtuous cycle where:
- **Production feedback** drives model improvements
- **Automated alerts** catch issues early
- **Scheduled evaluations** prevent gradual degradation
- **Clear thresholds** remove ambiguity from decisions
- **Documented procedures** ensure consistency across team members
