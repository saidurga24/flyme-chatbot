#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Booking dialog - waterfall dialog to collect flight booking details."""

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
    Waterfall dialog to collect the 5 flight booking fields:
    1. Origin city (departure)
    2. Destination city
    3. Departure date
    4. Return date
    5. Maximum budget
    
    For each field, it checks if the value was already extracted by LUIS/CLU
    and skips the prompt if so.
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

    async def origin_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for origin city if not already provided."""
        booking_details = step_context.options

        if booking_details.origin is None:
            msg = "From which city will you be departing?"
            prompt_message = MessageFactory.text(
                msg, msg, InputHints.expecting_input
            )
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=prompt_message),
            )

        return await step_context.next(booking_details.origin)

    async def destination_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for destination city if not already provided."""
        booking_details = step_context.options
        booking_details.origin = step_context.result

        if booking_details.destination is None:
            msg = "Where would you like to travel to?"
            prompt_message = MessageFactory.text(
                msg, msg, InputHints.expecting_input
            )
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=prompt_message),
            )

        return await step_context.next(booking_details.destination)

    async def departure_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for departure date if not already provided."""
        booking_details = step_context.options
        booking_details.destination = step_context.result

        if booking_details.departure_date is None:
            msg = "When would you like to depart? (e.g., March 15, 2025)"
            prompt_message = MessageFactory.text(
                msg, msg, InputHints.expecting_input
            )
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=prompt_message),
            )

        return await step_context.next(booking_details.departure_date)

    async def return_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for return date if not already provided."""
        booking_details = step_context.options
        booking_details.departure_date = step_context.result

        if booking_details.return_date is None:
            msg = "When would you like to return? (e.g., March 22, 2025)"
            prompt_message = MessageFactory.text(
                msg, msg, InputHints.expecting_input
            )
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=prompt_message),
            )

        return await step_context.next(booking_details.return_date)

    async def budget_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for maximum budget if not already provided."""
        booking_details = step_context.options
        booking_details.return_date = step_context.result

        if booking_details.budget is None:
            msg = "What is your maximum budget for the tickets? (e.g., $1000)"
            prompt_message = MessageFactory.text(
                msg, msg, InputHints.expecting_input
            )
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(prompt=prompt_message),
            )

        return await step_context.next(booking_details.budget)

    async def confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Present booking summary and ask for confirmation."""
        booking_details = step_context.options
        booking_details.budget = step_context.result

        msg = (
            f"Please confirm your booking details:\n\n"
            f"✈️ **From:** {booking_details.origin}\n"
            f"🛬 **To:** {booking_details.destination}\n"
            f"📅 **Departure:** {booking_details.departure_date}\n"
            f"📅 **Return:** {booking_details.return_date}\n"
            f"💰 **Budget:** {booking_details.budget}\n\n"
            f"Is this correct?"
        )
        prompt_message = MessageFactory.text(
            msg, msg, InputHints.expecting_input
        )
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=prompt_message),
        )

    async def final_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Complete the booking or restart."""
        if step_context.result:
            booking_details = step_context.options
            return await step_context.end_dialog(booking_details)

        await step_context.context.send_activity(
            MessageFactory.text(
                "Booking cancelled. Feel free to start a new booking request!",
                input_hint=InputHints.expecting_input,
            )
        )
        return await step_context.end_dialog()
