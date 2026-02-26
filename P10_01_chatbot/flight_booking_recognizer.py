#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""CLU Recognizer wrapper for the Flight Booking Bot.

Uses the Azure AI Language – Conversational Language Understanding (CLU)
service instead of the deprecated LUIS service.
"""

from azure.core.credentials import AzureKeyCredential
from azure.ai.language.conversations import ConversationAnalysisClient
from botbuilder.core import TurnContext, Recognizer, RecognizerResult

from config import DefaultConfig


class FlightBookingRecognizer(Recognizer):
    """
    CLU recognizer for the Flight Booking Bot.

    Wraps the Azure AI Language ConversationAnalysisClient to provide
    intent recognition and entity extraction for booking flight requests.
    """

    def __init__(self, configuration: DefaultConfig):
        self._client = None
        self._project_name = configuration.CLU_PROJECT_NAME
        self._deployment_name = configuration.CLU_DEPLOYMENT_NAME

        clu_is_configured = (
            configuration.CLU_PROJECT_NAME
            and configuration.CLU_DEPLOYMENT_NAME
            and configuration.CLU_API_KEY
            and configuration.CLU_ENDPOINT
        )

        if clu_is_configured:
            credential = AzureKeyCredential(configuration.CLU_API_KEY)
            self._client = ConversationAnalysisClient(
                configuration.CLU_ENDPOINT, credential
            )

    @property
    def is_configured(self) -> bool:
        """Returns True if CLU is properly configured."""
        return self._client is not None

    async def recognize(self, turn_context: TurnContext) -> RecognizerResult:
        """
        Recognize user intent and entities from the turn context.

        Calls the CLU prediction endpoint and maps the response
        to a Bot Framework RecognizerResult.
        """
        utterance = turn_context.activity.text or ""

        if not utterance.strip():
            return RecognizerResult(
                text=utterance,
                intents={"None": {"score": 1.0}},
                entities={},
            )

        # Call CLU
        result = self._client.analyze_conversation(
            task={
                "kind": "Conversation",
                "analysisInput": {
                    "conversationItem": {
                        "participantId": "user",
                        "id": "1",
                        "modality": "text",
                        "language": "en",
                        "text": utterance,
                    }
                },
                "parameters": {
                    "projectName": self._project_name,
                    "deploymentName": self._deployment_name,
                    "verbose": True,
                },
            }
        )

        # Map CLU response → RecognizerResult
        return self._map_clu_to_recognizer_result(utterance, result)

    @staticmethod
    def _map_clu_to_recognizer_result(
        utterance: str, clu_result: dict
    ) -> RecognizerResult:
        """Convert a CLU prediction response into a RecognizerResult."""
        prediction = clu_result.get("result", {}).get("prediction", {})

        # --- Intents ---
        top_intent = prediction.get("topIntent", "None")
        intents = {}
        for intent_obj in prediction.get("intents", []):
            name = intent_obj.get("category", intent_obj.get("intent", "None"))
            score = intent_obj.get("confidenceScore", 0.0)
            intents[name] = {"score": score}
        if not intents:
            intents = {"None": {"score": 1.0}}

        # --- Entities ---
        entities = {}
        for entity_obj in prediction.get("entities", []):
            category = entity_obj.get("category", "")
            text_value = entity_obj.get("text", "")

            # Check for resolutions (e.g. dates, numbers)
            resolutions = entity_obj.get("resolutions", [])
            if resolutions:
                value = resolutions[0].get("value", text_value)
            else:
                value = text_value

            # Collect as lists (same entity category may appear multiple times)
            if category not in entities:
                entities[category] = []
            entities[category].append(str(value))

        return RecognizerResult(
            text=utterance,
            intents=intents,
            entities=entities,
        )
