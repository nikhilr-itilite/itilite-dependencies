"""
This holds all the constants used in the application
"""
from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass(frozen=True)
class TripInfoConstants:
    """
    Hold all the collection names of Mongo TripInfo DB
    """

    TRIP_DB: str = "trip_info"
    TRIP_COLLECTION: str = "trip"
    HOTEL_REQUEST_COLLECTION: str = "hotel_request"
    FLIGHT_REQUEST_COLLECTION: str = "flight_request"
    HOTEL_VENDOR_REQUEST_COLLECTION: str = "hotel_vendor_request"
    FLIGHT_VENDOR_REQUEST_COLLECTION: str = "flight_vendor_request"
    TRIP_INFO_DB: str = "trip_info"
    CURRENCY_CONVERSION_COLLECTION: str = "currency_conversion"


@dataclass(frozen=True)
class FilterViewConstants:
    """Hold all the collection names of FilterView DB"""

    pass


@dataclass(frozen=True)
class StaticDBConstants:
    """Hold all the collection names of Static DB"""

    HOTEL_COMPANY_RAC_MAPPING_COLLECTION: str = "HOTEL_COMPANY_RAC_MAPPING"
    HOTEL_CHAIN_MEMBERSHIP_DEAL_COLLECTION: str = "hotel_chain_membership_deal"
    FLIGHT_STATIC_DATA: str = "flight_static_data"
    FLIGHT_MAPPING: str = "flight_mapping"
    AIRPORT_COLLECTION: str = "airport"
    STATIC_DB: str = "static_content"
    STATIC_AIRPORT_DB: str = "static_content"
    HOTEL_CITIES: str = "hotel_cities"
    STATIC_AIRPORT_DB: str = "static_content"


@dataclass(frozen=True)
class HotelDbConstants:
    MONGO_HOTEL_DB: str = "hotel"
    MONGO_HOTEL_DB_COLLECTION: str = "hotel_master_vt_05_oct_2024"
    ROOM_MAPPING_COLLECTION: str = "vt-hotel-room-mapping"
    MONGO_HOTEL_COLD_CACHE_DB_NAME: str = "hotel"


@dataclass(frozen=True)
class SelectionConstants:
    SELECTION_DB: str = "selection"
    SELECTION_COLLECTION: str = "selection"


@dataclass(frozen=True)
class PriceDbConstants:
    PRICE_COLLECTION: str = "price_details"
    PRICE_DETAILS_COLLECTION: str = "price_details"


@dataclass(frozen=True)
class PaymentDbConstants:
    PAYMENT_DB: str = "payment"
    PAYMENT_COLLECTION: str = "payment_mapper"


# @dataclass(frozen=True)
# class ProdS3BucketConstants:
#     COLLEAGUE_FEEDBACK_S3_BUCKET_NAME: str = "fast-api-colleague-feedback-streaming"
#     HOTEL_S3_BUCKET_NAME: str = "fast-api-hotel"
#     FLIGHT_S3_BUCKET_NAME: str = "fast-api-flight"

# @dataclass(frozen=True)
# class StageS3BucketConstants:
#     COLLEAGUE_FEEDBACK_S3_BUCKET_NAME: str = "fast-api-colleague-feedback-streaming"
#     HOTEL_S3_BUCKET_NAME: str = "fast-api-hotel"
#     FLIGHT_S3_BUCKET_NAME: str = "fast-api-flight"


@dataclass(frozen=True)
class FlightConstants:
    """
    Holds all the hardcoded airline and cabin class information.
    """

    AIRLINE_CLASSES: Dict[str, Set[str]] = field(default_factory=lambda: {"6E": {"business"}})
    CABIN_CLASSES: Set[str] = field(default_factory=lambda: {"business"})


@dataclass(frozen=True)
class AlliedDetailsConstants:
    """
    Holds all the Marriott hotel chains.
    """

    ALLIED_US_PCC: str = "ALLIED_US_PCC"

    ALLIED_MEMBER_RATE_DEAL_CODE: str = "Y45"

    ALLIED_MARRIOTT_HOTEL_CHAINS: Set[str] = field(
        default_factory=lambda: {
            "FN",
            "AR",
            "MC",
            "TO",
            "CY",
            "XV",
            "VC",
            "OX",
            "BR",
            "RC",
            "DE",
            "XR",
            "WH",
            "EB",
            "MA",
            "AK",
            "TB",
            "DS",
            "GW",
            "ME",
            "SI",
            "WI",
            "MD",
            "EL",
        }
    )


class NewRelicConstants:
    NEWRELIC_FLIGHT_L2_METRICS: str = "FlightL2CardMetrics"
