from enum import Enum


class ApiFormat(Enum):
    JSON = "json"
    XML = "xml"

    @classmethod
    def list_vendors(cls):
        """Returns a list of all available JSON vendors."""
        return [vendor.value for vendor in cls]
