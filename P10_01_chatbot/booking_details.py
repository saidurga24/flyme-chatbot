"""BookingDetails - holds the flight booking info from the conversation."""


class BookingDetails:
    def __init__(
        self,
        origin: str = None,
        destination: str = None,
        departure_date: str = None,
        return_date: str = None,
        budget: str = None,
    ):
        self.origin = origin
        self.destination = destination
        self.departure_date = departure_date
        self.return_date = return_date
        self.budget = budget

    def __repr__(self):
        return (
            f"BookingDetails(origin='{self.origin}', "
            f"destination='{self.destination}', "
            f"departure='{self.departure_date}', "
            f"return='{self.return_date}', "
            f"budget='{self.budget}')"
        )

    def to_dict(self):
        """For telemetry logging."""
        return {
            "origin": self.origin or "",
            "destination": self.destination or "",
            "departure_date": self.departure_date or "",
            "return_date": self.return_date or "",
            "budget": self.budget or "",
        }
