#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Flight Booking Bot - main bot class."""

from botbuilder.core import (
    ActivityHandler,
    ConversationState,
    TurnContext,
    UserState,
)
from botbuilder.dialogs import Dialog
from botbuilder.schema import ChannelAccount
from helpers.dialog_helper import DialogHelper


class FlightBookingBot(ActivityHandler):
    """
    Main bot class for the FlyMe Flight Booking Bot.
    
    Extends ActivityHandler to handle incoming activities (messages, 
    member additions, etc.) and delegate to dialogs.
    """

    def __init__(
        self,
        conversation_state: ConversationState,
        user_state: UserState,
        dialog: Dialog,
    ):
        if conversation_state is None:
            raise TypeError(
                "FlightBookingBot: conversation_state is required."
            )
        if user_state is None:
            raise TypeError("FlightBookingBot: user_state is required.")
        if dialog is None:
            raise TypeError("FlightBookingBot: dialog is required.")

        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog = dialog
        self.dialog_state = self.conversation_state.create_property(
            "DialogState"
        )

    async def on_turn(self, turn_context: TurnContext):
        """Process every incoming activity."""
        await super().on_turn(turn_context)
        # Save any state changes
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming message activities by running the dialog."""
        await DialogHelper.run_dialog(
            self.dialog,
            turn_context,
            self.dialog_state,
        )

    async def on_members_added_activity(
        self,
        members_added: list[ChannelAccount],
        turn_context: TurnContext,
    ):
        """Send a welcome message when new members join the conversation."""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_text = (
                    "Welcome to **FlyMe** ✈️ - Your Travel Booking Assistant!\n\n"
                    "I can help you find and book flights. Just tell me:\n"
                    "• 🏙️ Where you're flying from and to\n"
                    "• 📅 Your departure and return dates\n"
                    "• 💰 Your maximum budget\n\n"
                    "Type **help** at any time for assistance, "
                    "or **cancel** to start over."
                )
                await turn_context.send_activity(welcome_text)
