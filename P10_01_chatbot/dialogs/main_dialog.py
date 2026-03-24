"""Main dialog - handles CLU intent recognition and routes to booking."""

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
        if not self._clu_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "CLU is not configured. Check your .env file.\n\n"
                    "You can still test the dialog flow though - "
                    "tell me about your trip!",
                    input_hint=InputHints.ignoring_input,
                )
            )
            return await step_context.next(None)

        message_text = (
            str(step_context.options)
            if step_context.options
            else "What flight are you looking for?\n\n"
            "Tell me where you want to go, your dates, and your budget."
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
        """Recognize the intent and route accordingly."""
        booking_details = BookingDetails()

        if not self._clu_recognizer.is_configured:
            # no CLU - let user fill everything manually
            return await step_context.begin_dialog(
                self._booking_dialog_id, booking_details
            )

        recognizer_result = await self._clu_recognizer.recognize(
            step_context.context
        )

        intent = sorted(
            recognizer_result.intents,
            key=lambda k: recognizer_result.intents[k].get("score", 0.0),
            reverse=True,
        )[0] if recognizer_result.intents else Intent.NONE_INTENT

        # log to App Insights
        await self._track_intent(step_context, intent, recognizer_result)

        if intent == Intent.BOOK_FLIGHT:
            booking_details = CluHelper.extract_booking_details(
                intent, recognizer_result
            )
            return await step_context.begin_dialog(
                self._booking_dialog_id, booking_details
            )

        elif intent == Intent.GREETING:
            msg = "Hey! Tell me about your travel plans and I'll help you book a flight."
            await step_context.context.send_activity(
                MessageFactory.text(msg, msg, InputHints.ignoring_input)
            )

        elif intent == Intent.CANCEL:
            msg = "No problem! Let me know if you need anything."
            await step_context.context.send_activity(
                MessageFactory.text(msg, msg, InputHints.ignoring_input)
            )

        else:
            msg = (
                "Sorry, I didn't quite get that.\n"
                "Try something like: 'Book a flight from London to Tokyo "
                "on April 1, returning April 10, budget $2000'"
            )
            await step_context.context.send_activity(
                MessageFactory.text(msg, msg, InputHints.ignoring_input)
            )
            await self._track_failed_comprehension(step_context)

        return await step_context.next(None)

    async def final_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Show booking confirmation if completed, then restart."""
        if step_context.result is not None:
            result = step_context.result
            msg = (
                f"Booking confirmed!\n\n"
                f"From: {result.origin}\n"
                f"To: {result.destination}\n"
                f"Dates: {result.departure_date} - {result.return_date}\n"
                f"Budget: {result.budget}\n\n"
                f"You'll receive a confirmation shortly."
            )
            await step_context.context.send_activity(
                MessageFactory.text(msg, input_hint=InputHints.ignoring_input)
            )

        prompt_message = "What else can I help with?"
        return await step_context.replace_dialog(
            self.id, prompt_message
        )

    async def _track_intent(self, step_context, intent, recognizer_result):
        if self.telemetry_client:
            self.telemetry_client.track_event(
                "CluIntent",
                {
                    "intent": intent,
                    "score": str(recognizer_result.intents.get(intent, {})),
                    "text": step_context.context.activity.text or "",
                },
            )

    async def _track_failed_comprehension(self, step_context):
        if self.telemetry_client:
            self.telemetry_client.track_event(
                "BotComprehensionFailure",
                {
                    "text": step_context.context.activity.text or "",
                    "error_type": "comprehension_failure",
                },
            )
