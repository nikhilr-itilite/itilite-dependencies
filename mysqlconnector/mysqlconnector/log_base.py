import traceback
import json
from datetime import datetime

from mysqlconnector.connector import DatabaseConnection
from opensearchlogger.logging import logger


def insert_queue_logger(db_type, request_for, types, request):
    try:
        logger.info("entered insert_queue_logger file")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        request1 = json.dumps(request)
        request1 = request1.replace("null", " null").replace("'", "")
        with conn.cursor() as cursor:
            if not request_for:
                values = {"logger_type": types, "request": request1}
                sql_query = """INSERT INTO queue_logger(`logger_type`,`request`) VALUES ('%s', '%s')
                """ % (
                    values["logger_type"],
                    values["request"],
                )
                cursor.execute(sql_query)
                result = cursor.fetchall()
                conn.commit()
                logger.info(f"------Last Logger Inserted---- : {cursor.lastrowid}")
                return cursor.lastrowid
            values = {
                "logger_type": types,
                "vendor": request_for["vendor"],
                "trip_id": request_for["trip_id"],
                "request": request1,
            }
            sql_query = """INSERT INTO queue_logger(`logger_type`,`vendor`,`trip_id`,`request`) VALUES ('%s', '%s', '%s', '%s')
            """ % (
                values["logger_type"],
                values["vendor"],
                values["trip_id"],
                values["request"],
            )
            cursor.execute(sql_query)
            result = cursor.fetchall()
            conn.commit()
            logger.info(f"*insert_gds_query_logger*result**************** : {result}")
            return cursor.lastrowid
    except Exception:
        logger.error(f"Error in insert_queue_logger: {traceback.format_exc()}")
        return {}


def update_queue_logger(db_type, logger_id, col, request):
    try:
        logger.info("entered update_queue_logger file")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn.cursor() as cursor:
            if isinstance(request, dict or list):
                reqData = json.dumps(request)
            else:
                reqData = request
            reqData = json.JSONEncoder().encode(reqData)
            sql_query = (
                "update queue_logger set " + col + "=" + reqData + ", updated_at = now() where logger_id = " + str(logger_id)
            )
            cursor.execute(sql_query)
            result = cursor.fetchall()
            conn.commit()
            logger.info(f"update_queue_logger result: {result}")
    except Exception:
        logger.error(f"exception in update_queue_logger---------: {traceback.format_exc()}")
        return {}


