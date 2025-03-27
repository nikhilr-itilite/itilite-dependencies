import helperlayer.tripmodels as helpers
import json
import os
import urllib
from pymongo import MongoClient
from odmantic import SyncEngine
from enum import Enum
from bson.objectid import ObjectId
from opensearchlogger.logging import logger
from datetime import datetime

pyMongoConnection = None
MONGO_DB_PASSWORD = os.environ.get("MONGO_DB_PASSWORD")
MONGO_DB_USERNAME = os.environ.get("MONGO_DB_USERNAME")
MONGO_HOST = os.environ.get("MONGO_HOST")
TRIP_DB = os.environ.get("TRIP_DB")

LEG_KEY_MAPPING = {"connector_status": "leg_connector_status"}


class Status(Enum):
    PENDING = 0
    STARTED = 1
    SUCCESS = 2
    NO_RESULT = 3
    FAILED = 4
    NOT_IMPLEMENTED = 5
    PARTIAL_SUCCESS = 6
    SUCCESS_EXCEPT_ADDITIONAL_CONFIG = 7
    SUCCESS_EXCEPT_SPECIFIC_CABIN_CLASS = 8
    SKIPPED = 9


def initialise_mongo_connector_helper_layer(connection_obj):
    global pyMongoConnection
    pyMongoConnection = connection_obj
    pyMongoConnection.ping()


def leg_request_status_update(leg_request_id, params, mode="flight"):
    ts = datetime.now()
    MONGOCLIENT = pyMongoConnection.get_client()
    TRIP_ENGINE = SyncEngine(client=MONGOCLIENT, database=TRIP_DB)
    try:
        if mode == "flight":
            leg_request_data = TRIP_ENGINE.find_one(
                helpers.FlightRequest,
                helpers.FlightRequest.leg_request_id == ObjectId(leg_request_id),
            )
        else:
            leg_request_data = TRIP_ENGINE.find_one(
                helpers.HotelRequest,
                helpers.HotelRequest.leg_request_id == ObjectId(leg_request_id),
            )
        if leg_request_data is not None:
            leg_request_json = json.loads(leg_request_data.json())
            for key in params:
                leg_request_json[key] = params[key]
            if mode == "flight":
                leg_req = helpers.FlightRequest(**leg_request_json)
            else:
                leg_req = helpers.HotelRequest(**leg_request_json)
            TRIP_ENGINE.save(leg_req)
    except Exception as e:
        logger.error("failed to update leg status {0}, exception  {1}".format(leg_request_id, e))
    finally:
        print("leg_request_status_update start:", datetime.now())
        print("leg_request_status_update time taken:", datetime.now() - ts)


def trip_request_status_update(trip_request_id, key, value):
    MONGOCLIENT = pyMongoConnection.get_client()
    TRIP_ENGINE = SyncEngine(client=MONGOCLIENT, database=TRIP_DB)
    try:
        trip_request_data = TRIP_ENGINE.find_one(helpers.Trip, helpers.Trip.trip_id == trip_request_id)
        if trip_request_data is not None:
            trip_request_json = json.loads(trip_request_data.json())
            trip_request_json[key] = value
            trip_req = helpers.HotelRequest(**trip_request_json)
            TRIP_ENGINE.save(trip_req)
    except Exception as e:
        logger.error("failed to update trip_request_status_update {0}, exception  {1}".format(trip_request_id, e))
    finally:
        pass


def get_leg_vendor_request(leg_request_ids, mode="flight"):
    # Changes : leg_request_id : [], mode should be same for all legs passed
    # This will be useful in case of multi_city, so that we didn't make one more call that will lead to one more conn
    ts = datetime.now()
    print("get_leg_vendor_request start:", ts)
    MONGOCLIENT = pyMongoConnection.get_client()
    TRIP_ENGINE = SyncEngine(client=MONGOCLIENT, database=TRIP_DB)
    final_vendor_request_data = []
    try:
        if mode == "flight":
            for leg_request_id in leg_request_ids:
                vendor_request_data = TRIP_ENGINE.find(
                    helpers.FlightVendorRequest,
                    helpers.FlightVendorRequest.leg_request_id == ObjectId(leg_request_id),
                )
                vendors_request_data = list(vendor_request_data)
                vendors_request_data = [json.loads(vendor_request_data.json()) for vendor_request_data in vendors_request_data]
                final_vendor_request_data.extend(vendors_request_data)
        else:
            for leg_request_id in leg_request_ids:
                vendor_request_data = TRIP_ENGINE.find(
                    helpers.HotelVendorRequest,
                    helpers.HotelVendorRequest.leg_request_id == ObjectId(leg_request_id),
                )
                vendors_request_data = list(vendor_request_data)
                vendors_request_data = [json.loads(vendor_request_data.json()) for vendor_request_data in vendors_request_data]
                final_vendor_request_data.extend(vendors_request_data)

        return final_vendor_request_data
    except Exception as e:
        logger.error(f"failed to get_leg_vendor_request {leg_request_ids} , Exception {str(e)}")
    finally:
        print("get_leg_vendor_request end:", datetime.now())
        print("get_leg_vendor_request time taken:", datetime.now() - ts)


