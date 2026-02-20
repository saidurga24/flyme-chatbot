#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""
FlyMe Flight Booking Bot - Application Entry Point.

Runs the bot as an aiohttp web application with Bot Framework adapter.
Serves the web chat interface and handles bot messages via /api/messages.
"""

import sys
import traceback
import logging
from datetime import datetime

from aiohttp import web
from aiohttp.web import Request, Response
import aiohttp

from botbuilder.core import (
    BotFrameworkAdapterSettings,
    BotFrameworkAdapter,
    ConversationState,
    MemoryStorage,
    UserState,
    TurnContext,
)
from botbuilder.schema import Activity, ActivityTypes

from config import DefaultConfig
from bot import FlightBookingBot
from dialogs import MainDialog, BookingDialog
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.telemetry_helper import TelemetryHelper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG = DefaultConfig()

# Create adapter settings and adapter
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


# Error handler
async def on_error(context: TurnContext, error: Exception):
    """Handle errors from the bot adapter."""
    logger.error(f"[on_turn_error] unhandled error: {error}", exc_info=True)
    traceback.print_exc()

    # Send error message to user
    await context.send_activity(
        "I'm sorry, something went wrong. Please try again or type 'cancel' to start over."
    )
    # Send a trace activity (visible in Bot Framework Emulator)
    await context.send_activity(
        Activity(
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
            label="TurnError",
        )
    )
    # Track error in Application Insights
    if TELEMETRY_CLIENT:
        TELEMETRY_CLIENT.track_exception(error)

    # Clear conversation state on error
    nonlocal CONVERSATION_STATE
    await CONVERSATION_STATE.delete(context)


ADAPTER.on_turn_error = on_error

# Create state management
MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)
USER_STATE = UserState(MEMORY)

# Create telemetry client
TELEMETRY_CLIENT = TelemetryHelper(
    connection_string=CONFIG.APPINSIGHTS_CONNECTION_STRING,
    instrumentation_key=CONFIG.APPINSIGHTS_INSTRUMENTATION_KEY,
)

# Create the LUIS/CLU recognizer
RECOGNIZER = FlightBookingRecognizer(CONFIG)

# Create dialogs
BOOKING_DIALOG = BookingDialog()
MAIN_DIALOG = MainDialog(RECOGNIZER, BOOKING_DIALOG, TELEMETRY_CLIENT)

# Create bot
BOT = FlightBookingBot(CONVERSATION_STATE, USER_STATE, MAIN_DIALOG)

# --- In-memory conversation store for the web chat ---
CONVERSATIONS = {}


async def messages(req: Request) -> Response:
    """Handle incoming Bot Framework messages via POST /api/messages."""
    if "application/json" in req.headers.get("Content-Type", ""):
        body = await req.json()
    else:
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    if response:
        return Response(body=response.body, status=response.status)
    return Response(status=201)


async def chat_api(req: Request) -> Response:
    """
    Simple REST API for the web chat interface.
    POST /api/chat with JSON body {"message": "user text", "conversation_id": "..."}
    Returns JSON {"reply": "bot response"}
    """
    try:
        body = await req.json()
        user_message = body.get("message", "")
        conversation_id = body.get("conversation_id", "default")

        if not user_message:
            return web.json_response({"reply": "Please enter a message."})

        # Create a simple activity for processing
        activity = Activity(
            type=ActivityTypes.message,
            text=user_message,
            channel_id="webchat",
            from_property={"id": f"user_{conversation_id}", "name": "User"},
            recipient={"id": "bot", "name": "FlyMe Bot"},
            conversation={"id": conversation_id},
            service_url="http://localhost",
            id=f"msg_{datetime.now().timestamp()}",
        )

        # Collect bot responses
        bot_responses = []

        async def aux_func(turn_context: TurnContext):
            # Override send_activity to capture responses
            original_send = turn_context.send_activity

            async def capture_send(activity_or_text, speak=None, input_hint=None):
                if isinstance(activity_or_text, str):
                    bot_responses.append(activity_or_text)
                elif hasattr(activity_or_text, "text") and activity_or_text.text:
                    bot_responses.append(activity_or_text.text)
                return await original_send(activity_or_text, speak, input_hint)

            turn_context.send_activity = capture_send
            await BOT.on_turn(turn_context)

        await ADAPTER.process_activity(activity, "", aux_func)

        reply = "\n".join(bot_responses) if bot_responses else "I'm thinking..."
        return web.json_response({"reply": reply})

    except Exception as e:
        logger.error(f"Chat API error: {e}", exc_info=True)
        return web.json_response(
            {"reply": "Sorry, something went wrong. Please try again."},
            status=500,
        )


async def index(req: Request) -> Response:
    """Serve the web chat interface."""
    return web.FileResponse("./static/index.html")


def init_app():
    """Initialize the aiohttp web application."""
    app = web.Application()

    # Serve static files
    app.router.add_static("/static", "./static")

    # Routes
    app.router.add_get("/", index)
    app.router.add_post("/api/messages", messages)
    app.router.add_post("/api/chat", chat_api)

    return app


if __name__ == "__main__":
    app = init_app()
    try:
        port = CONFIG.PORT
        logger.info(f"Starting FlyMe bot on port {port}...")
        logger.info(f"Web chat: http://localhost:{port}")
        logger.info(f"Bot endpoint: http://localhost:{port}/api/messages")
        web.run_app(app, host="0.0.0.0", port=port)
    except Exception as error:
        logger.error(f"Failed to start bot: {error}")
        raise error
