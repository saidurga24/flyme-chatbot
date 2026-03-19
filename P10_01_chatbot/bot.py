"""Main bot class for FlyMe."""

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
    Handles incoming activities and delegates to dialogs.
    """

    def __init__(
        self,
        conversation_state: ConversationState,
        user_state: UserState,
        dialog: Dialog,
    ):
        if conversation_state is None:
            raise TypeError("conversation_state is required")
        if user_state is None:
            raise TypeError("user_state is required")
        if dialog is None:
            raise TypeError("dialog is required")

        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog = dialog
        self.dialog_state = self.conversation_state.create_property(
            "DialogState"
        )

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
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
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_text = (
                    "Welcome to **FlyMe** ✈️\n\n"
                    "I can help you book flights. Just tell me:\n"
                    "• Where you're flying from and to\n"
                    "• Your travel dates\n"
                    "• Your budget\n\n"
                    "Type **help** anytime, or **cancel** to start over."
                )
                await turn_context.send_activity(welcome_text)
