#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Cancel and help dialog - base class for handling interruptions."""

from botbuilder.dialogs import (
    ComponentDialog,
    DialogContext,
    DialogTurnResult,
    DialogTurnStatus,
)
from botbuilder.schema import ActivityTypes, InputHints
from botbuilder.core import MessageFactory


class CancelAndHelpDialog(ComponentDialog):
    """
    Base dialog class that handles 'cancel' and 'help' interruptions.
    
    All other dialogs should inherit from this class to get automatic
    support for cancel and help commands.
    """

    def __init__(self, dialog_id: str):
        super(CancelAndHelpDialog, self).__init__(dialog_id)

    async def on_continue_dialog(self, inner_dc: DialogContext) -> DialogTurnResult:
        """Check for interruptions before continuing the dialog."""
        result = await self.interrupt(inner_dc)
        if result is not None:
            return result
        return await super(CancelAndHelpDialog, self).on_continue_dialog(inner_dc)

    async def interrupt(self, inner_dc: DialogContext) -> DialogTurnResult:
        """
        Detect and handle 'cancel' and 'help' interruptions.
        
        Returns None if no interruption was detected.
        """
        if inner_dc.context.activity.type == ActivityTypes.message:
            text = inner_dc.context.activity.text
            if text:
                text = text.strip().lower()
            else:
                return None

            if text in ("help", "?"):
                help_message = MessageFactory.text(
                    "I can help you book a flight! Just tell me where you want to go, "
                    "when you want to travel, and your budget.\n\n"
                    "For example: 'I want to fly from Paris to New York on March 15, "
                    "returning March 22, with a budget of $1000.'\n\n"
                    "Type 'cancel' to start over.",
                    input_hint=InputHints.expecting_input,
                )
                await inner_dc.context.send_activity(help_message)
                return DialogTurnResult(DialogTurnStatus.Waiting)

            if text in ("cancel", "quit", "exit"):
                cancel_message = MessageFactory.text(
                    "Cancelling your booking request. How else can I help you?",
                    input_hint=InputHints.expecting_input,
                )
                await inner_dc.context.send_activity(cancel_message)
                return await inner_dc.cancel_all_dialogs()

        return None
