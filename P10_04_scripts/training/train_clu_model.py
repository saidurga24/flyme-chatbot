#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""
Train CLU model using Azure AI Language REST APIs.

This script:
1. Imports the training data into a CLU project
2. Triggers model training
3. Deploys the trained model

Requires Azure credentials in the .env file.
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# CLU API Configuration
CLU_API_KEY = os.environ.get("CluAPIKey", "")
CLU_ENDPOINT = os.environ.get("CluEndpoint", "")
CLU_PROJECT_NAME = os.environ.get("CluProjectName", "FlyMe-FlightBooking")
CLU_DEPLOYMENT_NAME = os.environ.get("CluDeploymentName", "production")
API_VERSION = "2023-04-01"

# Training data path
TRAINING_DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "clu_train_data.json"
)


def get_headers():
    """Get headers for CLU API requests."""
    return {
        "Ocp-Apim-Subscription-Key": CLU_API_KEY,
        "Content-Type": "application/json",
    }


def import_clu_project(training_data_path: str):
    """Import a CLU project from JSON."""
    print(f"📤 Importing CLU project from: {training_data_path}")

    with open(training_data_path, "r", encoding="utf-8") as f:
        clu_data = json.load(f)

    url = (
        f"{CLU_ENDPOINT}/language/authoring/analyze-conversations/"
        f"projects/{CLU_PROJECT_NAME}/:import"
    )
    params = {"api-version": API_VERSION}

    response = requests.post(
        url, headers=get_headers(), json=clu_data, params=params
    )

    if response.status_code in (200, 202):
        print(f"✅ CLU project '{CLU_PROJECT_NAME}' imported successfully!")
        # Poll for completion if async
        operation_location = response.headers.get("operation-location")
        if operation_location:
            _poll_operation(operation_location)
        return True
    else:
        print(f"❌ Failed to import CLU project: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def train_clu_model():
    """Trigger training of the CLU model."""
    print("🎯 Training CLU model...")

    # Use a unique training job name
    train_job_name = f"train-{int(time.time())}"
    url = (
        f"{CLU_ENDPOINT}/language/authoring/analyze-conversations/"
        f"projects/{CLU_PROJECT_NAME}/:train"
    )
    params = {"api-version": API_VERSION}
    payload = {
        "modelLabel": train_job_name,
        "trainingMode": "standard",
        "trainingConfigVersion": "latest",
        "evaluationOptions": {
            "kind": "percentage",
            "testingSplitPercentage": 20,
            "trainingSplitPercentage": 80,
        },
    }

    response = requests.post(
        url, headers=get_headers(), json=payload, params=params
    )

    if response.status_code in (200, 202):
        print("   Training started. Waiting for completion...")
        operation_location = response.headers.get("operation-location")
        if operation_location:
            _poll_operation(operation_location)
        print(f"✅ Training completed! Model label: {train_job_name}")
        return train_job_name
    else:
        print(f"❌ Failed to start training: {response.status_code}")
        print(f"   Response: {response.text}")
        return None


def deploy_clu_model(model_label: str):
    """Deploy the trained CLU model."""
    print(f"🚀 Deploying CLU model '{model_label}' to '{CLU_DEPLOYMENT_NAME}'...")

    url = (
        f"{CLU_ENDPOINT}/language/authoring/analyze-conversations/"
        f"projects/{CLU_PROJECT_NAME}/deployments/{CLU_DEPLOYMENT_NAME}"
    )
    params = {"api-version": API_VERSION}
    payload = {
        "trainedModelLabel": model_label,
    }

    response = requests.put(
        url, headers=get_headers(), json=payload, params=params
    )

    if response.status_code in (200, 201, 202):
        operation_location = response.headers.get("operation-location")
        if operation_location:
            _poll_operation(operation_location)
        print(f"✅ Model deployed to '{CLU_DEPLOYMENT_NAME}'!")
        return True
    else:
        print(f"❌ Failed to deploy: {response.status_code}")
        print(f"   Response: {response.text}")
        return False


def _poll_operation(operation_url: str, interval: int = 5, max_wait: int = 300):
    """Poll an async operation until completion."""
    elapsed = 0
    while elapsed < max_wait:
        time.sleep(interval)
        elapsed += interval
        response = requests.get(operation_url, headers=get_headers())
        if response.status_code == 200:
            body = response.json()
            status = body.get("status", "").lower()
            if status in ("succeeded", "completed"):
                return True
            elif status in ("failed", "cancelled"):
                print(f"❌ Operation failed: {body}")
                return False
            print(f"   Status: {status} ({elapsed}s elapsed)...")
        else:
            print(f"⚠️ Status check returned: {response.status_code}")
    print("⚠️ Operation timed out.")
    return False


def main():
    """Main function to train and deploy the CLU model."""
    if not CLU_API_KEY or not CLU_ENDPOINT:
        print("❌ CLU API credentials not configured!")
        print("   Please set CluAPIKey and CluEndpoint in your .env file.")
        print("\n📋 To configure CLU:")
        print("   1. Go to https://language.cognitive.azure.com/")
        print("   2. Create a Language resource")
        print("   3. Copy the key and endpoint to your .env file")
        sys.exit(1)

    if not os.path.exists(TRAINING_DATA_PATH):
        print("❌ Training data not found!")
        print("   Please run prepare_training_data.py first.")
        sys.exit(1)

    # Import the CLU project
    if not import_clu_project(TRAINING_DATA_PATH):
        sys.exit(1)

    # Train the model
    model_label = train_clu_model()
    if not model_label:
        sys.exit(1)

    # Deploy the model
    if not deploy_clu_model(model_label):
        sys.exit(1)

    print(f"\n✅ CLU model is trained and deployed!")
    print(f"   Project: {CLU_PROJECT_NAME}")
    print(f"   Deployment: {CLU_DEPLOYMENT_NAME}")
    print(f"   Update your .env file with:")
    print(f"     CluProjectName={CLU_PROJECT_NAME}")
    print(f"     CluDeploymentName={CLU_DEPLOYMENT_NAME}")


if __name__ == "__main__":
    main()
