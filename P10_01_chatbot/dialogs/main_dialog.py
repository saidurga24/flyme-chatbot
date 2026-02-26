#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Main dialog - entry point dialog with CLU recognition."""

from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions
from botbuilder.core import MessageFactory
from botbuilder.schema import InputHints

from booking_details import BookingDetails
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.clu_helper import CluHelper, Intent
from .booking_dialog import BookingDialog


class MainDialog(ComponentDialog):
    """
    Main dialog that handles the initial user message.
    
    Uses Azure AI Language CLU to recognize intent and extract entities,
    then routes to the appropriate dialog.
    """

    def __init__(
        self,
        clu_recognizer: FlightBookingRecognizer,
        booking_dialog: BookingDialog,
        telemetry_client=None,
    ):
        super(MainDialog, self).__init__(MainDialog.__name__)

        self._clu_recognizer = clu_recognizer
        self._booking_dialog_id = booking_dialog.id

        if telemetry_client:
            self.telemetry_client = telemetry_client

        self.add_dialog(TextPrompt(TextPrompt.__name__))
        self.add_dialog(booking_dialog)
        self.add_dialog(
            WaterfallDialog(
                "WFDialog",
                [self.intro_step, self.act_step, self.final_step],
            )
        )

        self.initial_dialog_id = "WFDialog"

    async def intro_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """
        Introduction step: check if CLU is configured. 
        If not, inform the user. Otherwise, prompt for input.
        """
        if not self._clu_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "⚠️ CLU is not configured. Please check your .env file.\n\n"
                    "You can still test the dialog flow - just tell me about "
                    "your travel plans!",
                    input_hint=InputHints.ignoring_input,
                )
            )
            return await step_context.next(None)

        message_text = (
            str(step_context.options)
            if step_context.options
            else "Hello! I'm your FlyMe travel assistant. ✈️\n\n"
            "I can help you book a flight. Just tell me:\n"
            "• Where you're flying from and to\n"
            "• Your departure and return dates\n"
            "• Your maximum budget\n\n"
            "For example: 'I want to fly from Paris to New York on March 15, "
            "returning March 22, with a budget of $1000.'"
        )
        prompt_message = MessageFactory.text(
            message_text, message_text, InputHints.expecting_input
        )
        return await step_context.prompt(
            TextPrompt.__name__,
            PromptOptions(prompt=prompt_message),
        )

    async def act_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """
        Action step: call CLU to recognize intent and entities,
        then route to the appropriate dialog.
        """
        booking_details = BookingDetails()

        if not self._clu_recognizer.is_configured:
            # CLU not configured - go directly to booking dialog
            # and let user fill in all fields manually
            return await step_context.begin_dialog(
                self._booking_dialog_id, booking_details
            )

        # Call CLU and process the result
        recognizer_result = await self._clu_recognizer.recognize(
            step_context.context
        )

        intent = sorted(
            recognizer_result.intents,
            key=recognizer_result.intents.get,
            reverse=True,
        )[0] if recognizer_result.intents else Intent.NONE_INTENT

        # Track intent for telemetry
        await self._track_intent(step_context, intent, recognizer_result)

        if intent == Intent.BOOK_FLIGHT:
            # Extract booking details from CLU entities
            booking_details = CluHelper.extract_booking_details(
                intent, recognizer_result
            )
            return await step_context.begin_dialog(
                self._booking_dialog_id, booking_details
            )

        elif intent == Intent.GREETING:
            greeting_msg = (
                "Hello! 👋 I'm your FlyMe travel assistant.\n"
                "Tell me about your travel plans and I'll help you book a flight!"
            )
            await step_context.context.send_activity(
                MessageFactory.text(
                    greeting_msg, greeting_msg, InputHints.ignoring_input
                )
            )

        elif intent == Intent.CANCEL:
            cancel_msg = "No problem! Let me know if you need anything else."
            await step_context.context.send_activity(
                MessageFactory.text(
                    cancel_msg, cancel_msg, InputHints.ignoring_input
                )
            )

        else:
            didnt_understand_text = (
                "I'm sorry, I didn't understand that. 🤔\n"
                "I'm a flight booking assistant. Try saying something like:\n"
                "'Book a flight from London to Tokyo on April 1, returning April 10, "
                "budget $2000'"
            )
            await step_context.context.send_activity(
                MessageFactory.text(
                    didnt_understand_text,
                    didnt_understand_text,
                    InputHints.ignoring_input,
                )
            )
            # Track failed comprehension for App Insights alert
            await self._track_failed_comprehension(step_context)

        return await step_context.next(None)

    async def final_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """
        Final step: if a booking was completed, show confirmation.
        Then restart the dialog for the next interaction.
        """
        if step_context.result is not None:
            result = step_context.result
            msg = (
                f"✅ **Booking confirmed!**\n\n"
                f"✈️ {result.origin} → {result.destination}\n"
                f"📅 {result.departure_date} - {result.return_date}\n"
                f"💰 Budget: {result.budget}\n\n"
                f"Your booking request has been submitted. "
                f"A confirmation will be sent to you shortly!"
            )
            await step_context.context.send_activity(
                MessageFactory.text(msg, input_hint=InputHints.ignoring_input)
            )

        prompt_message = "What else can I help you with?"
        return await step_context.replace_dialog(
            self.id, prompt_message
        )

    async def _track_intent(self, step_context, intent, recognizer_result):
        """Track the recognized intent in Application Insights."""
        if self.telemetry_client:
            properties = {
                "intent": intent,
                "score": str(
                    recognizer_result.intents.get(intent, {})
                ),
                "text": step_context.context.activity.text or "",
            }
            self.telemetry_client.track_event(
                "CluIntent", properties
            )

    async def _track_failed_comprehension(self, step_context):
        """Track failed comprehension for Application Insights alerting."""
        if self.telemetry_client:
            properties = {
                "text": step_context.context.activity.text or "",
                "error_type": "comprehension_failure",
            }
            self.telemetry_client.track_event(
                "BotComprehensionFailure", properties
            )
