#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""
Prepare training data for Azure AI Language CLU from the Frames dataset.

Parses the Frames dataset JSON to extract training utterances with 
labeled intents and entities:
    - Intent: BookFlight
    - Entities: or_city, dst_city, str_date, end_date, budget

Outputs training data in CLU-compatible JSON format.
"""

import json
import os
import sys
import re
from typing import List, Dict, Any


# Paths
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_FILE = os.path.join(DATA_DIR, "..", "data", "frames.json")
OUTPUT_DIR = DATA_DIR
TRAIN_OUTPUT = os.path.join(OUTPUT_DIR, "clu_train_data.json")
TEST_OUTPUT = os.path.join(OUTPUT_DIR, "clu_test_data.json")


def load_frames_dataset(filepath: str) -> list:
    """Load the raw Frames dataset JSON."""
    print(f"📂 Loading Frames dataset from: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"   Loaded {len(data)} dialogues")
    return data


def extract_user_utterances(frames_data: list) -> List[Dict[str, Any]]:
    """
    Extract user utterances with their associated entity values from the 
    Frames dataset dialogue turns.
    
    Returns a list of training examples with text, intent, and entities.
    """
    training_examples = []
    
    for dialogue in frames_data:
        turns = dialogue.get("turns", [])
        
        for turn in turns:
            author = turn.get("author", "")
            text = turn.get("text", "").strip()
            
            if author != "user" or not text:
                continue
            
            # Extract entities from the turn's labels/acts
            entities = extract_entities_from_turn(turn)
            
            # Determine intent
            intent = determine_intent(turn, entities)
            
            if intent == "BookFlight" and entities:
                example = {
                    "text": text,
                    "intent": intent,
                    "entities": entities,
                }
                training_examples.append(example)
            elif text.lower() in ("hi", "hello", "hey", "good morning", "good afternoon"):
                training_examples.append({
                    "text": text,
                    "intent": "Greeting",
                    "entities": [],
                })
            elif text.lower() in ("cancel", "quit", "stop", "never mind", "nevermind"):
                training_examples.append({
                    "text": text,
                    "intent": "Cancel",
                    "entities": [],
                })
    
    print(f"   Extracted {len(training_examples)} training examples")
    return training_examples


def extract_entities_from_turn(turn: dict) -> List[Dict[str, Any]]:
    """Extract entity labels from a dialogue turn."""
    entities = []
    labels = turn.get("labels", {})
    acts = labels.get("acts", [])
    
    for act in acts:
        act_args = act.get("args", [])
        for arg in act_args:
            key = arg.get("key", "")
            val = arg.get("val", "")
            
            if not val or val == "-1":
                continue
            
            entity_type = map_entity_type(key)
            if entity_type:
                entities.append({
                    "entity": entity_type,
                    "value": str(val),
                })
    
    return entities


def map_entity_type(key: str) -> str:
    """Map Frames dataset keys to CLU entity names."""
    mapping = {
        "or_city": "or_city",
        "dst_city": "dst_city",
        "str_date": "str_date",
        "end_date": "end_date",
        "budget": "budget",
        "price": "budget",
        "max_price": "budget",
    }
    return mapping.get(key, "")


def determine_intent(turn: dict, entities: list) -> str:
    """Determine the intent of a user utterance."""
    labels = turn.get("labels", {})
    acts = labels.get("acts", [])
    
    for act in acts:
        act_name = act.get("name", "").lower()
        if act_name in ("inform", "request", "suggest"):
            if entities:
                return "BookFlight"
    
    # Check text for booking-related keywords
    text = turn.get("text", "").lower()
    booking_keywords = [
        "book", "fly", "flight", "travel", "trip",
        "going to", "want to go", "looking for",
        "departing", "departure", "returning",
    ]
    if any(kw in text for kw in booking_keywords):
        return "BookFlight"
    
    return "None"


def format_for_clu(examples: List[Dict]) -> Dict:
    """
    Format training examples into CLU application JSON format.
    
    Reference: https://learn.microsoft.com/en-us/azure/ai-services/language-service/
    conversational-language-understanding/concepts/data-formats
    """
    intents = set(ex["intent"] for ex in examples)
    entity_types = set()
    for ex in examples:
        for ent in ex.get("entities", []):
            entity_types.add(ent["entity"])
    
    # Build utterances in CLU format
    clu_utterances = []
    for example in examples:
        utterance_entities = []
        for entity in example.get("entities", []):
            entity_value = entity["value"]
            start_pos = example["text"].lower().find(entity_value.lower())
            if start_pos >= 0:
                utterance_entities.append({
                    "category": entity["entity"],
                    "offset": start_pos,
                    "length": len(entity_value),
                })
        
        clu_utterances.append({
            "text": example["text"],
            "language": "en-us",
            "intent": example["intent"],
            "entities": utterance_entities,
            "dataset": "Train",
        })
    
    clu_project = {
        "projectFileVersion": "2022-10-01-preview",
        "stringIndexType": "Utf16CodeUnit",
        "metadata": {
            "projectKind": "Conversation",
            "projectName": "FlyMe-FlightBooking",
            "multilingual": False,
            "description": "FlyMe flight booking chatbot - CLU model",
            "language": "en-us",
        },
        "assets": {
            "projectKind": "Conversation",
            "intents": [{"category": intent} for intent in intents],
            "entities": [{"category": et} for et in entity_types],
            "utterances": clu_utterances,
        },
    }
    
    return clu_project


def split_train_test(examples: list, test_ratio: float = 0.2):
    """Split examples into training and test sets."""
    import random
    random.seed(42)
    random.shuffle(examples)
    
    split_idx = int(len(examples) * (1 - test_ratio))
    train = examples[:split_idx]
    test = examples[split_idx:]
    
    return train, test


def main():
    """Main function to prepare training data."""
    # Check if frames.json exists
    if not os.path.exists(FRAMES_FILE):
        print("❌ Frames dataset not found. Please run download_frames.py first.")
        print(f"   Expected path: {FRAMES_FILE}")
        sys.exit(1)
    
    # Load and process
    frames_data = load_frames_dataset(FRAMES_FILE)
    examples = extract_user_utterances(frames_data)
    
    if not examples:
        print("⚠️ No training examples extracted. Check the dataset format.")
        sys.exit(1)
    
    # Split into train/test
    train_examples, test_examples = split_train_test(examples)
    print(f"\n📊 Data split:")
    print(f"   Training: {len(train_examples)} examples")
    print(f"   Testing:  {len(test_examples)} examples")
    
    # Format for CLU
    train_clu = format_for_clu(train_examples)
    test_clu = format_for_clu(test_examples)
    
    # Save outputs
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(TRAIN_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(train_clu, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Training data saved: {TRAIN_OUTPUT}")
    print(f"   {len(train_clu['assets']['utterances'])} utterances")
    
    with open(TEST_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(test_clu, f, indent=2, ensure_ascii=False)
    print(f"✅ Test data saved: {TEST_OUTPUT}")
    print(f"   {len(test_clu['assets']['utterances'])} utterances")
    
    # Print intent distribution
    intent_counts = {}
    for ex in examples:
        intent_counts[ex["intent"]] = intent_counts.get(ex["intent"], 0) + 1
    print(f"\n📈 Intent distribution:")
    for intent, count in sorted(intent_counts.items()):
        print(f"   {intent}: {count}")


if __name__ == "__main__":
    main()
