"""
Prepare training data for CLU from the Frames dataset.

Parses Frames dialogues to extract utterances with intents and entities:
  - Intent: BookFlight (+ Greeting, Cancel)
  - Entities: or_city, dst_city, str_date, end_date, budget

Outputs CLU-compatible JSON for import.
"""

import json
import os
import sys
import re
from typing import List, Dict, Any


DATA_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMES_FILE = os.path.join(DATA_DIR, "..", "data", "frames", "frames.json")
OUTPUT_DIR = DATA_DIR
TRAIN_OUTPUT = os.path.join(OUTPUT_DIR, "clu_train_data.json")
TEST_OUTPUT = os.path.join(OUTPUT_DIR, "clu_test_data.json")


def load_frames_dataset(filepath: str) -> list:
    print(f"Loading dataset from {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  {len(data)} dialogues loaded")
    return data


def extract_user_utterances(frames_data: list) -> List[Dict[str, Any]]:
    """Go through all dialogues and pull out user turns with entity labels."""
    training_examples = []

    for dialogue in frames_data:
        turns = dialogue.get("turns", [])

        for turn in turns:
            author = turn.get("author", "")
            text = turn.get("text", "").strip()

            if author != "user" or not text:
                continue

            entities = extract_entities_from_turn(turn)
            intent = determine_intent(turn, entities)

            if intent == "BookFlight" and entities:
                training_examples.append({
                    "text": text,
                    "intent": intent,
                    "entities": entities,
                })
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

    print(f"  Extracted {len(training_examples)} examples")
    return training_examples


def extract_entities_from_turn(turn: dict) -> List[Dict[str, Any]]:
    entities = []
    labels = turn.get("labels", {})
    acts = labels.get("acts", [])

    for act in acts:
        for arg in act.get("args", []):
            key = arg.get("key", "")
            val = arg.get("val", "")

            if not val or val == "-1":
                continue

            entity_type = map_entity_type(key)
            if entity_type:
                entities.append({"entity": entity_type, "value": str(val)})

    return entities


def map_entity_type(key: str) -> str:
    """Map Frames dataset field names to our CLU entity names."""
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
    labels = turn.get("labels", {})
    acts = labels.get("acts", [])

    for act in acts:
        act_name = act.get("name", "").lower()
        if act_name in ("inform", "request", "suggest"):
            if entities:
                return "BookFlight"

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
    """Build the CLU import JSON structure."""
    intents = set(ex["intent"] for ex in examples)
    entity_types = set()
    for ex in examples:
        for ent in ex.get("entities", []):
            entity_types.add(ent["entity"])

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

    return {
        "projectFileVersion": "2022-10-01-preview",
        "stringIndexType": "Utf16CodeUnit",
        "metadata": {
            "projectKind": "Conversation",
            "projectName": "FlyMe-FlightBooking",
            "multilingual": False,
            "description": "FlyMe flight booking chatbot",
            "language": "en-us",
        },
        "assets": {
            "projectKind": "Conversation",
            "intents": [{"category": i} for i in intents],
            "entities": [{"category": e} for e in entity_types],
            "utterances": clu_utterances,
        },
    }


def split_train_test(examples: list, test_ratio: float = 0.2):
    import random
    random.seed(42)
    random.shuffle(examples)

    split_idx = int(len(examples) * (1 - test_ratio))
    return examples[:split_idx], examples[split_idx:]


def main():
    if not os.path.exists(FRAMES_FILE):
        print(f"Error: Frames dataset not found at {FRAMES_FILE}")
        print("Run download_frames.py first.")
        sys.exit(1)

    frames_data = load_frames_dataset(FRAMES_FILE)
    examples = extract_user_utterances(frames_data)

    if not examples:
        print("No training examples extracted - check the dataset.")
        sys.exit(1)

    train_examples, test_examples = split_train_test(examples)
    print(f"\nTrain: {len(train_examples)}, Test: {len(test_examples)}")

    train_clu = format_for_clu(train_examples)
    test_clu = format_for_clu(test_examples)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(TRAIN_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(train_clu, f, indent=2, ensure_ascii=False)
    print(f"Saved training data: {TRAIN_OUTPUT} ({len(train_clu['assets']['utterances'])} utterances)")

    with open(TEST_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(test_clu, f, indent=2, ensure_ascii=False)
    print(f"Saved test data: {TEST_OUTPUT} ({len(test_clu['assets']['utterances'])} utterances)")

    # show intent counts
    intent_counts = {}
    for ex in examples:
        intent_counts[ex["intent"]] = intent_counts.get(ex["intent"], 0) + 1
    print("\nIntent distribution:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count}")


if __name__ == "__main__":
    main()
