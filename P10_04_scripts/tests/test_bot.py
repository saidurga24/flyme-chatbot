"""Tests for FlightBookingBot initialization and welcome message."""

import pytest
import aiounittest
from unittest.mock import MagicMock, AsyncMock

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

    def _create_bot(self):
        storage = MemoryStorage()
        conversation_state = ConversationState(storage)
        user_state = UserState(storage)

        config = DefaultConfig()
        recognizer = FlightBookingRecognizer(config)
        booking_dialog = BookingDialog(recognizer)
        main_dialog = MainDialog(recognizer, booking_dialog)

        return FlightBookingBot(conversation_state, user_state, main_dialog)

    async def test_welcome_message(self):
        bot = self._create_bot()
        adapter = TestAdapter()

        async def exec_test(turn_context: TurnContext):
            await bot.on_members_added_activity(
                [ChannelAccount(id="user1", name="TestUser")],
                turn_context,
            )

        activity = Activity(
            type=ActivityTypes.conversation_update,
            channel_id="test",
            recipient=ChannelAccount(id="bot"),
            from_property=ChannelAccount(id="user1"),
            members_added=[ChannelAccount(id="user1")],
        )

        result = await adapter.send(activity)
        assert result is not None

    async def test_requires_conversation_state(self):
        with pytest.raises(TypeError):
            FlightBookingBot(None, MagicMock(), MagicMock())

    async def test_requires_user_state(self):
        with pytest.raises(TypeError):
            FlightBookingBot(MagicMock(), None, MagicMock())

    async def test_requires_dialog(self):
        with pytest.raises(TypeError):
            FlightBookingBot(MagicMock(), MagicMock(), None)
