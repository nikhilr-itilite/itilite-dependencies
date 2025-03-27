import base64
import json
import os
import shutil
import html
import re
import time
import traceback
import uuid
from decimal import Decimal

import requests
from datetime import time as t
from datetime import datetime, timedelta, date, timezone
from enum import Enum

import pyaes
from collections import OrderedDict
import copy

from helperlayer.validator import StaticFareRule, Baggage, DetailBaggage, BrandDesc, PaxFareBreakup
from helperlayer.category_mapping import gds
from bson import json_util
from opensearchlogger.logging import logger

from helperlayer.botoclient import get_events_boto_client, get_lambda_boto_client
from functools import wraps
from helperlayer.application_constants import StaticDBConstants, FlightConstants, TripInfoConstants, NewRelicConstants
from typing import Optional, Tuple, List, Dict, Any

NR_API_EXECUTION_EVENT = "APIExecutionLog"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"

MONGO_DB_PASSWORD = os.environ.get("MONGO_DB_PASSWORD")
MONGO_DB_USERNAME = os.environ.get("MONGO_DB_USERNAME")
MONGO_HOST = os.environ.get("MONGO_HOST")
HOTEL_REQUEST_DATE_FORMAT = "%d %b, %Y"


class BookingStatus(Enum):
    STARTED = "booking_initiated"
    PENDING = "booking_pending"
    INPROGRESS = "booking_inprogress"
    SUCCESS = "booking_completed"
    FAILED = "booking_failure"


class HotelAPITypes(Enum):
    PPN_AVAILABILITY = "ppn_availability"
    PPN_RESULTS = "ppn_results"
    PPN_CONTRACT = "ppn_contract"
    PPN_BOOK = "ppn_book"
    PPN_LOOKUP = "ppn_lookup"
    PPN_CANCEL = "ppn_cancel"

    GDS_SEARCH = "gds_search"
    GDS_DETAIL = "gds_detail"
    GDS_FAREQUOTE = "gds_farequote"  # This is GDS_DETAIL but separate entry to distinguish
    GDS_UNIVERSAL_API = "gdS_universal_api"
    GDS_RULES = "gds_rules"
    GDS_RESERVATION = "gds_reservation"
    GDS_QUEUE = "gds_queue"

    DESIYA_CITY_SEARCH = "desiya_json_city_search"
    DESIYA_HOTEL_SEARCH = "desiya_json_hotel_search"
    DESIYA_CONTENT_SEARCH = "desiya_json_content"
    DESIYA_REVIEW_SEARCH = "desiya_json_review"
    DESIYA_CREATE_PROVISIONAL_BOOKING = "desiya_json_create_provisional_booking"
    DESIYA_CONFIRM_PROVISIONAL_BOOKING = "desiya_json_confirm_provisional_booking"
    DESIYA_RETRIEVE_BOOKING = "desiya_json_retrieve_booking"


class FlightAPITypes(Enum):
    PPN_CONTRACT = "ppn_contract"
    PPN_CONTRACT_MF = "ppn_contract_mf"
    PPN_RETURN_FLIGHT_CALL = "ppn_return_call"


class SelectionStatus(Enum):
    DRAFT = 0
    BOOKING_COMPLETED = 1
    APPROVAL = 2  # approval_initiated/approval_approved/approval_rejected
    USER_CARD_PAYMENT = 3  # payment_initiated/payment_failed/payment_completed
    CENTRAL_CARD_PAYMENT = 4  # payment_initiated/payment_failed/payment_completed
    BOOKING_REQUESTED = 5
    BOOKING_PARTIAL_SUCCESS = 6
    BOOKING_FAILED = 7
    BOOKING_TRIGGERED = 8


class CurrentTripStatus(Enum):
    DRAFT = 0
    AWAITING_APPROVAL = 1
    TRIP_APPROVED = 2
    TRIP_REJECTED = 3
    PAYMENT_PENDING = 4
    PAYMENT_COMPLETED = 5
    BOOKING_REQUESTED = 6
    BOOKING_FAILED = 7
    BOOKING_COMPLETED = 8
    BOOKING_PARTIALLY_COMPLETED = 9


class PaymentStatus(Enum):
    PAYMENT_INITIATED = 1
    PAYMENT_COMPLETED = 2
    PAYMENT_FAILED = 3


class FarequoteStatus(Enum):
    PENDING = 0
    STARTED = 1
    SUCCESS = 2
    NO_RESULT = 3
    FAILED = 4


class HotelRateOrder(Enum):
    COMPANY_RATE: int = 1
    MEMBERSHIP_RATE: int = 2
    ITILITE_RATE: int = 3
    RETAIL_RATE: int = 3
    FLEXI_RATE: int = 3  # This is retail rate
    AAA_RATE: int = 6
    REWARDS_2X: int = 7
    AARP_RATE: int = 8


class HotelRateType(Enum):
    COMPANY_RATE: str = "company_rate"
    MEMBERSHIP_RATE: str = "membership_rate"
    ITILITE_RATE: str = "itilite_rate"
    RETAIL_RATE: str = "retail_rate"
    AAA_RATE: str = "aaa_rate"
    REWARDS_2X: str = "rewards_2x"
    AARP_RATE: str = "aarp_rate"
    FLEXI_RATE: str = "flexi_rate"


def push_newrelic_custom_event(new_relic_agent, custom_event_name, new_relic_custom_event):
    try:
        new_relic_agent.record_custom_event(custom_event_name, new_relic_custom_event)
    except Exception:
        logger.error(f"Error while pushing newrelic events. error: {traceback.format_exc()}")


def newrelic_api_execution_log_decorator(api_type, event_name, vendor_name, **kwargs):
    """
    Decorator that tracks API execution details and sends them to New Relic.
    """
    import newrelic.agent  # Nr is not added in all the lambdas

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            _api_start = datetime.now()
            try:
                response = func(self, *args, **kwargs)
                new_relic_custom_event = {
                    "api_type": api_type,  # The API type being executed
                    "execution_time": (datetime.now() - _api_start).total_seconds(),  # Time taken for execution
                    "api_status_code": response.status_code if hasattr(response, "status_code") else 500,
                    # HTTP Status Code
                    "vendor": self.fre_config.get(vendor_name),
                }
                new_relic_custom_event.update(**kwargs)
                push_newrelic_custom_event(newrelic.agent, event_name, new_relic_custom_event)

                return response

            except Exception as e:
                push_newrelic_custom_event(
                    newrelic.agent,
                    event_name,
                    new_relic_custom_event={
                        "api_type": api_type,
                        "execution_time": (datetime.now() - _api_start).total_seconds(),
                        "api_status_code": 500,  # Failed request
                        "vendor": self.fre_config.get(vendor_name),
                    },
                )
                raise e

        return wrapper

    return decorator


def AES_decryption_data(encrypted_data):
    # DECRYPTION
    AES_KEY = os.environ["AES_KEY"]
    key = AES_KEY.encode("utf-8")
    aes = pyaes.AESModeOfOperationCTR(key)
    encrypted_data = base64.b64decode(encrypted_data)
    decrypted_data = aes.decrypt(encrypted_data).decode("utf-8")
    return decrypted_data


def datetime_format_converter(datetime_inp: str, req_format: str, resp_format: str):
    """
    Datetime converter
    :param datetime_inp: datetime inp int string
    :param req_format: request format
    :param resp_format: response format
    :return:
    """
    return datetime.strftime(datetime.strptime(datetime_inp, req_format), resp_format)


def get_currency_conv_rate(vendor_currency, client_currency, staff_currency):
    try:
        print("helper input -----------", vendor_currency, client_currency, staff_currency)
        cc = {"type": "", "rate": ""}
        sc = {"type": "", "rate": ""}
        currency = {}
        vc_to_inr = 1 / float(vendor_currency["rate"])

        cc_rate = float(client_currency["rate"]) * vc_to_inr
        cc["type"] = client_currency["type"]
        cc["rate"] = 1.00 if vendor_currency["type"] == client_currency["type"] else cc_rate

        usrc_rate = float(staff_currency["rate"]) * vc_to_inr
        sc["rate"] = 1.00 if vendor_currency["type"] == staff_currency["type"] else usrc_rate
        sc["type"] = staff_currency["type"]

        vc = {"type": vendor_currency["type"], "rate": 1}
        ic = {"type": "INR", "rate": vc_to_inr}
        currency = {"cc": cc, "sc": sc, "vc": vc, "ic": ic}
        print("cc-----", currency)
        return currency
    except Exception as ex:
        print("error in currency conversion", ex)
        raise ex


def get_cache_key_hotel(city, country, check_in_date, check_out_date):
    cache_key = str(
        uuid.uuid3(
            uuid.NAMESPACE_X500,
            json.dumps(
                {
                    city: city,
                    country: country,
                    check_in_date: check_in_date,
                    check_out_date: check_out_date,
                }
            ),
        )
    )
    cold_cache_key = str(uuid.uuid3(uuid.NAMESPACE_X500, json.dumps({city: city, country: country})))
    return cache_key, cold_cache_key


def get_cache_key_flight(from_iata, to_iata, onward_date, return_date, is_rt):
    cache_key = str(
        uuid.uuid3(
            uuid.NAMESPACE_X500,
            json.dumps(
                {
                    from_iata: from_iata,
                    to_iata: to_iata,
                    onward_date: onward_date,
                    return_date: return_date,
                    is_rt: is_rt,
                }
            ),
        )
    )
    cold_cache_key = str(uuid.uuid3(uuid.NAMESPACE_X500, json.dumps({from_iata: from_iata, to_iata: to_iata})))
    return cache_key, cold_cache_key


def get_currency_conversion_rate(from_currency, to_currency):
    fc_to_tc_rate = ""
    tc_to_inr = round(1 / float(to_currency["rate"]), 2)
    cc_rate = float(from_currency["rate"]) * tc_to_inr
    fc_to_tc_rate = round(cc_rate, 2)
    return fc_to_tc_rate


