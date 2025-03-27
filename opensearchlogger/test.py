# import json

# import app


# if __name__ == '__main__':
#     # os.getenv("LOGGER_OPENSEARCH_HOST", "https://search-devlogger-4pacty2fsuq5g4gkgjslo2aheu.us-east-1.es.amazonaws.com")
#     # os.getenv("LOGGER_OPENSEARCH_USERNAME",
#     #           "devlogger")
#     # os.getenv("LOGGER_OPENSEARCH_PASSWORD",
#     #           "Devlogger@123")
#     # os.getenv("LOGGER_OPENSEARCH_INDEX_NAME",
#     #           "streaming_package_logger_v1")
#     # os.getenv("LOGGER_OPENSEARCH_HOST_PORT","9200")
#     # os.getenv("LOGGER_OPENSEARCH_LOG_LEVEL","INFO")
#     # logging_request_uuid.set(str(uuid.uuid4()))

#     # logging_data.set({"trip_id":"0307-0001","farequote_request_id":"","selection_id":"","confirmation_id":""})
#     # test = json.dumps({"mode": "flight", "version": 2, "pax_info": {"Adult": 1, "Child": 0, "Infant": 0},
#     "trip_type": "one_way", "request_id": "41d6e339-30cc-4e17-bbf5-c282939edb6d", "request_for": {"leg": 0, "vendor":
#     "ach", "trip_id": "0006-0858", "client_id": "6"}, "travel_type": "domestic", "request_data": {"td": 125, "api": "ach",
#     "pax": {"adt": [{"dob": "1990-01-31", "name": "sivaramakrishnan Desavasagan", "salutation": "Mr"}], "chd": [], "inf": []},
#     "class": "economy", "filters": {"arrival_date_timestamp": 1682433000, "departure_date_timestamp": 1682425500}, "flights":
#     [{"to": "CCU", "via": [], "from": "DEL", "baggage": {"cabin": "7 Kg", "check_in": "15 Kg"},
#     "carrier_id": "6E 6557", "class_code": "M",
#     "carrier_iata": "6E", "carrier_name": "IndiGo", "result_index": "RS1",
#     "flight_duration": 125, "arrival_date_time": "25-04-2023 14:30",
#     "departure_date_time": "25-04-2023 12:25"}], "fullDay": 0, "request":
#     {"travel_to": "Kolkata, India (CCU)", "travel_date": "25 Apr 2023",
#     "travel_from": "New Delhi, India (DEL)", "travel_type": "domestic", "travel_time_end": 16,
#     "travel_time_start": 12, "customize_gst_abstraction": "NA"},
#     "cvwdm_id": 570, "leg_uuid": "755f5200-e028-11ed-83cb-0625f3fce5b8", "trace_id":
#     "ffca83b0-fa60-47a3-9543-d1cec58a93a4", "fare_type": "ec", "unique_id":
#     "74faaa6de02811edba7bf9a6e4bd2ab3", "base_price": 3400, "fare_brand": "1098508", "sale_price": 4188, "gst_details":
#     {"id": "2", "name": "Itilite Wallet USD", "pan_no": "12assaasas", "email_id": "t@yopmail.com", "username": "us@yopmail.com",
#     "client_id": "6", "entity_id": "4", "contact_no": "7676767667", "gst_number": "06AAGCC1389R1Z2", "is_default": "1",
#     "company_name": "DOMINOS", "stamp_created": "2022-11-13 0:52:33", "stamp_updated": "2022-11-12 19:22:33",
#     "office_address": "sas,Karnataka,BANGALORE-53422", "state_gstin_registration": "Karnataka"},
#     "compare_fare": 4188, "final_amount": 4188,
#     "result_index": "RS1", "manual_option": 0, "product_class": None, "refund_status": "Non-Refundable", "static_leg_id": "5259",
#     "static_leg_no": "1", "codeshare_hash": "e124b1e0-5fea-3a86-92b6-5b7019fc6d90",
#     "fare_selection": "RETAIL", "total_duration": "2h 5m",
#     "fare_basis_code": [["RMIP"]], "fare_brand_name": "Small corporate fare",
#     "static_leg_uuid": "c5ef4d27-5e99-44c8-ae84-d7b07b11583c",
#     "multivendor_hash": "35b0b795-c7a2-3a45-8065-7b5a9660789b", "flight_start_date": "25-04-2023",
#     "connection_priorty": 2, "special_instructions": [],
#     "static_return_leg_id": None, "static_return_leg_no": None, "compare_fare_priority": 2, "gordian_seat_selection": "1",
#     "static_return_leg_uuid": None}})
#     logger.info(f">>>>>>>>>>>>>>>>>>>> {test}")
#     # logger.info(f"Database operation took {test} {test} seconds")

#     app.lambda_handler(None, None)