def get_vendor_request(vendor_request_id, key, mode):
    MONGOCLIENT = MongoClient(
        "mongodb+srv://" + urllib.parse.quote(MONGO_DB_USERNAME) + ":" + urllib.parse.quote(MONGO_DB_PASSWORD) + "@" + MONGO_HOST
    )
    try:
        trip_db = MONGOCLIENT[TRIP_DB]
        collection_name = "flight_vendor_request" if mode == "flight" else "hotel_vendor_request"  # TODO
        vendor_request_collection = trip_db[collection_name]
        vendor_request_data = vendor_request_collection.find_one({"_id": ObjectId(vendor_request_id)})
        return vendor_request_data
    except Exception as e:
        logger.error("failed to get_vendor_request {0}, exception  {1}".format(vendor_request_id, e))
    finally:
        MONGOCLIENT.close()


def vendor_request_status_update(
    vendor_request_id,
    key,
    value,
    mode,
    layer_name=None,
    total_batches=None,
    total_hotels=None,
    start_time=None,
    end_time=None,
    vendor_total_time=None,
    vendor_call_date=None,
    detailed_error=None,
):
    mongo_client = MongoClient(
        "mongodb+srv://" + urllib.parse.quote(MONGO_DB_USERNAME) + ":" + urllib.parse.quote(MONGO_DB_PASSWORD) + "@" + MONGO_HOST
    )
    with mongo_client.start_session(causal_consistency=True) as session:
        with session.start_transaction():
            trip_db = mongo_client[TRIP_DB]
            collection_name = "flight_vendor_request" if mode == "flight" else "hotel_vendor_request"  # TODO
            vendor_request_collection = trip_db[collection_name]
            vendor_request_data = vendor_request_collection.find_one({"_id": ObjectId(vendor_request_id)})
            vendor_request_data[key] = value
            if mode == "flight":
                vendor_request_data["detailed_error"] = detailed_error
            vendor_request_data["request_status"] = Status.SUCCESS.value  # TODO
            if layer_name == "connector":
                if start_time:
                    vendor_request_data["connector_start_time"] = start_time
                if end_time:
                    vendor_request_data["connector_end_time"] = end_time
                if vendor_total_time:
                    vendor_request_data["vendor_total_time"] = vendor_total_time
                if vendor_call_date:
                    vendor_request_data["vendor_call_date"] = vendor_call_date

                if mode == "hotel":  # param mismatch for back support
                    if total_batches:
                        vendor_request_data["batch_count"] = total_batches
                    if total_hotels:
                        vendor_request_data["hotel_count"] = total_hotels

            vendor_request_collection.replace_one({"_id": vendor_request_data["_id"]}, vendor_request_data)
    mongo_client.close()


def get_leg_status_for_no_result(all_vendor_request_data):
    try:
        leg_status = None
        all_cabin_class = set()
        for cabin in all_vendor_request_data:
            all_cabin_class.add(cabin["cabin_class"])
        no_result_vendor = list()
        for vendor_data in all_vendor_request_data:
            if vendor_data["connector_status"] == Status.NO_RESULT.value:
                no_result_vendor.append(vendor_data)
        message_set, connector_with_err_msg = set(), 0
        for vendor in no_result_vendor:
            if vendor.get("detailed_error", None) is not None:
                message_set.add(vendor.get("err_msg", None))
                connector_with_err_msg += 1

        if len(no_result_vendor) == connector_with_err_msg:
            leg_status = Status.SUCCESS_EXCEPT_ADDITIONAL_CONFIG.value
        else:
            failed_cabin_class_list = []
            for vendor in no_result_vendor:
                failed_cabin_class = {}
                if vendor.get("detailed_error", None) is None:
                    failed_cabin_class["cabin_class"] = vendor["cabin_class"]
                    failed_cabin_class["vendor"] = vendor["name"]
                    failed_cabin_class_list.append(failed_cabin_class)
            for failed_cabin in failed_cabin_class_list:
                vendor_data_with_cabin_class = list()
                for vendor_data in all_vendor_request_data:
                    if failed_cabin["cabin_class"] == vendor_data["cabin_class"]:
                        vendor_data_with_cabin_class.append(vendor_data)
                if all(
                    all_vendor_for_specific_cabin_class.get("connector_status", 0) == 3
                    for all_vendor_for_specific_cabin_class in vendor_data_with_cabin_class
                ):
                    leg_status = Status.SUCCESS_EXCEPT_SPECIFIC_CABIN_CLASS.value
                else:
                    leg_status = Status.PARTIAL_SUCCESS.value
                    break
        return leg_status
    except Exception as e:
        logger.error(f"Error While fetching leg details : {e}")
        return Status.PENDING.value


