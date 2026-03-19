"""Azure Application Insights telemetry integration."""

import logging
from typing import Optional

from opencensus.ext.azure.log_exporter import AzureLogHandler

logger = logging.getLogger(__name__)


class TelemetryHelper:
    """Sends custom events and exceptions to App Insights for monitoring."""

    def __init__(self, connection_string: str = None, instrumentation_key: str = None):
        self._logger = logging.getLogger("BotTelemetry")
        self._is_configured = False

        if connection_string or instrumentation_key:
            try:
                conn = connection_string or f"InstrumentationKey={instrumentation_key}"
                handler = AzureLogHandler(connection_string=conn)
                self._logger.addHandler(handler)
                self._is_configured = True
                logger.info("App Insights telemetry configured.")
            except Exception as e:
                logger.warning(f"Could not configure App Insights: {e}. Logging locally only.")

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    def track_event(self, name: str, properties: Optional[dict] = None):
        props = properties or {}
        self._logger.info(
            f"Event: {name}",
            extra={"custom_dimensions": props}
        )

    def track_booking_completed(self, booking_details: dict):
        self.track_event("BookingCompleted", booking_details)

    def track_comprehension_failure(self, user_text: str):
        self.track_event(
            "BotComprehensionFailure",
            {"user_text": user_text, "error_type": "comprehension_failure"},
        )

    def track_dialog_cancelled(self, user_text: str):
        self.track_event("DialogCancelled", {"user_text": user_text})

    def track_exception(self, exception: Exception, properties: Optional[dict] = None):
        props = properties or {}
        self._logger.exception(
            f"Exception: {str(exception)}",
            extra={"custom_dimensions": props},
        )
