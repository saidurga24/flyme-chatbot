#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""
Train LUIS/CLU model using Azure REST APIs.

This script:
1. Imports the training data into LUIS/CLU
2. Triggers model training
3. Publishes the trained model

Requires Azure credentials in the .env file.
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# LUIS API Configuration
LUIS_AUTHORING_KEY = os.environ.get("LuisAPIKey", "")
LUIS_AUTHORING_ENDPOINT = os.environ.get("LuisAPIHostName", "")
LUIS_APP_ID = os.environ.get("LuisAppId", "")
LUIS_VERSION_ID = "0.1"

# Training data path
TRAINING_DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "luis_train_data.json"
)


def get_headers():
    """Get headers for LUIS API requests."""
    return {
        "Ocp-Apim-Subscription-Key": LUIS_AUTHORING_KEY,
        "Content-Type": "application/json",
    }


def create_luis_app():
    """Create a new LUIS application."""
    print("🔧 Creating LUIS application...")
    
    url = f"https://{LUIS_AUTHORING_ENDPOINT}/luis/authoring/v3.0/apps/"
    payload = {
        "name": "FlyMe-FlightBooking",
        "description": "FlyMe flight booking chatbot",
        "culture": "en-us",
        "versionId": LUIS_VERSION_ID,
    }
    
    response = requests.post(url, headers=get_headers(), json=payload)
    
    if response.status_code == 201:
        app_id = response.json()
        print(f"✅ LUIS app created with ID: {app_id}")
        return app_id
    else:
        print(f"❌ Failed to create LUIS app: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def import_luis_app(training_data_path: str):
    """Import a LUIS application from JSON."""
    print(f"📤 Importing LUIS app from: {training_data_path}")
    
    with open(training_data_path, "r", encoding="utf-8") as f:
        luis_app = json.load(f)
    
    url = f"https://{LUIS_AUTHORING_ENDPOINT}/luis/authoring/v3.0/apps/import"
    params = {"appName": "FlyMe-FlightBooking"}
    
    response = requests.post(
        url, headers=get_headers(), json=luis_app, params=params
    )
    
    if response.status_code in (200, 201):
        app_id = response.json()
        print(f"✅ LUIS app imported with ID: {app_id}")
        return app_id
    else:
        print(f"❌ Failed to import LUIS app: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def train_luis_model(app_id: str):
    """Trigger training of the LUIS model."""
    print("🎯 Training LUIS model...")
    
    url = (
        f"https://{LUIS_AUTHORING_ENDPOINT}/luis/authoring/v3.0/"
        f"apps/{app_id}/versions/{LUIS_VERSION_ID}/train"
    )
    
    response = requests.post(url, headers=get_headers())
    
    if response.status_code == 202:
        print("   Training started. Waiting for completion...")
        
        # Poll for training status
        while True:
            time.sleep(5)
            status_response = requests.get(url, headers=get_headers())
            
            if status_response.status_code == 200:
                statuses = status_response.json()
                all_done = all(
                    s["details"]["status"] in ("Success", "UpToDate")
                    for s in statuses
                )
                if all_done:
                    print("✅ Training completed successfully!")
                    return True
                
                # Check for failures
                failed = [
                    s for s in statuses
                    if s["details"]["status"] == "Fail"
                ]
                if failed:
                    print(f"❌ Training failed: {failed}")
                    return False
                
                print("   Still training...")
            else:
                print(f"⚠️ Status check failed: {status_response.status_code}")
    else:
        print(f"❌ Failed to start training: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def publish_luis_model(app_id: str):
    """Publish the trained LUIS model."""
    print("🚀 Publishing LUIS model...")
    
    url = (
        f"https://{LUIS_AUTHORING_ENDPOINT}/luis/authoring/v3.0/"
        f"apps/{app_id}/publish"
    )
    payload = {
        "versionId": LUIS_VERSION_ID,
        "isStaging": False,
        "directVersionPublish": False,
    }
    
    response = requests.post(url, headers=get_headers(), json=payload)
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Model published!")
        print(f"   Endpoint: {result.get('endpointUrl', 'N/A')}")
        return True
    else:
        print(f"❌ Failed to publish: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def main():
    """Main function to train and publish the LUIS model."""
    if not LUIS_AUTHORING_KEY or not LUIS_AUTHORING_ENDPOINT:
        print("❌ LUIS API credentials not configured!")
        print("   Please set LuisAPIKey and LuisAPIHostName in your .env file.")
        print("\n📋 To configure LUIS:")
        print("   1. Go to https://www.luis.ai/ (or https://language.cognitive.azure.com/ for CLU)")
        print("   2. Create a Language Understanding resource")
        print("   3. Copy the key and endpoint to your .env file")
        sys.exit(1)
    
    if not os.path.exists(TRAINING_DATA_PATH):
        print("❌ Training data not found!")
        print("   Please run prepare_training_data.py first.")
        sys.exit(1)
    
    # Import or create the LUIS app
    app_id = LUIS_APP_ID or import_luis_app(TRAINING_DATA_PATH)
    if not app_id:
        sys.exit(1)
    
    # Train the model
    if not train_luis_model(app_id):
        sys.exit(1)
    
    # Publish the model
    if not publish_luis_model(app_id):
        sys.exit(1)
    
    print("\n✅ LUIS model is trained and published!")
    print(f"   App ID: {app_id}")
    print(f"   Update your .env file with: LuisAppId={app_id}")


if __name__ == "__main__":
    main()