def get_value_for_3_status(status_set):
    leg_status = Status.PENDING.value
    try:
        if (
            Status.SUCCESS.value in status_set
            and (
                (
                    Status.NO_RESULT.value in status_set
                    and (
                        Status.PENDING.value in status_set
                        or Status.STARTED.value in status_set
                        or Status.NOT_IMPLEMENTED.value in status_set
                        or Status.FAILED.value in status_set
                        or Status.SKIPPED.value in status_set
                    )
                )
                or (
                    Status.PENDING.value in status_set
                    and (
                        Status.STARTED.value in status_set
                        or Status.NOT_IMPLEMENTED.value in status_set
                        or Status.SKIPPED.value in status_set
                        or Status.FAILED.value in status_set
                    )
                )
            )
        ) or (
            Status.STARTED.value in status_set
            and (
                (Status.NOT_IMPLEMENTED.value in status_set and Status.FAILED.value in status_set)
                or (Status.SKIPPED.value in status_set and Status.FAILED.value in status_set)
            )
        ):
            leg_status = Status.PARTIAL_SUCCESS.value
        elif (
            (
                Status.STARTED.value in status_set
                and (
                    (
                        (Status.NO_RESULT.value in status_set)
                        and (
                            Status.PENDING.value in status_set
                            or Status.NOT_IMPLEMENTED.value in status_set
                            or Status.SKIPPED.value in status_set
                            or Status.FAILED.value
                        )
                    )
                )
            )
            or (
                Status.PENDING.value in status_set
                and Status.STARTED.value in status_set
                and (Status.NOT_IMPLEMENTED.value in status_set or Status.SKIPPED.value in status_set)
            )
            or (
                Status.FAILED.value in status_set
                and Status.STARTED.value in status_set
                and (Status.NOT_IMPLEMENTED.value in status_set or Status.SKIPPED.value in status_set)
            )
        ):
            leg_status = Status.STARTED.value
        elif Status.PENDING.value in status_set and (
            (
                (Status.NOT_IMPLEMENTED.value in status_set or Status.SKIPPED.value in status_set)
                and Status.NO_RESULT.value in status_set
            )
            or (Status.FAILED.value in status_set and Status.NO_RESULT.value in status_set)
            or (
                (Status.NOT_IMPLEMENTED.value in status_set or Status.SKIPPED.value in status_set)
                and Status.FAILED.value in status_set
            )
        ):
            leg_status = Status.PENDING.value
        elif (
            (Status.NOT_IMPLEMENTED.value in status_set or Status.SKIPPED.value in status_set)
            and Status.NO_RESULT.value in status_set
            and Status.FAILED.value in status_set
        ):
            leg_status = Status.FAILED.value
        return leg_status
    except Exception as e:
        logger.error(f"Exception While fetching status : {e}")
        return leg_status


def get_value_for_2_status(status_set, all_vendor_request_data):
    leg_status = Status.PENDING.value
    try:
        if Status.SUCCESS.value in status_set and (
            Status.NOT_IMPLEMENTED.value in status_set or Status.SKIPPED.value in status_set
        ):
            leg_status = Status.SUCCESS.value
        elif Status.SUCCESS.value in status_set and (
            Status.PENDING.value in status_set or Status.STARTED.value in status_set or Status.FAILED.value in status_set
        ):
            leg_status = Status.PARTIAL_SUCCESS.value
        elif Status.STARTED.value in status_set and (
            Status.NO_RESULT.value in status_set
            or Status.PENDING.value in status_set
            or Status.NOT_IMPLEMENTED.value in status_set
            or Status.FAILED.value in status_set
            or Status.SKIPPED.value in status_set
        ):
            leg_status = Status.STARTED.value
        elif Status.PENDING.value in status_set and (
            Status.NO_RESULT.value in status_set
            or Status.NOT_IMPLEMENTED.value in status_set
            or Status.FAILED.value in status_set
            or Status.SKIPPED.value in status_set
        ):
            leg_status = Status.PENDING.value
        elif (
            Status.NO_RESULT.value in status_set
            and (
                Status.FAILED.value in status_set
                or Status.NOT_IMPLEMENTED.value in status_set
                or Status.SKIPPED.value in status_set
            )
        ) or (
            (Status.NOT_IMPLEMENTED.value in status_set or Status.SKIPPED.value in status_set) and Status.FAILED.value in status_set
        ):
            leg_status = Status.FAILED.value
        elif Status.SUCCESS.value in status_set and Status.NO_RESULT.value in status_set:
            leg_status = get_leg_status_for_no_result(all_vendor_request_data)
        return leg_status
    except Exception as e:
        logger.error(f"Exception while fetching leg connector status : {e}")
        return leg_status


