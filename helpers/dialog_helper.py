#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Dialog helper utility for running dialogs."""

from botbuilder.core import StatePropertyAccessor, TurnContext
from botbuilder.dialogs import Dialog, DialogSet, DialogTurnStatus


class DialogHelper:
    """Helper class for running dialogs from the bot."""

    @staticmethod
    async def run_dialog(
        dialog: Dialog,
        turn_context: TurnContext,
        accessor: StatePropertyAccessor,
    ):
        """
        Run a dialog from the bot's message handler.
        
        Creates a DialogSet, creates a DialogContext, and either continues
        the existing dialog or starts a new one.
        """
        dialog_set = DialogSet(accessor)
        dialog_set.add(dialog)

        dialog_context = await dialog_set.create_context(turn_context)

        results = await dialog_context.continue_dialog()

        if results.status == DialogTurnStatus.Empty:
            await dialog_context.begin_dialog(dialog.id)
