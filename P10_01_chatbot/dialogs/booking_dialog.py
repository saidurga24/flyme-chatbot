"""Booking dialog - collects the 5 flight booking fields via waterfall steps."""

from botbuilder.dialogs import (
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions, ConfirmPrompt
from botbuilder.core import MessageFactory
from botbuilder.schema import InputHints

from .cancel_and_help_dialog import CancelAndHelpDialog
from booking_details import BookingDetails


class BookingDialog(CancelAndHelpDialog):
    """
    Walks through each booking field (origin, destination, departure date,
    return date, budget) and skips any that CLU already extracted.
    """

    def __init__(self, dialog_id: str = None):
        super(BookingDialog, self).__init__(
            dialog_id or BookingDialog.__name__
        )

        self.add_dialog(TextPrompt(TextPrompt.__name__))
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

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options

        if booking_details.origin is None:
            msg = "Where will you be departing from?"
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(msg, msg, InputHints.expecting_input)),
            )

        return await step_context.next(booking_details.origin)

    async def destination_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.origin = step_context.result

        if booking_details.destination is None:
            msg = "Where would you like to go?"
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(msg, msg, InputHints.expecting_input)),
            )

        return await step_context.next(booking_details.destination)

    async def departure_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.destination = step_context.result

        if booking_details.departure_date is None:
            msg = "When do you want to leave? (e.g. March 15, 2025)"
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(msg, msg, InputHints.expecting_input)),
            )

        return await step_context.next(booking_details.departure_date)

    async def return_date_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.departure_date = step_context.result

        if booking_details.return_date is None:
            msg = "And when do you want to come back?"
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(msg, msg, InputHints.expecting_input)),
            )

        return await step_context.next(booking_details.return_date)

    async def budget_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.return_date = step_context.result

        if booking_details.budget is None:
            msg = "What's your max budget for the tickets?"
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(msg, msg, InputHints.expecting_input)),
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
