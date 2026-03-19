# FlyMe - Flight Booking Chatbot

A chatbot built with Microsoft Bot Framework SDK v4 (Python) that helps users book airline tickets for holidays.

## Project Overview

FlyMe is a chatbot that identifies five key elements in a user's flight booking request:
1. Departure city (origin)
2. Destination city
3. Departure date
4. Return date
5. Maximum budget

It uses Azure AI Language (CLU) for natural language understanding, asks follow-up questions for any missing info, and confirms the booking details before submitting.

## Architecture

```
User → Web Chat UI → aiohttp Server → Bot Framework Adapter → MainDialog
                                                                    ↓
                                                              CLU Recognizer
                                                                    ↓
                                                              BookingDialog
                                                                    ↓
                                                          Application Insights
```

## Project Structure

```
flyme-chatbot/
├── P10_01_chatbot/               # Chatbot application
│   ├── app.py                    # Main entry point (aiohttp server)
│   ├── bot.py                    # FlightBookingBot class
│   ├── config.py                 # Config from environment vars
│   ├── booking_details.py        # BookingDetails data class
│   ├── flight_booking_recognizer.py  # CLU recognizer wrapper
│   ├── dialogs/
│   │   ├── main_dialog.py        # Main dialog with CLU routing
│   │   ├── booking_dialog.py     # Waterfall dialog for booking
│   │   └── cancel_and_help_dialog.py
│   ├── helpers/
│   │   ├── clu_helper.py         # CLU entity extraction
│   │   ├── dialog_helper.py      # Dialog lifecycle
│   │   └── telemetry_helper.py   # App Insights integration
│   ├── static/                   # Web chat frontend
│   ├── requirements.txt
│   ├── Procfile
│   └── startup.sh
├── P10_02_monitoring_tool/       # App Insights setup guide
├── P10_03_methodology/           # Monitoring methodology doc
├── P10_04_scripts/               # Pipeline scripts + tests
│   ├── data/
│   ├── training/
│   ├── tests/
│   └── .github/workflows/ci.yml
├── P10_05_presentation/          # Presentation outline
├── .env.example
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.9+
- Azure account (for CLU and Application Insights)
- Bot Framework Emulator (optional)

### Installation

```bash
git clone git@github.com:saidurga24/flyme-chatbot.git
cd flyme-chatbot

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -r P10_01_chatbot/requirements.txt

cp .env.example .env
# Edit .env with your Azure credentials
```

### Running Locally

```bash
cd P10_01_chatbot && python app.py
```

Then open http://localhost:3978 in your browser.

You can also use the [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases) and connect to `http://localhost:3978/api/messages`.

## Data Pipeline

```bash
# Download the Frames dataset
python P10_04_scripts/data/download_frames.py

# Prepare the training data in CLU format
python P10_04_scripts/training/prepare_training_data.py

# Train the CLU model (needs Azure credentials)
python P10_04_scripts/training/train_clu_model.py

# Evaluate the model
python P10_04_scripts/training/evaluate_model.py
```

## Testing

```bash
cd P10_01_chatbot && python -m pytest ../P10_04_scripts/tests/ -v
```

## Deployment

Deploy to Azure Web App:
```bash
az webapp up --name flyme-chatbot --resource-group YOUR_RG --runtime "PYTHON:3.11"
```

## Monitoring

Application Insights tracks:
- CLU intent recognition events
- Comprehension failure alerts (when bot doesn't understand)
- Booking completions
- Errors and exceptions

See [P10_02_monitoring_tool.md](P10_02_monitoring_tool/P10_02_monitoring_tool.md) for details.

## Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| P10_01 | Chatbot | Web application with chat interface |
| P10_02 | Monitoring Tool | Application Insights setup |
| P10_03 | Methodology | Performance monitoring methodology |
| P10_04 | Scripts | Training pipeline and tests |
| P10_05 | Presentation | Slides for project defense |

---
OpenClassrooms AI Engineer Path - Project 10
