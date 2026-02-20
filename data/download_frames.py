#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""
Download the Frames dataset from Microsoft Research.

The Frames dataset contains 1,369 human-human dialogues about booking
vacation packages (flights + hotels). It was developed by Maluuba/Microsoft.

Dataset paper: https://arxiv.org/abs/1704.00057
"""

import os
import json
import urllib.request
import sys


FRAMES_URL = "https://raw.githubusercontent.com/Maluuba/frames/master/frames.json"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "frames.json")


def download_frames_dataset():
    """Download the Frames dataset JSON file."""
    if os.path.exists(OUTPUT_FILE):
        print(f"✅ Frames dataset already exists at: {OUTPUT_FILE}")
        file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"   File size: {file_size:.2f} MB")
        return OUTPUT_FILE

    print(f"📥 Downloading Frames dataset from: {FRAMES_URL}")
    print(f"   Saving to: {OUTPUT_FILE}")

    try:
        urllib.request.urlretrieve(FRAMES_URL, OUTPUT_FILE)
        file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"✅ Download complete! File size: {file_size:.2f} MB")

        # Validate JSON
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"   Contains {len(data)} dialogues")

        return OUTPUT_FILE

    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        sys.exit(1)


if __name__ == "__main__":
    download_frames_dataset()
