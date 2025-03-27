from flight_helper_layer.service.json.priceline.priceline import Priceline
from flight_helper_layer.service.json.cleartrip.cleartrip import Cleartrip
from .enums import JsonVendor


class JSONFactory:
    @staticmethod
    def get_vendor(vendor: str):
        if vendor == JsonVendor.PRICELINE.value:
            return Priceline()
        elif vendor == JsonVendor.CLEARTRIP.value:
            return Cleartrip()
        else:
            raise ValueError(f"Unsupported JSON vendor: {vendor}")
