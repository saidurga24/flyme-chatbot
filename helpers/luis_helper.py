#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Helper functions for parsing LUIS/CLU responses."""

from botbuilder.core import RecognizerResult
from booking_details import BookingDetails


class Intent:
    """Known LUIS/CLU intents."""
    BOOK_FLIGHT = "BookFlight"
    CANCEL = "Cancel"
    NONE_INTENT = "None"
    GREETING = "Greeting"


class LuisHelper:
    """Helper class for parsing LUIS/CLU results into BookingDetails."""

    @staticmethod
    def extract_booking_details(
        intent: str, recognizer_result: RecognizerResult
    ) -> BookingDetails:
        """
        Extract booking details from the LUIS/CLU recognizer result.
        
        Parses the entities returned by LUIS/CLU and maps them to
        BookingDetails fields.
        """
        booking_details = BookingDetails()

        if intent == Intent.BOOK_FLIGHT:
            entities = recognizer_result.entities
            booking_details = LuisHelper._parse_entities(entities)

        return booking_details

    @staticmethod
    def _parse_entities(entities: dict) -> BookingDetails:
        """Parse the entities dictionary from LUIS/CLU response."""
        booking_details = BookingDetails()

        # Origin city
        origin = (
            LuisHelper._get_entity_value(entities, "or_city")
            or LuisHelper._get_entity_value(entities, "origin")
            or LuisHelper._get_entity_value(entities, "From")
            or LuisHelper._get_composite_entity(entities, "From", "Airport")
        )
        if origin:
            booking_details.origin = origin

        # Destination city
        destination = (
            LuisHelper._get_entity_value(entities, "dst_city")
            or LuisHelper._get_entity_value(entities, "destination")
            or LuisHelper._get_entity_value(entities, "To")
            or LuisHelper._get_composite_entity(entities, "To", "Airport")
        )
        if destination:
            booking_details.destination = destination

        # Departure date
        departure_date = (
            LuisHelper._get_entity_value(entities, "str_date")
            or LuisHelper._get_entity_value(entities, "departure_date")
            or LuisHelper._get_datetime_entity(entities, "datetime", 0)
        )
        if departure_date:
            booking_details.departure_date = departure_date

        # Return date
        return_date = (
            LuisHelper._get_entity_value(entities, "end_date")
            or LuisHelper._get_entity_value(entities, "return_date")
            or LuisHelper._get_datetime_entity(entities, "datetime", 1)
        )
        if return_date:
            booking_details.return_date = return_date

        # Budget
        budget = (
            LuisHelper._get_entity_value(entities, "budget")
            or LuisHelper._get_money_entity(entities)
        )
        if budget:
            booking_details.budget = budget

        return booking_details

    @staticmethod
    def _get_entity_value(entities: dict, entity_name: str) -> str:
        """Extract a simple entity value from the entities dict."""
        if entity_name in entities:
            entity = entities[entity_name]
            if isinstance(entity, list) and len(entity) > 0:
                value = entity[0]
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0])
                return str(value)
            return str(entity)
        return None

    @staticmethod
    def _get_composite_entity(
        entities: dict, composite_name: str, child_name: str
    ) -> str:
        """Extract a value from a composite entity."""
        if composite_name in entities:
            composite = entities[composite_name]
            if isinstance(composite, list) and len(composite) > 0:
                first = composite[0]
                if isinstance(first, dict) and child_name in first:
                    children = first[child_name]
                    if isinstance(children, list) and len(children) > 0:
                        return str(children[0][0]) if isinstance(
                            children[0], list
                        ) else str(children[0])
        return None

    @staticmethod
    def _get_datetime_entity(
        entities: dict, entity_name: str, index: int
    ) -> str:
        """Extract a datetime entity value by index."""
        if entity_name in entities:
            datetimes = entities[entity_name]
            if isinstance(datetimes, list) and len(datetimes) > index:
                dt = datetimes[index]
                if isinstance(dt, dict):
                    if "timex" in dt:
                        timex = dt["timex"]
                        if isinstance(timex, list) and len(timex) > 0:
                            return str(timex[0])
                    if "value" in dt:
                        return str(dt["value"])
                return str(dt)
        return None

    @staticmethod
    def _get_money_entity(entities: dict) -> str:
        """Extract a money/currency entity value."""
        for key in ["money", "number", "builtin_money"]:
            if key in entities:
                value = entities[key]
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0])
                return str(value)
        return None