def update_queue_logger_status_and_response(db_type, status_response, response, logger_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn.cursor() as cursor:
            query = "update queue_logger set status= '{0}',response = '{1}', updated_at = now() where logger_id = '{2}'".format(
                status_response, response, logger_id
            )
            cursor.execute(query)
            result = cursor.fetchall()
            conn.commit()
            logger.info(f"update_queue_logger result: {result}")
    except Exception:
        logger.error("Error while updating Queue logger")
        return {}


def insert_leg_metrics(leg_data_list):
    logger.info(f"Insertion started at {datetime.now()}")
    logger.info(f"Leg data List : {leg_data_list}")
    base_query = (
        "INSERT INTO leg_info_doc(`all_from_iata`, `all_to_iata`, `app_leg_id`, `app_leg_id_return`, "
        "`app_leg_uuid`, `app_leg_uuid_return`, `created_on`, `cwm_id`, `from_city`, `from_country`, "
        "`from_iata`, `leg_connector_status`, `leg_consolidation_status`, `leg_no`, "
        "`leg_recommendation_status`, `leg_request_status`, `leg_transformation_status`, `leg_unique_id`, "
        "`mode`, `onward_date`, `onward_end_time`, `onward_start_time`, `return_date`, `return_end_time`, "
        "`return_start_time`, `status`, `to_city`, `to_country`, `to_iata`, `travel_city_from`, "
        "`travel_city_to`, `trip_id`, `trip_unique_id`, `updated_on`, `connector_start_time`, "
        "`connector_end_time`, `transformation_start_time`, `transformation_end_time`, "
        "`consolidation_start_time`, `consolidation_end_time`, `recommendation_start_time`, "
        "`recommendation_end_time`, `first_response_time`, `cache_type`, `first_cache_response_time`, "
        "`checkin`, `checkout`, `hotel_id`, `is_location`, `location`, `place_id`, `country`, `continent`, "
        "`region`, `sub_region`, `political_locality`, `city`, `name`, `lat`, `lng`, `country_short_name`, "
        "`actual_status`, `voucher_status`, `mis_status`, `trip_creation_utc`, `leg_request_id`,"
        "`leg_event_recommendation_status`, `leg_event_message`, `client_id`,"
        "`analytics_leg_connector_status`) VALUES "
    )
    try:
        conn = DatabaseConnection.get_instance("log").get_connection()
        with conn.cursor() as cursor:
            for leg_data_batch in leg_data_list:
                values = []
                for leg_data in leg_data_batch:
                    values.append(
                        f'("{leg_data.get("all_from_iata")}","{leg_data.get("all_to_iata")}","{leg_data.get("app_leg_id")}",'
                        f'"{leg_data.get("app_leg_id_return")}","{leg_data.get("app_leg_uuid")}",'
                        f'"{leg_data.get("app_leg_uuid_return")}",'
                        f'"{leg_data.get("created_on")}","{leg_data.get("cwm_id")}",'
                        f'"{leg_data.get("from_city")}","{leg_data.get("from_country")}",'
                        f'"{leg_data.get("from_iata")}","{leg_data.get("leg_connector_status")}",'
                        f'"{leg_data.get("leg_consolidation_status")}",'
                        f'"{leg_data.get("leg_no")}","{leg_data.get("leg_recommendation_status")}",'
                        f'"{leg_data.get("leg_request_status")}",'
                        f'"{leg_data.get("leg_transformation_status")}",'
                        f'"{str(leg_data.get("leg_unique_id"))}","{leg_data.get("mode")}",'
                        f'"{leg_data.get("onward_date")}","{leg_data.get("onward_end_time")}",'
                        f'"{leg_data.get("onward_start_time")}",'
                        f'"{leg_data.get("return_date")}","{leg_data.get("return_end_time")}",'
                        f'"{leg_data.get("return_start_time")}",'
                        f'"{leg_data.get("status")}","{leg_data.get("to_city")}",'
                        f'"{leg_data.get("to_country")}","{leg_data.get("to_iata")}",'
                        f'"{leg_data.get("travel_city_from")}","{leg_data.get("travel_city_to")}",'
                        f'"{leg_data.get("trip_id")}",'
                        f'"{str(leg_data.get("trip_unique_id"))}","{leg_data.get("updated_on")}",'
                        f'"{leg_data.get("connector_start_time")}",'
                        f'"{leg_data.get("connector_end_time")}","{leg_data.get("transformation_start_time")}",'
                        f'"{leg_data.get("transformation_end_time")}","{leg_data.get("consolidation_start_time")}",'
                        f'"{leg_data.get("consolidation_end_time")}","{leg_data.get("recommendation_start_time")}",'
                        f'"{leg_data.get("recommendation_end_time")}",'
                        f'"{leg_data.get("first_response_time")}","{leg_data.get("cache_type")}",'
                        f'"{leg_data.get("first_cache_response_time")}",'
                        f'"{leg_data.get("checkin")}","{leg_data.get("checkout")}",'
                        f'"{leg_data.get("hotel_id")}","{leg_data.get("is_location")}",'
                        f'"{leg_data.get("location")}","{leg_data.get("place_id")}",'
                        f'"{leg_data.get("country")}","{leg_data.get("continent")}",'
                        f'"{leg_data.get("region")}","{leg_data.get("sub_region")}",'
                        f'"{leg_data.get("political_locality")}","{leg_data.get("city")}",'
                        f'"{leg_data.get("name")}","{leg_data.get("lat")}",'
                        f'"{leg_data.get("lng")}","{leg_data.get("country_short_name")}","{leg_data.get("actual_status")}",'
                        f'"{leg_data.get("voucher_status")}","{leg_data.get("mis_status")}",'
                        f'"{leg_data.get("trip_creation_utc")}","{leg_data.get("leg_request_id")}",'
                        f'"{leg_data.get("leg_event_recommendation_status")}","{leg_data.get("leg_event_message")}",'
                        f'"{leg_data.get("client_id")}","{leg_data.get("analytics_leg_connector_status", 0)}")'
                    )
                if values:
                    query = f"{base_query}{', '.join(values)}"
                    logger.info(f"SQL Query : {query}")
                    cursor.execute(query)
                    conn.commit()
                    logger.info(f"Insertion done at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error insert_leg_metrics {e} {traceback.format_exc()}")
        return {}


def insert_selection_metrics(selection_data_list):
    logger.info(f"Insertion started at {datetime.now()}")
    base_query = (
        "INSERT INTO selection_info_doc(`selection_id`, `client_id`, `role`, `is_personal_booking`, `payment_method`, "
        "`is_central_card`, `pay_at_vendor_enabled`, `status`, `approval_status`, `payment_status`, "
        "`booking_status`, `mis_status`, `voucher_status`, `confirmation_status`, `is_booking_triggered`, "
        "`is_booking_requested`, `is_booking_status_email_sent`, `active`, `is_postcost_approval_triggered`, "
        "`is_mobile`, `is_approval`, `booking_process_completed_at`, `created_at`) VALUES "
    )
    try:
        conn = DatabaseConnection.get_instance("log").get_connection()
        with conn.cursor() as cursor:
            for selection_data_batch in selection_data_list:
                values = []
                for selection_data in selection_data_batch:
                    values.append(
                        f'("{selection_data["selection_id"]}", "{selection_data["client_id"]}", "{selection_data["role"]}", '
                        f'"{selection_data["is_personal_booking"]}", "{selection_data["payment_method"]}", '
                        f'"{selection_data["is_central_card"]}", "{selection_data["pay_at_vendor_enabled"]}", '
                        f'"{selection_data["status"]}", "{selection_data["approval_status"]}", '
                        f'"{selection_data["payment_status"]}", '
                        f'"{selection_data["booking_status"]}", "{selection_data["mis_status"]}", '
                        f'"{selection_data["voucher_status"]}", "{selection_data["confirmation_status"]}", '
                        f'"{selection_data["is_booking_triggered"]}", "{selection_data["is_booking_requested"]}", '
                        f'"{selection_data["is_booking_status_email_sent"]}", "{selection_data["active"]}", '
                        f'"{selection_data["is_postcost_approval_triggered"]}", "{selection_data["is_mobile"]}", '
                        f'"{selection_data["is_approval"]}", "{selection_data["booking_process_completed_at"]}", '
                        f'"{selection_data["created_at"]}")'
                    )
                if values:
                    query = f"{base_query}{', '.join(values)}"
                    cursor.execute(query)
                    conn.commit()
                    logger.info(f"Insertion done at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error insert_selection_metrics {e} {traceback.format_exc()}")
        return {}


def update_leg_metrics_trip_status(trip_id_list):
    if not trip_id_list:
        logger.info("No trip_id tp update status to inactive")
        return
    query = f'UPDATE leg_info_doc SET status="inactive" WHERE trip_id IN ({",".join(filter(None, trip_id_list))})'
    logger.info(query)
    try:
        conn = DatabaseConnection.get_instance("log").get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query)
            cursor.fetchall()
            conn.commit()
    except Exception as e:
        logger.error(f"Error update_leg_metrics_trip_status {e} {traceback.format_exc()}")