def check_basic_economy(
    airline_mapping,
    lcc_airline_mapping,
    cabin_name,
    cabin_class,
    class_of_service,
    carrier_iata,
    from_country,
    to_country,
):
    if from_country != "US" or to_country != "US":
        return 0
    if cabin_class is None or str(cabin_class).lower() != "economy":
        return 0
    if cabin_name is not None or cabin_name != "":
        if "basic" in cabin_name.lower():
            return 1

    if lcc_airline_mapping is not None and str(carrier_iata) in lcc_airline_mapping:
        return 1

    carrier_airline_mapping = airline_mapping.get(carrier_iata, None)
    if carrier_airline_mapping is not None:
        bc_tags = carrier_airline_mapping.get("bc_tags", None)
        if bc_tags is not None:
            for i in range(0, len(bc_tags)):
                if cabin_name is not None and cabin_name != "" and str(bc_tags[i]).strip().lower() == cabin_name.lower():
                    return 1
        tags_booking_code = carrier_airline_mapping.get("tags_booking_code", None)
        if tags_booking_code is not None:
            for i in range(0, len(tags_booking_code)):
                if (
                    class_of_service is not None
                    and class_of_service != ""
                    and str(tags_booking_code[i]).lower() == class_of_service.lower()
                ):
                    return 1
    logger.info(f"Returning 0 {cabin_name} {cabin_class} {class_of_service} {carrier_iata}")
    return 0


def is_warmer(func):
    def wrapper(*args, **kwargs):
        event = args[0] or {}
        if not event:
            print("Why don't we have input event ?")
        if isinstance(event, dict) and event.get("warmer") is True:
            __WARMER_CONCURRENCY__ = int(event["__WARMER_CONCURRENCY__"])
            execution_multiplier = os.getenv("WARMER_EXECUTION_MULTIPLIER") or 4
            warmer_sleep_time = __WARMER_CONCURRENCY__ * int(execution_multiplier) / 1000
            print(f"Warmer is called. sleep time:{warmer_sleep_time}")
            time.sleep(warmer_sleep_time)
            # If there are 50 machines that need to be warmed up, and it currently takes 200ms for all the machines
            # to warm up, we need to ensure that we don't reuse the same warmed-up machines. Therefore, a delay must
            # be added. The current estimate for the sleep duration is four times the total execution time.
            return
        return func(*args, **kwargs)

    return wrapper


def get_airline_cabin_name_mapping(mongo_obj):
    try:
        logger.info("get_airline_cabin_name_mapping is called")
        mongo_db_name = os.getenv("STATIC_DATABASE")
        collection_name = os.getenv("FLIGHT_AIRLINE_MAPPING")
        mongo_res = mongo_obj.find(mongo_db_name, collection_name, {})
        flight_airline_mapping = {}
        for doc in mongo_res:
            vendor = doc["vendor"]
            flight_airline_mapping[vendor] = doc

        return flight_airline_mapping
    except Exception:
        logger.error(f"Error in get_airline_mapping {traceback.format_exc()}")
        return {}


def get_airline_inclusion(mongo_obj):
    try:
        logger.info("get_airline_inclusion is called")
        airline_inclusion_mapping = {}
        mongo_db_name = os.getenv("STATIC_DATABASE")
        collection_name = os.getenv("FLIGHT_INCLUSION_MAPPING")
        mongo_res = mongo_obj.find(mongo_db_name, collection_name, {})
        for doc in mongo_res:
            airline = doc["airline"]
            airline_inclusion_mapping[airline] = doc

        return airline_inclusion_mapping
    except Exception:
        logger.error(f"Error in get_airline_inclusion {traceback.format_exc()}")
        return None


def get_carrier_names(DatabaseConnection):
    """
    Fetches all iatacode and carrier names from database.
    :return: dictionary with iatacode as key and carrier name as value for faster fetch.
    """
    try:
        conn = DatabaseConnection.get_instance("api").get_connection()
        sql = "select iatacode,name from airline_iata_new"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                _result = cursor.fetchall()
                cursor.close()
                _carrier_data = {}
                for item in _result:
                    _carrier_data[item["iatacode"]] = item["name"]
                # print(_carrier_data)
        logger.info("Iata code fetched successfully from db")
        return _carrier_data
    except Exception as e:
        logger.error(f"Error while fetching airline iata data{e}")
        return {}


def format_currency_conversion_details(mongo_obj, requested_currency, fetch_all_currency=False):
    try:
        func_start_time = datetime.now()
        TRIP_DB = TripInfoConstants.TRIP_DB
        CURRENCY_CONVERSION_COLLECTION = TripInfoConstants.CURRENCY_CONVERSION_COLLECTION
        # fetching the currecny conversion details
        base_currency = "INR"  # default for itilite
        pipeline = [{"$match": {"base_currency": base_currency}}, {"$sort": {"date": -1}}, {"$limit": 1}]
        currency_conv_resp = mongo_obj.aggregate(TRIP_DB, CURRENCY_CONVERSION_COLLECTION, pipeline)
        resp = {}
        if len(currency_conv_resp) > 0:
            if currency_conv_resp[0].get("rates") is not None:
                if fetch_all_currency:
                    return currency_conv_resp[0].get("rates")
                resp["currency_rate"] = currency_conv_resp[0].get("rates").get(requested_currency)
        diff = datetime.now() - func_start_time
        logger.info(f"time to finish the format_currency_conversion_details is {diff.total_seconds()}")
        return resp
    except Exception:
        logger.error(f"Error in fetch_currency_conversion_details {traceback.format_exc()}")


def schedule_task(lambda_function_name, execution_time, auth_token, method, payload={}, query_parameters={}):
    try:
        logger.info(
            "--schedule_task-lambda_function_name %s execution_time %s auth_token %s method %s payload %s query_parameters %s--",
            lambda_function_name,
            execution_time,
            auth_token,
            method,
            payload,
            query_parameters,
        )
        aws_region = os.getenv("AWS_REGION_NAME")
        aws_account_id = os.getenv("CDK_DEFAULT_ACCOUNT")

        events_client = get_events_boto_client()

        lambda_client = get_lambda_boto_client()

        # execution time in UTC
        cron_expression = (
            f"{execution_time.minute} {execution_time.hour} {execution_time.day} {execution_time.month} ? {execution_time.year}"
        )
        schedule_rule_name = payload.get("schedule_rule_name")
        rule_name = schedule_rule_name if (schedule_rule_name) else str(uuid.uuid4())
        response = events_client.put_rule(Name=rule_name, ScheduleExpression=f"cron({cron_expression})", State="ENABLED")
        statement_id = f"{rule_name}_permission"

        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId=statement_id,
            Action="lambda:InvokeFunction",
            Principal="events.amazonaws.com",
            SourceArn=response["RuleArn"],
        )

        payload["triggered_by"] = "scheduler"
        payload["rule_name"] = rule_name
        payload["function_name"] = lambda_function_name

        body_params = json.dumps(payload) if (payload) else {}

        headers = {
            "Authorization": auth_token,
        }

        target_input = {"body": body_params, "queryStringParameters": query_parameters, "httpMethod": method, "headers": headers}

        target_id = str(uuid.uuid4())

        events_client.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    "Id": target_id,
                    "Arn": f"arn:aws:lambda:{aws_region}:{aws_account_id}:function:{lambda_function_name}",
                    "Input": json.dumps(target_input),
                }
            ],
        )

        logger.info(
            "---Event scheduled for lambda function %s with execution time %s with the params %s, %s, %s, %s, %s rule_name %s--",
            lambda_function_name,
            execution_time,
            auth_token,
            method,
            payload,
            query_parameters,
            headers,
            rule_name,
        )

    except Exception as ex:
        logger.error(
            "------ERROR in schedule_task %s------%s",
            lambda_function_name,
            ex,
            exc_info=True,
        )
        message = f"ERROR in schedule_task for lambda function {lambda_function_name}-----{ex, traceback.format_exc()}"
        send_bot_message(message)


def delete_scheduler_rule(function_name, rule_name):
    try:
        logger.info("-----delete_scheduler_rule %s------%s", function_name, rule_name)
        events_client = get_events_boto_client()

        response = events_client.list_targets_by_rule(Rule=rule_name)
        targets = response["Targets"]

        logger.info("--------------rule name %s -----------targets %s", rule_name, targets)

        for target in targets:
            response = events_client.remove_targets(Rule=rule_name, Ids=[target["Id"]])
            logger.info(f"Rule '{rule_name}' remove target response {response}.")

        lambda_client = get_lambda_boto_client()

        statement_id = f"{rule_name}_permission"
        lambda_client.remove_permission(FunctionName=function_name, StatementId=statement_id)

        events_client.disable_rule(Name=rule_name)
        events_client.delete_rule(Name=rule_name)
        logger.info(f"Rule '{rule_name}' deleted successfully.")
    except Exception as ex:
        logger.error(
            "------ERROR in delete_scheduler_rule %s------%s",
            rule_name,
            ex,
            exc_info=True,
        )
        message = f"ERROR in delete_scheduler_rule {rule_name}-----{ex, traceback.format_exc()}"
        send_bot_message(message)


def send_bot_message(msg):
    logger.info("----------send_bot_message-----%s", msg)
    if not int(os.getenv("ENABLE_BOT_NOTIFICATION")):
        return
    url = os.getenv("BOT_NOTIFICATION_URI")
    bot_message = {"text": msg}
    message_headers = {"Content-Type": "application/json; charset=UTF-8"}
    response = requests.post(url, headers=message_headers, json=bot_message)
    logger.info("----------message notification-----%s,%s", msg, response)


