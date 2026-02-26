#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Unit tests for CLU Helper entity extraction."""

import pytest
from unittest.mock import MagicMock

from botbuilder.core import RecognizerResult
from helpers.clu_helper import CluHelper, Intent
from booking_details import BookingDetails


class TestCluHelper:
    """Test suite for the CluHelper class."""

    def test_extract_booking_details_with_all_entities(self):
        """Test extraction of all 5 entity types from a CLU response."""
        recognizer_result = RecognizerResult()
        recognizer_result.intents = {"BookFlight": {"score": 0.95}}
        recognizer_result.entities = {
            "or_city": ["Paris"],
            "dst_city": ["New York"],
            "str_date": ["2025-03-15"],
            "end_date": ["2025-03-22"],
            "budget": ["1000"],
        }

        result = CluHelper.extract_booking_details(
            Intent.BOOK_FLIGHT, recognizer_result
        )

        assert isinstance(result, BookingDetails)
        assert result.origin == "Paris"
        assert result.destination == "New York"
        assert result.departure_date == "2025-03-15"
        assert result.return_date == "2025-03-22"
        assert result.budget == "1000"

    def test_extract_booking_details_with_partial_entities(self):
        """Test extraction when only some entities are present."""
        recognizer_result = RecognizerResult()
        recognizer_result.intents = {"BookFlight": {"score": 0.85}}
        recognizer_result.entities = {
            "or_city": ["London"],
            "dst_city": ["Tokyo"],
        }

        result = CluHelper.extract_booking_details(
            Intent.BOOK_FLIGHT, recognizer_result
        )

        assert result.origin == "London"
        assert result.destination == "Tokyo"
        assert result.departure_date is None
        assert result.return_date is None
        assert result.budget is None

    def test_extract_booking_details_no_entities(self):
        """Test extraction when no entities are present."""
        recognizer_result = RecognizerResult()
        recognizer_result.intents = {"BookFlight": {"score": 0.7}}
        recognizer_result.entities = {}

        result = CluHelper.extract_booking_details(
            Intent.BOOK_FLIGHT, recognizer_result
        )

        assert result.origin is None
        assert result.destination is None

    def test_extract_booking_details_wrong_intent(self):
        """Test that non-BookFlight intents return empty booking details."""
        recognizer_result = RecognizerResult()
        recognizer_result.intents = {"Greeting": {"score": 0.9}}
        recognizer_result.entities = {
            "or_city": ["Paris"],
        }

        result = CluHelper.extract_booking_details(
            Intent.GREETING, recognizer_result
        )

        assert result.origin is None
        assert result.destination is None

    def test_extract_with_alternative_entity_names(self):
        """Test extraction with alternative entity naming (From/To format)."""
        recognizer_result = RecognizerResult()
        recognizer_result.intents = {"BookFlight": {"score": 0.9}}
        recognizer_result.entities = {
            "From": ["Berlin"],
            "To": ["Rome"],
        }

        result = CluHelper.extract_booking_details(
            Intent.BOOK_FLIGHT, recognizer_result
        )

        assert result.origin == "Berlin"
        assert result.destination == "Rome"

    def test_extract_money_entity(self):
        """Test extraction of money/budget entity."""
        recognizer_result = RecognizerResult()
        recognizer_result.intents = {"BookFlight": {"score": 0.9}}
        recognizer_result.entities = {
            "money": ["500"],
        }

        result = CluHelper.extract_booking_details(
            Intent.BOOK_FLIGHT, recognizer_result
        )

        assert result.budget == "500"

    def test_intent_constants(self):
        """Test that intent constants are defined correctly."""
        assert Intent.BOOK_FLIGHT == "BookFlight"
        assert Intent.CANCEL == "Cancel"
        assert Intent.NONE_INTENT == "None"
        assert Intent.GREETING == "Greeting"
