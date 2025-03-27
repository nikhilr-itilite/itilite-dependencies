from .store import DBConfig, OperationWrapper


db_config = DBConfig()
operations = OperationWrapper(db_config)


def create_filter_format(field, operator, value):
    return {"field": field, "operator": operator, "value": value}


if __name__ == "__main__":
    import bson
    from datetime import datetime
    from farequote import Farequote
    from leg_event import LegEvent

    leg_event = LegEvent()
    farequote = Farequote()

    leg_request_id = bson.ObjectId()
    flight_leg_event = {
        "leg_request_id": leg_request_id,
        "type": "cold_cache",
        "status": "started",
        "message": None,
        "insert_tn": datetime.now(),
        "update_tn": datetime.now(),
    }

    insert_results = leg_event.insert_leg_event("flight", leg_request_id, flight_leg_event)
    print(f"Inserted document ID in farequote collection: {insert_results}")

    update_results = leg_event.update_leg_event("flight", leg_request_id, "cold_cache", "completed", True)
    print(f"Inserted document ID in farequote collection: {update_results}")

    query = {"leg_request_id": leg_request_id, "type": "cold_cache"}
    read_primary = leg_event.find_leg_event("flight", leg_request_id, query)

    for primary in read_primary:
        print("primary", primary)

    query = {"leg_request_id": leg_request_id, "type": "cold_cache"}
    read_secondary = leg_event.find_leg_event("flight", leg_request_id, query)

    for secondary in read_secondary:
        print("secondary", secondary)

    read_primary = farequote.find_farequote("flight", "66c8524c4d50337c7754707c")
    print("read_primary", read_primary)

    leg_event1 = LegEvent()
    farequote1 = Farequote()

    insert_results = leg_event1.insert_leg_event("flight", leg_request_id, flight_leg_event)
