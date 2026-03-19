"""Tests for BookingDetails."""

import aiounittest
from booking_details import BookingDetails


class TestBookingDetails(aiounittest.AsyncTestCase):

    async def test_all_fields(self):
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

    async def test_defaults_are_none(self):
        details = BookingDetails()
        assert details.origin is None
        assert details.destination is None
        assert details.departure_date is None
        assert details.return_date is None
        assert details.budget is None

    async def test_to_dict_partial(self):
        details = BookingDetails(origin="London", destination="Tokyo")
        result = details.to_dict()

        assert result["origin"] == "London"
        assert result["destination"] == "Tokyo"
        assert result["departure_date"] == ""
        assert result["return_date"] == ""
        assert result["budget"] == ""

    async def test_to_dict_full(self):
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

    async def test_repr(self):
        details = BookingDetails(origin="Paris", destination="London")
        r = repr(details)
        assert "Paris" in r
        assert "London" in r

    async def test_field_update(self):
        details = BookingDetails()
        details.origin = "Madrid"
        details.budget = "€800"

        assert details.origin == "Madrid"
        assert details.budget == "€800"
        assert details.destination is None