def retry(times, exceptions, delay=0):
    """
    Retry Decorator
    Retries the wrapped function/method `times` times if the exceptions listed
    in `exceptions` are thrown after a `delay` in seconds

    Definition:
    :param times: The number of times to repeat the wrapped function/method
    :type times: Int
    :param exceptions: Lists of exceptions that trigger a retry attempt
    :type exceptions: Tuple of Exceptions
    :param delay: Number of seconds to wait before next retry
    :type delay: Int

    Usage:
    @retry(times=3, exceptions=(ValueError, TypeError), delay=1)
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    time.sleep(delay)
                    logger.info("Exception thrown when attempting to run %s, attempt " "%d of %d" % (func, attempt, times))
                    attempt += 1
            return func(*args, **kwargs)

        return wrapper

    return decorator


def calc_flight_travel_time(origin_dt, destination_dt, date_time_format):
    origin_dt = datetime.strptime(origin_dt, date_time_format)
    destination_dt = datetime.strptime(destination_dt, date_time_format)
    flightTravelTime = (destination_dt - origin_dt).total_seconds() / 60
    return flightTravelTime


def currency_conversion(rate, price):
    """
    Calculates currency conversion.
    :param rate: conversion rate
    :param price: price
    """
    try:
        return float(rate) * float(price)
    except Exception as e:
        logger.error(f"Error in currency conversion: {traceback.format_exc()}")
        return e


def convert_fares(fare_list, itf_rate, vf_rate, cf_rate, tf_rate):
    itf_fare_list = [
        {"key": fare["key"], "category": fare["category"], "value": currency_conversion(itf_rate, fare["value"])}
        for fare in fare_list
    ]
    vf_fare_list = [
        {"key": fare["key"], "category": fare["category"], "value": currency_conversion(vf_rate, fare["value"])}
        for fare in fare_list
    ]
    cf_fare_list = [
        {"key": fare["key"], "category": fare["category"], "value": currency_conversion(cf_rate, fare["value"])}
        for fare in fare_list
    ]
    tf_fare_list = [
        {"key": fare["key"], "category": fare["category"], "value": currency_conversion(tf_rate, fare["value"])}
        for fare in fare_list
    ]

    return itf_fare_list, vf_fare_list, cf_fare_list, tf_fare_list


def is_over_night(check_time):
    begin_time = t(22, 00)
    end_time = t(4, 00)
    return 1 if check_time >= begin_time or check_time <= end_time else 0


def get_change_cancel_data(data, total_amount, namespace, fre_config=None):
    try:
        price, currency_type = None, None
        if total_amount:
            price = total_amount[3:]
            currency_type = total_amount[:3]
        amount = data.xpath("y:Amount", namespaces=namespace)
        percent = data.xpath("y:Percentage", namespaces=namespace)
        if amount:
            amount = amount[0].text
            amount = amount[3:]
        if percent:
            percent = percent[0].text
            amount = (Decimal(percent) * Decimal(price)) / Decimal(100)
        # What if amount is not there ??
        if amount is None:
            return None, None, None
        amount = Decimal(amount)
        price = Decimal(price)
        time_duration = data.get("PenaltyApplies")
        inc_val = None
        if amount is not None:
            if amount == 0:
                inc_val = 1
            elif amount == price:
                inc_val = 0
            elif amount < price:
                inc_val = 2
        if fre_config and currency_type and currency_type != fre_config.staff_currency.type and amount:
            amount = Decimal(amount) * Decimal(fre_config.staff_currency.rate)
        value = str(int(amount))
        desc = time_duration
        return desc, inc_val, value
    except Exception as e:
        logger.error(f"Error while transforming cancellation data : {e} : Traceback : {traceback.format_exc()}")
        return None, 0, 0


def custom_sort(item):
    try:
        order = ["rfn", "rbk", "crn", "cbg", "st", "mls", "y5", "brddesc", "frr", "fr"]
        return order.index(item.typ)
    except Exception as e:
        logger.error(f"Error while sorting data : {e}")
        return item


def convert_text(text):
    try:
        text = re.sub(r"UPTO(\d+)LI/(\d+)LCM", r"Up to \1LI (\2LCM)", text)
        text = re.sub(r"UPTO(\d+)LB/(\d+)KG", r"Up to \1lb (\2kg)", text)
        text = text.capitalize()
    except Exception as e:
        logger.error(f"Exception while converting text {e}: Please add regex for this text {text}")
        text = text.capitalize()
    return text


def to_sentence_case(text):
    lines = text.split("\n")
    result_lines = []
    for line in lines:
        words = line.split()
        if words:
            result_words = [words[0].capitalize()]
            for word in words[1:]:
                if word and word[0] in ".?!":
                    result_words.append(word[0])
                    if len(word) > 1:
                        result_words.append(word[1:].lower())
                else:
                    result_words.append(word.lower())
            result_lines.append(" ".join(result_words))
    return "\n".join(result_lines)


def format_fare_rule(fare_rule_list, vendor):
    fare_rule_data_list = list()
    try:
        for fare_rule in fare_rule_list:
            fare_rule_dict = {}
            if vendor == "gds":
                category_name = gds.get(fare_rule.get("category"))
            else:
                category_name = to_sentence_case(fare_rule.get("category").strip())
            if category_name and (vendor == "gds" or (vendor != "gds" and category_name.lower() == "penalties")):
                fare_rule_dict["heading"] = category_name
                formatted_charters = to_sentence_case(fare_rule["text"].strip())
                fare_rule_dict["text"] = formatted_charters
                fare_rule_data_list.append(fare_rule_dict)
        unique_values = {}
        for fare_rule_data in fare_rule_data_list:
            heading = fare_rule_data["heading"]
            if heading not in unique_values:
                unique_values[heading] = fare_rule_data
        fare_rule_data_list = list(unique_values.values())
        return fare_rule_data_list
    except Exception as e:
        logger.error(f"Error while formatting fare rule data : {e}. Traceback : {traceback.format_exc()}")
        return fare_rule_data_list


def send_reschedule_email(content_type, modification_request_id, content_passed=False, content="", addon_payload={}):
    try:
        logger.info(
            "------------reschedule email------ content_type %s modification_request_id %s "
            "flight reschedule request id %s content_passed %s content %s addon_payload %s------",
            content_type,
            modification_request_id,
            content_passed,
            content,
            addon_payload,
        )
        WEB_URL = os.getenv("WEB_URL")
        MIS_KEY = os.getenv("MIS_KEY")
        url = f"{WEB_URL}/traveldesk-mail"
        payload_data = {
            "mis_key": MIS_KEY,
            "email_type": "flight-reschedule",
            "content_type": content_type,  # reschedule-created reschedule-completed reschedule-failure
            "content_passed": content_passed,
            "content": content,
            "modification_request_id": modification_request_id,
        }
        payload_data.update(addon_payload)
        payload = json_util.dumps(payload_data)
        response = requests.request("POST", url, data=payload)
        logger.info(
            "-------email response for email type flight-reschedule and modification_request_id %s-------%s",
            modification_request_id,
            response,
        )
        try:
            email_response = json.loads(response.text)
        except Exception as ex:
            email_response = {"status": False, "message": response.text, "error": str(ex)}
            logger.error(f"Error while mail sent reschedule " f"response {str(ex)} = traceback = {traceback.format_exc()}")
        # email_details = {
        #     "email_type": f"{email_type} {content_type} email",
        #     "email_status": email_response,
        #     "email_triggered_time_type": f"{email_type} {content_type} email triggered at",
        # }
        # update_email_status(cancellation_request_id, email_details)
        logger.info(
            "-------email response for email type flight-reschedule and modification_request_id %s-------%s",
            modification_request_id,
            response,
        )
        logger.info(
            "-------email response json for email type flight-reschedule and modification_request_id %s -------%s",
            modification_request_id,
            email_response,
        )
        return email_response
    except Exception as ex:
        email_response = {"status": False, "message": str(ex)}
        logger.error(
            "---------ERROR in send_reschedule_email %s------%s",
            modification_request_id,
            ex,
            exc_info=True,
        )
        return email_response


def get_payment_config_details(entity_details, client_id, is_personal_booking, auth_token, webhook_token=None):
    try:
        logger.info(
            "----------get_payment_config_details-------%s,%s,%s",
            entity_details,
            client_id,
            is_personal_booking,
        )
        payment_base_url = os.getenv("PAYMENT_URL")
        auth_headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Authorization": auth_token,
            "cache-control": "no-cache",
        }
        if webhook_token:
            auth_headers["Webhooktoken"] = webhook_token
        response = {"status": False}
        url = f"{payment_base_url}/api/v1/payment/{client_id}/{entity_details['id']}/{is_personal_booking}/1"
        logger.info(
            "--payment config request client_id %s entity_details, %s, is_personal_booking"
            " %s--url %s, auth headers %s, auth token %s",
            client_id,
            entity_details,
            is_personal_booking,
            url,
            auth_headers,
            auth_token,
        )
        payment_response = requests.get(url, headers=auth_headers)
        logger.info(
            "---------payment response for client %s-------%s",
            client_id,
            payment_response,
        )
        if payment_response and payment_response.status_code == 200:
            payment_response = json.loads(payment_response.text)
            logger.info(
                "---------payment response json for client %s-------%s",
                client_id,
                payment_response,
            )
            if payment_response["status"]:
                response = {
                    "status": True,
                    "result": {
                        "payment_gateway_config": payment_response["result"][0],
                        "client_pay_at_vendor_config": payment_response.get("client_pay_at_vendor_config", []),
                        "pay_at_vendor_config": payment_response["result"][-1],
                    },
                }
        return response
    except Exception as ex:
        logger.error(
            "------ERROR in get_pg_charge_details %s------%s",
            client_id,
            ex,
            exc_info=True,
        )
        message = f"ERROR in get_pg_charge_details for client {client_id}-----{ex, traceback.format_exc()}"
        send_bot_message(message)
        response = {"status": False, "message": str(ex)}
        return response


def parse_duration(iso_duration):
    # Extract hours, minutes, and seconds from the ISO 8601 duration
    pattern = r"P(?:\d+D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, iso_duration)

    if not match:
        raise ValueError("Invalid duration format")

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    total_hours = hours + minutes / 60 + seconds / 3600
    total_seconds = total_hours * 3600

    if total_hours >= 24:
        tm, u, ts = total_hours / 24, "days", total_seconds
    else:
        tm, u, ts = total_hours, "hours", total_seconds

    return tm, u, ts


def frame_sfr_path(penalty_ids):
    if penalty_ids:
        return "-".join(sorted(set(penalty_ids)))
    return None


def fetch_cleartrip_inclusions(baggageAllowances, benefits, penalties, fare_details):
    try:
        template = {
            "desc": None,
            "inc": None,
            "value": None,
            "unit": None,
        }
        result = {key: copy.deepcopy(template) for key in ["cbg", "crn", "rbk", "rfn", "mls", "st", "wf"]}

        baggage_allowances = []
        baggage_id = None

        if "flightBenefits" in fare_details:
            bi = list(fare_details["flightBenefits"].values())
            if bi:
                baggage_id = bi[0]["baggageAllowances"]
        else:
            baggage_id = fare_details["subTravelOptionFare"][0]["flightFare"][0]["baggageAllowances"]

        if baggage_id:
            baggage_allowances = baggageAllowances.get(baggage_id[0]["baggageAllowanceId"], [])

        for ba in baggage_allowances:
            ba_type = "crn" if ba["type"] == "BAGGAGE_CABIN" else "cbg" if ba["type"] == "BAGGAGE_CHECK_IN" else None
            if ba_type:
                for allowed_baggage in ba["allowedBaggages"]:
                    # search call we get 1 value, in preview call we get multiple values so picking min for crn and max for cbg
                    if result[ba_type]["value"]:
                        if (ba_type == "crn" and allowed_baggage.get("quantity") < result[ba_type]["value"]) or (
                            ba_type == "cbg" and allowed_baggage.get("quantity") > result[ba_type]["value"]
                        ):
                            result[ba_type]["value"] = allowed_baggage.get("quantity")
                    else:
                        result[ba_type]["value"] = allowed_baggage.get("quantity")
                    result[ba_type]["unit"] = (
                        "Kilograms" if allowed_baggage.get("unit").lower() == "kg" else allowed_baggage.get("unit")
                    )
                    result[ba_type]["inc"] = 1
                    if result[ba_type]["value"] and result[ba_type]["unit"]:
                        result[ba_type]["desc"] = f'{result[ba_type]["value"]} {result[ba_type]["unit"]}'

        for bi in fare_details.get("benefitIds", []):
            benefit = benefits.get(bi, {})
            ba_type = {"MEAL": "mls", "SEAT": "st"}.get(benefit.get("benefitType"))

            if ba_type:
                result[ba_type]["value"] = benefit.get("amount")
                result[ba_type]["unit"] = benefit.get("currency")
                result[ba_type]["desc"] = "Chargeable" if benefit.get("value") == "PAID" else "Included"
                result[ba_type]["inc"] = 2 if benefit.get("value") == "PAID" else 1

        for pi in fare_details.get("penaltyIds", []):
            penalty = penalties.get(pi, {})
            ba_type = (
                "rfn"
                if penalty.get("penaltyType") == "CANCEL"
                else "rbk"
                if penalty.get("penaltyType") in ["AMEND_SAME_FARE", "AMEND_HIGHER_FARE", "AMENDMENT"]
                else None
            )

            if ba_type:
                result[ba_type]["value"] = result[ba_type]["value"] or None
                result[ba_type]["unit"] = "INR"

                for timeline in penalty.get("timeLines", []):
                    if timeline["permitted"]:
                        result[ba_type]["inc"] = 2

                        if (
                            not result[ba_type]["value"]
                            or timeline["passengerFareRuleCharges"]["ADT"]["charges"][0]["amount"] < result[ba_type]["value"]
                        ):
                            result[ba_type]["value"] = timeline["passengerFareRuleCharges"]["ADT"]["charges"][0]["amount"]

                        result[ba_type]["unit"] = timeline["passengerFareRuleCharges"]["ADT"]["charges"][0]["currency"]

        return result

    except KeyError as ex:
        logger.error(f"Error in fetch_cleartrip_inclusions KeyError : {ex}  =====> {traceback.format_exc()}")
        return {}
    except Exception as ex:
        logger.error(f"Error in fetch_cleartrip_inclusions : {ex}  =====> {traceback.format_exc()}")
        return {}


def fetch_cleartrip_static_fare_rules(
    penalties,
    fares_available,
    travel_options,
    sub_travel_options,
    flight_data,
    fareAssociations,
    restricted_airlines,
    default_fare=False,
    cabin_class=None,
):
    cleartrip_fare_rules = {}
    try:
        for index, each_travel_option in travel_options.items():
            for each_flight_itinerary in each_travel_option:
                if default_fare:
                    if each_flight_itinerary["defaultFare"] is None:
                        continue
                    fare_availability = [each_flight_itinerary["defaultFare"]["associations"][0]["fareId"]]
                else:
                    fare_availability = fareAssociations[
                        sub_travel_options[each_flight_itinerary["subTravelOptionIds"][0]]["fareAssocId"]
                    ]["fareIds"]
                all_segments = sub_travel_options[each_flight_itinerary["subTravelOptionIds"][0]]["sequenceToFlightIdMap"]
                if (
                    restricted_airlines
                    and all_segments.get("1")
                    and is_itinerary_restricted(flight_data[all_segments.get("1")]["airlineCode"], restricted_airlines, cabin_class)
                ):
                    continue
                for fa in fare_availability:
                    fare_availability_key = fa
                    static_fare_rule_path = None
                    if fare_availability_key in fares_available:
                        fare_details = fares_available[fare_availability_key]
                        static_fare_rule_path = frame_sfr_path(fare_details.get("penaltyIds", []))
                        fare_rules = {}
                        fare_rules_data = []
                        for pi in fare_details.get("penaltyIds", []):
                            penalty = penalties.get(pi, {})
                            ba_type = (
                                "rfn"
                                if penalty.get("penaltyType") == "CANCEL"
                                else "rbk"
                                if penalty.get("penaltyType") in ["AMEND_SAME_FARE", "AMEND_HIGHER_FARE", "AMENDMENT"]
                                else None
                            )

                            if ba_type:
                                for timeline in penalty.get("timeLines", []):
                                    if timeline["permitted"]:
                                        start_time, start_unit, sts = parse_duration(timeline["startTime"])
                                        end_time, end_unit, ets = parse_duration(timeline["endTime"])
                                        time_desc = (
                                            f"Between {int(start_time)}-{int(end_time)} {start_unit}"
                                            if start_unit == end_unit
                                            else f"Between {int(start_time)} {start_unit}-{int(end_time)} {end_unit}"
                                        ) + " before departure"

                                        fare_rules.setdefault(time_desc, {})
                                        fare_rules[time_desc][
                                            ba_type
                                        ] = f'INR {int(timeline["passengerFareRuleCharges"]["ADT"]["charges"][0]["amount"])}'

                                        fare_rules[time_desc]["start"] = sts

                                        fare_rules[time_desc]["end"] = ets

                                        fare_rules[time_desc]["start_time_secs"] = sts
                            sorted_fare_rules = OrderedDict(
                                sorted(fare_rules.items(), key=lambda x: x[1].get("start_time_secs", float("inf")))
                            )

                            fare_rules_data = [
                                {
                                    "schedules": time,
                                    "cancelation_fees": fees.get("rfn", "-"),
                                    "reschedule_fees": fees.get("rbk", "-"),
                                    "start_time_in_secs": fees.get("start", "-"),
                                    "end_time_in_secs": fees.get("end", "-"),
                                }
                                for time, fees in sorted_fare_rules.items()
                            ]

                    if static_fare_rule_path and fare_rules_data:
                        cleartrip_fare_rules[static_fare_rule_path] = fare_rules_data
        return cleartrip_fare_rules
    except KeyError as ex:
        logger.error(f"Error in fetch_cleartrip_static_fare_rules KeyError : {ex}  =====> {traceback.format_exc()}")
        return cleartrip_fare_rules
    except Exception as ex:
        logger.error(f"Error in fetch_cleartrip_static_fare_rules : {ex}  =====> {traceback.format_exc()}")
        return cleartrip_fare_rules


def is_time_difference_valid(onward_flight, return_flight):
    onward_fgt = onward_flight["leg"][0]["fgt"]
    onward_adt = datetime.strptime(onward_flight["leg"][0]["fgt"][len(onward_fgt) - 1]["adt"], DATE_TIME_FORMAT)
    return_ddt = datetime.strptime(return_flight["leg"][0]["fgt"][0]["ddt"], DATE_TIME_FORMAT)
    time_difference = return_ddt - onward_adt
    if time_difference.total_seconds() <= 90 * 60:  # 90 minutes in seconds
        return False
    return True


def handle_cbg_crn(o, r, onward_bd, oi):
    """
    Logic implemented:
    If any one has Information not available:
        Information not available shown
    Else:
        If both flights' cbg and crn matches we return True, else False.

    """
    if o["inc"] is None or r["inc"] is None:
        if r["inc"] is None:
            onward_bd[oi] = r
    else:
        if o["desc"] != r["desc"] or o["inc"] != r["inc"] or o["val"] != r["val"]:
            return False
    return True


def handle_mls_st_y5(o, r, onward_bd, oi):
    """
    Inclusion values:
    ________________________________________
    | 0     -   Not available              |
    | 1     -   Included                   |
    | 2     -   Available for a fee        |
    | None  -   Information not available  |
    |______________________________________|

    Logic implemented:
    1. both same inc values ---> same value taken
    2. any one has Information not available ---> Information not available shown
    3. any one Not available ---> Not available shown
    4. any one Available for a fee ---> Available for a fee shown

    """
    if o["inc"] is None or r["inc"] is None:
        if r["inc"] is None:
            onward_bd[oi] = r
    elif o["inc"] != r["inc"]:
        if o["inc"] == 0 or r["inc"] == 0:
            if r["inc"] == 0:
                onward_bd[oi] = r
        elif o["inc"] == 2 or r["inc"] == 2:
            if r["inc"] == 2:
                onward_bd[oi] = r

    return True


def handle_rfn_rbk(o, r, onward_bd, oi):
    """
    Logic implemented:
    1. any one has Information not available ---> Information not available shown
    2. If both are same then we sum up the onward and return flight cancellation and reschedule fee

    """
    if o["inc"] is None or r["inc"] is None:
        if r["inc"] is None:
            onward_bd[oi] = r
    elif o["inc"] == r["inc"]:
        if o["val"] and r["val"]:
            q = float(o["val"]) + float(r["val"])
            onward_bd[oi] = {"typ": o["typ"], "desc": None, "inc": o["inc"], "val": q, "add_ons": []}
    else:
        return False

    return True


def inclusions_matching(onward_bd1, return_bd):
    """
    We combine if airline code, cabin class, brand name matches.

    Parameters:
        onward_bd1 (list): List of onward inclusions.
        return_bd (list): List of return inclusions.

    Returns:
        tuple: A tuple containing a boolean indicating success and the modified onward_bd.
    """
    onward_bd = copy.deepcopy(onward_bd1)

    try:
        for oi, o in enumerate(onward_bd):
            for ri, r in enumerate(return_bd):
                if o["typ"] != r["typ"]:
                    continue

                if o["typ"] in ["cbg", "crn"]:
                    if not handle_cbg_crn(o, r, onward_bd, oi):
                        return False, []

                elif o["typ"] in ["mls", "st", "y5"]:
                    if not handle_mls_st_y5(o, r, onward_bd, oi):
                        return False, []

                elif o["typ"] in ["rfn", "rbk"]:
                    if not handle_rfn_rbk(o, r, onward_bd, oi):
                        return False, []

                break

        return True, onward_bd

    except Exception as ex:
        logger.error(f"Exception occurred in inclusions_matching function: {ex}")
        return False, []


def create_cleartrip_sector(index, origin, destination, depart_date, cabin_class, passenger_info):
    return {
        "index": index,
        "origin": origin,
        "destination": destination,
        "departDate": depart_date,
        "cabinType": cabin_class,
        "paxInfos": passenger_info,
    }


def format_date(date_str, date_format, expected_format):
    try:
        return datetime.strptime(date_str, date_format).strftime(expected_format)
    except ValueError as e:
        logger.error(f"Date formatting error: {e} for date {date_str} with format {date_format}")
        raise e


def get_fare_wrapper_list(fre_config):
    v2_wrapper = getattr(fre_config, "v2_wrapper", None) if not isinstance(fre_config, dict) else fre_config.get("v2_wrapper")
    return v2_wrapper.split(",") if v2_wrapper else []


def build_passenger_info(trip_info):
    key_names = {"Adult": "ADT", "Child": "CHD", "Infant": "INF"}
    return [
        {"paxType": key_names[key], "paxCount": value, "paxFareType": "DEFAULT"}
        for key, value in sorted(trip_info.items())
        if value > 0
    ]


def process_fare_rule(fare_rule):
    return [
        (
            entry["start_time_in_secs"],
            entry["end_time_in_secs"],
            float(entry["cancelation_fees"].split(" ")[1])
            if len(entry["cancelation_fees"].split(" ")) > 1
            else entry["cancelation_fees"],
            float(entry["reschedule_fees"].split(" ")[1])
            if len(entry["reschedule_fees"].split(" ")) > 1
            else entry["reschedule_fees"],
            entry["schedules"],
        )
        for entry in fare_rule
    ]


def process_schedules(fr1, fr2):
    """
    Process fare rules and create a mapping of schedules.
    """
    aa = process_fare_rule(fr1)
    bb = process_fare_rule(fr2)

    asch = {f"{entry['start_time_in_secs']}-{entry['end_time_in_secs']}": entry["schedules"] for entry in fr1}
    bsch = {f"{entry['start_time_in_secs']}-{entry['end_time_in_secs']}": entry["schedules"] for entry in fr2}
    asch.update(bsch)

    return aa + bb, asch


def calculate_endpoints(ranges):
    """
    Calculate unique endpoints from the given ranges.
    """
    endpoints = sorted(list(set([r[0] for r in ranges] + [r[1] for r in ranges])))
    return endpoints


def calculate_time(total_seconds: int) -> Tuple[int, str]:
    delta = timedelta(seconds=total_seconds)
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)

    if days > 0:
        return days, "day" if days == 1 else "days"
    elif hours > 0:
        return hours, "hour" if hours == 1 else "hours"
    else:
        minutes = delta.seconds // 60
        return minutes, "minute" if minutes == 1 else "minutes"  # Default to "minutes" for durations under an hour


def calculate_fees_sum(current_fees, fee_type):
    total_sum = 0

    for f in current_fees.values():
        if f[fee_type] == "-":
            continue
        total_sum += f[fee_type]

    if all(f[fee_type] == "-" for f in current_fees.values()):
        return "-"
    else:
        return f"INR {int(total_sum)}"


def accumulate_current_fees(start, end, endpoints, sch):
    """
    Accumulate the current fees based on start and end data.
    """
    current_fees = {}
    output = []

    for e1, e2 in zip(endpoints[:-1], endpoints[1:]):
        for cancel_fee, reschedule_fee, schedule in end[e1]:
            if schedule in current_fees:
                if cancel_fee != "-" and current_fees[schedule]["cancelation_fees"] != "-":
                    current_fees[schedule]["cancelation_fees"] -= cancel_fee
                if reschedule_fee != "-" and current_fees[schedule]["reschedule_fees"] != "-":
                    current_fees[schedule]["reschedule_fees"] -= reschedule_fee
                if current_fees[schedule]["cancelation_fees"] == 0 and current_fees[schedule]["reschedule_fees"] == 0:
                    del current_fees[schedule]

        for cancel_fee, reschedule_fee, schedule in start[e1]:
            if schedule in current_fees:
                if cancel_fee != "-" and current_fees[schedule]["cancelation_fees"] != "-":
                    current_fees[schedule]["cancelation_fees"] += cancel_fee
                if reschedule_fee != "-" and current_fees[schedule]["reschedule_fees"] != "-":
                    current_fees[schedule]["reschedule_fees"] += reschedule_fee
            else:
                current_fees[schedule] = {"cancelation_fees": cancel_fee, "reschedule_fees": reschedule_fee}

        if current_fees:  # Only output active schedules
            cancel_sum = calculate_fees_sum(current_fees, "cancelation_fees")
            reschedule_sum = calculate_fees_sum(current_fees, "reschedule_fees")

            key = f"{e1}-{e2}"
            if sch.get(key):
                schedules = sch[key]
            else:
                start_time, start_unit = calculate_time(e1)
                end_time, end_unit = calculate_time(e2)
                if start_unit == end_unit:
                    time_desc = f"Between {int(start_time)}-{int(end_time)} {start_unit} before departure"
                else:
                    time_desc = f"Between {int(start_time)} {start_unit}-{int(end_time)} {end_unit} before departure"
                schedules = time_desc

            output.append(
                {
                    "schedules": schedules,
                    "cancelation_fees": cancel_sum,
                    "reschedule_fees": reschedule_sum,
                    "start_time_in_secs": e1,
                    "end_time_in_secs": e2,
                }
            )

    return output


def process_via_flights(via_flight_details):
    via_list = []

    for detail in via_flight_details:
        current_flight_adt = detail["arrivalTime"]
        next_flight_ddt = detail["departTime"]
        via_duration = calculate_flight_travel_time(current_flight_adt, next_flight_ddt)
        via_list.append({"airport": detail["airportCode"], "duration": via_duration})

    return via_list


def calculate_layover_time(previous_segment_adt, current_segment_ddt):
    return datetime.strptime(current_segment_ddt, DATE_TIME_FORMAT) - datetime.strptime(previous_segment_adt, DATE_TIME_FORMAT)


def calculate_fare(currency_details, vendor_total_price, vendor_base_price, vendor_tax):
    return {
        "total_price": currency_conversion(currency_details.rate, vendor_total_price),
        "base_price": currency_conversion(currency_details.rate, vendor_base_price),
        "tax": currency_conversion(currency_details.rate, vendor_tax),
        "currency": currency_details.type,
    }


def create_flight_preview_data(search_id, data_id, sectors, travel_options):
    return {
        "searchId": search_id,
        "dataId": data_id,
        "flightPreviewCriteria": {
            "isMultiFareRequest": True,
            # "maxFareCount": 0,  # Uncomment if needed
            "sellingCountryCode": "IN",
            "sellingCurrencyCode": "INR",
        },
        "searchIntents": {"sectors": sectors},
        "travelOptions": travel_options,
    }


def frame_cleartrip_travel_options(result_index):
    return {
        "subTravelOptions": [{"subTravelOptionId": result_index[2], "fareId": result_index[3]}],
        "travelOptionId": result_index[2],
        "price": result_index[4],
    }


def merge_fares(onward_fl, return_fl, vtp, compare_fare_dict, bd, sfr=None, flag=False):
    """
    Merges fare details from onward and return flights.
    """
    merged_fare = {
        "vtp": vtp,
        "vbp": onward_fl["vbp"] + return_fl["vbp"],
        "vc": onward_fl["vc"],
        "vt": onward_fl["vt"] + return_fl["vt"],
        "pc": onward_fl["pc"],
        "pcn": onward_fl["pcn"],
        "api": onward_fl["api"],
        "pfb": [
            {
                "pax": onward_pfb["pax"],
                "fb": onward_pfb["fb"] + return_fl["pfb"][0]["fb"],
                "vtp": vtp,
                "vbp": onward_fl["vbp"] + return_fl["vbp"],
                "vc": onward_fl["vc"],
                "vt": onward_fl["vt"] + return_fl["vt"],
            }
            for onward_pfb in onward_fl["pfb"]
        ],
        "rp": onward_fl["rp"] + return_fl["rp"],
        "cp": onward_fl["cp"] + return_fl["cp"],
        "fs": onward_fl["fs"].upper(),
        "cfv": compare_fare_dict["compare_fare"],
        "cfp": compare_fare_dict["compare_fare_priority"],
        "cvwdm_id": onward_fl["cvwdm_id"],
        "cnp": onward_fl["cnp"],
        "bn": onward_fl["bn"],
        "scc": onward_fl["scc"],
        "bid": onward_fl["bid"],
        "cc": onward_fl["cc"],
        "bd": bd,
        "md": {"type": "ref", "path": ""},
        "sid": onward_fl["sid"],
        "rs": onward_fl["rs"] + return_fl["rs"],
        "bg": onward_fl["bg"] + return_fl["bg"],
        "fid": onward_fl["fid"],
        "ppn_bid": onward_fl["ppn_bid"],
        "df": onward_fl["df"],
        "tf": {
            "tp": onward_fl["tf"]["tp"] + return_fl["tf"]["tp"],
            "bp": onward_fl["tf"]["bp"] + return_fl["tf"]["bp"],
            "cur": onward_fl["tf"]["cur"],
            "tax": onward_fl["tf"]["tax"] + return_fl["tf"]["tax"],
            "reward": 0,
        },
        "itf": {
            "tp": onward_fl["itf"]["tp"] + return_fl["itf"]["tp"],
            "bp": onward_fl["itf"]["bp"] + return_fl["itf"]["bp"],
            "cur": onward_fl["itf"]["cur"],
            "tax": onward_fl["itf"]["tax"] + return_fl["itf"]["tax"],
        },
        "vf": {
            "tp": onward_fl["vf"]["tp"] + return_fl["vf"]["tp"],
            "bp": onward_fl["vf"]["bp"] + return_fl["vf"]["bp"],
            "cur": onward_fl["vf"]["cur"],
            "tax": onward_fl["vf"]["tax"] + return_fl["vf"]["tax"],
        },
        "cf": {
            "tp": onward_fl["cf"]["tp"] + return_fl["cf"]["tp"],
            "bp": onward_fl["cf"]["bp"] + return_fl["cf"]["bp"],
            "cur": onward_fl["cf"]["cur"],
            "tax": onward_fl["cf"]["tax"] + return_fl["cf"]["tax"],
            "reward": 0,
        },
        "bnh": onward_fl["bnh"],
        "afcr": onward_fl["afcr"],
        "obn": onward_fl["obn"],
    }

    if flag:
        merged_fare["ac"] = onward_fl["ac"]
        merged_fare["ssr"] = onward_fl["ssr"]
        merged_fare["frl"] = onward_fl["frl"]
        merged_fare["sfr"] = {"type": "tbl", "path": sfr}

    return merged_fare


def extract_currency_details(fre_config):
    return fre_config.staff_currency, fre_config.client_currency, fre_config.itilite_currency, fre_config.vendor_currency


def create_static_fare_rule(static_fare_rule_path):
    static_fare_rule = StaticFareRule()
    if static_fare_rule_path:
        static_fare_rule.type = "tbl"
        static_fare_rule.path = static_fare_rule_path
    return static_fare_rule


def frame_baggage_details(inclusions):
    return Baggage(
        checkin_baggage=inclusions.get("cbg", {}).get("value"),
        checkin_baggage_unit=inclusions.get("cbg", {}).get("unit"),
        hand_baggage=inclusions.get("crn", {}).get("value"),
        hand_baggage_unit=inclusions.get("crn", {}).get("unit"),
    )


def frame_detail_baggage(inclusions, origin, destination):
    return DetailBaggage(
        hand_baggage=inclusions.get("crn", {}).get("value"),
        hand_baggage_unit=inclusions.get("crn", {}).get("unit"),
        checkin_baggage=inclusions.get("cbg", {}).get("value"),
        checkin_baggage_unit=inclusions.get("cbg", {}).get("unit"),
        origin=origin,
        destination=destination,
    )


def get_brand_desc(inclusions, inclusion_types, sfr=None):
    brand_desc = []

    for type_of_inclusion in inclusion_types:
        inclusion_data = inclusions.get(type_of_inclusion, {})
        brand_desc.append(
            BrandDesc(
                type_of_inclusion=type_of_inclusion,
                inclusion_value=(1 if type_of_inclusion == "fr" else 3 if type_of_inclusion == "y5" else inclusion_data.get("inc")),
                description=sfr if type_of_inclusion == "fr" else inclusion_data.get("desc"),
                value=inclusion_data.get("desc") if type_of_inclusion in {"crn", "cbg"} else inclusion_data.get("value"),
            )
        )
    return brand_desc


def calculate_pax_breakup(paxwise_amt_breakup, vendor_currency, cancellation_policy_first, reschedule_policy_first):
    pax_fare_breakup = []
    for ind, val in paxwise_amt_breakup.items():
        pax_fare_breakup.append(
            PaxFareBreakup(
                pax_type=ind,
                fare_breakup=[val["fb"]],
                vendor_total_price=val["vtp"],
                vendor_base_price=val["vbp"],
                vendor_currency=vendor_currency,
                vendor_tax=val["vt"],
                cancellation_policy=cancellation_policy_first,
                reschedule_policy=reschedule_policy_first,
            )
        )

    return pax_fare_breakup


def frame_desiya_room_stay(no_of_rooms: int, no_of_adults: int, no_of_children: int, child_dob: Optional[List[str]] = None) -> str:
    """
    Frames the room stay details for Desiya.

    Args:
        no_of_rooms (int): The number of rooms.
        no_of_adults (int): The number of adults.
        no_of_children (int): The number of children.
        child_dob (Optional[List[str]]): List of children's dates of birth.

    Returns:
        str: The constructed query string with room stay details.
    """
    # Calculate child ages or default to 10
    child_age = [age_calculator(dob) for dob in child_dob] if child_dob else [10] * no_of_children

    # Initialize room parameters
    params = {"rooms": []}

    # If there's only one room, assign all adults and children to it
    if no_of_rooms == 1:
        room = {"noOfAdults": no_of_adults, "noOfChildren": no_of_children}
        if no_of_children:
            room["childrenAge"] = child_age
        params["rooms"].append(room)
    else:
        # Distribute adults and children across rooms
        adults_per_room, extra_adults = divmod(no_of_adults, no_of_rooms)
        children_per_room, extra_children = divmod(no_of_children, no_of_rooms)

        for i in range(no_of_rooms):
            room = {
                "noOfAdults": adults_per_room + (1 if i < extra_adults else 0),
                "noOfChildren": children_per_room + (1 if i < extra_children else 0),
            }
            if room["noOfChildren"] > 0:
                room["childrenAge"] = [child_age.pop(0) for _ in range(room["noOfChildren"])]
            params["rooms"].append(room)

    # Construct query string
    output = "&".join(
        f"rooms[{i}].noOfAdults={room['noOfAdults']}&rooms[{i}].noOfChildren={room['noOfChildren']}"
        + "".join(f"&rooms[{i}].childrenAge[{j}]={age}" for j, age in enumerate(room.get("childrenAge", [])))
        for i, room in enumerate(params["rooms"])
    )
    return output


def time_conversion_with_dynamic_format(ci: str, date_format: str) -> str:
    """
    Converts a date string to the format "%Y-%m-%d".

    Args:
        ci (str): The date string to convert.
        date_format (str): The format of the input date string.

    Returns:
        str: The converted date string in the format "%Y-%m-%d".
    """
    return datetime.strptime(ci, date_format).date().strftime("%Y-%m-%d")


def get_days_difference(checkout: str, checkin: str) -> int:
    """
    Calculates the difference in days between check-in and check-out dates.

    Args:
        checkout (str): The check-out date.
        checkin (str): The check-in date.

    Returns:
        int: The difference in days between check-in and check-out dates.
    """
    try:
        a = datetime.strptime(checkin, HOTEL_REQUEST_DATE_FORMAT)
        b = datetime.strptime(checkout, HOTEL_REQUEST_DATE_FORMAT)
        delta = b - a
        logger.info(f"output of get_days_difference : {delta}")
        return delta.days
    except Exception:
        logger.error(f"Error in checkin checkout days difference: {traceback.format_exc()}")


def age_calculator(dob: str) -> int:
    """
    Calculates the age based on the date of birth.

    Args:
        dob (str): The date of birth in the format "%Y-%m-%d".

    Returns:
        int: The calculated age.
    """
    pax_dob = datetime.strptime(dob, "%Y-%m-%d")
    today = date.today()
    age = today.year - pax_dob.year - ((today.month, today.day) < (pax_dob.month, pax_dob.day))
    return age


def remove_html_tags(text: str) -> str:
    """
    Removes HTML tags from a string.

    Args:
        text (str): The input string containing HTML tags.

    Returns:
        str: The string with HTML tags removed.
    """
    decoded_text = html.unescape(text)
    clean = re.compile("<.*?>")
    return re.sub(clean, "", decoded_text)


def deduplicate_amenities(amenities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates a list of amenities based on their ID and name.

    Args:
        amenities (List[Dict[str, Any]]): The list of amenities.

    Returns:
        List[Dict[str, Any]]: The deduplicated list of amenities.
    """
    # Create a set to track unique amenities by normalized id and name
    seen = set()
    deduplicated_amenities = []

    for amenity in amenities:
        # Normalize the 'id' to string for comparison
        normalized_id = str(amenity["id"])  # Ensure both are strings for comparison
        amenity_tuple = (normalized_id, amenity["name"])

        if amenity_tuple not in seen:
            deduplicated_amenities.append(amenity)
            seen.add(amenity_tuple)

    return deduplicated_amenities


