#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Unit tests for BookingDialog and BookingDetails."""

import pytest
import aiounittest
from unittest.mock import MagicMock

from booking_details import BookingDetails


class TestBookingDetails(aiounittest.AsyncTestCase):
    """Test suite for the BookingDetails data class."""

    async def test_booking_details_creation_with_all_fields(self):
        """Test that BookingDetails correctly stores all 5 fields."""
        details = BookingDetails(
            origin="Paris",
            destination="New York",
            departure_date="2025-03-15",
            return_date="2025-03-22",
            budget="$1000",
        )

        assert details.origin == "Paris"
        assert details.destination == "New York"
        assert details.departure_date == "2025-03-15"
        assert details.return_date == "2025-03-22"
        assert details.budget == "$1000"

    async def test_booking_details_default_values(self):
        """Test that BookingDetails defaults to None for all fields."""
        details = BookingDetails()

        assert details.origin is None
        assert details.destination is None
        assert details.departure_date is None
        assert details.return_date is None
        assert details.budget is None

    async def test_booking_details_to_dict(self):
        """Test BookingDetails to_dict conversion with partial data."""
        details = BookingDetails(
            origin="London",
            destination="Tokyo",
        )
        result = details.to_dict()

        assert result["origin"] == "London"
        assert result["destination"] == "Tokyo"
        assert result["departure_date"] == ""
        assert result["return_date"] == ""
        assert result["budget"] == ""

    async def test_booking_details_to_dict_full(self):
        """Test BookingDetails to_dict conversion with all fields."""
        details = BookingDetails(
            origin="Berlin",
            destination="Rome",
            departure_date="2025-06-01",
            return_date="2025-06-10",
            budget="$500",
        )
        result = details.to_dict()

        assert result["origin"] == "Berlin"
        assert result["destination"] == "Rome"
        assert result["departure_date"] == "2025-06-01"
        assert result["return_date"] == "2025-06-10"
        assert result["budget"] == "$500"

    async def test_booking_details_repr(self):
        """Test BookingDetails string representation."""
        details = BookingDetails(
            origin="Paris",
            destination="London",
        )
        repr_str = repr(details)
        
        assert "Paris" in repr_str
        assert "London" in repr_str
        assert "BookingDetails" in repr_str

    async def test_booking_details_partial_update(self):
        """Test updating individual fields of BookingDetails."""
        details = BookingDetails()
        details.origin = "Madrid"
        details.budget = "€800"

        assert details.origin == "Madrid"
        assert details.budget == "€800"
        assert details.destination is None
        assert details.departure_date is None
        assert details.return_date is None
