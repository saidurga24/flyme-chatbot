#!/usr/bin/env python
# Copyright (c) 2024. All rights reserved.
# Licensed under the MIT License.

"""Telemetry helper for Azure Application Insights integration."""

import logging
from typing import Optional

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter

logger = logging.getLogger(__name__)


class TelemetryHelper:
    """
    Helper class for Azure Application Insights telemetry.
    
    Tracks custom events, metrics, and exceptions for monitoring
    the chatbot's performance in production.
    """

    def __init__(self, connection_string: str = None, instrumentation_key: str = None):
        self._connection_string = connection_string
        self._instrumentation_key = instrumentation_key
        self._logger = logging.getLogger("BotTelemetry")
        self._is_configured = False

        if connection_string or instrumentation_key:
            try:
                conn = connection_string or f"InstrumentationKey={instrumentation_key}"
                handler = AzureLogHandler(connection_string=conn)
                self._logger.addHandler(handler)
                self._is_configured = True
                logger.info("Application Insights telemetry configured successfully.")
            except Exception as e:
                logger.warning(
                    f"Failed to configure Application Insights: {e}. "
                    "Telemetry will be logged locally only."
                )

    @property
    def is_configured(self) -> bool:
        """Return whether Application Insights is configured."""
        return self._is_configured

    def track_event(self, name: str, properties: Optional[dict] = None):
        """
        Track a custom event in Application Insights.
        
        Args:
            name: Name of the event (e.g., 'BookingCompleted', 'ComprehensionFailure')
            properties: Dictionary of custom properties to attach to the event
        """
        props = properties or {}
        self._logger.info(
            f"Event: {name}",
            extra={"custom_dimensions": props}
        )

    def track_booking_completed(self, booking_details: dict):
        """Track a successful booking completion."""
        self.track_event("BookingCompleted", booking_details)

    def track_comprehension_failure(self, user_text: str):
        """
        Track a failed comprehension attempt.
        
        This is used to trigger alerts in Application Insights when
        the chatbot fails to understand user input multiple times.
        """
        self.track_event(
            "BotComprehensionFailure",
            {"user_text": user_text, "error_type": "comprehension_failure"},
        )

    def track_dialog_cancelled(self, user_text: str):
        """Track when a user cancels a dialog."""
        self.track_event(
            "DialogCancelled",
            {"user_text": user_text},
        )

    def track_exception(self, exception: Exception, properties: Optional[dict] = None):
        """Track an exception in Application Insights."""
        props = properties or {}
        self._logger.exception(
            f"Exception: {str(exception)}",
            extra={"custom_dimensions": props},
        )