def fetch_hotel_cities(mongo_obj: Any, vendor: str, city: str) -> List[str]:
    """
    Fetches hotel cities from the MongoDB collection.

    Args:
        mongo_obj (Any): The MongoDB connection object.
        vendor (str): The vendor name.
        city (str): The city name.

    Returns:
        List[str]: A list of matching city names.
    """
    try:
        mongo_db_name = StaticDBConstants.STATIC_DB
        collection_name = StaticDBConstants.HOTEL_CITIES
        query = {"vendor": vendor, "cities": {"$regex": f"^{city}$", "$options": "i"}}

        mongo_res = mongo_obj.find_one(mongo_db_name, collection_name, query)

        if mongo_res:
            return [city]

    except Exception as e:
        logger.error(f"Error in fetch_hotel_cities: {e}")

    return []


def is_itinerary_restricted(airline_code: str, restricted_airlines: List[str], cabin_class: str) -> bool:
    """
    Checks if a flight segment is restricted based on airline code and cabin type.

    Args:
        airline_code (str): The airline code of the flight segment.
        restricted_airlines (List[str]): List of restricted airline codes.
        cabin_class (str): The cabin class of the flight segment (e.g., "economy", "business").

    Returns:
        bool: True if the itinerary is restricted, False otherwise.
    """
    if not restricted_airlines:
        return False

    # Check if the airline is restricted
    if airline_code in restricted_airlines:
        flight_constants = FlightConstants()
        # Allow if the airline has an exception for the given cabin class
        if (
            airline_code in flight_constants.AIRLINE_CLASSES
            and cabin_class.lower() in flight_constants.AIRLINE_CLASSES[airline_code]
        ):
            return False
        return True  # Restrict other cases

    return False  # Not restricted


