"""Bot configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class DefaultConfig:
    PORT = int(os.environ.get("PORT", 3978))
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

    # CLU (Azure AI Language) settings
    CLU_PROJECT_NAME = os.environ.get("CluProjectName", "")
    CLU_DEPLOYMENT_NAME = os.environ.get("CluDeploymentName", "")
    CLU_API_KEY = os.environ.get("CluAPIKey", "")
    CLU_ENDPOINT = os.environ.get("CluEndpoint", "")

    # Application Insights
    APPINSIGHTS_INSTRUMENTATION_KEY = os.environ.get(
        "AppInsightsInstrumentationKey", ""
    )
    APPINSIGHTS_CONNECTION_STRING = os.environ.get(
        "AppInsightsConnectionString", ""
    )
