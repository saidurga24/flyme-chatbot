"""Base dialog that handles 'cancel' and 'help' interruptions."""

from botbuilder.dialogs import (
    ComponentDialog,
    DialogContext,
    DialogTurnResult,
    DialogTurnStatus,
)
from botbuilder.schema import ActivityTypes, InputHints
from botbuilder.core import MessageFactory


class CancelAndHelpDialog(ComponentDialog):
    """Other dialogs inherit from this to get cancel/help support."""

    def __init__(self, dialog_id: str):
        super(CancelAndHelpDialog, self).__init__(dialog_id)

    async def on_continue_dialog(self, inner_dc: DialogContext) -> DialogTurnResult:
        result = await self.interrupt(inner_dc)
        if result is not None:
            return result
        return await super(CancelAndHelpDialog, self).on_continue_dialog(inner_dc)

    async def interrupt(self, inner_dc: DialogContext) -> DialogTurnResult:
        """Check if the user typed 'cancel' or 'help'."""
        if inner_dc.context.activity.type == ActivityTypes.message:
            text = inner_dc.context.activity.text
            if text:
                text = text.strip().lower()
            else:
                return None

            if text in ("help", "?"):
                help_msg = MessageFactory.text(
                    "I can help you book a flight! Just tell me your origin, "
                    "destination, dates, and budget.\n\n"
                    "Type 'cancel' to start over.",
                    input_hint=InputHints.expecting_input,
                )
                await inner_dc.context.send_activity(help_msg)
                return DialogTurnResult(DialogTurnStatus.Waiting)

            if text in ("cancel", "quit", "exit"):
                cancel_msg = MessageFactory.text(
                    "Alright, cancelling. How else can I help?",
                    input_hint=InputHints.expecting_input,
                )
                await inner_dc.context.send_activity(cancel_msg)
                return await inner_dc.cancel_all_dialogs()

        return None