def should_use_hardcoded_fare_rule(cabin_class: str, platting_carrier: str, brand_name_mapping: Dict[str, Any]) -> bool:
    """
    Determines if hardcoded fare rules should be used based on cabin class and brand name mapping.

    Args:
        cabin_class (str): The cabin class of the flight segment.
        platting_carrier (str): The airline code of the platting carrier.
        brand_name_mapping (Dict[str, Any]): The brand name mapping data.

    Returns:
        bool: True if hardcoded fare rules should be used, False otherwise.
    """
    if not brand_name_mapping:
        return False

    airlines = FlightConstants().AIRLINE_CLASSES.get(platting_carrier)
    if not airlines:
        return False

    return cabin_class.lower() in airlines


def get_baggage_info(travel_type: str, brand_name_mapping: Dict[str, Any]) -> Dict[str, Optional[Any]]:
    """
    Retrieves baggage information based on travel type and brand name mapping.

    Args:
        travel_type (str): The type of travel (e.g., "international", "domestic").
        brand_name_mapping (Dict[str, Any]): The brand name mapping data.

    Returns:
        Dict[str, Optional[Any]]: A dictionary containing baggage information.
    """
    baggage_type = "int_value" if travel_type == "international" else "dom_value"
    baggage_unit_type = "int_value_unit" if travel_type == "international" else "dom_value_unit"
    checkin_baggage, checkin_baggage_unit, carry_on_baggage, carry_on_baggage_unit = None, None, None, None
    checkin_baggage = brand_name_mapping.get("check_in_baggage", {}).get(baggage_type)
    checkin_baggage_unit = brand_name_mapping.get("check_in_baggage", {}).get(baggage_unit_type)
    carry_on_baggage = brand_name_mapping.get("hand_baggage", {}).get(baggage_type)
    carry_on_baggage_unit = brand_name_mapping.get("hand_baggage", {}).get(baggage_unit_type)
    data = {
        "checkin_baggage": checkin_baggage,
        "checkin_baggage_unit": checkin_baggage_unit,
        "carry_on_baggage": carry_on_baggage,
        "carry_on_baggage_unit": carry_on_baggage_unit,
    }
    return data


