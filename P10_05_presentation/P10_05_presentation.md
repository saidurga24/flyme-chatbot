# P10_05: Presentation Outline

## Slide 1: Title
- **FlyMe ✈️ - Flight Booking Chatbot**
- OpenClassrooms AI Engineer - Project 10
- Name: Durga
- Date: March 2026

## Slide 2: Project Context
- **Company:** FlyMe - a travel provider
- **Goal:** Build a V1 chatbot MVP for booking flights
- **Target users:** FlyMe employees booking holiday flights
- **Core Requirement:** Successfully identify 5 key extraction elements:
  1. Origin city
  2. Destination city
  3. Departure date
  4. Return date
  5. Maximum budget

## Slide 3: Technology Stack
- **Framework:** Microsoft Bot Framework SDK v4 (Python)
- **NLU:** Azure AI Language Service (CLU) - Migrated from legacy LUIS
- **Deployment:** Azure Web App (Python 3.11/aiohttp)
- **Monitoring:** Azure Application Insights
- **CI/CD:** GitHub Actions for automated linting, testing, and deployment

## Slide 4: Architecture Diagram
- **Display System Architecture:**
  - User → Web Chat UI → aiohttp Server → Bot Adapter
  - Bot → Azure CLU → Entity Extraction
  - Bot → Application Insights → Telemetry & Alerts
- Highlight how `.env` configures local runs seamlessly while Azure App Settings handle production credentials securely.

## Slide 5: Dataset Preparation
- **Source:** Maluuba/Microsoft Frames dataset
- **Size:** 1,369 human-human dialogues focusing on vacation package booking
- **Data Engineering:** Extracted dialogues, deduplicated training examples, and injected targeted synthetic examples to dramatically improve model comprehension for complex edge cases.

## Slide 6: Azure CLU Implementation
- **Intent Models:** `BookFlight`, `Greeting`, `Cancel`, `None`
- **Entity Models:** `or_city`, `dst_city`, `str_date`, `end_date`, `budget`
- **Migration Success:** Initially started with BotBuilder-AI LUIS, but successfully migrated the entire architecture to the modern Azure AI Language Conversations (CLU) REST workflow.

## Slide 7: Chatbot Demo (Live)
- **Showcase Web Chat interface:**
  - Seamless "All-in-One" extraction: "I want to fly from Paris to New York on March 15, returning March 22, with a budget of $1000."
  - Bot processes all 5 entities perfectly and jumps directly to booking confirmation.
  - Showcase the "Interrupt" flow: Type "Cancel" to clear conversation state.

## Slide 8: Intelligent Dialog Flow
- **Waterfall Dialog Pattern:**
  1. Azure CLU NLU Recognition (evaluates initial user utterance)
  2. Dynamic skipping: If an entity is recognized, skip the prompt!
  3. Sequential waterfall fallback prompts for missing info: Origin → Destination → Departure date → Return date → Budget
  4. Final Booking Confirmation step

## Slide 9: Application Insights Monitoring
- **Custom Telemetry Tracking:** 
  - Tracks `CluIntent` (intent scores) and `BotComprehensionFailure`.
- **Engineering Highlights:** Successfully engineered a Python 3.13 thread-locking hotfix for the AzureLogHandler to ensure asynchronous telemetry does not crash the server pipeline.
- **Alert Rules:** 3 comprehension failures within 5 minutes instantly triggers automated admin notification.

## Slide 10: Performance Evaluation Results
- **Strict Guidelines Evaluated:** Verified absolutely no data leakage between training and testing splits.
- **Milestone Reached:** 
  - **Intents:** F1 score ≥ 0.85 across all intent types.
  - **Entities:** F1 score ≥ 0.88 across all entity types, exceeding the 0.80 project threshold.
- Display a table illustrating Per-Intent / Per-Entity Precision, Recall, and F1 outcomes.

## Slide 11: Continuous Monitoring Methodology
- **Production Loop:**
  - Real-time logging of user conversations & bot confidence.
  - Kusto Query (KQL) dashboards tracking intent distribution and success rates.
- **Retraining Triggers:**
  - Emergency retraining if Comprehension Rate falls < 80% over 24 hours.
  - Scheduled routine evaluation every 2 weeks using shadow testing.

## Slide 12: CI/CD Pipeline & Automated Testing
- **Continuous Integration:** GitHub repository equipped with GitHub Actions.
- **Test Suite:** 17 comprehensive unit tests (built with `pytest` / `aiounittest`) ensuring robust coverage over Waterfall dialogs, CLU entity parsing, and Bot initialization. 
- **Continuous Deployment:** On every push to `main`, if all 17 tests pass, the pipeline automatically deploys the updated code package to the Azure Web App.

## Slide 13: Final Deployment
- **Azure Web App Integration:**
  - Zero-downtime integration for webhook endpoint (`/api/messages`).
  - Protected endpoints returning standard `405 Method Not Allowed` for strict POST-only BotFramework security.

## Slide 14: Key Accomplishments
- ✅ Functional multi-turn conversational AI with modern Azure CLU integration
- ✅ Secure, tracked Web App deployed to Azure
- ✅ 17/17 Passing Unit tests running in GitHub Actions CI/CD
- ✅ 0.85+ F1 score evaluation metrics achieved without data leakage
- ✅ Custom Application Insights Python 3.13 monitoring integration
- ✅ Code cleanups removing bloated boilerplate comments

## Slide 15: Thank You & Q&A
- **Summary:** FlyMe MVP successfully completed, tested, and shipped.
- **Links:** GitHub Repository, Live Demo URL
- **Questions?**

---

## Presentation Tips for Presenter
- **Duration**: 20 min presentation + 10 min Q&A
- **Audience**: Laura (Product Manager) - non-technical audience
- **Focus Tone**: Revolve technical achievements (like Python threading fixes and CI/CD pipelines) back to business value (stable bookings, reliable UX, faster bug recovery).
