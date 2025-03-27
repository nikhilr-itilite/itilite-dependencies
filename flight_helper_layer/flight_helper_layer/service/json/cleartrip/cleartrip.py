from flight_helper_layer.service.base import FlightProcessor


class Cleartrip(FlightProcessor):
    def __init__(self):
        super().__init__()
        self.vendor = "Cleartrip"

    def transformation(self):
        print("Processing Cleartrip JSON data...")
        # Implement your processing logic here
