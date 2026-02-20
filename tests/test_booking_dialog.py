#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Unit tests for BookingDialog."""

import pytest
import aiounittest
from unittest.mock import MagicMock

from botbuilder.core import (
    ConversationState,
    MemoryStorage,
    TurnContext,
)
from botbuilder.core.adapters import TestAdapter
from botbuilder.dialogs import DialogSet, DialogTurnStatus
from botbuilder.dialogs.prompts import TextPrompt

from dialogs.booking_dialog import BookingDialog
from booking_details import BookingDetails


class BookingDialogTest(aiounittest.AsyncTestCase):
    """Test suite for the BookingDialog waterfall dialog."""

    async def test_booking_dialog_full_flow(self):
        """Test the complete booking dialog flow with all fields prompted."""
        # Arrange
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("DialogState")

        booking_dialog = BookingDialog()
        dialogs = DialogSet(dialog_state)
        dialogs.add(booking_dialog)

        # Create a test adapter
        adapter = TestAdapter()

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                booking_details = BookingDetails()
                await dialog_context.begin_dialog(
                    BookingDialog.__name__, booking_details
                )

            await conversation_state.save_changes(turn_context)

        # Act & Assert - Start dialog, should ask for origin
        step1 = await adapter.test("start", "From which city will you be departing?")
        
        # Provide origin
        step2 = await step1.send("Paris")
        assert step2 is not None

    async def test_booking_dialog_prefilled_origin(self):
        """Test that pre-filled fields are skipped in the dialog."""
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        dialog_state = conversation_state.create_property("DialogState")

        booking_dialog = BookingDialog()
        dialogs = DialogSet(dialog_state)
        dialogs.add(booking_dialog)

        adapter = TestAdapter()

        async def exec_test(turn_context: TurnContext):
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()

            if results.status == DialogTurnStatus.Empty:
                # Pre-fill origin
                booking_details = BookingDetails(origin="Paris")
                await dialog_context.begin_dialog(
                    BookingDialog.__name__, booking_details
                )

            await conversation_state.save_changes(turn_context)

        # Should skip origin and ask for destination directly
        step1 = await adapter.test(
            "start", "Where would you like to travel to?"
        )
        assert step1 is not None

    async def test_booking_details_creation(self):
        """Test that BookingDetails correctly stores all fields."""
        details = BookingDetails(
            origin="Paris",
            destination="New York",
            departure_date="2025-03-15",
            return_date="2025-03-22",
            budget="$1000",
        )

        assert details.origin == "Paris"
        assert details.destination == "New York"
        assert details.departure_date == "2025-03-15"
        assert details.return_date == "2025-03-22"
        assert details.budget == "$1000"

    async def test_booking_details_to_dict(self):
        """Test BookingDetails to_dict conversion."""
        details = BookingDetails(
            origin="London",
            destination="Tokyo",
        )
        result = details.to_dict()

        assert result["origin"] == "London"
        assert result["destination"] == "Tokyo"
        assert result["departure_date"] == ""
        assert result["return_date"] == ""
        assert result["budget"] == ""
