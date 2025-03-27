from enum import Enum


class JsonVendor(Enum):
    PRICELINE = "pricelinev2"
    CLEARTRIP = "cleartrip"

    @classmethod
    def list_vendors(cls):
        """Returns a list of all available JSON vendors."""
        return [vendor.value for vendor in cls]