def analytics_leg_status_update(all_vendor_request_data, mode, key):
    leg_status = Status.STARTED.value
    try:
        status_set, no_result_connector = set(), list()
        for vendor_request_collection in all_vendor_request_data:
            status_set.add(vendor_request_collection[key])
            if vendor_request_collection[key] == Status.NO_RESULT.value and mode == "flight":
                no_result_connector.append(vendor_request_collection)
        if len(status_set) == 1:  # return leg_status if leg of status set is equal to 1.
            if Status.SKIPPED.value in status_set:
                leg_status = 2
            else:
                leg_status = list(status_set)[0]
        elif len(status_set) == 2:
            leg_status = get_value_for_2_status(status_set, all_vendor_request_data)
        elif len(status_set) == 3:
            leg_status = get_value_for_3_status(status_set)
        else:
            leg_status = Status.PENDING.value

        return leg_status
    except Exception as e:
        logger.error(f"Error While updating Analytics leg_connector_status : {e}")
        return leg_status


def leg_status_update(leg_request_id, key, mode):
    mongo_client = MongoClient(
        "mongodb+srv://" + urllib.parse.quote(MONGO_DB_USERNAME) + ":" + urllib.parse.quote(MONGO_DB_PASSWORD) + "@" + MONGO_HOST
    )
    with mongo_client.start_session(causal_consistency=True) as session:
        with session.start_transaction():
            trip_db = mongo_client[TRIP_DB]
            vendor_request_collection = trip_db["hotel_vendor_request"] if mode == "hotel" else trip_db["flight_vendor_request"]
            all_vendor_request_data = vendor_request_collection.find({"leg_request_id": ObjectId(leg_request_id)})
            status_set = set()
            for vendor_request_data in all_vendor_request_data:
                if vendor_request_data["name"].lower() != "cph":
                    status_set.add(vendor_request_data[key])
            all_vendor_request_data.rewind()
            if len(status_set) == 1:
                if Status.SKIPPED.value in status_set:
                    leg_status = 2
                else:
                    leg_status = list(status_set)[0]
            elif (
                len(status_set) == 2
                and Status.SUCCESS.value in status_set
                and (Status.NOT_IMPLEMENTED.value in status_set or Status.SKIPPED.value in status_set)
            ):
                leg_status = Status.SUCCESS.value  # Very unusual case
            elif Status.STARTED.value in status_set or Status.SUCCESS.value in status_set:
                leg_status = Status.STARTED.value  # partially complete
            else:
                leg_status = Status.PENDING.value

            request_collection = trip_db["hotel_request"] if mode == "hotel" else trip_db["flight_request"]
            # request_collection = trip_db[request_collection_name]
            if mode == "flight":
                analytics_leg_status = analytics_leg_status_update(list(all_vendor_request_data), mode, key)
            request_data = request_collection.find_one({"_id": ObjectId(leg_request_id)})
            if request_data is not None:
                request_data[LEG_KEY_MAPPING[key]] = leg_status
                if mode == "flight":
                    request_data["analytics_leg_connector_status"] = analytics_leg_status
                request_collection.replace_one({"_id": request_data["_id"]}, request_data)
            else:
                logger.error(f"leg_request_id:{leg_request_id} not found.")
    mongo_client.close()


def leg_timestamp_update(leg_request_id, params):
    ts = datetime.now()
    print("leg_timestamp_update start:", ts)
    MONGOCLIENT = pyMongoConnection.get_client()
    TRIP_ENGINE = SyncEngine(client=MONGOCLIENT, database=TRIP_DB)
    try:
        leg_timestamp_data = TRIP_ENGINE.find_one(
            helpers.LegTimestampLog,
            helpers.LegTimestampLog.leg_request_id == ObjectId(leg_request_id),
        )

        if leg_timestamp_data is None:
            leg_timestamp_json = {"leg_request_id": ObjectId(leg_request_id)}
        else:
            leg_timestamp_json = json.loads(leg_timestamp_data.json())
        for key in params:
            leg_timestamp_json[key] = params[key]
        leg_req = helpers.LegTimestampLog(**leg_timestamp_json)
        TRIP_ENGINE.save(leg_req)
    except Exception as e:
        logger.error(str(e))
    finally:
        print("leg_timestamp_update end:", datetime.now())
        print("leg_timestamp_update time taken:", datetime.now() - ts)
