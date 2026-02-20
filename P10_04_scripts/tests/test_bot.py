#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Unit tests for the FlightBookingBot class."""

import pytest
import aiounittest
from unittest.mock import MagicMock, AsyncMock, patch

from botbuilder.core import (
    ConversationState,
    MemoryStorage,
    TurnContext,
    UserState,
)
from botbuilder.core.adapters import TestAdapter
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount

from bot import FlightBookingBot
from dialogs.main_dialog import MainDialog
from dialogs.booking_dialog import BookingDialog
from flight_booking_recognizer import FlightBookingRecognizer
from config import DefaultConfig


class TestFlightBookingBot(aiounittest.AsyncTestCase):
    """Test suite for the FlightBookingBot class."""

    def _create_bot(self):
        """Create a bot instance for testing."""
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        user_state = UserState(storage)
        
        config = DefaultConfig()
        recognizer = FlightBookingRecognizer(config)
        booking_dialog = BookingDialog()
        main_dialog = MainDialog(recognizer, booking_dialog)
        
        return FlightBookingBot(conversation_state, user_state, main_dialog)

    async def test_bot_welcome_message(self):
        """Test that the bot sends a welcome message when a member is added."""
        bot = self._create_bot()

        adapter = TestAdapter()

        async def exec_test(turn_context: TurnContext):
            await bot.on_members_added_activity(
                [ChannelAccount(id="user1", name="TestUser")],
                turn_context,
            )

        # Start conversation and check welcome message is sent
        activity = Activity(
            type=ActivityTypes.conversation_update,
            channel_id="test",
            recipient=ChannelAccount(id="bot"),
            from_property=ChannelAccount(id="user1"),
            members_added=[ChannelAccount(id="user1")],
        )

        result = await adapter.send(activity)
        # The welcome message should contain "FlyMe"
        assert result is not None

    async def test_bot_requires_conversation_state(self):
        """Test that bot raises TypeError if conversation_state is None."""
        with pytest.raises(TypeError):
            FlightBookingBot(None, MagicMock(), MagicMock())

    async def test_bot_requires_user_state(self):
        """Test that bot raises TypeError if user_state is None."""
        with pytest.raises(TypeError):
            FlightBookingBot(MagicMock(), None, MagicMock())

    async def test_bot_requires_dialog(self):
        """Test that bot raises TypeError if dialog is None."""
        with pytest.raises(TypeError):
            FlightBookingBot(MagicMock(), MagicMock(), None)