def get_change_cancel_data_cleartrip(
    reschedule_cancellation: List[Dict[str, Any]],
    vendor_price: Decimal,
    vendor_currency: str,
    travel_type: str,
    fre_config: Any,
    refund_min_amt: Optional[Decimal],
) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Retrieves change and cancellation data for Cleartrip.

    Args:
        reschedule_cancellation (List[Dict[str, Any]]): List of reschedule and cancellation data.
        vendor_price (Decimal): The vendor price.
        vendor_currency (str): The vendor currency.
        travel_type (str): The type of travel (e.g., "international", "domestic").
        fre_config (Any): The FRE configuration.
        refund_min_amt (Optional[Decimal]): The minimum refund amount.

    Returns:
        Tuple[Optional[str], Optional[int], Optional[str]]: A tuple containing description, inclusion value, and value.
    """
    try:
        min_amount = []
        min_amount_final = []
        desc = "anytime"
        inc_val = None
        value = None

        if reschedule_cancellation:
            for changes_refund in reschedule_cancellation:
                desc = changes_refund.get("desc")
                amount = changes_refund.get("int_value") if travel_type == "international" else changes_refund.get("dom_value")
                handle_amounts(amount, min_amount, min_amount_final)

        desc, inc_val, value = process_final_amounts(min_amount, min_amount_final, refund_min_amt, fre_config, vendor_currency)

        return desc, inc_val, value

    except Exception as e:
        logger.error(f"Error while transforming cancellation data: {e}")
        return None, None, None


def handle_amounts(amount: str, min_amount: List[Decimal], min_amount_final: List[str]) -> None:
    """
    Handles the amounts for change and cancellation data.

    Args:
        amount (str): The amount as a string.
        min_amount (List[Decimal]): List to store minimum amounts.
        min_amount_final (List[str]): List to store final amounts.

    Returns:
        None
    """
    if amount.lower() in ["nil", "free", ""]:
        min_amount_final.append(amount)
    else:
        value = Decimal(amount) if amount != "" else 0
        # if value > 0.0:
        min_amount.append(value)


def process_final_amounts(
    min_amount: List[Decimal], min_amount_final: List[str], refund_min_amt: Optional[Decimal], fre_config: Any, vendor_currency: str
) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Processes the final amounts for change and cancellation data.

    Args:
        min_amount (List[Decimal]): List of minimum amounts.
        min_amount_final (List[str]): List of final amounts.
        refund_min_amt (Optional[Decimal]): The minimum refund amount.
        fre_config (Any): The FRE configuration.
        vendor_currency (str): The vendor currency.

    Returns:
        Tuple[Optional[str], Optional[int], Optional[str]]: A tuple containing description, inclusion value, and value.
    """
    desc = "anytime"
    inc_val = None
    value = None

    if "free" in min_amount_final:
        inc_val = 1
        value = 0
        desc = "fully refundable" if refund_min_amt else "fully changeable"
    elif min_amount:
        amount = calculate_amount(min(min_amount), fre_config, vendor_currency)
        inc_val = 1 if refund_min_amt and amount <= Decimal(refund_min_amt) else 2
        value = str(amount) if min_amount else None
    elif "nil" in min_amount_final:
        inc_val = 0
        desc = "not refundable" if refund_min_amt else "not changeable"

    return desc, inc_val, value


