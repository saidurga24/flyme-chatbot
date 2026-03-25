"""Booking dialog - collects the 5 flight booking fields via waterfall steps."""

from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions, ConfirmPrompt, PromptValidatorContext
from botbuilder.core import MessageFactory
from botbuilder.schema import InputHints

from .cancel_and_help_dialog import CancelAndHelpDialog
from booking_details import BookingDetails
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.clu_helper import CluHelper


class BookingDialog(CancelAndHelpDialog):
    """
    Walks through each booking field (origin, destination, departure date,
    return date, budget) and skips any that CLU already extracted.
    """

    def __init__(self, clu_recognizer: FlightBookingRecognizer, dialog_id: str = None):
        super(BookingDialog, self).__init__(
            dialog_id or BookingDialog.__name__
        )

        self._clu_recognizer = clu_recognizer

        self.add_dialog(TextPrompt("OriginPrompt", self.validate_origin_city))
        self.add_dialog(TextPrompt("DestinationPrompt", self.validate_dest_city))
        self.add_dialog(TextPrompt("DatePrompt", self.validate_date))
        self.add_dialog(TextPrompt("BudgetPrompt", self.validate_budget))
        
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(
            WaterfallDialog(
                WaterfallDialog.__name__,
                [
                    self.origin_step,
                    self.destination_step,
                    self.departure_date_step,
                    self.return_date_step,
                    self.budget_step,
                    self.confirm_step,
                    self.final_step,
                ],
            )
        )

        self.initial_dialog_id = WaterfallDialog.__name__

    async def validate_origin_city(self, prompt_context: PromptValidatorContext) -> bool:
        return await self._validate_entity(prompt_context, "origin")

    async def validate_dest_city(self, prompt_context: PromptValidatorContext) -> bool:
        return await self._validate_entity(prompt_context, "destination")

    async def validate_date(self, prompt_context: PromptValidatorContext) -> bool:
        if not prompt_context.recognized.succeeded:
            return False
            
        value = prompt_context.recognized.value
        if value and value.lower() in ["cancel", "quit", "exit"]:
            return True
            
        booking_details = await self._extract_from_clu(prompt_context)
        if booking_details.departure_date:
            prompt_context.recognized.value = booking_details.departure_date
            return True
        if booking_details.return_date:
            # We accept return_date extraction as validity for DatePrompt generally
            prompt_context.recognized.value = booking_details.return_date
            return True
        return False

    async def validate_budget(self, prompt_context: PromptValidatorContext) -> bool:
        return await self._validate_entity(prompt_context, "budget")

    async def _validate_entity(self, prompt_context: PromptValidatorContext, property_name: str) -> bool:
        if not prompt_context.recognized.succeeded:
            return False
            
        value = prompt_context.recognized.value
        if value and value.lower() in ["cancel", "quit", "exit"]:
            return True
            
        booking_details = await self._extract_from_clu(prompt_context)
        extracted_val = getattr(booking_details, property_name, None)
        if extracted_val:
            prompt_context.recognized.value = extracted_val
            return True
        return False

    async def _extract_from_clu(self, prompt_context: PromptValidatorContext):
        if not self._clu_recognizer.is_configured:
            bd = BookingDetails()
            setattr(bd, "origin", prompt_context.recognized.value)
            setattr(bd, "destination", prompt_context.recognized.value)
            setattr(bd, "departure_date", prompt_context.recognized.value)
            setattr(bd, "return_date", prompt_context.recognized.value)
            setattr(bd, "budget", prompt_context.recognized.value)
            return bd

        recognizer_result = await self._clu_recognizer.recognize(prompt_context.context)
        intent = sorted(
            recognizer_result.intents,
            key=lambda k: recognizer_result.intents[k].get("score", 0.0),
            reverse=True,
        )[0] if recognizer_result.intents else None
        
        return CluHelper.extract_booking_details(intent, recognizer_result)

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options

        if booking_details.origin is None:
            msg = "Where will you be departing from?"
            retry_msg = "I couldn't quite catch the city name. Where are you flying from?"
            return await step_context.prompt(
                "OriginPrompt",
                PromptOptions(
                    prompt=MessageFactory.text(msg, msg, InputHints.expecting_input),
                    retry_prompt=MessageFactory.text(retry_msg, retry_msg, InputHints.expecting_input)
                ),
            )

        return await step_context.next(booking_details.origin)

    async def destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.origin = step_context.result

        if booking_details.destination is None:
            msg = "Where would you like to go?"
            retry_msg = "That doesn't look like a valid city. Where are you flying to?"
            return await step_context.prompt(
                "DestinationPrompt",
                PromptOptions(
                    prompt=MessageFactory.text(msg, msg, InputHints.expecting_input),
                    retry_prompt=MessageFactory.text(retry_msg, retry_msg, InputHints.expecting_input)
                ),
            )

        return await step_context.next(booking_details.destination)

    async def departure_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.destination = step_context.result

        if booking_details.departure_date is None:
            msg = "When do you want to leave? (e.g. March 15, 2025)"
            retry_msg = "Please provide a valid departure date containing a month and day."
            return await step_context.prompt(
                "DatePrompt",
                PromptOptions(
                    prompt=MessageFactory.text(msg, msg, InputHints.expecting_input),
                    retry_prompt=MessageFactory.text(retry_msg, retry_msg, InputHints.expecting_input)
                ),
            )

        return await step_context.next(booking_details.departure_date)

    async def return_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.departure_date = step_context.result

        if booking_details.return_date is None:
            msg = "And when do you want to come back?"
            retry_msg = "I didn't understand that return date. When will you be coming back?"
            return await step_context.prompt(
                "DatePrompt",
                PromptOptions(
                    prompt=MessageFactory.text(msg, msg, InputHints.expecting_input),
                    retry_prompt=MessageFactory.text(retry_msg, retry_msg, InputHints.expecting_input)
                ),
            )

        return await step_context.next(booking_details.return_date)

    async def budget_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.return_date = step_context.result

        if booking_details.budget is None:
            msg = "What's your max budget for the tickets?"
            retry_msg = "I couldn't detect a currency or real amount. What is your maximum budget?"
            return await step_context.prompt(
                "BudgetPrompt",
                PromptOptions(
                    prompt=MessageFactory.text(msg, msg, InputHints.expecting_input),
                    retry_prompt=MessageFactory.text(retry_msg, retry_msg, InputHints.expecting_input)
                ),
            )

        return await step_context.next(booking_details.budget)

    async def confirm_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.budget = step_context.result

        msg = (
            f"Here's what I have:\n\n"
            f"From: {booking_details.origin}\n"
            f"To: {booking_details.destination}\n"
            f"Departure: {booking_details.departure_date}\n"
            f"Return: {booking_details.return_date}\n"
            f"Budget: {booking_details.budget}\n\n"
            f"Does that look right?"
        )
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(msg, msg, InputHints.expecting_input)),
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if step_context.result:
            booking_details = step_context.options
            return await step_context.end_dialog(booking_details)

        await step_context.context.send_activity(
            MessageFactory.text(
                "No worries, booking cancelled. Let me know if you want to try again!",
                input_hint=InputHints.expecting_input,
            )
        )
        return await step_context.end_dialog()
