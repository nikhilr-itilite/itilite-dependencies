from flight_helper_layer.service.xml.travelportus.travelportus import TravelportUSProcessor
from flight_helper_layer.service.xml.ach.ach import ACHProcessor


class XMLFactory:
    @staticmethod
    def get_vendor(vendor: str):
        if vendor == "travelport":
            return TravelportUSProcessor()
        elif vendor == "ach":
            return ACHProcessor()
        else:
            raise ValueError(f"Unsupported XML vendor: {vendor}")
