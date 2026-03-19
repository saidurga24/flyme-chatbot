"""Helper for parsing CLU responses into BookingDetails."""

from botbuilder.core import RecognizerResult
from booking_details import BookingDetails


class Intent:
    """Intent name constants matching what's defined in the CLU model."""
    BOOK_FLIGHT = "BookFlight"
    CANCEL = "Cancel"
    NONE_INTENT = "None"
    GREETING = "Greeting"


class CluHelper:
    @staticmethod
    def extract_booking_details(
        intent: str, recognizer_result: RecognizerResult
    ) -> BookingDetails:
        """Pull out booking fields from the CLU recognizer result."""
        booking_details = BookingDetails()

        if intent == Intent.BOOK_FLIGHT:
            entities = recognizer_result.entities
            booking_details = CluHelper._parse_entities(entities)

        return booking_details

    @staticmethod
    def _parse_entities(entities: dict) -> BookingDetails:
        booking_details = BookingDetails()

        # try multiple entity name variants (CLU can use different names)
        origin = (
            CluHelper._get_entity_value(entities, "or_city")
            or CluHelper._get_entity_value(entities, "origin")
            or CluHelper._get_entity_value(entities, "From")
        )
        if origin:
            booking_details.origin = origin

        destination = (
            CluHelper._get_entity_value(entities, "dst_city")
            or CluHelper._get_entity_value(entities, "destination")
            or CluHelper._get_entity_value(entities, "To")
        )
        if destination:
            booking_details.destination = destination

        departure_date = (
            CluHelper._get_entity_value(entities, "str_date")
            or CluHelper._get_entity_value(entities, "departure_date")
        )
        if departure_date:
            booking_details.departure_date = departure_date

        return_date = (
            CluHelper._get_entity_value(entities, "end_date")
            or CluHelper._get_entity_value(entities, "return_date")
        )
        if return_date:
            booking_details.return_date = return_date

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
        """Get the first value for an entity category. CLU stores them as lists."""
        if entity_name in entities:
            entity = entities[entity_name]
            if isinstance(entity, list) and len(entity) > 0:
                value = entity[0]
                if isinstance(value, list) and len(value) > 0:
                    return str(value[0])
                return str(value)
            return str(entity)
        return None
