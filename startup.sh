#!/bin/bash
# Startup script for Azure Web App

# Install dependencies
pip install -r requirements.txt

# Start the bot
python app.py
