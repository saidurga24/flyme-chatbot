"""
FlyMe Flight Booking Bot - main entry point.

Runs the bot on an aiohttp web server and serves the web chat UI.
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
from botbuilder.schema import Activity, ActivityTypes, ConversationAccount, ChannelAccount

from config import DefaultConfig
from bot import FlightBookingBot
from dialogs import MainDialog, BookingDialog
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.telemetry_helper import TelemetryHelper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

CONFIG = DefaultConfig()

SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


async def on_error(context: TurnContext, error: Exception):
    """Log the error and let the user know something went wrong."""
    logger.error(f"[on_turn_error] unhandled error: {error}", exc_info=True)
    traceback.print_exc()

    await context.send_activity(
        "I'm sorry, something went wrong. Please try again or type 'cancel' to start over."
    )
    await context.send_activity(
        Activity(
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
            label="TurnError",
        )
    )
    if TELEMETRY_CLIENT:
        TELEMETRY_CLIENT.track_exception(error)

    # clear state so the bot doesn't get stuck
    await CONVERSATION_STATE.delete(context)


ADAPTER.on_turn_error = on_error

MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)
USER_STATE = UserState(MEMORY)

TELEMETRY_CLIENT = TelemetryHelper(
    connection_string=CONFIG.APPINSIGHTS_CONNECTION_STRING,
    instrumentation_key=CONFIG.APPINSIGHTS_INSTRUMENTATION_KEY,
)

RECOGNIZER = FlightBookingRecognizer(CONFIG)

BOOKING_DIALOG = BookingDialog()
MAIN_DIALOG = MainDialog(RECOGNIZER, BOOKING_DIALOG, TELEMETRY_CLIENT)

BOT = FlightBookingBot(CONVERSATION_STATE, USER_STATE, MAIN_DIALOG)

# in-memory store for web chat conversations
CONVERSATIONS = {}


async def messages(req: Request) -> Response:
    """Handle Bot Framework messages (POST /api/messages)."""
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
    Simple REST endpoint for the web chat UI.
    POST /api/chat with {"message": "...", "conversation_id": "..."}
    Returns {"reply": "bot response"}
    """
    try:
        body = await req.json()
        user_message = body.get("message", "")
        conversation_id = body.get("conversation_id", "default")

        if not user_message:
            return web.json_response({"reply": "Please enter a message."})

        activity = Activity(
            type=ActivityTypes.message,
            text=user_message,
            channel_id="webchat",
            from_property=ChannelAccount(id=f"user_{conversation_id}", name="User"),
            recipient=ChannelAccount(id="bot", name="FlyMe Bot"),
            conversation=ConversationAccount(id=conversation_id),
            service_url="http://localhost",
            id=f"msg_{datetime.now().timestamp()}",
        )

        bot_responses = []

        async def aux_func(turn_context: TurnContext):
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
    """Serve the web chat page."""
    return web.FileResponse("./static/index.html")


def init_app():
    app = web.Application()
    app.router.add_static("/static", "./static")
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
