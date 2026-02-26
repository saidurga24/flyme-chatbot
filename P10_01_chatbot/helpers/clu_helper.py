#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Helper functions for parsing CLU (Azure AI Language) responses."""

from botbuilder.core import RecognizerResult
from booking_details import BookingDetails


class Intent:
    """Known CLU intents."""
    BOOK_FLIGHT = "BookFlight"
    CANCEL = "Cancel"
    NONE_INTENT = "None"
    GREETING = "Greeting"


class CluHelper:
    """Helper class for parsing CLU results into BookingDetails."""

    @staticmethod
    def extract_booking_details(
        intent: str, recognizer_result: RecognizerResult
    ) -> BookingDetails:
        """
        Extract booking details from the CLU recognizer result.

        Parses the entities returned by CLU and maps them to
        BookingDetails fields.
        """
        booking_details = BookingDetails()

        if intent == Intent.BOOK_FLIGHT:
            entities = recognizer_result.entities
            booking_details = CluHelper._parse_entities(entities)

        return booking_details

    @staticmethod
    def _parse_entities(entities: dict) -> BookingDetails:
        """Parse the entities dictionary from CLU response."""
        booking_details = BookingDetails()

        # Origin city
        origin = (
            CluHelper._get_entity_value(entities, "or_city")
            or CluHelper._get_entity_value(entities, "origin")
            or CluHelper._get_entity_value(entities, "From")
        )
        if origin:
            booking_details.origin = origin

        # Destination city
        destination = (
            CluHelper._get_entity_value(entities, "dst_city")
            or CluHelper._get_entity_value(entities, "destination")
            or CluHelper._get_entity_value(entities, "To")
        )
        if destination:
            booking_details.destination = destination

        # Departure date
        departure_date = (
            CluHelper._get_entity_value(entities, "str_date")
            or CluHelper._get_entity_value(entities, "departure_date")
        )
        if departure_date:
            booking_details.departure_date = departure_date

        # Return date
        return_date = (
            CluHelper._get_entity_value(entities, "end_date")
            or CluHelper._get_entity_value(entities, "return_date")
        )
        if return_date:
            booking_details.return_date = return_date

        # Budget
        budget = (
            CluHelper._get_entity_value(entities, "budget")
            or CluHelper._get_entity_value(entities, "money")
            or CluHelper._get_entity_value(entities, "number")
        )
        if budget:
            booking_details.budget = budget

        return booking_details

    @staticmethod
    def _get_entity_value(entities: dict, entity_name: str) -> str:
        """Extract a simple entity value from the entities dict.

        CLU entities are stored as lists of string values by category.
        """
        if entity_name in entities:
            entity = entities[entity_name]
            if isinstance(entity, list) and len(entity) > 0:
                value = entity[0]
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0])
                return str(value)
            return str(entity)
        return None
