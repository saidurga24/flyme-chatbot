#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""
Evaluate the trained LUIS/CLU model offline.

Computes precision, recall, and F1 score for:
- Intent classification
- Entity extraction (per entity type)

Uses a held-out test set from the training data preparation step.
"""

import os
import sys
import json
from collections import defaultdict
from typing import Dict, List, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()

# Configuration
LUIS_APP_ID = os.environ.get("LuisAppId", "")
LUIS_API_KEY = os.environ.get("LuisAPIKey", "")
LUIS_ENDPOINT = os.environ.get("LuisAPIHostName", "")

TEST_DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "luis_test_data.json"
)
RESULTS_OUTPUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "evaluation_results.json"
)


def load_test_data(filepath: str) -> dict:
    """Load the test data from LUIS JSON format."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def predict_utterance(text: str) -> dict:
    """
    Send an utterance to the LUIS/CLU endpoint for prediction.
    
    Returns the prediction result with intent and entities.
    """
    url = (
        f"https://{LUIS_ENDPOINT}/luis/prediction/v3.0/"
        f"apps/{LUIS_APP_ID}/slots/production/predict"
    )
    params = {
        "subscription-key": LUIS_API_KEY,
        "verbose": True,
        "show-all-intents": True,
        "query": text,
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None


def evaluate_intent_classification(
    test_utterances: list, predictions: list
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate intent classification performance.
    
    Returns per-intent precision, recall, and F1 score.
    """
    # Count true positives, false positives, false negatives
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    
    for utterance, prediction in zip(test_utterances, predictions):
        true_intent = utterance["intent"]
        pred_intent = (
            prediction["prediction"]["topIntent"]
            if prediction
            else "None"
        )
        
        if true_intent == pred_intent:
            tp[true_intent] += 1
        else:
            fn[true_intent] += 1
            fp[pred_intent] += 1
    
    # Calculate metrics per intent
    results = {}
    all_intents = set(list(tp.keys()) + list(fp.keys()) + list(fn.keys()))
    
    for intent in all_intents:
        precision = tp[intent] / (tp[intent] + fp[intent]) if (tp[intent] + fp[intent]) > 0 else 0
        recall = tp[intent] / (tp[intent] + fn[intent]) if (tp[intent] + fn[intent]) > 0 else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )
        
        results[intent] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "true_positives": tp[intent],
            "false_positives": fp[intent],
            "false_negatives": fn[intent],
        }
    
    return results


def evaluate_entity_extraction(
    test_utterances: list, predictions: list
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate entity extraction performance.
    
    Returns per-entity precision, recall, and F1 score.
    """
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    
    entity_types = ["or_city", "dst_city", "str_date", "end_date", "budget"]
    
    for utterance, prediction in zip(test_utterances, predictions):
        true_entities = {e["entity"]: e.get("value", "") for e in utterance.get("entities", [])}
        
        pred_entities = {}
        if prediction and "prediction" in prediction:
            pred_entity_data = prediction["prediction"].get("entities", {})
            for entity_type in entity_types:
                if entity_type in pred_entity_data:
                    pred_entities[entity_type] = str(pred_entity_data[entity_type])
        
        for entity_type in entity_types:
            true_has = entity_type in true_entities
            pred_has = entity_type in pred_entities
            
            if true_has and pred_has:
                tp[entity_type] += 1
            elif not true_has and pred_has:
                fp[entity_type] += 1
            elif true_has and not pred_has:
                fn[entity_type] += 1
    
    results = {}
    for entity_type in entity_types:
        precision = tp[entity_type] / (tp[entity_type] + fp[entity_type]) if (tp[entity_type] + fp[entity_type]) > 0 else 0
        recall = tp[entity_type] / (tp[entity_type] + fn[entity_type]) if (tp[entity_type] + fn[entity_type]) > 0 else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )
        
        results[entity_type] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "true_positives": tp[entity_type],
            "false_positives": fp[entity_type],
            "false_negatives": fn[entity_type],
        }
    
    return results