def calculate_amount(min_amount: Decimal, fre_config: Any, vendor_currency: str) -> Decimal:
    """
    Calculates the amount based on the FRE configuration and vendor currency.

    Args:
        min_amount (Decimal): The minimum amount.
        fre_config (Any): The FRE configuration.
        vendor_currency (str): The vendor currency.

    Returns:
        Decimal: The calculated amount.
    """
    if fre_config and vendor_currency and vendor_currency != fre_config.staff_currency.type:
        amount = Decimal(min_amount) * Decimal(fre_config.staff_currency.rate)
    else:
        amount = Decimal(min_amount)
    return amount


def get_selection_data(
    selection_type: str, travel_type: str, brand_tier_data: Dict[str, Any]
) -> Tuple[Optional[str], Optional[Any]]:
    """
    Retrieves selection data based on selection type, travel type, and brand tier data.

    Args:
        selection_type (str): The type of selection (e.g., "meal_selection", "seat_selection").
        travel_type (str): The type of travel (e.g., "international", "domestic").
        brand_tier_data (Dict[str, Any]): The brand tier data.

    Returns:
        Tuple[Optional[str], Optional[Any]]: A tuple containing description and value.
    """
    selection = brand_tier_data.get(selection_type)
    if not selection:
        return None, None
    desc = selection.get("desc")
    value = selection.get("int_value" if travel_type == "international" else "dom_value")
    return desc, value


def process_baggage_and_inclusions(
    travel_type: str, brand_name_mapping: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str], Dict[str, Dict[str, Any]]]:
    """
    Processes baggage and inclusions based on travel type and brand name mapping.

    Args:
        travel_type (str): The type of travel (e.g., "international", "domestic").
        brand_name_mapping (Dict[str, Any]): The brand name mapping data.

    Returns:
        Tuple[Optional[str], Optional[str], Dict[str, Dict[str, Any]]]: A tuple containing
        check-in baggage description, carry-on baggage description, and inclusions.
    """
    data = get_baggage_info(travel_type, brand_name_mapping)
    checkin_baggage = data["checkin_baggage"]
    checkin_baggage_unit = data["checkin_baggage_unit"]
    carry_on_baggage = data["carry_on_baggage"]
    carry_on_baggage_unit = data["carry_on_baggage_unit"]
    checkin_baggage_desc = f"{checkin_baggage} {checkin_baggage_unit}" if checkin_baggage and checkin_baggage_unit else None
    carry_on_baggage_desc = f"{carry_on_baggage} {carry_on_baggage_unit}" if carry_on_baggage and carry_on_baggage_unit else None
    inclusions = frame_inclusions(
        brand_name_mapping.get("inclusions", {}), checkin_baggage, checkin_baggage_unit, carry_on_baggage, carry_on_baggage_unit
    )
    return checkin_baggage_desc, carry_on_baggage_desc, inclusions


def frame_inclusions(
    original: Dict[str, Any], checkin_baggage: Any, checkin_baggage_unit: Any, carry_on_baggage: Any, carry_on_baggage_unit: Any
) -> Dict[str, Dict[str, Any]]:
    """
    Frames the inclusions dictionary by mapping original keys to new keys and adding additional information.

    Args:
        original (Dict[str, Any]): The original dictionary containing inclusion data.
        checkin_baggage (Any): The value for checked baggage.
        checkin_baggage_unit (Any): The unit for checked baggage.
        carry_on_baggage (Any): The value for carry-on baggage.
        carry_on_baggage_unit (Any): The unit for carry-on baggage.

    Returns:
        Dict[str, Dict[str, Any]]: A new dictionary with mapped keys and additional information.
    """
    key_mapping = {
        "checked_baggage": "cbg",
        "carry_on_baggage": "crn",
        "changes": "rbk",
        "refundable": "rfn",
        "seat": "st",
        "meal": "mls",
        "wifi": "wf",
    }
    new_dict = {}
    for old_key, new_key in key_mapping.items():
        if old_key == "checked_baggage":
            new_dict[new_key] = {
                "desc": None,
                "inc": original.get(old_key),
                "value": checkin_baggage,
                "unit": checkin_baggage_unit,
            }
        elif old_key == "carry_on_baggage":
            new_dict[new_key] = {
                "desc": None,
                "inc": original.get(old_key),
                "value": carry_on_baggage,
                "unit": carry_on_baggage_unit,
            }
        else:
            new_dict[new_key] = {"desc": None, "inc": original.get(old_key), "value": None, "unit": None}
    return new_dict


