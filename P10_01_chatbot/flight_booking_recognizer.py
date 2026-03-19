"""
CLU Recognizer - wraps the Azure AI Language conversation analysis client.

Replaces the deprecated LUIS service with CLU for intent/entity recognition.
"""

from azure.core.credentials import AzureKeyCredential
from azure.ai.language.conversations import ConversationAnalysisClient
from botbuilder.core import TurnContext, Recognizer, RecognizerResult

from config import DefaultConfig


class FlightBookingRecognizer(Recognizer):
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
        return self._client is not None

    async def recognize(self, turn_context: TurnContext) -> RecognizerResult:
        """Send the user's message to CLU and return the recognized intent + entities."""
        utterance = turn_context.activity.text or ""

        if not utterance.strip():
            return RecognizerResult(
                text=utterance,
                intents={"None": {"score": 1.0}},
                entities={},
            )

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

        return self._map_clu_to_recognizer_result(utterance, result)

    @staticmethod
    def _map_clu_to_recognizer_result(
        utterance: str, clu_result: dict
    ) -> RecognizerResult:
        """Convert the CLU API response into a Bot Framework RecognizerResult."""
        prediction = clu_result.get("result", {}).get("prediction", {})

        # intents
        top_intent = prediction.get("topIntent", "None")
        intents = {}
        for intent_obj in prediction.get("intents", []):
            name = intent_obj.get("category", intent_obj.get("intent", "None"))
            score = intent_obj.get("confidenceScore", 0.0)
            intents[name] = {"score": score}
        if not intents:
            intents = {"None": {"score": 1.0}}

        # entities
        entities = {}
        for entity_obj in prediction.get("entities", []):
            category = entity_obj.get("category", "")
            text_value = entity_obj.get("text", "")

            # use resolved value if available (dates, numbers, etc.)
            resolutions = entity_obj.get("resolutions", [])
            if resolutions:
                value = resolutions[0].get("value", text_value)
            else:
                value = text_value

            if category not in entities:
                entities[category] = []
            entities[category].append(str(value))

        return RecognizerResult(
            text=utterance,
            intents=intents,
            entities=entities,
        )
