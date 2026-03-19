"""Tests for CluHelper entity extraction."""

import pytest
from botbuilder.core import RecognizerResult
from helpers.clu_helper import CluHelper, Intent
from booking_details import BookingDetails


class TestCluHelper:

    def test_all_entities(self):
        result = RecognizerResult()
        result.intents = {"BookFlight": {"score": 0.95}}
        result.entities = {
            "or_city": ["Paris"],
            "dst_city": ["New York"],
            "str_date": ["2025-03-15"],
            "end_date": ["2025-03-22"],
            "budget": ["1000"],
        }

        details = CluHelper.extract_booking_details(Intent.BOOK_FLIGHT, result)

        assert isinstance(details, BookingDetails)
        assert details.origin == "Paris"
        assert details.destination == "New York"
        assert details.departure_date == "2025-03-15"
        assert details.return_date == "2025-03-22"
        assert details.budget == "1000"

    def test_partial_entities(self):
        result = RecognizerResult()
        result.intents = {"BookFlight": {"score": 0.85}}
        result.entities = {
            "or_city": ["London"],
            "dst_city": ["Tokyo"],
        }

        details = CluHelper.extract_booking_details(Intent.BOOK_FLIGHT, result)

        assert details.origin == "London"
        assert details.destination == "Tokyo"
        assert details.departure_date is None
        assert details.budget is None

    def test_no_entities(self):
        result = RecognizerResult()
        result.intents = {"BookFlight": {"score": 0.7}}
        result.entities = {}

        details = CluHelper.extract_booking_details(Intent.BOOK_FLIGHT, result)
        assert details.origin is None

    def test_wrong_intent_returns_empty(self):
        result = RecognizerResult()
        result.intents = {"Greeting": {"score": 0.9}}
        result.entities = {"or_city": ["Paris"]}

        details = CluHelper.extract_booking_details(Intent.GREETING, result)
        assert details.origin is None

    def test_alternative_entity_names(self):
        """CLU might use From/To instead of or_city/dst_city."""
        result = RecognizerResult()
        result.intents = {"BookFlight": {"score": 0.9}}
        result.entities = {"From": ["Berlin"], "To": ["Rome"]}

        details = CluHelper.extract_booking_details(Intent.BOOK_FLIGHT, result)
        assert details.origin == "Berlin"
        assert details.destination == "Rome"

    def test_money_entity(self):
        result = RecognizerResult()
        result.intents = {"BookFlight": {"score": 0.9}}
        result.entities = {"money": ["500"]}

        details = CluHelper.extract_booking_details(Intent.BOOK_FLIGHT, result)
        assert details.budget == "500"

    def test_intent_constants(self):
        assert Intent.BOOK_FLIGHT == "BookFlight"
        assert Intent.CANCEL == "Cancel"
        assert Intent.NONE_INTENT == "None"
        assert Intent.GREETING == "Greeting"
