#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Configuration for the Flight Booking Bot."""

import os
from dotenv import load_dotenv

load_dotenv()


class DefaultConfig:
    """Bot Configuration."""

    PORT = int(os.environ.get("PORT", 3978))
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

    # LUIS / CLU Configuration
    LUIS_APP_ID = os.environ.get("LuisAppId", "")
    LUIS_API_KEY = os.environ.get("LuisAPIKey", "")
    LUIS_API_HOST_NAME = os.environ.get("LuisAPIHostName", "")

    # Application Insights
    APPINSIGHTS_INSTRUMENTATION_KEY = os.environ.get(
        "AppInsightsInstrumentationKey", ""
    )
    APPINSIGHTS_CONNECTION_STRING = os.environ.get(
        "AppInsightsConnectionString", ""
    )
