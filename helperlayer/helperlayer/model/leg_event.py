import bson
from enum import Enum
from datetime import datetime

from opensearchlogger.logging import logger
from .common import operations


class EventStatus(str, Enum):
    FAILED = "failed"
    INPROGRESS = "inprogress"
    STARTED = "started"
    COMPLETED = "completed"


class CacheType(str, Enum):
    COLD = "cold_cache"
    HOT = "hot_cache"
    WARM = "warm_cache"
    RECOMMENDATION = "recommendation"


cache_order = {
    "hot_cache": 2,
    "warm_cache": 3,
    "cold_cache": 4,
    "recommendation": 1,
}


class LegEvent:
    def find_leg_event(self, mode, leg_request_id, query={}):
        query["leg_request_id"] = bson.ObjectId(leg_request_id)
        if mode == "flight":
            leg_event_data = operations.read("flight_leg_event", query, use_secondary=True)
        elif mode == "hotel":
            leg_event_data = operations.read("hotel_leg_event", query, use_secondary=True)
        logger.info("find leg event %s", leg_event_data)
        if leg_event_data and len(leg_event_data) == 1:
            return leg_event_data[0]
        return leg_event_data

    def upsert_leg_event(
        self, mode, leg_request_id, cache_type, event_status, message=None, error_details=None, error=None, extra={}
    ):
        print("handle upsert by redirecting to proper fn below")

    def update_leg_event(
        self, mode, leg_request_id, cache_type, event_status, message=None, error_details=None, error=None, extra={}
    ):
        update_fields = {}
        cache_type_value = CacheType(cache_type).value
        query = {"leg_request_id": bson.ObjectId(leg_request_id), "type": cache_type_value, "order": cache_order[cache_type_value]}
        update_fields = {}
        if event_status and isinstance(event_status, list):
            query["status"] = {"$in": event_status}
        else:
            update_fields = {
                "status": EventStatus(event_status).value,
            }
        logger.info("Leg event updating document in %s_leg_event collection: %s, query: %s" % (mode, update_fields, query))
        if message is not None:
            update_fields["message"] = message
        if error_details is not None:
            update_fields["error_details"] = error_details
        if error is not None:
            update_fields["error"] = error
        update_fields["upsert_tn"] = datetime.now()

        if extra:
            update_fields.update(extra)

        if mode == "flight":
            update_id = operations.update("flight_leg_event", query, update_fields, True)
        elif mode == "hotel":
            update_id = operations.update("hotel_leg_event", query, update_fields, True)

        logger.info("Updated document ID in %s_leg_event collection: %s", mode, update_id)
        return update_id

    def insert_leg_event(self, mode, leg_request_id, data):
        data["leg_request_id"] = bson.ObjectId(leg_request_id)
        data["order"] = cache_order[data["type"]]
        print(f"Leg event inserting document in {mode}_leg_event collection: {data}")
        if mode == "flight":
            insert_id = operations.write("flight_leg_event", data)
        elif mode == "hotel":
            insert_id = operations.write("hotel_leg_event", data)
        logger.info("Insert document ID in %s_leg_event collection: %s", mode, insert_id)
        return insert_id