def insert_flight_vendor_request_metrics(flight_request_data_list):
    base_query = (
        "INSERT INTO `flight_vendor_request_data` (`vendor_request_id`, `leg_request_id`, `vendor_name`,"
        "`vendor_display_name`, `vendor_start_time`, `vendor_end_time`, `vendor_status`, `time_diff`,"
        "`total`, `cabin_class`, `search_refundable`) VALUES"
    )
    try:
        conn = DatabaseConnection.get_instance("log").get_connection()
        with conn.cursor() as cursor:
            for flight_request_data_batch in flight_request_data_list:
                values = []
                for flight_request_data in flight_request_data_batch:
                    values.append(
                        f'("{flight_request_data["vendor_request_id"]}","{flight_request_data["leg_request_id"]}",'
                        f'"{flight_request_data["vendor_name"]}","{flight_request_data["vendor_display_name"]}",'
                        f'"{flight_request_data["vendor_start_time"]}","{flight_request_data["vendor_end_time"]}",'
                        f'"{flight_request_data["vendor_status"]}","{flight_request_data["time_diff"]}",'
                        f'"{flight_request_data["total"]}","{flight_request_data["cabin_class"]}",'
                        f'"{flight_request_data["search_refundable"]}")'
                    )
                if values:
                    query = f"{base_query}{', '.join(values)}"
                    cursor.execute(query)
                    conn.commit()
                    logger.info(f"Insertion flight_vendor_request_metrics done at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error flight_vendor_request_metrics {e} {traceback.format_exc()}")
        return {}


def insert_hotel_vendor_request_metrics(hotel_request_data_list):
    base_query = (
        "INSERT INTO `hotel_vendor_request_data` (`vendor_request_id`, `leg_request_id`, `vendor_name`,"
        "`vendor_display_name`, `vendor_start_time`, `vendor_end_time`, `vendor_status`, `time_diff`,"
        "`total`) VALUES"
    )
    try:
        conn = DatabaseConnection.get_instance("log").get_connection()
        with conn.cursor() as cursor:
            for hotel_request_data_batch in hotel_request_data_list:
                values = []
                for hotel_request_data in hotel_request_data_batch:
                    values.append(
                        f'("{hotel_request_data["vendor_request_id"]}","{hotel_request_data["leg_request_id"]}",'
                        f'"{hotel_request_data["vendor_name"]}","{hotel_request_data["vendor_display_name"]}",'
                        f'"{hotel_request_data["vendor_start_time"]}","{hotel_request_data["vendor_end_time"]}",'
                        f'"{hotel_request_data["vendor_status"]}","{hotel_request_data["time_diff"]}",'
                        f'"{hotel_request_data["total"]}")'
                    )
                if values:
                    query = f"{base_query}{', '.join(values)}"
                    cursor.execute(query)
                    conn.commit()
                    logger.info(f"Insertion hotel_request_metrics done at {datetime.now()}")
    except Exception as e:
        logger.error(f"Error hotel_request_metrics {e} {traceback.format_exc()}")
        return {}
