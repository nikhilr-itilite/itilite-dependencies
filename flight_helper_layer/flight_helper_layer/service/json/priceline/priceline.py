from flight_helper_layer.service.base import FlightProcessor
from opensearchlogger.logging import logger
from flight_helper_layer.mapping.lfs.priceline import mapping as priceline_lfs_mapping
import json
import os
import traceback
from datetime import datetime
import uuid
import orjson
from helperlayer import (
    Flight,
    LegDetails,
    Fare,
    FlightSegment,
    FareBreakup,
    FlightResult,
    PaxFareBreakup,
    Baggage,
    DetailBaggage,
    BrandDesc,
    MoreDetail,
    MoreDetailData,
    ViaDetails,
    ViaBase,
    check_basic_economy,
    custom_sort,
    update_l2_info_missing,
)

# from static_content import airline_inclusion_mapping, airline_cabin_name_mapping
from helperlayer.helperfunctions import (
    is_over_night,
    datetime_format_converter,
    currency_conversion,
)


def time_to_sec(time):
    try:
        hh, mm, ss = time.split(":")
        time_sec = int(hh) * 3600 + int(mm) * 60 + int(ss)
        # time_min = time_sec / 60
        return time_sec
    except Exception:
        logger.error(f"error in time_to_hr {traceback.format_exc()}")


inclusion_map = {"INCLUDED": 1, "NOT_INCLUDED": 0, "CHARGEABLE": 2}

VENDOR_FARE_ATTRIBUTE_BASE = [
    "cbg",
    "crn",
    "rbk",
    "rfn",
    "st",
    "mls",
    "y5",
]


ancillaries_type_code = {
    "CHECKED_BAGGAGE": "cbg",
    "CARRYON_BAGGAGE": "crn",
    "CHANGES": "rbk",
    "REFUNDS": "rfn",
    "SEAT_SELECTION": "st",
    "WIFI": "y5",
    "MEAL_BEVERAGE": "mls",
}

BAGGAGE_DATA_ALLOWED_COUNTRY = json.loads(os.getenv("BAGGAGE_DATA_ALLOWED_COUNTRY"))
CABIN_CLASS_KEYS_MAPPING = {
    "ECO": "economy",
    "BEC": "economy",
    "PEC": "premium_economy",
    "BUS": "business",
    "FST": "first",
}
CARRIER_DATA = {}
CARRIER_DATA_ID = {}
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"
AIRLINE_MAPPING = {}
# GLOBAL_AIRLINE_MAPPING = {}
LCC_AIRLINE_MAPPING = []
AIRLINE_INCLUSION_MAPPING = {}
CLEARTRIP_VENDOR_NAME = ["cleartrip"]
ROUND_TRIP_INDICATOR = 1

FLIGHT_STATIC_DATA_NEW = {}
AIRLINE_MAPPING_NEW = {}
FLIGHT_BRAND_DESC_NEW = {}

# Please add keys which you want to compare to say two fare have same description
brand_description_to_compare = {"rfn": 0, "rbk": 1, "crn": 2, "cbg": 3, "st": 4}

CABIN_CLASS_KEYS_MAPPING = {
    "ECO": "economy",
    "BEC": "economy",
    "PEC": "premium_economy",
    "BUS": "business",
    "FST": "first",
}

CABIN_NAME_FIRST_MAPPING = {
    "first or business": "First",
    "first or business full ref": "First flexible",
    "first or business fully ref": "First flexible",
}
CABIN_NAME_BUSINESS_MAPPING = {
    "first or business": "Business",
    "first or business full ref": "Business flexible",
    "first or business fully ref": "Business flexible",
}

CABIN_CLASS_MAPPING = {
    "Economy": "economy",
    "PremiumEconomy": "premium_economy",
    "Business": "business",
    "First": "first",
    "Upper": "upper",
}

BAGGAGE_DATA_ALLOWED_COUNTRY = json.loads(os.getenv("BAGGAGE_DATA_ALLOWED_COUNTRY"))

MOREFARE_LAMBDA_FUNCTION = os.getenv("MOREFARE_LAMBDA_FUNCTION", "")
MOREFARE_FLIGHTS_PER_BATCH = int(os.getenv("MOREFARE_FLIGHTS_PER_BATCH", 8))
TRIP_INFO_DB = os.environ["TRIP_DB"]


def get_compare_fare_value(fare_preference_group, compare_type, sale_price):
    compare_fare_value = 0
    compare_fare_priority = 0
    if fare_preference_group:
        for value in fare_preference_group:
            if value.fare == compare_type.upper():
                compare_fare_priority = value.priority
                if value.x_type == 1:
                    compare_fare_value = sale_price + ((sale_price * value.x_value) / 100)
                else:
                    compare_fare_value = sale_price + value.x_value
    else:
        compare_fare_value = sale_price

    return {
        "compare_fare": compare_fare_value,
        "compare_fare_priority": compare_fare_priority,
    }