def run_offline_evaluation(test_utterances: list) -> Tuple[list, list]:
    """
    Run predictions for all test utterances.
    
    In offline mode (no LUIS endpoint), generates mock predictions
    based on simple keyword matching for demonstration.
    """
    predictions = []
    
    use_api = LUIS_APP_ID and LUIS_API_KEY and LUIS_ENDPOINT
    
    if use_api:
        print("🔗 Using LUIS API for predictions...")
        for i, utterance in enumerate(test_utterances):
            result = predict_utterance(utterance["text"])
            predictions.append(result)
            if (i + 1) % 50 == 0:
                print(f"   Processed {i + 1}/{len(test_utterances)}")
    else:
        print("📴 LUIS not configured - using offline keyword matching for evaluation demo...")
        for utterance in test_utterances:
            pred = offline_predict(utterance["text"])
            predictions.append(pred)
    
    return predictions


def offline_predict(text: str) -> dict:
    """
    Simple offline prediction using keyword matching.
    
    This is a fallback for when LUIS is not configured, useful for
    testing the evaluation pipeline.
    """
    text_lower = text.lower()
    
    # Intent classification
    booking_keywords = [
        "book", "fly", "flight", "travel", "trip", "going to",
        "want to go", "departing", "from", "to",
    ]
    greeting_keywords = ["hello", "hi", "hey", "good morning"]
    cancel_keywords = ["cancel", "quit", "stop", "never mind"]
    
    if any(kw in text_lower for kw in greeting_keywords):
        intent = "Greeting"
    elif any(kw in text_lower for kw in cancel_keywords):
        intent = "Cancel"
    elif any(kw in text_lower for kw in booking_keywords):
        intent = "BookFlight"
    else:
        intent = "None"
    
    return {
        "prediction": {
            "topIntent": intent,
            "intents": {intent: {"score": 0.9}},
            "entities": {},
        }
    }


def print_results(intent_results: dict, entity_results: dict):
    """Print evaluation results in a formatted table."""
    print("\n" + "=" * 60)
    print("📊 INTENT CLASSIFICATION RESULTS")
    print("=" * 60)
    print(f"{'Intent':<15} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-" * 60)
    
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    for intent, metrics in sorted(intent_results.items()):
        print(
            f"{intent:<15} "
            f"{metrics['precision']:<12.4f} "
            f"{metrics['recall']:<12.4f} "
            f"{metrics['f1_score']:<12.4f}"
        )
        total_tp += metrics["true_positives"]
        total_fp += metrics["false_positives"]
        total_fn += metrics["false_negatives"]
    
    # Overall accuracy
    total = total_tp + total_fn
    accuracy = total_tp / total if total > 0 else 0
    print("-" * 60)
    print(f"{'Overall':<15} {'Accuracy:':<12} {accuracy:.4f}")
    
    print("\n" + "=" * 60)
    print("📊 ENTITY EXTRACTION RESULTS")
    print("=" * 60)
    print(f"{'Entity':<15} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-" * 60)
    
    for entity, metrics in sorted(entity_results.items()):
        print(
            f"{entity:<15} "
            f"{metrics['precision']:<12.4f} "
            f"{metrics['recall']:<12.4f} "
            f"{metrics['f1_score']:<12.4f}"
        )
    print("=" * 60)


def main():
    """Main function to run model evaluation."""
    if not os.path.exists(TEST_DATA_PATH):
        print("❌ Test data not found!")
        print("   Please run prepare_training_data.py first.")
        sys.exit(1)
    
    # Load test data
    test_data = load_test_data(TEST_DATA_PATH)
    test_utterances = test_data.get("utterances", [])
    
    if not test_utterances:
        print("⚠️ No test utterances found.")
        sys.exit(1)
    
    print(f"📝 Evaluating {len(test_utterances)} test utterances...")
    
    # Run predictions
    predictions = run_offline_evaluation(test_utterances)
    
    # Evaluate
    intent_results = evaluate_intent_classification(test_utterances, predictions)
    entity_results = evaluate_entity_extraction(test_utterances, predictions)
    
    # Print results
    print_results(intent_results, entity_results)
    
    # Save results
    results = {
        "num_test_utterances": len(test_utterances),
        "intent_classification": intent_results,
        "entity_extraction": entity_results,
    }
    
    with open(RESULTS_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to: {RESULTS_OUTPUT}")


if __name__ == "__main__":
    main()
