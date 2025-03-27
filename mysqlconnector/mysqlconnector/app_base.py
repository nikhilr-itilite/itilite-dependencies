import json
import os
import traceback
from datetime import datetime

from mysqlconnector.connector import DatabaseConnection
from opensearchlogger.logging import logger

# from mysqlconnector.connector import MysqlConnector, DatabaseConnection

APP_DB = "app_slave" if os.environ.get("USE_APP_SLAVE_DB") == "1" else "app"


def get_trip_info(db_type, trip_id):
    """
    Desc : Fetch the trip data and client data from app db
    Input:
        db_type: master/slave db to connect
        trip_id : reference client id
        travel_type : domestic/international
        ogn_country : country of hotel location
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT * from trip WHERE trip_id ='%s'""" % (trip_id)
        logger.info(f"get_trip_info------- {sql}")

        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                logger.info(f"--------trip info result------ {result}")
                if len(result) != 0:
                    return result
    except Exception as ex:
        logger.error(f"ERROR:  {ex}")
        logger.error(traceback.format_exc())


def check_trip_approved(trip_id, db_type="app"):
    result = []
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT * FROM selected_rule WHERE trip_id = '%s' AND active=1 AND status ='Approved'""" % (trip_id)
        logger.info(f"sql result---------- {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()

    except Exception as ex:
        logger.error(f"Error in check trip approved====>{traceback.format_exc()}")
        logger.error(f"ERROR:  {ex}")
        logger.error(traceback.format_exc())
    return result


def get_env_config_info(db_type, client_id):
    """
    Desc : Fetch the client data from app db
    Input:
        db_type: master/slave db to connect central  paymet_method =2 ,paybyvcard version=3, user card paymet_method=1
        trip_id : reference client id
        travel_type : domestic/international
        ogn_country : country of hotel location
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        logger.info(f"-------------- connection object----------- {conn}")
        sql = """SELECT e.flight_corporate_fare,e.hotel_corporate_deal,c.multicurrency_enable,e.rt_split,
                e.enable_membership_config, c.payment_method,e.paybycard_version,e.package_timer,
                e.booking_timer,e.payment_based_currency, e.instant_hotel_book,
                e.enable_postpaid, e.switch_postpaid_as_prepaid, e.is_postpaid ,e.is_prepaid, e.enable_hotel_gst_tag,
                e.enable_unused_ticket, e.allow_window_break_hours, e.enable_hotel_aaa_rate
                FROM client c
                INNER JOIN env_config e on c.id = e.client_id
                WHERE c.id =%d""" % (
            int(client_id)
        )
        logger.info(f"get_client_info------- {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result
    except Exception as ex:
        logger.error(f"ERROR ====>{traceback.format_exc()} ")
        logger.error(f"ERROR:  {ex}")


def get_staff_details(db_type, staff_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT * from staff
                WHERE id =%d""" % (
            int(staff_id)
        )
        logger.info(f"get staff details------- {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def get_staff_details_from_email(db_type, staff_email):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = f"SELECT * from staff WHERE username = '{staff_email}'"
        logger.info(f"get staff details------- {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result
    except Exception as ex:
        logger.error(f"ERROR while get_staff_details_from_email: {ex}")
        logger.error(traceback.format_exc())


def get_staff_details_from_trip(db_type, trip_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT trip_id, first_name, name FROM trip
                JOIN staff ON trip.staff_id = staff.id
                WHERE trip_id = '%s';
                """ % (
            trip_id
        )

        logger.info(f"get_staff_details_from_trip------- {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def update_traveller_info(db_type, data):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ UPDATE traveller_info
                SET salutation='%s', first_name='%s', last_name='%s', email='%s', dob='%s',
                phone='%s', code='%s', passport_no='%s', passport_expiry='%s', nationality='%s',
                passport_issue_country='%s', passport_issue_date='%s'
                WHERE id=%s
                """ % (
            data["salutation"],
            data["first_name"],
            data["last_name"],
            data["email"],
            data["dob"],
            data["contact_number"],
            data["country_code"],
            data["passport_no"],
            data["passport_expiry"],
            data["nationality"],
            data["passport_issue_country"],
            data["passport_issue_date"],
            data["traveller_id"],
        )
        logger.info(f"----------traveler info query update------- {sql}")
        logger.info(f"connection---------- {conn}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                result = True
                return result
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def update_guest_info(db_type, data):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ UPDATE staff_guest_info
                SET salutation='%s', first_name='%s', last_name='%s', email='%s', dob='%s',
                phone='%s', code='%s', passport_no='%s', passport_expiry='%s', nationality='%s',
                passport_issue_country='%s', passport_issue_date='%s'
                WHERE id=%s
                """ % (
            data["salutation"],
            data["first_name"],
            data["last_name"],
            data["email"],
            data["dob"],
            data["contact_number"],
            data["country_code"],
            data["passport_no"],
            data["passport_expiry"],
            data["nationality"],
            data["passport_issue_country"],
            data["passport_issue_date"],
            data["guest_id"],
        )
        logger.info(f"----------update_guest_info sql------ {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                result = True
                return result
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def get_traveller_details(db_type, trip_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT * from  traveller_info
                Where  trip_id='%s', status=1
                """ % (
            trip_id
        )
        logger.info(f"----------traveler info query update------- {sql}")
        logger.info(f"connection----------  {conn}")
        final_result = {}
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                logger.info(f"traveller info result---------- {result}")
                if len(result) != 0:
                    # Book for Others trip
                    final_result = result
                else:
                    # Single self traveller trip
                    sql = """ SELECT * from  trip
                        Where  trip_id=%s
                        """ % (
                        trip_id
                    )
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    staff_id = result[0]["staff_id"]
                    logger.info(f"staff id---------- {staff_id}")
                    sql = """ SELECT * from  staff s join profile p where s.id=%s""" % (staff_id)
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    cursor.close()
                    logger.info(f"-------staff and profile result--------- {result}")
                    final_result = [result]
        logger.info(f"-------------final result---------- {final_result}")
        return final_result

    except Exception as ex:
        logger.error(f"---------ERROR in get_traveller_details-------- {ex}")
        logger.error(traceback.format_exc())


def get_policy_flight_info(db_type, client_id):
    """
    Desc : Fetch the flight policies for a client from app db
    Input:
        db_type: master/slave db to connect
        client_id : reference client id
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = (
            "SELECT `id`, `order`, `active`, `deleted`, `client_id`, `description`, `cabin_class`, `policy`,\
            `defult` FROM policy_flight WHERE client_id="
            + str(client_id)
            + " AND active = 1 AND deleted=0 ORDER BY FIELD(defult,1) , `order` ASC"
        )
        logger.info(f"get_policy_flight_info------- {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                logger.info(f"sql result---------- {result}")
                if len(result) != 0:
                    return result
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def get_staff_info(db_type, staff_id):
    """
    Desc : Fetch the staff info from app db
    Input:
        db_type: master/slave db to connect
        staff_id : reference staff id
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        # conn = MysqlConnector.connect_db(db_type)
        sql = """SELECT s.id, s.first_name, s.name, s.username, s.level, s.internal_level, s.client_id, p.currency,
                p.timezone FROM staff s INNER JOIN profile p on p.username = s.username
                WHERE s.id = '%s'""" % (
            staff_id
        )
        logger.info(f"get_staff_info------- {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    logger.info(f"get_staff_info------- {result}")
                    return result
    except Exception as ex:
        logger.error(f"ERROR: {ex}")


def get_company_configurations(db_type, client_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT * from env_config env left join convenience_fee_config cf on
                cf.client_id = env.client_id WHERE env.client_id =%d""" % (
            int(client_id)
        )
        logger.info(f"get_company_configurations------- {sql}")
        with conn:
            logger.info(f"-------sql-get_company_configurations-------- {conn}")
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                if len(result) != 0:
                    logger.info(f"----------get_company_configurations-------result {result}")
                    return result
    except Exception as ex:
        logger.error(f"--------ERROR in get_company_configurations-----------: {ex}")
        logger.error(traceback.format_exc())


def get_company_configurations_personal(db_type, client_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT * from env_config env left join convenience_fee_config_personal cf
                on cf.client_id = env.client_id WHERE env.client_id =%d""" % (
            int(client_id)
        )
        logger.info(f"get_company_configurations personal------- {sql}")
        with conn:
            logger.info(f"-------sql--------- {conn}")
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                if len(result) != 0:
                    return result
    except Exception as ex:
        logger.error(f"--------ERROR in get_company_configurations-----------: {ex}")
        logger.error(traceback.format_exc())


def get_traveller_info(db_type, trip_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT * from  traveller_info
                Where  trip_id='%s' and status != 0 ORDER BY pax_type,id
                """ % (
            trip_id
        )
        logger.info(f"----------traveler info query update------- {sql}")
        logger.info(f"connection---------- {conn}")
        traveller_details = {}
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if result and len(result) != 0:
                    traveller_details = result
                logger.info(f"traveller info result---------- {result}")
        logger.info(f"-------------final result---------- {traveller_details}")
        return traveller_details
    except Exception as ex:
        logger.error(f"---------ERROR in get_traveller_details--------: {ex}")
        logger.error(traceback.format_exc())


def get_currency_conversion_details(db_type, currency, date):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT currency_rate, conversion_date FROM currency_conversion WHERE currency_code='%s'
                  AND conversion_date = DATE(%s) AND enable=1 LIMIT 1
                """ % (
            currency,
            date,
        )
        logger.info(f"----------get_currency_conversion_details------- {sql}")
        logger.info(f"connection---------- {conn}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                if result and len(result):
                    cursor.close()
                    return result
                else:
                    sql = """ SELECT currency_rate, conversion_date FROM currency_conversion WHERE currency_code='%s'
                              AND enable=1 order by stamp_created desc LIMIT 1
                            """ % (
                        currency
                    )
                    cursor.execute(sql)
                    result = cursor.fetchone()
                    cursor.close()
                    if result and len(result):
                        return result
    except Exception as ex:
        logger.error(f"---------ERROR in get_currency_conversion_details--------: {ex},{traceback.format_exc()}")


def get_staff_and_profile_details(db_type, staff_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT * from  staff s join profile p on s.id = p.employee_id
                Where  s.id='%s'
                """ % (
            staff_id
        )
        logger.info(f"----------get_user_staff_and_profile_details sql------- {sql}")
        logger.info(f"connection---------- {conn}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                logger.info(f"----staff and profile details---- {result}")
                if result and len(result):
                    return result
    except Exception as ex:
        logger.error(f"---------ERROR in get_staff_and_profile_details--------: {ex}")
        logger.error(traceback.format_exc())


def get_entity_details(db_type, staff_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT entity.id,entity.name,entity.country FROM profile JOIN entity JOIN staff ON
                entity.name = profile.entity and entity.client_id = staff.client_id and staff.id = profile.employee_id
                WHERE profile.employee_id = %s
                """ % (
            staff_id
        )
        logger.info(f"----------get_entity_details sql------- {sql}")
        logger.info(f"connection---------- {conn}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                logger.info(f"----get_entity_details result---- {result}")
                if result and len(result):
                    return result
    except Exception as ex:
        logger.error(f"---------ERROR in get_entity_details--------: {ex}")
        logger.error(traceback.format_exc())


def get_currency_conversion(db_type, to_currency, date):
    try:
        logger.info(f"currency conversion input db -------- {to_currency}, {date}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                latest_cur_sql = (
                    "SELECT currency_rate, conversion_date FROM currency_conversion WHERE currency_code='"
                    + to_currency
                    + "' AND conversion_date = DATE("
                    + str(date)
                    + ") AND enable=1 LIMIT 1"
                )
                logger.info(f"latest currency sql ----- {latest_cur_sql}")
                cursor.execute(latest_cur_sql)
                latest_cur = cursor.fetchall()
                if len(latest_cur) == 0:
                    last_cur_sql = (
                        "SELECT currency_rate, conversion_date FROM currency_conversion WHERE currency_code='"
                        + to_currency
                        + "' AND enable=1 order by stamp_created desc LIMIT 1"
                    )
                    logger.info(f"last currency sql ----- {last_cur_sql}")
                    cursor.execute(last_cur_sql)
                    latest_cur = cursor.fetchall()
                    cursor.close()
                logger.info(f"currency result ------- {latest_cur}")
                logger.info(f"currency result ------- {latest_cur[0]}")
                return latest_cur[0]

    except Exception as ex:
        logger.error(f"ERROR: {ex}")


def get_multiple_currency_conversions(db_type, to_currencies, date):
    """
    Fetch foreign exchange rates for multiple currencies w.r.t INR
    :param db_type: app dbtype
    :param to_currencies: Currencies for which fx rate is fetched
    :param date: Latest date for which FX rate is fetched
    """
    try:
        logger.info(f"Currency conversion input: {to_currencies} and date: {date}")
        if isinstance(to_currencies, str):
            to_currencies = to_currencies.split(",")
        to_currencies = tuple(to_currencies) if len(to_currencies) > 1 else f'("{to_currencies[0]}")'

        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                latest_date_query = (
                    f"SELECT currency_code, currency_rate, conversion_date FROM currency_conversion WHERE "
                    f"currency_code in {to_currencies} AND conversion_date = DATE({str(date)}) AND enable=1"
                )
                logger.info(f"Latest date query is: {latest_date_query}")  # latest rate query is latest date query :P
                cursor.execute(latest_date_query)
                result = cursor.fetchall()
                if not result:
                    last_inserted_query = (
                        f"SELECT currency_code, currency_rate, conversion_date FROM currency_conversion "
                        f"WHERE currency_code in {to_currencies} AND enable=1 order by stamp_created desc"
                    )
                    logger.info(f"last inserted query is: {last_inserted_query}")
                    cursor.execute(last_inserted_query)
                    result = cursor.fetchall()
                    cursor.close()
                return result

    except Exception:
        logger.error(f"Error while fetching currency conversions. error: {traceback.format_exc()}")


def get_app_leg_uuid_data(db_type, uuid):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                sql = "SELECT * from all_trips WHERE leg_uuid='" + str(uuid) + "';"
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                return result[0]

    except Exception as ex:
        logger.error(f"ERROR fetching leg uuid info : {ex}")
        logger.error(traceback.format_exc())


def fetch_client_balance_details(db_type, client_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT balance, threshold_unit, threshold_amount FROM client_balance_threshold
                WHERE client_id = %s
                """ % (
            client_id
        )
        logger.info(f"----------fetch_client_balance_details------- {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                logger.info(f"----get_entity_details result---- {result}")
                if result and len(result):
                    return result
    except Exception as ex:
        logger.error(f"---------Error fetch_client_balance_details--------: {ex}")
        logger.error(traceback.format_exc())


def get_booking_automation_details(db_type, client_id, user_role, trip_owner):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT * FROM booking_automation_config
                WHERE client_id = %s
                """ % (
            client_id
        )
        logger.info(f"----------get_booking_automation_details------ {sql}, {client_id}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                logger.info(f"----get_booking_automation_details result---- {result}, {client_id}")
                if result and len(result):
                    if user_role == "staff" and result["group_override"] and result["group_override"] != "NA":
                        sql = """ SELECT gmap.status from `group_mapping` as gmap
                             INNER JOIN `groups` as grp on grp.id IN(%s) AND gmap.group_id = grp.id AND grp.status = 1
                             where gmap.status = 1 AND gmap.group_id IN (%s) and gmap.user_name = '%s' AND gmap.client_id = %s
                             """ % (
                            result["group_override"],
                            result["group_override"],
                            trip_owner,
                            client_id,
                        )
                        logger.info(f"group booking info sql------- {client_id}, {sql}")
                        cursor.execute(sql)
                        group_enable_result = cursor.fetchone()
                        if not group_enable_result and result["flight_booking"] == 1 and result["flight_self_client_domestic"] == 1:
                            result["flight_self_client_domestic"] = 0
                        if not group_enable_result and result["flight_booking"] == 1 and result["hotel_self_client_domestic"] == 1:
                            result["hotel_self_client_domestic"] = 0
                        if not group_enable_result and result["flight_booking"] == 1 and result["bus_self_client"] == 1:
                            result["bus_self_client"] = 0
                        if (
                            not group_enable_result
                            and result["flight_booking"] == 1
                            and result["flight_self_client_international"] == 1
                        ):
                            result["flight_self_client_international"] = 0
                        if (
                            not group_enable_result
                            and result["flight_booking"] == 1
                            and result["hotel_self_client_international"] == 1
                        ):
                            result["hotel_self_client_international"] = 0

                        if group_enable_result and group_enable_result["status"] == 1 and result["flight_booking"] == 1:
                            if result["flight_self_client_domestic"] != 0:
                                result["flight_self_client_domestic"] = 1
                            if result["hotel_self_client_domestic"] != 0:
                                result["hotel_self_client_domestic"] = 1
                            if result["bus_self_client"] != 0:
                                result["bus_self_client"] = 1
                            if result["flight_self_client_international"] != 0:
                                result["flight_self_client_international"] = 1
                            if result["hotel_self_client_international"] != 0:
                                result["hotel_self_client_international"] = 1
                        else:
                            result["flight_self_client_domestic"] = 0
                            result["hotel_self_client_domestic"] = 0
                            result["bus_self_client"] = 0
                            result["flight_self_client_international"] = 0
                            result["hotel_self_client_international"] = 0
                        return result
                    else:
                        return result
                else:
                    result = get_default_booking_config()
                    return result
    except Exception as ex:
        logger.error(f"---------Error get_booking_automation_details--------: {ex}, {client_id}")
        logger.error(traceback.format_exc())
        result = get_default_booking_config()
        return result


def get_default_booking_config():
    default_booking_config = {
        "group_override": 0,
        "enable_queue": 0,
        "flight_booking": 0,
        "flight_self_admin_domestic": 0,
        "bus_self_admin": 0,
        "flight_bookforothers_admin_domestic": 0,
        "flight_self_client_domestic": 0,
        "bus_self_client": 0,
        "flight_bookforothers_client_domestic": 0,
        "hotel_self_admin_domestic": 0,
        "hotel_bookforothers_admin_domestic": 0,
        "hotel_self_client_domestic": 0,
        "hotel_bookforothers_client_domestic": 0,
        "flight_self_admin_international": 0,
        "flight_bookforothers_admin_international": 0,
        "flight_self_client_international": 0,
        "flight_bookforothers_client_international": 0,
        "hotel_self_admin_international": 0,
        "hotel_bookforothers_admin_international": 0,
        "block_booking": 0,
        "blocked_by_payment": 0,
        "hotel_self_client_international": 0,
        "hotel_bookforothers_client_international": 0,
        "flight_vendor_wrapper": 0,
    }
    return default_booking_config


def get_client_details(db_type, client_id):
    """
    Desc : Fetch the client name from client table
    Input:
        db_type: master/slave db to connect
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT company_name,currency,payment_method FROM client where id=%d" % (client_id)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in get_client_details: {traceback.format_exc()}")


def get_country_details(country_code, db_type="app"):
    try:
        logger.info(f"-----get_country_details for country cod {country_code}------")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT * FROM country where internet='%s'" % (country_code)
        logger.info(f"----------sql for get_country_details {country_code}-----{sql}")
        logger.info(f"{sql} country details---------")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                if result:
                    return result
                else:
                    return False
    except Exception:
        logger.error(f"Error in get_country_details: {traceback.format_exc()}")


def get_all_country_details(db_type="app"):
    try:
        logger.info("-----get_all_country_details---")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT country,internet FROM country"
        logger.info(f"----------sql for get_all_country_details-----{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if result:
                    return result
                else:
                    return False
    except Exception:
        logger.error(f"Error in get_all_country_details: {traceback.format_exc()}")


def get_iata_details(iata_ids, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        # conn = MysqlConnector.connect_db(db_type)
        sql = f"SELECT * FROM iata_info where id IN {iata_ids}"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    return result
                else:
                    return False
    except Exception:
        logger.error(f"Error in get_country_details: {traceback.format_exc()}")


def get_country_code(country_names, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        # conn = MysqlConnector.connect_db(db_type)
        sql = f"SELECT * FROM country where country IN {country_names}"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if result:
                    return result
                else:
                    return False
    except Exception:
        logger.error(f"Error in get_country_details: {traceback.format_exc()}")


def get_client_plan(client_id, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "select name from plans pl join client_plan cp on cp.plan_id = pl.id where client_id=%d" % (client_id)
        logger.info("get_client_plan sql----------", sql)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                if result:
                    return result["name"]
                else:
                    return False
    except Exception as ex:
        logger.error(f"Error in get_client_plan: {traceback.format_exc()}")
        logger.error(f"ERROR: {ex}")


def update_trip_status(trip_id, status, db_type="app"):
    try:
        # This function used in flight/hotel consolidator and recommender to update trip budget pending and generated
        # Query will update only trip 2 and 4 so exist trip status should not be 8 or 9
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ UPDATE trip SET trip_status=%d WHERE trip_id='%s' and trip_status not in (4,8,9)""" % (status, trip_id)
        trip_base_sql = """ UPDATE trip_base SET status=%d WHERE trip_id='%s' and status not in (4,8,9)""" % (status, trip_id)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                cursor.execute(trip_base_sql)
                conn.commit()
                cursor.close()
                logger.info(f"Updated {trip_id} trip_status as {status}")
                return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def update_payment_mapper(itilite_order_id, status, is_booking_triggered, only_booking_trigger=False, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ UPDATE payment_mapper SET status='%s',is_booking_triggered=%d WHERE itilite_order_id='%s'""" % (
            status,
            is_booking_triggered,
            itilite_order_id,
        )
        if only_booking_trigger:
            sql = """ UPDATE payment_mapper SET is_booking_triggered=%d WHERE itilite_order_id='%s'""" % (
                is_booking_triggered,
                itilite_order_id,
            )
        logger.info(f"update_payment_mapper sql {sql}----------{itilite_order_id}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception as ex:
        logger.error(
            f"------------ERROR in update_payment_mapper for order id-{itilite_order_id}----{ex}",
            exc_info=True,
        )
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def update_trip_status_value(trip_id, status, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        # sql = """ UPDATE trip SET trip_status=%d WHERE trip_id='%s' and trip_status not in (4,8,9)""" % (
        sql = """ UPDATE trip SET trip_status=%d WHERE trip_id='%s'""" % (
            status,
            trip_id,
        )
        logger.info(f"sql result----------{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def update_trip_base_status(trip_id, status, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ UPDATE trip_base SET status=%d WHERE trip_id='%s'""" % (
            status,
            trip_id,
        )
        logger.info(f"update_trip_base_status sql-----trip id {trip_id}----{status}---{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def update_trip_status_code(status_code, trip_id, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT status_id from  all_trip_status Where  status_code='%s'
                """ % (
            status_code
        )
        logger.info(f"---------fetch status id sql-------{sql}")
        logger.info(f"connection---------- : {conn}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                logger.info(f"----update_trip_status_code----{trip_id}, {result}")
                if result and len(result):
                    logger.info(f"{result}==========result============")
                    status_id = result["status_id"]
                    sql = """ UPDATE all_trips SET status=%d WHERE trip_id='%s'""" % (
                        status_id,
                        trip_id,
                    )
                    logger.info(f"---------update_trip_status_code sql-------{sql}")
                    cursor.execute(sql)
                    conn.commit()
                    cursor.close()
                    return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def update_all_trip_status(status_code, trip_id, leg_uuid=None, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT status_id from  all_trip_status Where  status_code='%s'
                """ % (
            status_code
        )
        logger.info(f"---------fetch status id sql-------{sql}")
        logger.info(f"connection----------{conn}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                logger.info(f"----update_trip_status_code----{trip_id}, {result}")
                if result and len(result):
                    logger.info(f"{result}, result============")
                    status_id = result["status_id"]
                    if leg_uuid:
                        sql = """ update all_trips alt join trip_base tb on tb.id = alt.trip_base_id set alt.status=%d
                            where tb.trip_id='%s' and alt.leg_uuid='%s'""" % (
                            status_id,
                            trip_id,
                            leg_uuid,
                        )
                    else:
                        sql = """ update all_trips alt join trip_base tb on tb.id = alt.trip_base_id
                            set alt.status=%d where tb.trip_id='%s'""" % (
                            status_id,
                            trip_id,
                        )
                    logger.info(f"---------update_trip_status_code sql-------{sql}")
                    cursor.execute(sql)
                    conn.commit()
                    cursor.close()
                    return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def update_selected_option(trip_id, option_selected, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ UPDATE trip SET option_selected=%d WHERE trip_id='%s' """ % (
            option_selected,
            trip_id,
        )
        logger.info(f"sql for update_selected_option----------{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR in update_selected_option---------: {ex}", ex)
        logger.error(traceback.format_exc())


def get_threshold_check(db_type, client_id, entity_id, internal_level):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT * FROM threshold_check WHERE client_id=%d AND entity_id=%d AND internal_level='%s'""" % (
            client_id,
            entity_id,
            internal_level,
        )
        logger.info(f"get_threshold_check-------{sql}")
        with conn:
            logger.info(f"-------get_threshold_check sql---------{conn}, {sql}")
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                if not result:
                    sql = """SELECT * FROM threshold_check WHERE client_id=%d AND entity_id=%d AND internal_level='NA'""" % (
                        client_id,
                        entity_id,
                    )
                    cursor.execute(sql)
                    result = cursor.fetchone()
                    cursor.close()
                    return result
                else:
                    cursor.close()
                    return result
    except Exception as ex:
        logger.error(f"--------ERROR in get_threshold_check-----------: {ex}")
        logger.error(traceback.format_exc())


def update_highcost_reason(db_type, trip_id, highcost_reason):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ UPDATE trip SET high_cost_approval_empl_remarks='%s' WHERE trip_id='%s' """ % (highcost_reason, trip_id)
        logger.info(f"sql for update_highcost_reason----------{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR in update_highcost_reason---------: {ex}")


def update_details(db_type, table_name, column_name, update_value, where_column, where_value):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ UPDATE %s SET %s='%s' WHERE %s='%s' """ % (
            table_name,
            column_name,
            update_value,
            where_column,
            where_value,
        )
        logger.info(f"sql for update_details----------{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR in update_details {table_name}---------:{column_name},{update_value}, {ex}")


def update_trip_report(trip_id, report_type, user, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """insert into `trip_report` (trip_id, type, user,
                                  created_at, updated_at)
            values (%s, %s, %s, %s, %s)
        """
        logger.info(f"sql for update_trip_report----------{trip_id}, {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (trip_id, report_type, user, datetime.now(), datetime.now()))
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR in update_trip_report {trip_id}---------: {ex}")


def insert_payment_mapper(
    itilite_order_id,
    payment_request,
    payment_method,
    status,
    is_booking_triggered,
    is_requested,
    db_type="app",
):
    try:
        logger.info(f"------------insert payment mapper {payment_request['trip_id']}-----------{itilite_order_id}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """INSERT INTO `payment_mapper`(itilite_order_id,trip_id,payment_details,status,is_requested,is_booking_triggered,
            created_on,created_by,updated_by,card_type,is_pay_at_vendor_included,latest_fare_price_splitup,new_app) values
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
        logger.info(f"sql for insert payment mapper {payment_request['trip_id']}----------{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql,
                    (
                        itilite_order_id,
                        payment_request["actual_trip_id"],
                        json.dumps(payment_request),
                        status,
                        is_requested,
                        is_booking_triggered,
                        datetime.now(),
                        payment_request["user_name"],
                        payment_request["user_name"],
                        payment_method,
                        payment_request["is_pay_at_vendor_included"],
                        json.dumps(payment_request),
                        True,
                    ),
                )
                conn.commit()
                cursor.close()
                return "inserted Successfully"
    except Exception as ex:
        logger.error(
            f"ERROR in insert_payment_mapper {payment_request['trip_id']}---------: {ex}",
            exc_info=True,
        )


def get_city_with_idx(db_type, lat, lng, idx=2):
    """
    Desc : Fetch the list of cities wrt lat , lng
    Input:
        db_type: master/slave db to connect central  paymet_method =2 ,paybyvcard version=3, user card paymet_method=1
    """
    try:
        lat_idx = lat.index(".") + idx
        lng_idx = lng.index(".") + idx
        f_lat = lat[0:lat_idx]
        f_lng = lng[0:lng_idx]
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT DISTINCT City FROM cities WHERE Latitude LIKE '" + str(f_lat) + "%' AND Longitude LIKE '" + str(f_lng) + "%'"
        logger.info(f"get cities with lat,lang sql idx------- : {idx}")
        logger.info(f"get cities with lat,lang sql------- : {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                cities = []
                if len(result) != 0:
                    for city in result:
                        cities.append(city["City"])
                return cities
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def get_cities_with_lat_lng(db_type, lat, lng):
    try:
        cities = []
        cities = get_city_with_idx("app", lat, lng, 2)
        if cities is None or len(cities) == 0:
            cities = get_city_with_idx("app", lat, lng, 1)
        return cities
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def get_airport_details(db_type, airport_name):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT * FROM iata_info where airport_name LIKE %s"
        logger.info(f"iata_info sql-----------{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, ("%" + airport_name + "%",))
                # cursor.execute(sql)
                result = cursor.fetchall()
                logger.info(f"iata_info sql------result-----{sql , result}")
                cursor.close()
                if len(result) != 0:
                    return result[0]
                else:
                    return []
    except Exception:
        logger.error(f"Error in get_airport_details: {traceback.format_exc()}")


def get_membership_config(db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT * FROM membership_config"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                logger.info(f"-----------get_membership_config result---------{result}")
                if len(result) != 0:
                    membership_config_details = {}
                    for row in result:
                        membership_config_details[row["vendor"]] = row
                    logger.info(f"-----------membership_config_details result---------{membership_config_details}")
                    return membership_config_details
                else:
                    return {}
    except Exception:
        logger.error(f"Error in get_membership_config: {traceback.format_exc()}")


def fetch_client_details(db_type, client_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT * FROM client where id=%d" % (client_id)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                if result:
                    return result
                else:
                    return {}
    except Exception:
        logger.error(f"Error in fetch_client_details: {traceback.format_exc()}")


def check_eligible_queue(db_type, client_id):
    try:
        logger.info("entered into check_eligibility_queue")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                sql_query = "SELECT enable_reshop, payment_method, e.paybycard_version\
                      FROM `client` JOIN `env_config` `e` \
                    ON client.id = e.client_id WHERE id = {0}".format(
                    client_id
                )
                cursor.execute(sql_query)
                records = cursor.fetchall()
                cursor.close()
                result = records[0]
                return result

    except Exception:
        logger.error(f"exception in check_eligible_queue---------: {traceback.format_exc()}")
        return {}


def insert_queue_record(db_type, data):
    try:
        logger.info("entered into insert_queue_record")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                query = (
                    'INSERT INTO price_reshop (`client_id`, `staff_id`, `trip_id`, `vendor`, `gds_pnr`, `airline_pnr`,\
                    `origin`, `destination`, `leg_no`, `departure`, `meal`, `baggage`, `seat`) VALUES ("{0}", '
                    '"{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", "{8}", "{9}", "{10}", "{11}", "{12}")'.format(
                        data["client_id"],
                        data["staff_id"],
                        data["trip_id"],
                        data["vendor"],
                        data["gds_pnr"],
                        data["airline_pnr"],
                        str(data["origin"]),
                        str(data["destination"]),
                        data["leg_no"],
                        data["departure"],
                        data["meal"],
                        data["baggage"],
                        data["seat"],
                    )
                )

                cursor.execute(query)
                # result = cursor.fetchall()
                conn.commit()
                cursor.close()
                logger.info(f"cursor_last_row_id: {cursor.lastrowid}")
                return cursor.lastrowid
    except Exception:
        logger.error(f"exception in insert_queue_record---------: {traceback.format_exc()}")
        return {}


def update_queue_record(db_type, id, col, val):
    try:
        logger.info("entered into update_queue_record")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                sql_query = "UPDATE price_reshop SET {0} = {1} WHERE id = {2}".format(col, val, id)
                cursor.execute(sql_query)
                # result = cursor.fetchall()
                conn.commit()
                cursor.close()

    except Exception:
        logger.error(f"exception in update_queue_record---------: {traceback.format_exc()}")
        return {}


def update_hotel_budget_total(trip_id, budget_total, db_type="app"):
    try:
        logger.info(f"-------update_hotel_budget_total {trip_id}---------{budget_total}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """UPDATE trip SET trip_budget_total = trip_budget_total + %d, trip_budget_accomodation =
            trip_budget_accomodation + %d WHERE trip_id='%s'""" % (
            budget_total,
            budget_total,
            trip_id,
        )
        logger.info(f"--------update_hotel_budget_total hotel sql {sql}---------")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception:
        logger.error(f"exception in update_hotel_budget_total---------: {traceback.format_exc()}")


def update_travel_budget_total(trip_id, budget_total, db_type="app"):
    try:
        logger.info(f"-------update_travel_budget_total {trip_id}---------{budget_total}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """UPDATE trip SET trip_budget_total = trip_budget_total + %d, trip_budget_travel =
            trip_budget_travel + %d WHERE trip_id='%s'""" % (
            budget_total,
            budget_total,
            trip_id,
        )
        logger.info(f"--------update_travel_budget_total sql {sql}---------")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception:
        logger.error(f"exception in update_travel_budget_total---------: {traceback.format_exc()}")


def reset_trip_budget_to_beat(trip_id, db_type="app"):
    try:
        logger.info(f"-------reset_trip_budget_to_beat---------{trip_id}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """UPDATE trip SET trip_budget_total = 0, trip_budget_travel = 0, trip_budget_accomodation = 0
            WHERE trip_id='%s'""" % (
            trip_id
        )
        logger.info(f"--------reset_trip_budget_to_beat sql {sql}---------")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception:
        logger.error(f"exception in reset_trip_budget_to_beat---------: {traceback.format_exc()}")


def insert_membership_booking_logger(membership_log_data, db_type):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        data = membership_log_data
        sql = """insert into `membership_booking_logger` (trip_id, leg_id, vendor,
                                  mode, membership_data, status)
            values (%s, %s, %s, %s, %s, %s)
        """
        logger.info(f"-----------insert_membership_booking_logger {membership_log_data}----------{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    sql, (data["trip_id"], data["leg_id"], data["vendor"], data["mode"], data["membership_data"], data["status"])
                )
                conn.commit()
                return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR in update_trip_report {data['trip_id']}---------: {ex}")
        logger.error(
            f"-----------ERROR in insert_membership_booking_logger {membership_log_data}----------{str(traceback.format_exc())}"
        )


def get_trip_details(db_type, trip_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT client_id, trip_status, cost_approval_status, high_cost_approval_status, option_selected,
            is_travel, is_accomodation, staff_id, trip_id, no_of_rooms_count, overall_approval_trip_type,
            overall_mis_trip_type, personal_booking, parent_client_id,trip_requester, trip_type,no_of_adults_count,
            no_of_child_count,no_of_infant_count from trip WHERE trip_id ='%s'""" % (
            trip_id
        )
        logger.info(f"--------get_trip_details sql {trip_id}-------{sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                logger.info(f"--------trip details result {trip_id}------{result}")
                if len(result) != 0:
                    return result
    except Exception as ex:
        logger.error(f"------------ERROR in get_trip_details {trip_id}---------{ex}", exc_info=True)


def get_all_completed_trips(travel_date_from, accomodation_date_from, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = f"""
                SELECT `travel_date_from`, `trip_id`, `trip_status`, `travel_date_to`, `mode`, `accomodation_date_from`,
                `is_travel`, `is_accomodation` FROM trip
                WHERE ((is_travel = {True} AND travel_date_from < '{travel_date_from}')
                OR (is_accomodation = {True} AND accomodation_date_from < '{accomodation_date_from}'))
            """
        logger.info(f"Get all Completed Trips ---> {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    logger.info(f"Successfully fetched all completed trips, Count : {len(result)}")
                    return result
    except Exception as ex:
        logger.error(f"------------ERROR in get_trip_details {ex}", exc_info=True)


def get_available_unused_credit(db_type, trip_id, unused_credit_ids=[]):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        query = (
            f"SELECT id FROM unused_tickets_info WHERE id in ({','.join(map(str, unused_credit_ids))}) AND "
            f"(status = 0 OR (status = 1 and applied_trip = '{trip_id}'));"
        )
        logger.info(f"--------get available unused credit sql {unused_credit_ids}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                cursor.close()
                logger.info("--------Updated applied unused credit details")
                if result:
                    result = [list(d.values())[0] for d in result]
                return result
    except Exception as ex:
        logger.error(f"------------ERROR in get_unused_ticket {ex}", exc_info=True)
        return []


def update_applied_unused_credit(db_type, trip_id, applied_unused_credit_ids=[]):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        query = f"UPDATE unused_tickets_info SET status = 0, applied_trip = NULL " f"WHERE applied_trip = '{trip_id}';"
        query2 = None
        if applied_unused_credit_ids:
            query2 = (
                f"UPDATE unused_tickets_info SET status = 1, applied_trip = '{trip_id}' WHERE id in "
                f"({','.join(map(str, applied_unused_credit_ids))}); "
            )

        logger.info(
            f"--------update applied unused credit sql {applied_unused_credit_ids} query - {query} query2 {query2}",
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                if query2:
                    cursor.execute(query2)
                conn.commit()
                cursor.close()
                logger.info("--------available unused credit details result")
    except Exception as ex:
        logger.error(f"------------ERROR in update unused_ticket {ex}", exc_info=True)


def update_airport_city(iata_city_list, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "CREATE TEMPORARY TABLE temp_airport (iata VARCHAR(3),city VARCHAR(255))"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                insert_query = "INSERT INTO temp_airport (iata, city) VALUES (%s, %s)"
                cursor.executemany(insert_query, iata_city_list)
                update_query = "UPDATE Airport AS a JOIN temp_airport AS ta ON a.iata = ta.iata SET a.city = ta.city"
                cursor.execute(update_query)
                drop_query = "DROP TEMPORARY TABLE temp_airport"
                cursor.execute(drop_query)
                conn.commit()
                cursor.close()
                return "Update Successfully"
    except Exception:
        logger.error(f"---------Error in update_airport_city-------: {traceback.format_exc()}")


def get_gst_entity_id_from_custom_dimension(db_type, client_id, trip_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = f"""SELECT tcd.*, ccd.name, ccd.type, ccd.id as ccdId, gam.abstraction, gam.client_id, gam.entity_id
        FROM trip_custom_dimensions AS tcd
        left join client_custom_dimensions AS ccd on ccd.id = tcd.custom_dimension_id
        left join gst_abstraction_mappings AS gam ON gam.entity_id = tcd.value
        where ccd.client_id = {client_id} AND ccd.type = 'customizeGst' AND tcd.trip_id = '{trip_id}'"""
        logger.info(f"--------get_gst_entity_id_from_custom_dimension sql - {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception as ex:
        logger.error(f"---------ERROR in get_gst_entity_id_from_custom_dimension---{ex}----: {traceback.format_exc()}")


def get_hotel_gst_details(db_type, client_id, entity_id, states):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        filter_cond = f"""(state in ("{states}") or is_default = 1)""" if states else " is_default = 1 "
        sql = f"SELECT * FROM client_gst WHERE client_id = {client_id} and entity_id \
            = {entity_id} and {filter_cond} order by is_default asc limit 1"
        logger.info(f"--------get_hotel_gst_details sql - {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result[0]
                else:
                    return {}
    except Exception as ex:
        logger.error(f"---------ERROR in get_hotel_gst_details--{ex}-----: {traceback.format_exc()}")
        return {}


def find_region(db_type, city, country):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = f"""select st.region from country cy
                left join cities ct on ct.countryID = cy.countryid
                left join states st on st.regionid = ct.RegionID
                where cy.country="{country}" and ct.City = "{city}"
                """
        logger.info(f"--------find_region sql - {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result[0]["region"]
                else:
                    return ""
    except Exception as ex:
        logger.error(f"---------ERROR in find_region--{ex}-----: {traceback.format_exc()}")
        return ""


def get_client_origin_based_gst_details(db_type, client_id, staff_id, city, country):
    try:
        region = find_region(db_type, city, country)
        sql = f"""SELECT pf.username, e.name, gst.*
                FROM staff st
                LEFT JOIN profile pf ON pf.username = st.username
                LEFT JOIN entity e ON e.name = pf.entity
                AND e.client_id = st.client_id
                LEFT JOIN gst_details gst ON gst.client_id = st.client_id
                WHERE st.id = {staff_id}
                AND st.client_id = {client_id}
                AND if(e.name IS NULL OR e.name ="",
                        ((gst.entity_id = 0 AND gst.state_gstin_registration = "{region}")\
                              OR (gst.entity_id = e.id AND gst.is_default = 1)),
                        ((gst.entity_id = e.id AND gst.state_gstin_registration = "{region}")\
                              OR (gst.entity_id = e.id AND gst.is_default = 1))
                )
                ORDER BY gst.is_default ASC
                LIMIT 1"""
        logger.info(f"--------get_client_origin_based_gst_details sql - {sql}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result[0]
                else:
                    return {}
    except Exception as ex:
        logger.error(f"---------ERROR in get_client_origin_based_gst_details---{ex}----: {traceback.format_exc()}")
        return {}


def get_gst_detail_by_entity_id(db_type, client_id, entity_id, city, country):
    try:
        region = find_region(db_type, city, country)
        sql = f"""SELECT e.name, gst.*
                FROM entity e
                LEFT JOIN gst_details gst ON gst.client_id = {client_id}
                WHERE e.id = {entity_id}
                AND e.client_id = {client_id}
                AND if(e.name IS NULL OR e.name ="",
                    ((gst.entity_id = 0 AND gst.state_gstin_registration = "{region}")\
                          OR (gst.entity_id = e.id AND gst.is_default = 1)),
                    ((gst.entity_id = e.id AND gst.state_gstin_registration = "{region}")\
                          OR (gst.entity_id = e.id AND gst.is_default = 1))
                )
                ORDER BY gst.is_default ASC
                LIMIT 1"""
        logger.info(f"--------get_gst_detail_by_entity_id sql - {sql}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result[0]
                else:
                    return {}
    except Exception as ex:
        logger.error(f"---------ERROR in get_gst_detail_by_entity_id----{ex}---: {traceback.format_exc()}")
        return {}


def get_flight_personal_booking_gst(db_type, client_id, city, country):
    try:
        region = find_region(db_type, city, country)
        sql = f"""select gst.* from gst_details gst
                where gst.entity_id=0 and gst.client_id = "{client_id}"
                AND (gst.state_gstin_registration = "{region}" OR gst.is_default=1)
                order by gst.is_default asc
                limit 1"""
        logger.info(f"--------get_flight_personal_booking_gst sql - {sql}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result[0]
                else:
                    return {}
    except Exception as ex:
        logger.error(f"---------ERROR in get_flight_personal_booking_gst---{ex}----: {traceback.format_exc()}")
        return {}


def insert_single_record(db_type, table, kwargs: dict):
    if kwargs:
        try:
            placeholder = ", ".join(["%s"] * len(kwargs))
            keys = kwargs.keys()
            key_list = ["`" + x + "`" for x in keys]
            columns = ",".join(key_list)
            values = placeholder
            query = f"insert into `{table}` ({columns}) values ({values});"
            logger.info(f"insert_single_record--sql-------: {query}")
            conn = DatabaseConnection.get_instance(db_type).get_connection()
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, list(kwargs.values()))
                    conn.commit()
                    cursor.close()
                    logger.info(f"cursor_last_row_id: {cursor.lastrowid}")
                    return cursor.lastrowid
        except Exception as e:
            logger.error(f"exception in insert_single_record----{e}-----: {traceback.format_exc()}")
    return None


def fetch_client_gst_details(db_type, client_id):
    try:
        sql = f"""SELECT distinct gd.gst_number, e.name, gd.state_gstin_registration\
              as 'state', gd.company_name, gd.office_address, gd.email_id, gd.contact_no,
        gd.pan_no, gd.client_id, gd.entity_id FROM `gst_details` gd inner join entity\
              e on e.id=gd.entity_id WHERE gd.client_id = {client_id}"""
        logger.info(f"--------fetch_client_gst_details sql - {sql}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception as ex:
        logger.error(f"---------ERROR in fetch_client_gst_details----{ex}---: {traceback.format_exc()}")
        return []


def check_service_fees_voucher_attached(trip_id, db_type="app"):
    result = {}
    try:
        logger.info("------------check_service_fees_voucher_attached---------%s", trip_id)
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                sql_query = (
                    f"""SELECT * from uploaded_only_vouchers where trip_id = '{trip_id}' and leg_id = 'trip_service_fee_voucher'"""
                )
                logger.info("-------sql_query check_service_fees_voucher_attached %s-----%s", sql_query, trip_id)
                cursor.execute(sql_query)
                result = cursor.fetchone()
                if not result:
                    sql_query = f"""SELECT * from booking_log where trip_id = '{trip_id}' and leg_id = 'trip_service_fee_voucher'"""
                    logger.info("-------sql_query check_service_fees_voucher_attached %s-----%s", sql_query, trip_id)
                    cursor.execute(sql_query)
                    result = cursor.fetchone()
                cursor.close()
    except Exception:
        logger.error(f"ERROR in check_service_fees_voucher_attached-----{trip_id}----: {traceback.format_exc()}")
    finally:
        logger.info("-------check_service_fees_voucher_attached result %s------%s", trip_id, result)
        return result


def get_booking_data(booking_id, db_type="app"):
    result = {}
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                sql_query = f"""SELECT * from booking_data where id = '{booking_id}'"""
                cursor.execute(sql_query)
                result = cursor.fetchone()
                cursor.close()
    except Exception:
        logger.error(f"ERROR in get_booking_data-----{booking_id}----: {traceback.format_exc()}")
    finally:
        return result


def update_all_trip_status_with_booking_id(status_id, booking_id, db_type="app"):
    try:
        if not booking_id:
            return
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT id, all_trip_leg_id from  booking_data where id='%s'
                """ % (
            booking_id
        )
        logger.info(f"---------fetch status id sql-------{sql}")
        logger.info(f"connection---------- : {conn}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                if result and len(result):
                    logger.info(f"{result}==========result============")
                    all_trip_leg_id = result["all_trip_leg_id"]
                    sql = """ UPDATE all_trips SET status=%d WHERE id='%s'""" % (
                        status_id,
                        all_trip_leg_id,
                    )
                    logger.info(f"---------update_trip_status_code sql-------{sql}")
                    cursor.execute(sql)
                    conn.commit()
                    cursor.close()
                    return "Update Successfully"
    except Exception as ex:
        logger.error(f"ERROR: {ex}")
        logger.error(traceback.format_exc())


def get_country_name_with_iata_code(iata_code, db_type="app"):
    result = {}
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn:
            with conn.cursor() as cursor:
                sql_query = f"""SELECT country FROM iata_map WHERE iata='{iata_code}'"""
                cursor.execute(sql_query)
                result = cursor.fetchone()
                cursor.close()
    except Exception as e:
        logger.error(f"Exception while retriving country code with iata code : {e}, {traceback.format_exc()}")
    finally:
        return result


def get_city_name(db_type, lat, lng):
    """
    Fetch city name from mysql database.
    """
    try:
        if not lat or not lng:
            return []

        query_start_time = datetime.now()
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        query = f"""SELECT City as name FROM cities WHERE cities.Latitude LIKE '{lat}%' AND cities.Longitude LIKE '{lng}%' """
        logger.info(f"List hotel city name query: {query}")
        hotel_cities = []
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                hotel_cities = cursor.fetchall()
        delta = datetime.now() - query_start_time
        logger.info(f"Time taken for fetch hotel cities from mysqldb is: {delta.total_seconds()}")
        return hotel_cities
    except Exception as e:
        logger.error(f"Error while fetching get_city_name: {lat} and {lng} from mysql database. error: {traceback.format_exc()}")
        raise e


def get_trip_info_for_approver(trip_id, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = (
            "SELECT trip.travel_title, trip.trip_status, trip.trip_state, trip.travel_instruction, "
            "trip_status_new.admin_status, trip_status_new.client_status, trip.approved_rejected_by, journey_from_date "
            "FROM trip JOIN trip_status_new ON trip_status_new.status_id = trip.trip_status "
            "WHERE trip_id = '%s'" % (trip_id)
        )

        logger.info(f"get_trip_info------- {sql}")

        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                logger.info(f"--------trip info for approver result------ {result}")
                if len(result) != 0:
                    return result
    except Exception as ex:
        logger.error(f"Error while executing get_trip_info_for_approver:  {ex}")
        logger.error(traceback.format_exc())


def get_custom_dimensions(trip_id, db_type="app"):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """
            SELECT trip_custom_dimensions.value, client_custom_dimensions.name
            FROM trip_custom_dimensions
            INNER JOIN client_custom_dimensions ON trip_custom_dimensions.custom_dimension_id = client_custom_dimensions.id
            WHERE trip_custom_dimensions.trip_id = '%s'
        """ % (
            trip_id
        )
        logger.info(f"get_custom_dimensions------- {sql}")

        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                logger.info(f"--------custom dimension result------ {result}")
                if len(result) != 0:
                    return result

    except Exception as ex:
        logger.error(f"Error while executing get_custom_dimensions:  {ex}")
        logger.error(traceback.format_exc())


def get_company_configuration_for_approval(db_type, client_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = (
            "SELECT enable_cost_approval_reason_config, enable_cost_rejection_reason_config, "
            "enable_high_cost_approval_reason_config, enable_high_cost_rejection_reason_config, react_cost_approval "
            "FROM env_config WHERE env_config.client_id = %d" % int(client_id)
        )

        logger.info(f"get_company_configuration_for_approval------- {sql}")
        with conn:
            logger.info(f"-------sql-get_company_configuration_for_approval-------- {conn}")
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                if len(result) != 0:
                    logger.info(f"----------get_company_configuration_for_approval-------result {result}")
                    return result
    except Exception as ex:
        logger.error(f"--------ERROR in get_company_configuration_for_approval-----------: {ex}")
        logger.error(traceback.format_exc())


def get_approval_token_for_email(email, trip_id, db_type=APP_DB):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = (
            f"select sr.trip_id, sata.token_id from selected_approval_tier_approvers as sata join selected_rule "
            f"as sr on sata.selected_rule_id_id=sr.id where sr.trip_id='{trip_id}' "
            f"and sata.approver_email='{email}'"
        )

        logger.info(f"get_approval_token_for_email------- {sql}")
        with conn:
            logger.info(f"-------sql-get_approval_token_for_email-------- {conn}")
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                cursor.close()
                if len(result) != 0:
                    logger.info(f"----------get_approval_token_for_email-------result {result}")
                    return result
    except Exception as ex:
        logger.error(f"--------ERROR in get_approval_token_for_email-----------: {ex} {traceback.format_exc()}")


def fetch_trip_exp_time(selected_rule_id, db_type="app"):
    result = []
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT id, trip_id, exp_date_time FROM selected_rule WHERE id = '%s' """ % (selected_rule_id)
        logger.info(f"fetch_trip_exp_time sql result---------- {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
    except Exception:
        logger.error(f"Error in fetch trip exp time====>{traceback.format_exc()}")
    return result