class Priceline(FlightProcessor):
    def _lfs_transform_data(
        self,
        flights,
        branding_data,
        transformed_queue,
        fre_config,
        trip_info,
        flight_request,
        from_country,
        to_country,
        new_relic_custom_event,
    ):
        try:
            # first convert the data to lfs format using
            l2_info_missing = {"data": {}}
            no_of_transformed_flight = 0
            country_travel_type = None
            start_country = None  # Will be used for multi_city
            if from_country == "US" and to_country == "US":
                country_travel_type = "US-D"
                start_country = "US"
            elif from_country == "IN" and to_country == "IN":
                country_travel_type = "IN-D"
                start_country = "IN"
            elif from_country == "US" and to_country != "US":
                country_travel_type = "US-I"
                start_country = "US"
            elif from_country == "IN" and to_country != "IN":
                country_travel_type = "IN-I"
                start_country = "IN"
            elif from_country not in ["US", "IN"]:
                country_travel_type = "ALL"
                start_country = "ALL"
            is_l3_card_trigger = True if country_travel_type and country_travel_type in BAGGAGE_DATA_ALLOWED_COUNTRY else False
            is_l3_card_trigger_mc = None
            travel_type = "-D"
            # flight_leg_info = flights.get("leg", {})
            # branding_data = flights.get("branding_data", {})
            # get_carrier_names()
            from_iata = flight_request["from_iata"]
            to_iata = flight_request["to_iata"]
            travel_city_from = flight_request["travel_city_from"]
            travel_city_to = flight_request["travel_city_to"]
            previous_booking_details = flight_request.get("previous_booking_details")
            is_reschedule_flow = False
            change_fees = None
            previous_total_fare = 0
            if previous_booking_details:
                is_reschedule_flow = True
                print("get all the previous booked details")
                previous_total_fare = flight_request["previous_booking_details"]["price"]["total_fare"]
                change_fees = flight_request["previous_booking_details"]["price"].get("change_fee")
            staff_currency_details = fre_config.staff_currency
            itilite_currency_details = fre_config.itilite_currency
            client_currency_details = fre_config.client_currency
            vendor_currency_details = fre_config.vendor_currency
            restricted_airlines = fre_config.restrict_airlines.split(",") if fre_config.restrict_airlines else []
            # detail_baggage = list()
            # brand_desc=list()
            more_detail_data = list()
            num_pax = int(trip_info["no_of_adults_count"]) + int(trip_info["no_of_child_count"])
            # default value
            morefare_status = 0
            multi_city_fare = 1 if flight_request.get("multi_city", 0) == 1 else 0
            legdetail = list()
            for each_flight_itenary in flights:
                is_data_hardcoded_inclusion, vendor_brand_data = False, []
                more_detail_data.append([])
                platting_carrier_iata = ""
                platting_carrier_name = ""
                is_restricted_journey = False

                round_trip_leg = list()
                fare_breakup_round_trip = list()
                pax_fare_breakup = list()
                flight_details = each_flight_itenary.get("flight_details", {})
                ppn_bundle = each_flight_itenary.get("ppn_contract_bundle")
                ppn_return_bundle = each_flight_itenary.get("ppn_return_bundle")
                origin_airport_check = False if "All Airports" in travel_city_from else True
                destination_airport_check = False if "All Airports" in travel_city_to else True
                # We are taking cabin leg of first sector first flight, this should be only used as fallback
                for flight_data in flight_details:
                    flight_data = flight_data.get("flight_data", {})
                    # Technical stop implementation
                    for legs in flight_data:
                        cabin_name_leg = legs.get("cabin_name", "")
                        cabin_name_leg = "Premium economy" if cabin_name_leg == "PremiumEconomy" else cabin_name_leg
                        class_of_service = legs.get("class_of_service", {})
                        carrier_id = legs.get("carrier_id", {})
                        cabin_class = legs.get("cabin_class", {})
                        destination = legs.get("arrival_airport_code", {})
                        break
                    break
                    # destination=flight_details[0].get("flight_data", {})[0].get("departure_airport_code", {})
                    # origin = flight_details[0].get("flight_data", {})[0].get("arrival_airport_code", {})
                pre_cabin_class = cabin_class
                cabin_class = CABIN_CLASS_KEYS_MAPPING.get(cabin_class)
                vendor_currency = each_flight_itenary.get("display_currency", {})
                vendor_base_price = each_flight_itenary.get("base_price")
                vendor_base_price = vendor_base_price * int(num_pax)
                base_fare_per_ticket = each_flight_itenary.get("base_fare_per_ticket", {})
                total_price_per_ticket = each_flight_itenary.get("total_price_per_ticket", {})
                vendor_total_price = each_flight_itenary.get("total_price", {})
                vendor_tax = each_flight_itenary.get("vendor_tax", {})
                reschedule_diff = 0
                logger.info(f"Is reschedule flow : {is_reschedule_flow}")
                if is_reschedule_flow:
                    reschedule_diff = vendor_total_price - previous_total_fare
                    if reschedule_diff < 0:
                        reschedule_diff = 0
                        total_price_per_ticket = 0
                        vendor_total_price = 0
                    else:
                        vendor_total_price = reschedule_diff
                        total_price_per_ticket = reschedule_diff / num_pax
                    vendor_base_price = 0
                    base_fare_per_ticket = 0
                    vendor_tax = 0
                traveller_fare = {
                    "total_price": currency_conversion(staff_currency_details.rate, vendor_total_price),
                    "base_price": currency_conversion(staff_currency_details.rate, vendor_base_price),
                    "currency": staff_currency_details.type,
                    "tax": currency_conversion(staff_currency_details.rate, vendor_tax),
                }
                itilite_fare = {
                    "total_price": currency_conversion(itilite_currency_details.rate, vendor_total_price),
                    "base_price": currency_conversion(itilite_currency_details.rate, vendor_base_price),
                    "currency": itilite_currency_details.type,
                    "tax": currency_conversion(itilite_currency_details.rate, vendor_tax),
                }
                client_fare = {
                    "total_price": currency_conversion(client_currency_details.rate, vendor_total_price),
                    "base_price": currency_conversion(client_currency_details.rate, vendor_base_price),
                    "currency": client_currency_details.type,
                    "tax": currency_conversion(client_currency_details.rate, vendor_tax),
                }
                vendor_fare = {
                    # We get requested currency from input.
                    "total_price": currency_conversion(vendor_currency_details.rate, vendor_total_price),
                    "base_price": currency_conversion(vendor_currency_details.rate, vendor_base_price),
                    "currency": vendor_currency_details.type,
                    "tax": currency_conversion(vendor_currency_details.rate, vendor_tax),
                }
                if is_reschedule_flow:
                    traveller_fare.update(
                        {
                            "change_fee": change_fees,
                            "reschedule_fare_breakup": {
                                "fare_difference": currency_conversion(staff_currency_details.rate, reschedule_diff),
                                "change_fee": change_fees,
                            },
                        }
                    )
                    itilite_fare.update(
                        {
                            "change_fee": change_fees,
                            "reschedule_fare_breakup": {
                                "fare_difference": currency_conversion(itilite_currency_details.rate, reschedule_diff),
                                "change_fee": change_fees,
                            },
                        }
                    )
                    client_fare.update(
                        {
                            "change_fee": change_fees,
                            "reschedule_fare_breakup": {
                                "fare_difference": currency_conversion(client_currency_details.rate, reschedule_diff),
                                "change_fee": change_fees,
                            },
                        }
                    )
                    vendor_fare.update(
                        {
                            "change_fee": change_fees,
                            "reschedule_fare_breakup": {
                                "fare_difference": currency_conversion(vendor_currency_details.rate, reschedule_diff),
                                "change_fee": change_fees,
                            },
                        }
                    )

                all_segment = list()
                # total_duration = 0
                count = 0
                round_segment = list()
                flight_count_iter = 0
                detail_baggage = list()
                cnt_flight_details = 0
                carrier_iata_first = ""
                carrier_iata_name_first = ""
                original_brand_name = None
                sector_wise_fare_list = []
                no_of_sectors = len(flight_details)
                for index_sector, flight_detail in enumerate(flight_details):
                    if flight_request.get("multi_city", 0) == 1:
                        # Overwriting these variable for multi city fares
                        vendor_brand_data = None
                        is_data_hardcoded_inclusion = False
                        from_country = flight_request["leg_data"][index_sector]["from_country"]
                        to_country = flight_request["leg_data"][index_sector]["to_country"]
                        from_iata = flight_request["leg_data"][index_sector]["from_iata"]
                        to_iata = flight_request["leg_data"][index_sector]["to_iata"]
                        travel_city_from = flight_request["leg_data"][index_sector]["travel_city_from"]
                        travel_city_to = flight_request["leg_data"][index_sector]["travel_city_to"]
                        origin_airport_check = False if "All Airports" in travel_city_from else True
                        destination_airport_check = False if "All Airports" in travel_city_to else True
                        flight_count_iter = 0
                        pax_fare_breakup = []
                        if is_l3_card_trigger_mc is None:
                            if from_country == to_country == "US":
                                if start_country == "IN" and travel_type == "-D":
                                    travel_type = "-I"
                            elif from_country == "US" and to_country != "US":
                                if start_country == "US" and travel_type == "-D":
                                    travel_type = "-I"
                                elif start_country == "IN" and travel_type == "-D":
                                    travel_type = "-I"
                            elif from_country == "IN" and to_country != "IN":
                                if start_country == "US" and travel_type == "-D":
                                    travel_type = "-I"
                                elif start_country == "IN" and travel_type == "-D":
                                    travel_type = "-I"
                            elif from_country not in ["US", "IN"]:
                                travel_type = "ALL"
                            else:
                                travel_type = None

                    current_sector_mvh = []
                    current_sector_sd = []
                    current_sector_cs = []
                    total_duration = 0
                    fare_breakup = list()
                    segment_list = list()
                    if int(trip_info["round_trip"]) == 1 or flight_request["multi_city"] == 1:
                        rt_fb_list = list()
                    cnt_flight_details += 1
                    flight_datas = flight_detail.get("flight_data", {})
                    # detail_baggage = list()
                    for index_flight, flight_data in enumerate(flight_datas):
                        # Cabin name of current sector current flight with fallback to use previous one
                        cabin_name_leg = flight_detail["flight_data"][index_flight].get("cabin_name", "") or cabin_name_leg
                        cabin_name_leg = "Premium economy" if cabin_name_leg == "PremiumEconomy" else cabin_name_leg
                        class_of_service = (
                            flight_detail["flight_data"][index_flight].get("class_of_service", "") or class_of_service
                        )
                        flight_count_iter += 1
                        origin = flight_data.get("departure_airport_code", {})
                        destination = flight_data.get("arrival_airport_code", {})
                        cancellation_policy = list()
                        reschedule_policy = list()
                        checked_baggage_unit_desc = None
                        hand_baggage_unit_desc = None
                        refunds_desc = None
                        meal_beverage_desc = None
                        seat_selection_desc = None
                        changes_desc = None
                        wifi_desc = None
                        hand_baggage_included = False
                        checked_baggage_included = False
                        carryon_baggage_para = ""
                        checked_baggage_para = ""
                        refunds_para = ""
                        changes_para = ""
                        seat_selection_para = ""
                        meal_para = ""
                        wifi_para = ""
                        brand_desc_para = ""
                        checked_baggage_desc = None
                        hand_baggage_desc = None
                        carrier_iata = flight_data.get("carrier_iata", "")
                        cabin_name = flight_data.get("cabin_name", "")
                        if original_brand_name is None:
                            original_brand_name = cabin_name
                        cabin_name = "Premium economy" if cabin_name == "PremiumEconomy" else cabin_name
                        # Always we should take cabin class of current flight
                        # If not present, taking cabin class of the first one
                        cabin_class = flight_data.get("cabin_class", pre_cabin_class)
                        fare_tags = {
                            "checked_baggage": None,
                            "carry_on_baggage": None,
                            "changes": None,
                            "refundable": None,
                            "meal": None,
                            "seat": None,
                            "wifi": None,
                        }
                        is_hardcoded_inclusion = True
                        # calling get_airline_inclusion and hard_coding the inclusions
                        # airline_inclusion_mapping = get_airline_inclusion(carrier_iata, cabin_name.lower())

                        platting_carrier_iata = flight_data.get("operating_carrier_iata")
                        platting_carrier_name = flight_data.get("operating_carrier_name")
                        if carrier_iata in restricted_airlines or platting_carrier_iata in restricted_airlines:
                            is_restricted_journey = True
                            break
                        # if platting_carrier_iata == "UA":
                        #     if cabin_class == "first":
                        #         cabin_name = CABIN_NAME_FIRST_MAPPING.get(cabin_name.lower(), cabin_name)
                        #     elif cabin_class == "business":
                        #         cabin_name = CABIN_NAME_BUSINESS_MAPPING.get(cabin_name.lower(), cabin_name)
                        if from_country == to_country == "US":
                            cabin_class_mapping = AIRLINE_MAPPING.get(carrier_iata, None)
                            if cabin_class_mapping:
                                cabin_details = cabin_class_mapping.get(cabin_name.lower(), None)
                                if cabin_details:
                                    fare_tags = cabin_details.get("inclusions", fare_tags)
                                # else:
                                # logger.error("we didnt get the detials for the brand_name in the db, using fallback")
                            # for using itilite_brand_name instead of cabin class
                            search_brand_name = AIRLINE_MAPPING.get(carrier_iata, None)
                            if search_brand_name is not None:
                                for mapped_brand_name in search_brand_name:
                                    if type(search_brand_name[mapped_brand_name]) is dict:
                                        if search_brand_name[mapped_brand_name].get("cabin_class") == cabin_class:
                                            if search_brand_name[mapped_brand_name].get("search_brand_name") is True:
                                                cabin_name = search_brand_name[mapped_brand_name]["itilite_brand_name"]
                                                fare_tags = search_brand_name[mapped_brand_name].get("inclusions", fare_tags)
                                                is_data_hardcoded_inclusion = True
                                                break
                        brand_desc_para += cabin_name + "\n"
                        # looping into the branding_data and getting matching the cabin class of the flights.
                        for cabin in branding_data:
                            # This might be wrong as we will get multiple cabin name in different legs.
                            if cabin == cabin_name_leg:
                                brand_attributes = branding_data[cabin].get("brand_attributes", {})
                                vendor_brand_data = [
                                    {
                                        "typ": typ,
                                        "inc": next(
                                            (
                                                inclusion_map[attr["inclusion"]]
                                                for attr in brand_attributes
                                                if ancillaries_type_code.get(attr["type"]) == typ
                                            ),
                                            None,
                                        ),
                                    }
                                    for typ in VENDOR_FARE_ATTRIBUTE_BASE
                                ]
                                for atr in brand_attributes:
                                    if atr["type"] == "CHECKED_BAGGAGE":
                                        checked_baggage_unit_desc = atr.get("description", "").lower()
                                        checked_baggage_desc = atr.get("description", "").lower()

                                        hardcoded_inc = fare_tags.get("checked_baggage", None) if is_hardcoded_inclusion else None
                                        inclusion = atr.get("inclusion").lower()
                                        checked_baggage_unit_desc = (
                                            "*  "
                                            + atr["type"].replace("_", " ").title()
                                            + " ("
                                            + inclusion
                                            + "): "
                                            + checked_baggage_unit_desc.lower()
                                            + "\n"
                                        )
                                        if hardcoded_inc == 0:
                                            continue
                                        elif inclusion == "chargeable":
                                            if hardcoded_inc == 2:
                                                checked_baggage_para += checked_baggage_unit_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["checked_baggage"] = 2
                                                checked_baggage_para += checked_baggage_unit_desc
                                        elif inclusion == "not_included" and hardcoded_inc is None:
                                            fare_tags["checked_baggage"] = 0
                                        elif inclusion == "included":
                                            if hardcoded_inc == 1:
                                                if "included" not in checked_baggage_desc:
                                                    checked_baggage_desc += " included"
                                                checked_baggage_tmp = checked_baggage_unit_desc.split(":")
                                                if "included" not in checked_baggage_tmp[1]:
                                                    checked_baggage_tmp[1] = checked_baggage_tmp[1].replace("\n", " included \n")
                                                    checked_baggage_unit_desc = (
                                                        checked_baggage_tmp[0] + ": " + checked_baggage_tmp[1]
                                                    )
                                                checked_baggage_included = True
                                                checked_baggage_para += checked_baggage_unit_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["checked_baggage"] = 1
                                                if "included" not in checked_baggage_desc:
                                                    checked_baggage_desc += " included"
                                                checked_baggage_tmp = checked_baggage_unit_desc.split(":")
                                                if "included" not in checked_baggage_tmp[1]:
                                                    checked_baggage_tmp[1] = checked_baggage_tmp[1].replace("\n", " included \n")
                                                    checked_baggage_unit_desc = (
                                                        checked_baggage_tmp[0] + ": " + checked_baggage_tmp[1]
                                                    )
                                                checked_baggage_included = True
                                                checked_baggage_para += checked_baggage_unit_desc
                                        else:
                                            if hardcoded_inc is not None:
                                                continue
                                            # if airline_inclusion_mapping is not None:
                                            #     fare_tags["checked_baggage"] = airline_inclusion_mapping.get(
                                            #         "checked_baggage", None
                                            #     )
                                            # else:
                                            fare_tags["checked_baggage"] = None

                                    elif (
                                        atr["type"] == "CARRYON_BAGGAGE"
                                        or "cabin bag" in atr["description"].lower()
                                        or "laptop" in atr["description"].lower()
                                        or "handbad" in atr["description"].lower()
                                    ):
                                        hand_baggage_unit_desc = atr.get("description", "").lower()
                                        hand_baggage_desc = atr.get("description", "").lower()
                                        # if platting_carrier_iata == "UA" and cabin_class.lower() == "economy":
                                        #     fare_tags["carry_on_baggage"] = 2
                                        #     is_hardcoded_inclusion = True
                                        hardcoded_inc = fare_tags.get("carry_on_baggage", None) if is_hardcoded_inclusion else None
                                        # is_hardcoded_inclusion = False
                                        inclusion = atr.get("inclusion").lower()
                                        hand_baggage_unit_desc = (
                                            "*  "
                                            + atr["type"].replace("_", " ").title()
                                            + " ("
                                            + inclusion
                                            + "): "
                                            + hand_baggage_unit_desc.lower()
                                            + "\n"
                                        )
                                        if hardcoded_inc == 0:
                                            continue
                                        elif inclusion == "chargeable":
                                            if hardcoded_inc == 2:
                                                carryon_baggage_para += hand_baggage_unit_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["checked_baggage"] = 2
                                                carryon_baggage_para += hand_baggage_unit_desc

                                        elif inclusion == "not_included" and hardcoded_inc is None:
                                            fare_tags["carry_on_baggage"] = 0
                                        elif inclusion == "included":
                                            if hardcoded_inc == 1:
                                                if "included" not in hand_baggage_desc:
                                                    hand_baggage_desc += " included"
                                                hand_baggage_tmp = hand_baggage_unit_desc.split(":")
                                                if "included" not in hand_baggage_tmp[1]:
                                                    hand_baggage_tmp[1] = hand_baggage_tmp[1].replace("\n", " included \n")
                                                    hand_baggage_unit_desc = hand_baggage_tmp[0] + ": " + hand_baggage_tmp[1]
                                                hand_baggage_included = True
                                                carryon_baggage_para += hand_baggage_unit_desc
                                            elif hardcoded_inc is None:
                                                hand_baggage_included = True
                                                fare_tags["carry_on_baggage"] = 1
                                                if "included" not in hand_baggage_desc:
                                                    hand_baggage_desc += " included"
                                                hand_baggage_tmp = hand_baggage_unit_desc.split(":")
                                                if "included" not in hand_baggage_tmp[1]:
                                                    hand_baggage_tmp[1] = hand_baggage_tmp[1].replace("\n", " included \n")
                                                    hand_baggage_unit_desc = hand_baggage_tmp[0] + ": " + hand_baggage_tmp[1]
                                                carryon_baggage_para += hand_baggage_unit_desc
                                        else:
                                            if hardcoded_inc is not None:
                                                continue
                                            # if airline_inclusion_mapping is not None:
                                            #     fare_tags["carry_on_baggage"] = airline_inclusion_mapping.get(
                                            #         "carry_on_baggage", None
                                            #     )
                                            # else:
                                            fare_tags["carry_on_baggage"] = None

                                    elif atr["type"] == "REFUNDS":
                                        refunds_desc = atr.get("description", "").lower()
                                        hardcoded_inc = fare_tags.get("refundable", None) if is_hardcoded_inclusion else None
                                        inclusion = atr.get("inclusion").lower()
                                        refunds_desc = (
                                            "*  "
                                            + atr["type"].replace("_", " ").title()
                                            + " ("
                                            + inclusion
                                            + "): "
                                            + refunds_desc.lower()
                                            + "\n"
                                        )
                                        if hardcoded_inc == 0:
                                            continue
                                        elif inclusion == "chargeable":
                                            if hardcoded_inc == 2:
                                                refunds_para += refunds_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["refundable"] = 2
                                                refunds_para += refunds_desc
                                        elif inclusion == "not_included" and hardcoded_inc is None:
                                            fare_tags["refundable"] = 0
                                        elif inclusion == "included":
                                            if hardcoded_inc == 1:
                                                refunds_para += refunds_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["refundable"] = 1
                                                refunds_para += refunds_desc
                                        else:
                                            if hardcoded_inc is not None:
                                                continue
                                            # if airline_inclusion_mapping is not None:
                                            #     fare_tags["refundable"] = airline_inclusion_mapping.get("refundable", None)
                                            # else:
                                            fare_tags["refundable"] = None

                                    elif atr["type"] == "MEAL_BEVERAGE":
                                        meal_beverage_desc = atr.get("description", "").lower()
                                        # if platting_carrier_iata == "UA":
                                        #     fare_tags["meal"] = 2
                                        #     is_hardcoded_inclusion = True
                                        hardcoded_inc = fare_tags.get("meal", None) if is_hardcoded_inclusion else None
                                        # is_hardcoded_inclusion = False
                                        inclusion = atr.get("inclusion").lower()
                                        meal_beverage_desc = (
                                            "*  "
                                            + atr["type"].replace("_", " ").title()
                                            + " ("
                                            + inclusion
                                            + "): "
                                            + meal_beverage_desc.lower()
                                            + "\n"
                                        )
                                        if hardcoded_inc == 0:
                                            continue
                                        elif inclusion == "chargeable":
                                            if hardcoded_inc == 2:
                                                meal_para += meal_beverage_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["meal"] = 2
                                                meal_para += meal_beverage_desc

                                        elif inclusion == "not_included" and hardcoded_inc is None:
                                            fare_tags["meal"] = 0
                                        elif inclusion == "included":
                                            if hardcoded_inc == 1:
                                                meal_para += meal_beverage_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["meal"] = 1
                                                meal_para += meal_beverage_desc
                                        else:
                                            if hardcoded_inc is not None:
                                                continue
                                            # if airline_inclusion_mapping is not None:
                                            #     fare_tags["meal"] = airline_inclusion_mapping.get("meal", None)
                                            # else:
                                            fare_tags["meal"] = None

                                    elif atr["type"] == "SEAT_SELECTION":
                                        seat_selection_desc = atr.get("description", "").lower()
                                        hardcoded_inc = fare_tags.get("seat", None) if is_hardcoded_inclusion else None
                                        inclusion = atr.get("inclusion").lower()
                                        seat_selection_desc = (
                                            "*  "
                                            + atr["type"].replace("_", " ").title()
                                            + " ("
                                            + inclusion
                                            + "): "
                                            + seat_selection_desc.lower()
                                            + "\n"
                                        )
                                        if hardcoded_inc == 0:
                                            continue
                                        elif inclusion == "chargeable":
                                            if hardcoded_inc == 2:
                                                seat_selection_para += seat_selection_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["seat"] = 2
                                                seat_selection_para += seat_selection_desc
                                        elif inclusion == "not_included" and hardcoded_inc is None:
                                            fare_tags["seat"] = 0
                                        elif inclusion == "included":
                                            if hardcoded_inc == 1:
                                                seat_selection_para += seat_selection_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["seat"] = 1
                                                seat_selection_para += seat_selection_desc
                                        else:
                                            if hardcoded_inc is not None:
                                                continue
                                            # if airline_inclusion_mapping is not None:
                                            #     fare_tags["seat"] = airline_inclusion_mapping.get("seat", None)
                                            # else:
                                            fare_tags["seat"] = None

                                    elif atr["type"] == "WIFI":
                                        wifi_desc = atr.get("description", "").lower()
                                        # if platting_carrier_iata == "UA":
                                        #     fare_tags["wifi"] = 2
                                        #     is_hardcoded_inclusion = True
                                        hardcoded_inc = fare_tags.get("wifi", None) if is_hardcoded_inclusion else None
                                        # is_hardcoded_inclusion = False
                                        inclusion = atr.get("inclusion").lower()
                                        wifi_desc = (
                                            "*  "
                                            + atr["type"].replace("_", " ").title()
                                            + " ("
                                            + inclusion
                                            + "): "
                                            + wifi_desc.lower()
                                            + "\n"
                                        )
                                        if hardcoded_inc == 0:
                                            continue
                                        elif inclusion == "chargeable":
                                            if hardcoded_inc == 2:
                                                wifi_para += wifi_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["wifi"] = 2
                                                wifi_para += wifi_desc
                                        elif inclusion == "not_included" and hardcoded_inc is None:
                                            fare_tags["wifi"] = 0
                                        elif inclusion == "included":
                                            if hardcoded_inc == 1:
                                                wifi_para += wifi_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["wifi"] = 1
                                                wifi_para += wifi_desc
                                        else:
                                            if hardcoded_inc is not None:
                                                continue
                                            # if airline_inclusion_mapping is not None:
                                            #     fare_tags["wifi"] = airline_inclusion_mapping.get("wifi", None)
                                            # else:
                                            fare_tags["wifi"] = None

                                    elif atr["type"] == "CHANGES":
                                        changes_desc = atr.get("description", "").lower()
                                        hardcoded_inc = fare_tags.get("changes", None) if is_hardcoded_inclusion else None
                                        inclusion = atr.get("inclusion").lower()
                                        changes_desc = (
                                            "*  "
                                            + atr["type"].replace("_", " ").title()
                                            + " ("
                                            + inclusion
                                            + "): "
                                            + changes_desc.lower()
                                            + "\n"
                                        )
                                        if inclusion == "chargeable":
                                            if hardcoded_inc == 2:
                                                changes_para += changes_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["changes"] = 2
                                                changes_para += changes_desc
                                        elif inclusion == "not_included" and hardcoded_inc is None:
                                            fare_tags["changes"] = 0
                                        elif inclusion == "included":
                                            if hardcoded_inc == 1:
                                                changes_para += changes_desc
                                            elif hardcoded_inc is None:
                                                fare_tags["changes"] = 1
                                                changes_para += changes_desc
                                        else:
                                            if hardcoded_inc is not None:
                                                continue
                                            # if airline_inclusion_mapping is not None:
                                            #     fare_tags["rebookable"] = airline_inclusion_mapping.get("rebookable", None)
                                            # else:
                                            fare_tags["changes"] = None
                                break

                        # have to iterate because at times we get an empty array for inclusions
                        # for ancillarie in fare_tags:
                        #     if platting_carrier_iata == "UA":
                        #         if ancillarie == "wifi" or ancillarie == "meal":
                        #             fare_tags[ancillarie] = 2
                        #     if fare_tags[ancillarie] is None and airline_inclusion_mapping:
                        #         fare_tags[ancillarie] = airline_inclusion_mapping.get(ancillarie, 0)

                        if carryon_baggage_para != "":
                            brand_desc_para += carryon_baggage_para
                        if checked_baggage_para != "":
                            brand_desc_para += checked_baggage_para
                        if refunds_para != "":
                            brand_desc_para += refunds_para
                        if changes_para != "":
                            brand_desc_para += changes_para
                        if seat_selection_para != "":
                            brand_desc_para += seat_selection_para
                        if meal_para != "":
                            brand_desc_para += meal_para
                        if wifi_para != "":
                            brand_desc_para += wifi_para

                        hand_baggage_desc = (
                            "Carry on baggage is not included"
                            if hand_baggage_desc is None or not hand_baggage_included or fare_tags.get("carry_on_baggage") == 2
                            else hand_baggage_desc.lower()
                        )
                        checked_baggage_desc = (
                            "Check in baggage is not included"
                            if checked_baggage_desc is None or not checked_baggage_included or fare_tags.get("checked_baggage") == 2
                            else checked_baggage_desc.lower()
                        )
                        # fallback for haredcoded inclusions
                        if fare_tags.get("carry_on_baggage") == 1:
                            if hand_baggage_desc is None or hand_baggage_desc == "Carry on baggage is not included":
                                hand_baggage_desc = "Carry on baggage is included"
                        if fare_tags.get("checked_baggage") == 1:
                            if checked_baggage_desc is None or checked_baggage_desc == "Check in baggage is not included":
                                checked_baggage_desc = "Check in baggage is included"

                        baggage = Baggage(
                            checkin_baggage=checked_baggage_desc,
                            checkin_baggage_unit=None,
                            hand_baggage=hand_baggage_desc,
                            hand_baggage_unit=None,
                        )
                        detail_baggage.append(
                            DetailBaggage(
                                checkin_baggage=checked_baggage_desc,
                                checkin_baggage_unit=None,
                                hand_baggage=hand_baggage_desc,
                                hand_baggage_unit=None,
                                origin=origin,
                                destination=destination,
                            )
                        )

                        stop_count = int(flight_detail.get("stop_count", 0))
                        carrier_name_vendor = flight_data.get("carrier_name", "")
                        cabin_class = flight_data.get("cabin_class", {})
                        cabin_class = CABIN_CLASS_KEYS_MAPPING.get(cabin_class)
                        # cabin class mapping will be there for all sectors
                        cabin_class_mapping = AIRLINE_MAPPING.get(carrier_iata, None)
                        if cabin_class_mapping:
                            # Assuming "premium economy" value for any cabin name related to PEC in AIRLINE_MAPPING
                            brand_name_mapping = cabin_class_mapping.get(cabin_name.lower(), None)
                            if brand_name_mapping is None:
                                cabin_class = "_".join(cabin_class.split(" ")).lower()
                            else:
                                cabin_class_brand_mapping = CABIN_CLASS_KEYS_MAPPING.get(brand_name_mapping.get("cabin_class"))
                                cabin_class = "_".join(cabin_class_brand_mapping.split(" ")).lower()

                        brand_desc = list()
                        brand_desc.append(
                            BrandDesc(
                                type_of_inclusion="cbg",
                                description=checked_baggage_unit_desc,
                                inclusion_value=fare_tags.get("checked_baggage"),
                            )
                        )
                        brand_desc.append(
                            BrandDesc(
                                type_of_inclusion="crn",
                                description=hand_baggage_unit_desc,
                                inclusion_value=fare_tags.get("carry_on_baggage"),
                            )
                        )
                        brand_desc.append(
                            BrandDesc(
                                type_of_inclusion="rbk",
                                description=changes_desc,
                                inclusion_value=fare_tags.get("changes"),
                            )
                        )
                        brand_desc.append(
                            BrandDesc(
                                type_of_inclusion="rfn",
                                description=refunds_desc,
                                inclusion_value=fare_tags.get("refundable"),
                            )
                        )
                        brand_desc.append(
                            BrandDesc(
                                type_of_inclusion="st",
                                description=seat_selection_desc,
                                inclusion_value=fare_tags.get("seat"),
                            )
                        )
                        brand_desc.append(
                            BrandDesc(
                                type_of_inclusion="mls",
                                description=meal_beverage_desc,
                                inclusion_value=fare_tags.get("meal"),
                            )
                        )
                        wifi_inclusion_value = 3 if from_country != "US" and to_country != "US" else fare_tags.get("wifi")
                        brand_desc.append(
                            BrandDesc(
                                type_of_inclusion="y5",
                                description=wifi_desc,
                                inclusion_value=wifi_inclusion_value,
                            )
                        )
                        carrier_id = flight_data.get("carrier_id", {})
                        ot = flight_data.get("origin_terminal")
                        dt = flight_data.get("destination_terminal")
                        arrival_time = datetime_format_converter(
                            flight_data.get("arrival_time", {}),
                            "%Y-%m-%dT%H:%M:%S",
                            DATE_TIME_FORMAT,
                        )
                        departure_time = datetime_format_converter(
                            flight_data.get("departure_time", {}),
                            "%Y-%m-%dT%H:%M:%S",
                            DATE_TIME_FORMAT,
                        )
                        duration = (
                            datetime.strptime(arrival_time, DATE_TIME_FORMAT) - datetime.strptime(departure_time, DATE_TIME_FORMAT)
                        ).total_seconds() / 60
                        duration = time_to_sec(flight_data.get("duration"))
                        carrier_name = CARRIER_DATA.get(carrier_iata, carrier_name_vendor)
                        carrier_name = str(carrier_name)
                        over_night = (is_over_night(datetime.strptime(arrival_time, DATE_TIME_FORMAT).time()),)
                        detail_arr = ViaDetails(airport=None, duration=None)
                        total_stop_count = stop_count
                        via = ViaBase(stops=total_stop_count, detail=[detail_arr])
                        brand_id = flight_data.get("brand_id")

                        if flight_count_iter == 1:
                            carrier_iata_first = platting_carrier_iata
                            carrier_iata_name_first = platting_carrier_name
                            cancellation_policy_first = cancellation_policy
                            reschedule_policy_first = reschedule_policy
                            brand_id_first = brand_id
                            cabin_name_first = cabin_name
                            cabin_class_first = cabin_class
                            brand_desc_first = brand_desc
                            brand_desc_para_first = brand_desc_para
                            class_of_service_first = class_of_service

                        flightData = Flight(
                            carrier_iata=carrier_iata,
                            carrier_id=carrier_id,
                            carrier_name=carrier_name,
                            platting_carrier_iata=platting_carrier_iata,
                            platting_carrier_name=platting_carrier_name,
                            cabin_class=cabin_class,
                            cabin_name=cabin_name,
                            duration=duration,
                            origin=origin,
                            destination=destination,
                            arrival_date_time=arrival_time,
                            departure_date_time=departure_time,
                            origin_terminal=ot,
                            destination_terminal=dt,
                            over_night=int(over_night[0]),
                        )
                        current_sector_mvh.append({"ci": carrier_iata, "cid": carrier_id, "ddt": departure_time})
                        current_sector_sd.append(
                            {"ci": carrier_iata, "cid": carrier_id, "adt": arrival_time, "ddt": departure_time}
                        )
                        current_sector_cs.append({"adt": arrival_time, "ddt": departure_time})
                        # For priceline via will be NULL
                        if len(segment_list):
                            previous_segment = segment_list[-1]
                            # previous_segment = previous_segment.dict()
                            layover_time = datetime.strptime(departure_time, DATE_TIME_FORMAT) - datetime.strptime(
                                previous_segment.adt, DATE_TIME_FORMAT
                            )
                            previous_segment.lo = layover_time.total_seconds() / 60
                            total_duration = total_duration + previous_segment.lo
                            previous_segment.on = (
                                previous_segment.on
                                if previous_segment.on
                                else is_over_night(datetime.strptime(departure_time, DATE_TIME_FORMAT).time())
                            )
                        segment_list.append(flightData)
                        total_duration = total_duration + duration
                        # vendor_base_price_per_ticket=None
                        if int(trip_info["round_trip"]) == 1 or flight_request["multi_city"] == 1:
                            rt_fb_list.append(
                                FareBreakup(
                                    booking_class_code=class_of_service,
                                    cabin_class=cabin_class,
                                    fare_basis_code=carrier_id,
                                    pax_type="ADT",
                                    origin=origin,
                                    destination=destination,
                                    vendor_base_price=base_fare_per_ticket,
                                    vendor_currency=vendor_currency,
                                    baggage=baggage,
                                    brand_id=brand_id,
                                    checked_baggage=fare_tags.get("checked_baggage"),
                                    carry_on_baggage=fare_tags.get("carry_on_baggage"),
                                    rebookable=fare_tags.get("changes"),
                                    refundable=fare_tags.get("refundable"),
                                    seat=fare_tags.get("seat"),
                                    meal=fare_tags.get("meal"),
                                    wifi=fare_tags.get("wifi"),
                                    beverage=None,
                                )
                            )
                        else:
                            fare_breakup.extend(
                                [
                                    FareBreakup(
                                        booking_class_code=class_of_service,
                                        cabin_class=cabin_class,
                                        fare_basis_code=carrier_id,
                                        pax_type="ADT",
                                        origin=origin,
                                        destination=destination,
                                        vendor_base_price=base_fare_per_ticket,
                                        vendor_currency=vendor_currency,
                                        baggage=baggage,
                                        brand_id=brand_id,
                                        checked_baggage=fare_tags.get("checked_baggage"),
                                        carry_on_baggage=fare_tags.get("carry_on_baggage"),
                                        rebookable=fare_tags.get("changes"),
                                        refundable=fare_tags.get("refundable"),
                                        seat=fare_tags.get("seat"),
                                        meal=fare_tags.get("meal"),
                                        wifi=fare_tags.get("wifi"),
                                        beverage=None,
                                    )
                                ]
                            )

                        # fare_breakup is being passing un the PaxFareBreakup
                    if is_restricted_journey:
                        break
                    # We need these for multi_city leg as it will be used for deduplication
                    mvh_cabin_class = [{"cc": cabin_class}]
                    leg_with_fare_hash = json.dumps([current_sector_mvh]) + json.dumps(mvh_cabin_class)
                    leg_with_fare_cs = json.dumps([current_sector_cs]) + json.dumps(mvh_cabin_class)
                    leg_with_fare_sd = json.dumps([current_sector_sd]) + json.dumps(mvh_cabin_class)
                    if int(trip_info["round_trip"]) == 1 or flight_request["multi_city"] == 1:
                        fare_breakup.append(rt_fb_list)
                        segment = FlightSegment(
                            flight=segment_list,
                            total_duration=total_duration,
                            morefare_status=morefare_status,
                            via=via,
                            leg_with_fare_hash=leg_with_fare_hash,
                            leg_with_fare_cs=leg_with_fare_cs,
                            leg_with_fare_sd=leg_with_fare_sd,
                        )
                        # print("segment---->>", segment.dict())
                        round_trip_leg.append(segment_list)
                        fare_breakup_round_trip.extend(fare_breakup)
                        round_segment.append(segment)
                        count += 1
                        if count == 1:
                            detail_baggage_first = detail_baggage

                    else:
                        detail_baggage_first = detail_baggage
                    # If it is part of multi_city, then different fare for each sector.
                    # if it is one way or multi_city, decide on last sector index
                    if flight_request.get("multi_city", 0) == 1 or index_sector == no_of_sectors - 1:
                        if flight_request.get("multi_city", 0) == 1:
                            final_fare_breakup = [rt_fb_list]
                            if origin_airport_check and segment_list[0].ogn != from_iata:
                                is_restricted_journey = True
                                break
                            if destination_airport_check and segment_list[-1].dty != to_iata:
                                is_restricted_journey = True
                                break

                        elif int(trip_info["round_trip"]) == 1:
                            final_fare_breakup = fare_breakup_round_trip
                            if origin_airport_check and (
                                round_segment[0].fgt[0].ogn != from_iata or round_segment[-1].fgt[-1].dty != from_iata
                            ):
                                is_restricted_journey = True
                                break
                            if destination_airport_check and (
                                round_segment[0].fgt[-1].dty != to_iata or round_segment[-1].fgt[0].ogn != to_iata
                            ):
                                is_restricted_journey = True
                                break
                        else:
                            final_fare_breakup = [fare_breakup]
                            if origin_airport_check and segment_list[0].ogn != from_iata:
                                is_restricted_journey = True
                                break

                            if destination_airport_check and segment_list[-1].dty != to_iata:
                                is_restricted_journey = True
                                break

                        for _ in range(num_pax):
                            pax_fare_breakup.append(
                                PaxFareBreakup(
                                    pax_type="ADT",
                                    fare_breakup=final_fare_breakup,
                                    vendor_total_price=total_price_per_ticket,
                                    vendor_base_price=base_fare_per_ticket,
                                    vendor_currency=vendor_currency,
                                    vendor_tax=vendor_tax,
                                    cancellation_policy=cancellation_policy_first,
                                    reschedule_policy=reschedule_policy_first,
                                )
                            )
                        scc = 0
                        scc = check_basic_economy(
                            AIRLINE_MAPPING,
                            LCC_AIRLINE_MAPPING,
                            cabin_name_first,
                            cabin_class_first,
                            class_of_service_first,
                            carrier_iata_first,
                            from_country,
                            to_country,
                        )
                        more_detail = MoreDetail(type="link")
                        # if(brand_id):
                        # update with ref and pass the path only when we are having cabin baggage details.
                        if (
                            brand_desc_first[0].inc == 1
                            or brand_desc_first[0].inc == 2
                            or brand_desc_first[1].inc == 1
                            or brand_desc_first[1].inc == 2
                        ):
                            uuid_str = str(uuid.uuid4())
                            more_detail = MoreDetail(type="ref", path=uuid_str)
                            brand_desc_first.append(
                                BrandDesc(
                                    type_of_inclusion="brddesc",
                                    description=brand_desc_para_first,
                                    inclusion_value=1,
                                )
                            )
                            more_detail_data[-1].append(MoreDetailData(path=uuid_str, description=brand_desc_para_first).dict())
                        logger.info(f"Brand rule : {brand_desc_first}")
                        brand_desc_first = sorted(brand_desc_first, key=custom_sort)
                        if cabin_name_first.lower() == cabin_class_first.lower():
                            brand_name_hash = cabin_class_first.replace(" ", "").lower()
                            # Brand name hash will be computed based on inclusions value
                            inclusion_str = ""
                            # All inclusions will be present in brand_desc_first
                            for each_brand_desc in brand_desc_first:
                                if each_brand_desc.typ in brand_description_to_compare:
                                    inclusion_str += f":{each_brand_desc.inc}"
                            brand_name_hash += inclusion_str
                        else:
                            brand_name_hash = cabin_name_first.replace(" ", "").lower()

                        sector_wise_fare_list.append(
                            {
                                "pax_fare_breakup": pax_fare_breakup,
                                "platting_carrier": carrier_iata_first,
                                "platting_carrier_name": carrier_iata_name_first,
                                "cancellation_policy": cancellation_policy_first,
                                "reschedule_policy": reschedule_policy_first,
                                "brand_id": brand_id_first,
                                "brand_name": cabin_name_first,
                                "brand_name_hash": brand_name_hash,
                                "scc": scc,
                                "cabin_class": cabin_class_first,
                                "brand_desc": brand_desc_first,
                                "more_detail": more_detail,
                                "detail_baggage": detail_baggage_first,
                                "original_brand_name": original_brand_name,
                                "vendor_brand_data": vendor_brand_data,
                                "is_hardcoded_data": is_data_hardcoded_inclusion,
                            }
                        )

                if is_restricted_journey:
                    continue
                all_segment = round_segment

                # TODO: need to get the exact context for ReschedulePolicy

                # reschedule_policy.append(rp_dict)
                # TODO: need to get the exact context for CancellationPolicy
                # cp_dict = CancellationPolicy(cancellation_amount_type='percentage', charge=00.00, applies_on="time_duration")
                # cancellation_policy.append(cp_dict)
                # print("fare_breakup--->>",fare_breakup)

                # total_stops = flight_data.get("total_stops", {})
                if int(trip_info["round_trip"]) != 1 and flight_request["multi_city"] != 1:
                    all_segment = [
                        FlightSegment(
                            flight=segment_list,
                            total_duration=total_duration,
                            morefare_status=morefare_status,
                            via=via,
                        )
                    ]
                adult_fare_client_rate = currency_conversion(client_currency_details.rate, total_price_per_ticket)
                fare_selection = "RETAIL"
                compare_fare_dict = get_compare_fare_value(fre_config.fare_preference_group, fare_selection, vendor_total_price)
                compare_fare = compare_fare_dict["compare_fare"]
                compare_fare_priority = compare_fare_dict["compare_fare_priority"]
                search_id = trip_info["search_id"]
                discounted_return = 0
                all_fare = list()
                travel_type = start_country + travel_type if travel_type and travel_type != "ALL" else travel_type
                if multi_city_fare:
                    is_l3_card_trigger_mc = True if travel_type and travel_type in BAGGAGE_DATA_ALLOWED_COUNTRY else False
                last_sector_fare = Fare(
                    **sector_wise_fare_list[-1],
                    vendor_total_price=vendor_total_price,
                    vendor_tax=vendor_tax,
                    vendor_currency=vendor_currency,
                    vendor_base_price=vendor_base_price,
                    api=fre_config.name,
                    compare_fare=compare_fare,
                    compare_fare_priority=compare_fare_priority,
                    cvwdm_id=fre_config.cvwdm_id,
                    connection_priority=fre_config.connection_priority,
                    search_id=search_id,
                    fare_selection=fare_selection,
                    ppn_bundle=ppn_bundle,
                    ppn_return_bundle=ppn_return_bundle,
                    discounted_return=discounted_return,
                    traveller_fare=traveller_fare,
                    itilite_fare=itilite_fare,
                    vendor_fare=vendor_fare,
                    client_fare=client_fare,
                    adult_fare_client_rate=adult_fare_client_rate,
                    is_l3_card_trigger=is_l3_card_trigger_mc if is_l3_card_trigger_mc is not None else is_l3_card_trigger,
                    multi_city_fare=multi_city_fare,
                )
                if multi_city_fare:
                    last_leg_fid = last_sector_fare.fid
                    last_sector_fare.mc_fid = last_leg_fid
                    for i in range(0, len(sector_wise_fare_list) - 1):
                        fare = Fare(
                            **sector_wise_fare_list[i],
                            vendor_total_price=vendor_total_price,
                            vendor_tax=vendor_tax,
                            vendor_currency=vendor_currency,
                            vendor_base_price=vendor_base_price,
                            api=fre_config.name,
                            compare_fare=compare_fare,
                            compare_fare_priority=compare_fare_priority,
                            cvwdm_id=fre_config.cvwdm_id,
                            connection_priority=fre_config.connection_priority,
                            search_id=search_id,
                            fare_selection=fare_selection,
                            ppn_bundle=ppn_bundle,
                            ppn_return_bundle=ppn_return_bundle,
                            discounted_return=discounted_return,
                            traveller_fare=traveller_fare,
                            itilite_fare=itilite_fare,
                            vendor_fare=vendor_fare,
                            client_fare=client_fare,
                            adult_fare_client_rate=adult_fare_client_rate,
                            is_l3_card_trigger=is_l3_card_trigger_mc if is_l3_card_trigger_mc is not None else is_l3_card_trigger,
                            multi_city_fare=multi_city_fare,
                            mc_fid=last_leg_fid,
                        )
                        all_fare.append(fare)
                all_fare.append(last_sector_fare)
                update_l2_info_missing(l2_info_missing, brand_desc_first, carrier_iata, fare_selection)
                legdetail_flight = LegDetails(leg=all_segment, fl=all_fare)
                legdetail.append(legdetail_flight)
                no_of_transformed_flight += 1

            flight_result = FlightResult(result=legdetail)
            _flight_result = orjson.loads(flight_result.json())

            # print("Final Json Result",flight_result.dict())
            # if reschedule flow for ppn
            # have the auth in place
            # make the more fare call
            # check for the brand fares returned
            # push only if the user requested brand name is present
            #
            transformed_queue.put(_flight_result)
            new_relic_custom_event.update(l2_info_missing)
            logger.info("Transformation of data to itilite standard completed successfully")
            return flight_result.dict(), more_detail_data, no_of_transformed_flight
        except Exception as ex:
            logger.error(f"There is an error while performing the transform: {str(ex)} {traceback.format_exc()}")

    def _get_mapping(self):
        return priceline_lfs_mapping