def get_airline_mapping_new(
    mongo_obj: Any, vendor: str, search_id: str, use_rt_static_fares: bool = False
) -> Tuple[Dict[str, Any], Dict[str, str], Dict[str, Any]]:
    """
    Retrieves airline mapping data from MongoDB and processes it.

    Args:
        mongo_obj (Any): MongoDB connection object.
        vendor (str): Vendor name.
        search_id (str): Search ID.
        use_rt_static_fares (bool): Flag to use real-time static fares.

    Returns:
        Tuple[Dict[str, Any], Dict[str, str], Dict[str, Any]]: Contains airline mapping,
        flight brand description, and flight static data.
    """
    airline_mapping_new = {}
    flight_brand_desc_new = {}
    flight_static_data_new = {}

    try:
        mongo_db_name = StaticDBConstants.STATIC_DB
        collection_name = StaticDBConstants.FLIGHT_STATIC_DATA
        query = {"vendor": vendor}
        flight_static_data_resp = mongo_obj.find(mongo_db_name, collection_name, query)

        if not flight_static_data_resp:
            logger.info(f"Fare Brand Details not found - {query}")
            return airline_mapping_new, flight_brand_desc_new, flight_static_data_new

        platting_carrier = {}
        brand_description_list = {}

        for fsd_loop in flight_static_data_resp:
            process_flight_static_data(
                fsd_loop, search_id, platting_carrier, brand_description_list, flight_static_data_new, use_rt_static_fares
            )

        airline_mapping_new = platting_carrier
        flight_brand_desc_new = brand_description_list

    except Exception as ex:
        logger.error(f"Error in get_airline_mapping_new {ex} {traceback.format_exc()}")

    return airline_mapping_new, flight_brand_desc_new, flight_static_data_new


def process_flight_static_data(
    fsd_loop: Dict[str, Any],
    search_id: str,
    platting_carrier: Dict[str, Any],
    brand_description_list: Dict[str, str],
    flight_static_data_new: Dict[str, Any],
    use_rt_static_fares: bool,
) -> None:
    """
    Processes flight static data and updates the provided dictionaries.

    Args:
        fsd_loop (Dict[str, Any]): A dictionary containing flight static data.
        search_id (str): The search ID.
        platting_carrier (Dict[str, Any]): A dictionary to store platting carrier data.
        brand_description_list (Dict[str, str]): A dictionary to store brand descriptions.
        flight_static_data_new (Dict[str, Any]): A dictionary to store flight static data.
        use_rt_static_fares (bool): Flag to use real-time static fares for round trips.

    Returns:
        None
    """
    product_class = fsd_loop.get("product_class")
    brand_description = fsd_loop.get("brand_description", None)
    airline_iata = fsd_loop.get("airline_iata")
    cabin_class = fsd_loop.get("cabin_class", "").lower()
    itilite_fare_type = fsd_loop.get("itilite_fare_type", "").lower()

    if itilite_fare_type != "retail":
        cabin_class = itilite_fare_type

    fare_rules_mapping_key = f"{airline_iata}-{cabin_class}-{product_class}"

    if use_rt_static_fares:
        static_fares = fsd_loop.get("static_fares_rt") or fsd_loop.get("static_fares")
    else:
        static_fares = fsd_loop.get("static_fares")

    if product_class.lower() != "default":
        platting_carrier[f"{airline_iata}|{product_class}"] = fsd_loop
        brand_desc_para = format_brand_description(brand_description)
        brand_description_list[f"{search_id}|{airline_iata}|{product_class}"] = brand_desc_para

    if static_fares is not None:
        flight_static_data_new[fare_rules_mapping_key] = static_fares


def format_brand_description(brand_description):
    if brand_description is not None:
        brand_desc_para = brand_description.strip("\n").split("\n")
        return "\r\n\u2022".join(brand_desc_para)
    return None


def parse_iso_datetime(iso_time):
    """
    Parse an ISO 8601 datetime string, including Zulu time ('Z').
    Converts 'Z' to '+00:00' for compatibility with datetime.fromisoformat.
    """
    if iso_time.endswith("Z"):
        iso_time = iso_time.replace("Z", "+00:00")
    return datetime.fromisoformat(iso_time)


def calculate_flight_travel_time(departure_time, arrival_time):
    departure_dt = parse_iso_datetime(departure_time)
    arrival_dt = parse_iso_datetime(arrival_time)
    duration = arrival_dt - departure_dt
    flightTravelTime = duration.total_seconds() / 60
    return flightTravelTime


def create_datetime_info(departure, arrival, departure_utc, arrival_utc):
    """
    Helper function to create datetime information.
    """
    return {
        "departure": departure,
        "arrival": arrival,
        "departure_time_utc": departure_utc,
        "arrival_time_utc": arrival_utc,
    }


def calculate_duration(data):
    if data.get("departure_time_utc") and data.get("arrival_time_utc"):
        # Use UTC times directly if available
        return calculate_flight_travel_time(data["departure_time_utc"], data["arrival_time_utc"])

    # Fallback to vendor-specific date formats
    return calc_flight_travel_time(data["departure"], data["arrival"], DATE_TIME_FORMAT)


def get_transformation_archival_time(hours=None, multicity=None):
    try:
        time_interval = int(os.getenv("TRANSFORMATION_ARCHIVAL_IN_HOURS", 2))
        if hours is not None:
            time_interval = hours
        if multicity:
            return datetime.now(timezone.utc) + timedelta(hours=time_interval)
        else:
            return {"$date": (datetime.now(timezone.utc) + timedelta(hours=time_interval)).isoformat()}
    except Exception:
        logger.error(traceback.format_exc())
        return None


def calculate_archival_hours(date_str, add_hours=24, fmt="%d %b, %Y"):
    """
    Helper function to calculate_archival_hours.
    we are setting archival time to min of {(onward date - current time)+ 1day buffer), 15day by default}
    """
    max_archival_hours = 15 * 24
    try:
        onward_date = datetime.strptime(date_str, fmt)
        hours_diff = abs((onward_date - datetime.now()).total_seconds()) // 3600 + add_hours
        archival_hours = min(max_archival_hours, int(hours_diff))
        logger.info(f"Calculated archival hours for flight transformation: {archival_hours}")
        return archival_hours
    except Exception as e:
        logger.error(f"Error calculating archival hours for flight transformation: {str(e)}")
        return max_archival_hours


def create_brand_desc(
    type_of_inclusion: str, inclusion_value: Optional[int], description: Optional[str], value: Optional[str]
) -> BrandDesc:
    """
    Creates a BrandDesc object.

    Args:
        type_of_inclusion (str): The type of inclusion.
        inclusion_value (Optional[int]): The inclusion value.
        description (Optional[str]): The description of the inclusion.
        value (Optional[str]): The value of the inclusion.

    Returns:
        BrandDesc: An object representing the brand description.
    """
    return BrandDesc(
        type_of_inclusion=type_of_inclusion,
        inclusion_value=inclusion_value,
        description=description,
        value=value,
    )


# Delete the complete ephemeral path storage
# Use it to delete files or complete folders
def delete_ephemeral_path(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)  # Remove directory and all its contents
        elif os.path.isfile(path):
            os.remove(path)  # Remove file


def check_value_is_null(brand_desc_list: List[BrandDesc]) -> List[str]:
    null_value_types = []
    try:
        for brand in brand_desc_list:
            if isinstance(brand, dict):
                if brand.get("inc") is None:
                    null_value_types.append(brand.get("typ"))
            else:
                if brand.inc is None:
                    null_value_types.append(brand.typ)

    except Exception as ex:
        logger.error(f"Error in check_value_is_null {ex}")

    return null_value_types


def update_l2_info_missing(l2_info_missing: Dict[str, Any], bd: Any, pcn: Optional[str], fare_selection: str) -> None:
    try:
        fare_selection = fare_selection.strip().upper()
        l2_data_missing = check_value_is_null(bd)
        # new_relic_custom_event["fare_count"] += 1
        # if l2_data_missing:
        airline_name = pcn or "others"
        if fare_selection not in l2_info_missing["data"]:
            l2_info_missing["data"][fare_selection] = {}
        if airline_name not in l2_info_missing["data"][fare_selection]:
            l2_info_missing["data"][fare_selection][airline_name] = {
                "fare_count": 0,
                "cbg": 0,
                "crn": 0,
                "rbk": 0,
                "rfn": 0,
                "st": 0,
                "mls": 0,
            }
        l2_info_missing["data"][fare_selection][airline_name]["fare_count"] += 1
        for l2_data in l2_data_missing:
            if l2_data in l2_info_missing["data"][fare_selection][airline_name]:
                l2_info_missing["data"][fare_selection][airline_name][l2_data] += 1
            else:
                l2_info_missing["data"][fare_selection][airline_name][l2_data] = 1

    except Exception as ex:
        logger.error(f"Error in update_l2_info_missing {ex} {traceback.format_exc()}")


def push_l2_metrics_to_new_relic(agent, new_relic_custom_event):
    try:
        base_event = {
            "trip_id": new_relic_custom_event["trip_id"],
            "leg_request_id": new_relic_custom_event["leg_request_id"],
            "vendor_name": new_relic_custom_event["vendor_name"],
            "vendor_request_id": new_relic_custom_event["vendor_request_id"],
            "cabin_class": new_relic_custom_event["cabin_class"],
            "is_morefarecall": new_relic_custom_event["is_morefarecall"],
            # "fare_count": new_relic_custom_event["fare_count"],
            "from_country": new_relic_custom_event["from_country"],
            "to_country": new_relic_custom_event["to_country"],
        }

        data = new_relic_custom_event.get("data", {})
        for faretype, vals in data.items():
            for airline, values in vals.items():
                event = {**base_event, "faretype": faretype, "airline": airline, **values}
                logger.info(f"Pushed data for airline: {event}")
                push_newrelic_custom_event(agent, NewRelicConstants.NEWRELIC_FLIGHT_L2_METRICS, event)

    except Exception as ex:
        logger.error(f"Error while pushing Flight L2 card metrics to NR {ex} {traceback.format_exc()}")
