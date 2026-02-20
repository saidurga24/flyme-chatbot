# FlyMe ✈️ - Flight Booking Chatbot

A chatbot web application built with Microsoft Bot Framework SDK v4 for Python that helps users book airline tickets for holidays.

## 🎯 Project Overview

**FlyMe** is an intelligent chatbot that identifies five key elements in a user's flight booking request:
1. **Departure city** (origin)
2. **Destination city**
3. **Departure date**
4. **Return date**
5. **Maximum budget**

The chatbot uses Azure LUIS/CLU for natural language understanding, asks clarifying questions for missing information, and confirms the booking once all details are gathered.

## 🏗️ Architecture

```
User → Web Chat UI → aiohttp Server → Bot Framework Adapter → MainDialog
                                                                    ↓
                                                              LUIS/CLU Recognizer
                                                                    ↓
                                                              BookingDialog
                                                                    ↓
                                                          Application Insights
```

## 📁 Project Structure

```
P10_Durga/
├── app.py                     # Main entry point (aiohttp server)
├── bot.py                     # FlightBookingBot class
├── config.py                  # Configuration from environment
├── booking_details.py         # BookingDetails data class
├── flight_booking_recognizer.py  # LUIS/CLU recognizer wrapper
├── dialogs/
│   ├── main_dialog.py         # Main dialog with LUIS routing
│   ├── booking_dialog.py      # Waterfall dialog for booking fields
│   └── cancel_and_help_dialog.py  # Base dialog for interruptions
├── helpers/
│   ├── luis_helper.py         # LUIS entity extraction
│   ├── dialog_helper.py       # Dialog lifecycle management
│   └── telemetry_helper.py    # Application Insights integration
├── static/
│   ├── index.html             # Web chat interface
│   ├── style.css              # WhatsApp-inspired styling
│   └── chat.js                # Chat frontend logic
├── data/
│   └── download_frames.py     # Download Frames dataset
├── training/
│   ├── prepare_training_data.py  # Parse Frames → LUIS format
│   ├── train_luis_model.py    # Train & publish LUIS model
│   └── evaluate_model.py     # Evaluate model performance
├── tests/
│   ├── test_booking_dialog.py # Dialog flow tests
│   ├── test_luis_helper.py    # Entity extraction tests
│   └── test_bot.py            # Bot initialization tests
├── docs/
│   ├── P10_02_monitoring_setup.md  # App Insights setup guide
│   └── P10_03_methodology.md      # Performance monitoring methodology
├── .github/workflows/ci.yml  # GitHub Actions CI
├── requirements.txt           # Python dependencies
├── Procfile                   # Azure Web App deployment
├── startup.sh                 # Azure startup script
├── .env.example               # Environment template
└── .gitignore
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Azure account (for LUIS/CLU and Application Insights)
- Bot Framework Emulator (optional, for testing)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/P10_Durga.git
cd P10_Durga

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Azure credentials
```

### Running Locally

```bash
cd P10_01_chatbot && python app.py
```

Open http://localhost:3978 in your browser to use the web chat interface.

### Using Bot Framework Emulator

1. Download [Bot Framework Emulator](https://github.com/Microsoft/BotFramework-Emulator/releases)
2. Connect to `http://localhost:3978/api/messages`

## 🔧 Data Pipeline

```bash
# 1. Download the Frames dataset
python data/download_frames.py

# 2. Prepare training data
python training/prepare_training_data.py

# 3. Train the LUIS model (requires Azure credentials)
python training/train_luis_model.py

# 4. Evaluate the model
python training/evaluate_model.py
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=.
```

## ☁️ Azure Deployment

1. Create an Azure Web App (Python 3.11)
2. Set environment variables in Application Settings
3. Deploy via Git push or Azure CLI:

```bash
az webapp up --name flyme-chatbot --resource-group YOUR_RG --runtime "PYTHON:3.11"
```

## 📊 Monitoring

Azure Application Insights is integrated for:
- **Intent tracking**: Every LUIS/CLU recognition is logged
- **Comprehension failure alerts**: Triggers when bot fails to understand
- **Booking completion tracking**: Successful bookings are recorded
- **Error tracking**: Exceptions are automatically captured

See [docs/P10_02_monitoring_setup.md](docs/P10_02_monitoring_setup.md) for setup details.

## 📄 Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| P10_01 | Chatbot | Web application with messaging interface |
| P10_02 | Monitoring Tool | Azure Application Insights setup |
| P10_03 | Methodology | Performance monitoring methodology |
| P10_04 | Scripts | GitHub-hosted pipeline scripts |
| P10_05 | Presentation | PowerPoint for project defense |

## 📝 License

This project is part of the OpenClassrooms AI Engineer path.
