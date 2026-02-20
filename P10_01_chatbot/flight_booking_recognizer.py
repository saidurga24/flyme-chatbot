#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""LUIS/CLU Recognizer wrapper for the Flight Booking Bot."""

from botbuilder.ai.luis import LuisApplication, LuisRecognizer
from botbuilder.core import TurnContext, Recognizer, RecognizerResult

from config import DefaultConfig


class FlightBookingRecognizer(Recognizer):
    """
    LUIS/CLU recognizer for the Flight Booking Bot.
    
    Wraps the LuisRecognizer to provide intent recognition and entity extraction
    for booking flight requests.
    """

    def __init__(self, configuration: DefaultConfig):
        self._recognizer = None

        luis_is_configured = (
            configuration.LUIS_APP_ID
            and configuration.LUIS_API_KEY
            and configuration.LUIS_API_HOST_NAME
        )

        if luis_is_configured:
            luis_application = LuisApplication(
                configuration.LUIS_APP_ID,
                configuration.LUIS_API_KEY,
                "https://" + configuration.LUIS_API_HOST_NAME,
            )

            self._recognizer = LuisRecognizer(
                luis_application,
                prediction_options={"include_all_intents": True},
                include_api_results=True,
            )

    @property
    def is_configured(self) -> bool:
        """Returns True if LUIS is properly configured."""
        return self._recognizer is not None

    async def recognize(self, turn_context: TurnContext) -> RecognizerResult:
        """
        Recognize user intent and entities from the turn context.
        
        Returns a RecognizerResult with intents and entities.
        """
        return await self._recognizer.recognize(turn_context)
