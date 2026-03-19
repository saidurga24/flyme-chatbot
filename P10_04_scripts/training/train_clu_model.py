"""
Train and deploy a CLU model via Azure AI Language REST APIs.

Steps:
  1. Import training data into a CLU project
  2. Trigger training
  3. Deploy the trained model

Needs Azure credentials set in .env.
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CLU_API_KEY = os.environ.get("CluAPIKey", "")
CLU_ENDPOINT = os.environ.get("CluEndpoint", "")
CLU_PROJECT_NAME = os.environ.get("CluProjectName", "FlyMe-FlightBooking")
CLU_DEPLOYMENT_NAME = os.environ.get("CluDeploymentName", "production")
API_VERSION = "2023-04-01"

TRAINING_DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "clu_train_data.json"
)


def get_headers():
    return {
        "Ocp-Apim-Subscription-Key": CLU_API_KEY,
        "Content-Type": "application/json",
    }


def import_clu_project(training_data_path: str):
    print(f"Importing project from {training_data_path}...")

    with open(training_data_path, "r", encoding="utf-8") as f:
        clu_data = json.load(f)

    url = (
        f"{CLU_ENDPOINT}/language/authoring/analyze-conversations/"
        f"projects/{CLU_PROJECT_NAME}/:import"
    )

    response = requests.post(
        url, headers=get_headers(), json=clu_data, params={"api-version": API_VERSION}
    )

    if response.status_code in (200, 202):
        print(f"Project '{CLU_PROJECT_NAME}' imported.")
        operation_location = response.headers.get("operation-location")
        if operation_location:
            _poll_operation(operation_location)
        return True
    else:
        print(f"Import failed ({response.status_code}): {response.text}")
        return False


def train_clu_model():
    print("Starting training...")

    train_job_name = f"train-{int(time.time())}"
    url = (
        f"{CLU_ENDPOINT}/language/authoring/analyze-conversations/"
        f"projects/{CLU_PROJECT_NAME}/:train"
    )
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
        url, headers=get_headers(), json=payload, params={"api-version": API_VERSION}
    )

    if response.status_code in (200, 202):
        print("  Training in progress...")
        operation_location = response.headers.get("operation-location")
        if operation_location:
            _poll_operation(operation_location)
        print(f"  Training done. Model: {train_job_name}")
        return train_job_name
    else:
        print(f"Training failed ({response.status_code}): {response.text}")
        return None


def deploy_clu_model(model_label: str):
    print(f"Deploying model '{model_label}' as '{CLU_DEPLOYMENT_NAME}'...")

    url = (
        f"{CLU_ENDPOINT}/language/authoring/analyze-conversations/"
        f"projects/{CLU_PROJECT_NAME}/deployments/{CLU_DEPLOYMENT_NAME}"
    )

    response = requests.put(
        url,
        headers=get_headers(),
        json={"trainedModelLabel": model_label},
        params={"api-version": API_VERSION},
    )

    if response.status_code in (200, 201, 202):
        operation_location = response.headers.get("operation-location")
        if operation_location:
            _poll_operation(operation_location)
        print(f"  Deployed to '{CLU_DEPLOYMENT_NAME}'.")
        return True
    else:
        print(f"Deploy failed ({response.status_code}): {response.text}")
        return False


def _poll_operation(operation_url: str, interval: int = 5, max_wait: int = 300):
    """Poll an async Azure operation until it finishes."""
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
                print(f"  Operation failed: {body}")
                return False
            print(f"  {status} ({elapsed}s)...")
        else:
            print(f"  Status check returned {response.status_code}")
    print("  Timed out waiting for operation.")
    return False


def main():
    if not CLU_API_KEY or not CLU_ENDPOINT:
        print("Error: CLU credentials not set.")
        print("Set CluAPIKey and CluEndpoint in your .env file.")
        print("See https://language.cognitive.azure.com/ to create a resource.")
        sys.exit(1)

    if not os.path.exists(TRAINING_DATA_PATH):
        print("Error: Training data not found. Run prepare_training_data.py first.")
        sys.exit(1)

    if not import_clu_project(TRAINING_DATA_PATH):
        sys.exit(1)

    model_label = train_clu_model()
    if not model_label:
        sys.exit(1)

    if not deploy_clu_model(model_label):
        sys.exit(1)

    print(f"\nAll done! Model deployed.")
    print(f"  Project: {CLU_PROJECT_NAME}")
    print(f"  Deployment: {CLU_DEPLOYMENT_NAME}")


if __name__ == "__main__":
    main()
