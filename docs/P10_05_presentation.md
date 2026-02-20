# P10_05: Presentation Outline

## Slide 1: Title
- **FlyMe ✈️ - Flight Booking Chatbot**
- OpenClassrooms AI Engineer - Project 10
- Name: Durga
- Date: February 2026

## Slide 2: Project Context
- Company: FlyMe - a travel provider
- Goal: Build a V1 chatbot MVP for booking flights
- Target users: FlyMe employees booking holiday flights
- 5 key elements to identify: origin, destination, departure date, return date, budget

## Slide 3: Technology Stack
- Microsoft Bot Framework SDK v4 (Python)
- Azure LUIS/CLU for Natural Language Understanding
- Azure Web App for deployment
- Azure Application Insights for monitoring
- GitHub + GitHub Actions for CI/CD

## Slide 4: Architecture Diagram
- Show system architecture:
  - User → Web Chat UI → aiohttp Server → Bot Adapter
  - Bot → LUIS/CLU → Entity Extraction
  - Bot → Application Insights → Alerts

## Slide 5: Dataset - Frames
- Maluuba/Microsoft Frames dataset
- 1,369 human-human dialogues
- Vacation package booking context
- Extracted intents and entities for training

## Slide 6: LUIS/CLU Model
- Intent: BookFlight (+ Greeting, Cancel, None)
- 5 entities: or_city, dst_city, str_date, end_date, budget
- Training pipeline: Frames → Extract → Format → Train → Evaluate

## Slide 7: Chatbot Demo (Live)
- Show the web chat interface
- Demo conversation:
  1. Welcome message
  2. User: "I want to fly from Paris to New York March 15"
  3. Bot extracts entities, asks missing fields
  4. Confirmation flow

## Slide 8: Dialog Flow
- Waterfall dialog pattern:
  1. LUIS/CLU Recognition
  2. Origin city prompt
  3. Destination city prompt
  4. Departure date prompt
  5. Return date prompt
  6. Budget prompt
  7. Confirmation summary

## Slide 9: Application Insights Monitoring
- Custom events tracked: intents, comprehension failures, bookings
- Alert rules: 3 failures in 5 min triggers notification
- Dashboard with KQL queries
- Show screenshots of monitoring dashboard

## Slide 10: Performance Evaluation
- Offline evaluation metrics: Precision, Recall, F1
- Per-intent and per-entity results table
- Targets: F1 ≥ 0.85 for intents, F1 ≥ 0.80 for entities

## Slide 11: Monitoring Methodology
- Evaluation criteria defined
- Production monitoring flow diagram
- Retraining triggers and procedures
- Frequency: routine (2 weeks), full (monthly), emergency (24h)

## Slide 12: CI/CD Pipeline
- GitHub repository with version control
- GitHub Actions: lint + pytest on every push
- 15+ unit tests covering dialogs, entity extraction, bot initialization
- Automated testing ensures regression safety

## Slide 13: Deployment
- Azure Web App deployment
- Environment variables for secure credential management
- Startup script and Procfile

## Slide 14: Key Accomplishments
- ✅ Functional chatbot with NLU integration
- ✅ WhatsApp-inspired web chat interface
- ✅ Application Insights telemetry & alerts
- ✅ Complete training/evaluation pipeline
- ✅ CI/CD with 15+ automated tests
- ✅ Performance monitoring methodology

## Slide 15: Thank You & Q&A
- Summary of deliverables
- Links: GitHub repo, demo URL
- Questions?

---

## Presentation Tips
- **Duration**: 20 min presentation + 10 min Q&A
- **Audience**: Laura (Product Manager) - non-technical
- **Focus on**: Business value, user experience, monitoring safety
- **Demo**: Have the bot running locally or on Azure before the presentation
