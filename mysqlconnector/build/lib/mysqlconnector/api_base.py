import base64
import json
import os
import traceback
from datetime import datetime

import pyaes
from mysqlconnector.connector import DatabaseConnection, MysqlConnector
from opensearchlogger.logging import logger

API_DB = "api_slave" if os.environ.get("USE_API_SLAVE_DB") == "1" else "api"


def get_hotel_fre(db_type, client_id, travel_type, ogn_country):
    """
    Desc : Fetch the FRE configuration of hotels
    Input:
        db_type: master/slave db to connect
        client_id : reference client id
        travel_type : domestic/international
        ogn_country : country of hotel location
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT
            vm.vendor_id,
            vm.name,
            vm.response_type,
            vm.max_stay,
            vm.max_room,
            vm.max_pax,
            cvwdm.cvwdm_id,
            cwm.cwm_id,
            vw.wrapper,
            cwm.trip_orign_country,
            cvwdm.detail_id,
            cvwdm.markup_id,
            cvwdm.commision_id,
            if((cvwdm.currency='NA' or cvwdm.currency=''),'USD',cvwdm.currency) as currency,
            vhd.property_id,
            vhd.uname,
            AES_DECRYPT(vhd.password,'%s') AS password,
            vhd.end_point,
            vhd.end_point_1,
            vhd.display_name,
            vhd.token_member_id,
            hmd.markup_type,
            hmd.markup_value,
            hdm.dynamic_markup_policy
            FROM client_wrapper_mapping as cwm
            LEFT JOIN client_vendor_wrapper_detail_mapping as cvwdm ON 1=1
            LEFT JOIN vendor_wrapper as vw ON vendor_wrapper_id=cvwdm.wrapper_id
            LEFT JOIN vendor_master as vm ON vm.vendor_id=vw.vendor_id
            LEFT JOIN vendor_hotel_detail vhd ON vhd.hotel_detail_id=cvwdm.detail_id
            LEFT JOIN hotel_markup_detail hmd ON hmd.markup_id=cvwdm.markup_id
            LEFT JOIN hotel_dynamic_markup hdm ON (hdm.markup_id=cvwdm.markup_id or hdm.dynamic_markup_id = hmd.dynamic_markup_id)
            AND hmd.cvwdm_id=cvwdm.cvwdm_id
            WHERE find_in_set(cvwdm.cvwdm_id,cwm.cvwdm_ids)
            AND cwm.client_id=%d
            AND cwm.mode='%s'
            AND cwm.travel_type='%s'
            AND cwm.trip_orign_country='%s'""" % (
            os.environ["SALT_KEY"],
            client_id,
            "hotel",
            travel_type,
            ogn_country,
        )

        json_conn = []
        xml_conn = []
        itilite_conn = []
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    for res in result:
                        if res["uname"] is not None:
                            res["uname"] = aes_encryption_data(res["uname"])
                        if res["password"] is not None:
                            res["password"] = aes_encryption_data(res["password"])
                        if res["property_id"] is not None:
                            res["property_id"] = aes_encryption_data(res["property_id"])
                        if res["dynamic_markup_policy"] is not None:
                            res["dynamic_markup_policy"] = json.loads(res["dynamic_markup_policy"])
                    logger.info(f"res---->{result}")
                    json_conn = list(filter(lambda d: d["response_type"] == "json", result))
                    xml_conn = list(filter(lambda d: d["response_type"] == "xml", result))
                    itilite_conn = list(filter(lambda d: d["response_type"] == "itilite", result))

                result = {
                    "json_connector": json_conn,
                    "xml_connector": xml_conn,
                    "itilite_connector": itilite_conn,
                }
                logger.info(f"result----------- {result}")
                return {
                    "xml_connector": xml_conn,
                    "json_connector": json_conn,
                    "itilite_connector": itilite_conn,
                }

    except Exception as ex:
        logger.error(f"ERROR:  {ex}")
        logger.error(traceback.format_exc())
    # finally:
    #     conn.close()


def get_flight_freconfig_bycvdm_id(db_type, cvwmd_id):
    """
    Desc : Fetch the flight Fre config by cvwmd_id
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """select cvwdm.detail_id ,vfd.vendor_id,vm.name as vendor_name,vfd.terminal_or_client_id as ref_id,
        AES_DECRYPT(vfd.password,'%s') as api_key,vfd.uname as uname,
        vfd.end_point as url from client_vendor_wrapper_detail_mapping cvwdm
        inner join vendor_flight_detail  vfd  on vfd.flight_detail_id = cvwdm.detail_id
        Inner Join vendor_master vm on vm.vendor_id = vfd.vendor_id
        where cvwdm.cvwdm_id = '%s'""" % (
            os.environ["SALT_KEY"],
            cvwmd_id,
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                freconfig = []
                for fre_result in result:
                    freconfig_result = {
                        "uname": fre_result["uname"],
                        "api_key": fre_result["api_key"],
                        "url": fre_result["url"],
                        "ref_id": fre_result["ref_id"],
                        "vendor_name": fre_result["vendor_name"],
                    }
                freconfig.append(freconfig_result)
                return freconfig[0]
    except Exception:
        logger.error(f"Exception in get_flight_freconfig_bycvdm_id: {traceback.format_exc()}")


def get_flight_fre(db_type, client_id, travel_type, ogn_country):
    """
    Desc : Fetch the FRE configuration of flight
    Input:
        db_type: master/slave db to connect
        client_id : reference client id
        travel_type : domestic/international
        ogn_country : sector's origin country
    """
    try:
        # conn = DatabaseConnection.get_instance(db_type).get_connection()
        conn = MysqlConnector.connect_db(db_type)
        sql = """SELECT
            cvwdm.cvwdm_id,
            vm.name,
            vw.wrapper,
            vm.response_type,
            vm.max_pax,
            cvwdm.detail_id,
            cvwdm.deal_codes,
            JSON_ARRAYAGG(JSON_OBJECT("deal_id",cvwd.deal_id,"airline_code",
            cvwd.airline_code, "promo_codes",
            cvwd.promo_codes,"account_codes",
            cvwd.account_codes)) as deal_code,
            cvwdm.search_refundable,
            cvwdm.preference_order as connection_priority,
            cvwdm.restrict_airlines,
            cwm.fare_preference_group_id,
            cwm.refundable,
            cwm.price_diff,
            cwm.window_break_hours,
            cwm.expanded_window_break_hours,
            cwm.default_preference_group_id,
            cwm.fixed_window_break_hours,
            cvwdm.markup_id,
            fmd.markup_value,
            fmd.markup_type,
            if((cvwdm.currency='NA' or cvwdm.currency=''),'USD',cvwdm.currency) as currency,
            cwm.travel_type,
            vw.v2_wrapper,
            cwm.trip_orign_country,
            cwm.cwm_id,
            vfd.vendor_id,
            vfd.terminal_or_client_id,
            vfd.uname,AES_DECRYPT(vfd.password,'%s') as password,
            vfd.end_point,
            vfd.end_point_1,
            vfd.token_agency_id,
            vfd.token_member_id,
            vfd.other_details,
            vfd.primary,
            vfd.secondary
            FROM client_wrapper_mapping as cwm
            LEFT JOIN client_vendor_wrapper_detail_mapping as cvwdm on 1 = 1 AND find_in_set(cvwdm.cvwdm_id,cwm.cvwdm_ids)
            LEFT JOIN vendor_wrapper as vw on vw.vendor_wrapper_id = cvwdm.wrapper_id
            LEFT JOIN vendor_master as vm on vm.vendor_id = vw.vendor_id
            LEFT JOIN vendor_flight_detail vfd ON vfd.flight_detail_id=cvwdm.detail_id
            LEFT JOIN flight_markup_detail fmd ON fmd.markup_id=cvwdm.markup_id
            LEFT JOIN client_vendor_wrapper_deals cvwd ON cvwd.cvwdm_id=cvwdm.cvwdm_id
            WHERE cwm.client_id =%d
            AND cwm.mode = '%s'
            AND cwm.travel_type = '%s'
            AND cwm.trip_orign_country = '%s'
            group by cvwdm.cvwdm_id""" % (
            os.environ["SALT_KEY"],
            client_id,
            "flight",
            travel_type,
            ogn_country,
        )
        json_conn = []
        xml_conn = []
        fare_preferences = []
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    for res in result:
                        fare_preferences = get_fare_preference(db_type, res["fare_preference_group_id"])
                        if res["uname"] is not None:
                            res["uname"] = aes_encryption_data(res["uname"])
                        if res["password"] is not None:
                            res["password"] = aes_encryption_data(res["password"])
                        res["fare_preference_group"] = fare_preferences
                    json_conn = list(filter(lambda d: d["response_type"] == "json", result))
                    xml_conn = list(filter(lambda d: d["response_type"] == "xml", result))
                return {"json_connector": json_conn, "xml_connector": xml_conn}

    except Exception:
        logger.error(f"Error in get_flight_fre {traceback.format_exc()}")
    # finally:
    #     conn.close()


def aes_encryption_data(original_data):
    try:
        AES_KEY = os.environ["AES_KEY"]
        # key must be bytes, so we convert it
        key = AES_KEY.encode("utf-8")
        aes = pyaes.AESModeOfOperationCTR(key)
        encrypted_data = aes.encrypt(original_data)
        encrypted_string = base64.b64encode(encrypted_data).decode("utf-8")
        # show the encrypted data
        logger.info(f"Encrypted_data--->{encrypted_string}")
        return encrypted_string
    except Exception as ex:
        logger.error(f"Error in aes_encryption_data : {traceback.format_exc()}")
        raise ex


def get_fare_preference(db_type, pref_group_id):
    conn = MysqlConnector.connect_db(db_type)
    sql = (
        "SELECT fare_type,preference_order as fare_priority,x_type_id,x_value FROM fare_preference WHERE group_id = '"
        + str(pref_group_id)
        + "'"
    )
    logger.info(f"sql fare pref -----{sql}")
    farePreferences = []
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            for fare_preference in result:
                preference = {
                    "fare": fare_preference["fare_type"],
                    "priority": fare_preference["fare_priority"],
                    "x_type": fare_preference["x_type_id"],
                    "x_value": fare_preference["x_value"],
                }
                farePreferences.append(preference)
    logger.info(f"fare pref output---- {farePreferences}")
    return farePreferences


def get_client_wrapper(db_type, client_id):
    conn = DatabaseConnection.get_instance(db_type).get_connection()
    sql = (
        "SELECT window_break_hours, expanded_window_break_hours, remove_flight_in_duration_hours, mode, "
        "travel_type, trip_orign_country FROM client_wrapper_mapping where client_id=" + str(client_id)
    )
    logger.info(f"sql get_client_wrapper ----- {sql}")
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
            cursor.close()
            if len(result) != 0:
                logger.info(f"sql get_client_wrapper---- {result}")
                return result


def getMergingPreferrenceGroupNew(db_type, clientId, cwm_id):
    conn = DatabaseConnection.get_instance(db_type).get_connection()
    try:
        vendorPreferrenceQuery = (
            "select group_concat(cvwdm.cvwdm_id ORDER BY cvwdm.preference_order) as vendor_priority from "
            "`client_wrapper_mapping` as `cwm` left join `client_vendor_wrapper_detail_mapping` as `cvwdm` on 1 = 1 AND "
            "find_in_set(cvwdm.cvwdm_id,cwm.cvwdm_ids) where `cwm`.`client_id` ='"
            + str(clientId)
            + "' and `cwm`.`cwm_id` = '"
            + str(cwm_id)
            + "' and cvwdm.preference_order != 0 GROUP by cvwdm.preference_order order by cvwdm.preference_order asc"
        )
        with conn.cursor() as cursor:
            cursor.execute(vendorPreferrenceQuery)
        vendorPreferrenceData = []
        for record in vendorPreferrenceQuery:
            vendorPreferrenceData.append(record[0])

        farePreferrenceQuery = (
            "SELECT fp.preference_order FROM client_wrapper_mapping cwm inner join fare_preference fp on fp.group_id = "
            "cwm.fare_preference_group_id WHERE cwm.client_id = "
            + str(clientId)
            + " and cwm.cwm_id = '"
            + str(cwm_id)
            + "' and fp.preference_order != 0 ORDER BY fp.preference_order"
        )
        with conn.cursor() as cursor:
            cursor.execute(farePreferrenceQuery)
        farePreferrenceData = []
        for record in farePreferrenceQuery:
            farePreferrenceData.append(record[0])

        defaultVendorPreferrenceQuery = (
            "select cvwdm.cvwdm_id as default_vendor_preference from `client_wrapper_mapping` as "
            "`cwm` left join `client_vendor_wrapper_detail_mapping` as `cvwdm` on 1 = 1 "
            "AND find_in_set(cvwdm.cvwdm_id,cwm.cvwdm_ids) where `cwm`.`client_id` ='"
            + str(clientId)
            + "' and `cwm`.`cwm_id` = '"
            + str(cwm_id)
            + "' order by cvwdm.deffault_preference_order asc"
        )
        with conn.cursor() as cursor:
            cursor.execute(defaultVendorPreferrenceQuery)
        defaultVendorPreferrenceData = []
        for record in defaultVendorPreferrenceQuery:
            defaultVendorPreferrenceData.append(str(record[0]))

        defaultFarePreferrenceQuery = (
            "SELECT fp.fare_type FROM client_wrapper_mapping cwm inner join fare_preference fp on fp.group_id = "
            "cwm.default_preference_group_id WHERE cwm.client_id = "
            + str(clientId)
            + " and cwm.cwm_id = '"
            + str(cwm_id)
            + "' ORDER BY fp.preference_order"
        )
        with conn.cursor() as cursor:
            cursor.execute(defaultFarePreferrenceQuery)
        defaultFarePreferrenceData = []
        for record in defaultFarePreferrenceQuery:
            defaultFarePreferrenceData.append(record[0])

        group = {
            "vendor_priority": vendorPreferrenceData,
            "fare_preference": farePreferrenceData,
            "default_vendor_preference": defaultVendorPreferrenceData,
            "default_fare_preference": defaultFarePreferrenceData,
        }

        return group
    finally:
        conn.close()


def get_hotel_fre_by_cvdwm_id(db_type, cvwdm_id):
    """
    Desc : Fetch the FRE configuration of hotels
    Input:
        db_type: master/slave db to connect
        cvwdm_id: cvdwm_id to fetch fre config
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """SELECT
        vm.vendor_id,
        vm.name,
        cvwdm.cvwdm_id,
        vw.wrapper,
        cvwdm.detail_id,
        cvwdm.markup_id,
        cvwdm.commision_id,
        cvwdm.currency,
        vhd.property_id,
        vhd.uname,
        AES_DECRYPT(vhd.password, '%s') AS password,
        vhd.end_point,
        vhd.display_name,
        vhd.token_member_id,
        hmd.markup_type,
        hmd.markup_value
        FROM client_vendor_wrapper_detail_mapping cvwdm
        JOIN vendor_wrapper as vw ON vendor_wrapper_id=cvwdm.wrapper_id
        JOIN vendor_master as vm ON vm.vendor_id=vw.vendor_id
        JOIN vendor_hotel_detail vhd ON vhd.hotel_detail_id=cvwdm.detail_id
        LEFT JOIN hotel_markup_detail hmd ON hmd.markup_id=cvwdm.markup_id
        AND hmd.cvwdm_id=cvwdm.cvwdm_id
        WHERE cvwdm.cvwdm_id=%d
        """ % (
            os.environ["SALT_KEY"],
            cvwdm_id,
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()

                logger.info(f"result----------- {result}")
                return result

    except Exception as ex:
        logger.error(f"ERROR:  {ex}")
        logger.error(traceback.format_exc())


def get_seat_api_details(db_type, v_name):
    """
    Desc : Fetch the Seat api details by vendor name
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "select vendor,api_key,end_point,allowed_vendors from seat_vendor_details where `vendor`='" + str(v_name) + "'limit 1"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                cursor.close()
                logger.info(f"*get_seat_api_details*result**************** {result}")
                seat_api = []
                for seat_result in result:
                    setaconfig_result = {
                        "api_key": seat_result["api_key"],
                        "end_point": seat_result["end_point"],
                        "vendor": seat_result["vendor"],
                        "allowed_vendors": seat_result["allowed_vendors"],
                    }
                    seat_api.append(setaconfig_result)
                logger.info(f"*get_seat_api_details*seat_api**************** {seat_api}")
                return seat_api[0]
    except Exception:
        logger.error(f"Error in get_seat_api_details: {traceback.format_exc()}")
        return {}


def insert_seat_data(db_type, trip_id, gordian_trip_id):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn.cursor() as cursor:
            sql_query = (
                "INSERT INTO gordian_seat_mapping(`trip_id`,`gordian_trip_id`) VALUES ('"
                + str(trip_id)
                + "','"
                + str(gordian_trip_id)
                + "')"
            )
            cursor.execute(sql_query)
            result = cursor.fetchall()
            conn.commit()
            logger.info(f"*insert_seat_data*sql_query**************** {sql_query}")
            logger.info(f"*insert_seat_data*result**************** {result}")
            return result
    except Exception:
        logger.error(f"Error in insert_seat_data: {traceback.format_exc()}")
        return {}


def get_card_details(mode, vendor, country_code, carrier_id, client_id, pcc):
    remittance_salt_key = os.environ["REMITTANCE_SALT_KEY"]
    query_text = (
        "select pcdm.id, pcdm.country_code, pcdm.address, cd.payment_type, "
        "cd.payment_desc as payment_mode, cd.client_card, cd.type, cd.bank_country_code, "
        "AES_DECRYPT(cd.bank_name,'{0}') as bank_name,"
        "AES_DECRYPT(cd.name,'{0}') as name, "
        "AES_DECRYPT(cd.cvv,'{0}') as cvv , "
        "AES_DECRYPT(cd.card_number,'{0}') as card_number ,"
        "AES_DECRYPT(cd.expiry_date,'{0}') as expiry_date, "
        "AES_DECRYPT(cd.password,'{0}') as password, "
        "AES_DECRYPT(cd.identifier,'{0}') as identifier, "
        "cd.code  from remittance_mapping pcdm "
        "join remittance_details cd on pcdm.card_id = cd.id where pcdm.mode='{1}' and vendor='{2}' "
        "and pcdm.pcc = '{3}' and pcdm.status = 1 ".format(remittance_salt_key, mode, vendor, pcc)
    )

    query = query_text + " and pcdm.client_id={} and carrier_id='{}' and country_code='{}'".format(
        client_id, carrier_id, country_code
    )
    conn = DatabaseConnection.get_instance("api").get_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            card = cursor.fetchall()
            if card:
                return card
            else:
                query = query_text + " and pcdm.client_id={} and carrier_id='{}' and country_code='{}'".format(
                    0, carrier_id, country_code
                )
                cursor.execute(query)
                card = cursor.fetchall()
                if card:
                    cursor.close()
                    return card
                else:
                    query = query_text + " and pcdm.client_id={} and carrier_id='{}' ".format(client_id, "NA")
                    cursor.execute(query)
                    card = cursor.fetchall()
                    if card:
                        return card
                    else:
                        query = query_text + " and pcdm.client_id={} and carrier_id='{}' ".format(0, "NA")
                        cursor.execute(query)
                        card = cursor.fetchall()
                        cursor.close()
                        if card:
                            return card


def fetch_iata_details_from_Mongo(iata_code):
    try:
        conn = DatabaseConnection.get_instance("api").get_connection()
        query = "SELECT * FROM Airport WHERE iata='{}'".format(iata_code)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                iata_data = cursor.fetchall()
                return iata_data
    except Exception:
        logger.error(f"Error in get_client_preferred_hotel: {traceback.format_exc()}")


def get_client_preferred_hotel(db_type, client_id, lat, lng, max_distance, emp_level):
    """
    Desc : Fetch the client preferred hotel data  from api db
    Input:
        db_type: master/slave db to connect
        client_id : reference client id
        lat : hotel location latitude
        lng : hotel location longitude
        max_distance : client maximum distance
        emp_level : emp level
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """select
                hvm.unique_id AS uid,
                hcd.name,
                hvm.vendor_unique_id as hid,
                hvm.vendor_id as vid,
                hcd.id as hotel_id,
                hcd.address,
                hcd.city,
                h.state as state,
                h.country as country,
                hcd.currency,
                hcd.inclusions,
                hcd.category AS star_rating,
                hcd.latitude,
                hcd.longitude,
                hcd.rating_provider,
                h.image_path as image,
                hcd.preference_rate,
                hcd.double_occupancy_rate,
                hcd.triple_occupancy_rate,
                hcd.rating ,
                hcd.reviews,
                hcd.preference_order As preference_number,
                hcd.deal_group_id,
                h.chain,
                h.tag_id,
                h.property_status,
                hcd.breakfast,
                h.unica_id as unica_id,
                hdgd.deal,
                hdgd.vendor_id,
                hcd.cancellation_policy_less_than_12hrs,
                hcd.cancellation_policy_less_than_24hrs,
                hcd.cancellation_policy_less_than_48hrs,
                hcd.cancellation_policy_greater_than_48hrs
            from
                hotel_client_dump hcd
                inner join hotel_vendor_mapping hvm
                ON hcd.client_id = % d
                AND hvm.client_id = %d
                AND hvm.client_dump_id = hcd.unique_id
                AND hcd.status != 0
                AND hcd.property_status=1
                AND 6373 * acos(cos(radians(%f)) * cos(radians(hcd.latitude)) *
                cos(radians(hcd.longitude) - radians(%f)) + sin(radians(%f)) *
                sin(radians(hcd.latitude))) < %f
                inner join hotel h ON h.unique_id=hvm.unique_id
                AND h.property_status=1
                left join hotel_deal_group hdg ON hcd.deal_group_id = hdg.id
                left join hotel_deal_group_detail hdgd ON hdg.id = hdgd.deal_group_id
            where
                hcd.latitude IS NOT NULL
                AND hcd.longitude IS NOT NULL
                AND (
                    find_in_set('%s', hcd.eligible_employees)
                    OR find_in_set('NA', hcd.eligible_employees)
                )
            ORDER BY
                hcd.preference_order,
                hcd.preference_rate""" % (
            client_id,
            client_id,
            lat,
            lng,
            lat,
            max_distance,
            emp_level,
        )

        logger.info(f"sql get_client_preferred_hotel: {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in get_client_preferred_hotel: {traceback.format_exc()}")


def get_hotel_geo_distance(db_type, client_id):
    """
    Desc : Fetch the client Geo distance from api db
    Input:
        db_type: master/slave db to connect
        client_id : reference client id
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT geo_distance FROM hotel_geo_distance WHERE client_id=%d" % (client_id)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    return result
                else:
                    return []

    except Exception:
        logger.error(f"Error in get_hotel_geo_distance: {traceback.format_exc()}")


def get_hotel_gst(db_type):
    """
    Desc : Fetch the all hotel gst from api db
    Input:
        db_type: master/slave db to connect
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT * FROM hotel_gst"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in get_hotel_gst: {traceback.format_exc()}")


def get_hotel_tags(db_type):
    """
    Desc : Fetch the all hotel tags from api db
    Input:
        db_type: master/slave db to connect
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT * FROM hotel_tags"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in get_hotel_tags: {traceback.format_exc()}")


def get_itilite_contract_hotels(db_type, client_id, vendor_id, lat, lng, max_distance, emp_level):
    """
    Desc : Fetch the all itilite preferred hotels from api db
    Input:
        db_type: master/slave db to connect
        client_id: refer client id
        vendor_id: refer vendor id
        lat: hotel latitude
        lng: hotel longitude
        max_distance: distance to find hotel near by
        emp_level: employee level
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """
                SELECT
                    h.unique_id as uid,
                    hvm.vendor_id as vid,
                    rtm.inclusions,
                    hid.id as hotel_id,
                    hvm.vendor_unique_id as hid,
                    hid.name as name,
                    h.address as address,
                    h.city as city,
                    h.state as state,
                    h.country as country,
                    h.category as star_rating,
                    h.latitude ,
                    h.longitude,
                    h.rating,
                    h.reviews,
                    h.rating_provider,
                    h.image_path AS image,
                    h.chain,
                    h.hashcode,
                    concat(
                        '[',
                        GROUP_CONCAT(
                            CONCAT(
                                '{"room_type":"', hrt.room_type,
                                    '", "room_type_id":',hrt.id,
                                    ',"breakfast":',rtm.breakfast,
                                    ',"currency":"',htcm.currency,
                                    '","preference_rate":',
                                        if(htcm.rate is null
                                            or htcm.rate =0
                                            or htcm.rate ='',
                                            rtm.rate,htcm.rate),
                                    ',"double_occupancy_rate":',
                                        if(htcm.double_occupancy_rate is null
                                            or htcm.double_occupancy_rate =0
                                            or htcm.double_occupancy_rate ='',
                                            rtm.double_occupancy_rate,htcm.double_occupancy_rate),
                                    ',"triple_occupancy_rate":',
                                        if(htcm.triple_occupancy_rate is null
                                            or htcm.triple_occupancy_rate =0
                                            or htcm.triple_occupancy_rate ='',
                                            rtm.triple_occupancy_rate,htcm.triple_occupancy_rate),
                                    ',"cp_less_than_12hrs":',if(rtm.cancellation_policy_less_than_12hrs=100,True,False),
                                    ',"cp_less_than_24hrs":',if(rtm.cancellation_policy_less_than_24hrs=100,True,False),
                                    ',"cp_less_than_48hrs":',if(rtm.cancellation_policy_less_than_48hrs=100,True,False),
                                    ',"cp_greater_than_48hrs":',if(rtm.cancellation_policy_greater_than_48hrs=100,True,False),
                                '}'
                            )
                        ),
                        ']'
                    ) as room_details,
                    hid.deal_group_id,
                    h.property_status,
                    h.tag_id
                FROM hotel_room_types hrt
                INNER JOIN hotel_itilite_room_type_mapping rtm ON rtm.room_type_id = hrt.id
                INNER JOIN hotel_itilite_client_mapping htcm ON htcm.client_id = %d
                    AND htcm.unique_id = rtm.unique_id
                    AND rtm.room_type_id = htcm.room_type_id
                INNER JOIN hotel_vendor_mapping hvm ON htcm.client_id = %d
                    AND hvm.vendor_id = %d
                    AND hvm.vendor_unique_id = htcm.unique_id
                INNER JOIN hotel h ON  h.unique_id = hvm.unique_id AND h.property_status=1
                INNER JOIN hotel_itilite_dump hid ON hid.unique_id=htcm.unique_id
                    AND hid.property_status=1
                LEFT JOIN hotel_blacklisted_dump AS bh ON h.unique_id = bh.unique_id
                    AND bh.client_id = %d
                WHERE
                    6373 * acos(cos(radians(%f)) * cos(radians(hid.latitude))
                        * cos(radians(hid.longitude) - radians(%f))
                        + sin(radians(%f)) * sin(radians(hid.latitude))) < %f
                    AND bh.unique_id IS NULL AND htcm.client_id = %d
                    AND (find_in_set('%s', htcm.eligible_employees) OR find_in_set('NA', htcm.eligible_employees) OR
                    htcm.eligible_employees is Null OR htcm.eligible_employees='')
                    AND htcm.status = 1
                GROUP BY h.unique_id
                """ % (
            client_id,
            client_id,
            vendor_id,
            client_id,
            lat,
            lng,
            lat,
            max_distance,
            client_id,
            emp_level,
        )
        logger.info(f"sql get_itilite_contract_hotels: {sql}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in get_hotel_tags: {traceback.format_exc()}")


def get_deal_group_detail(db_type, deal_group_id):
    """
    Desc : Fetch the all hotel deal group detail from api db
    Input:
        db_type: master/slave db to connect
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT deal FROM hotel_deal_group_detail where deal_group_id=%d" % (deal_group_id)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in get_hotel_tags: {traceback.format_exc()}")


def get_rating_provider_name(db_type, id):
    """
    Desc : Fetch the rating provider name from api db by provider id
    Input:
        db_type: master/slave db to connect
        id : provider id
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = "SELECT name FROM rating_providers where id=%d" % (id)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in get_rating_provider_name: {traceback.format_exc()}")


def get_tour_code(client_id, airline_id):
    try:
        tour_code = None
        conn = DatabaseConnection.get_instance("api").get_connection()
        query = 'select tour_code from gds_tour_code where client_id= {0} and airline_id = "{1}" and active = 1'.format(
            client_id, airline_id
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                cursor.close()
                for result in results:
                    tour_code = result
        return tour_code
    except Exception as e:
        logger.error(f"Exception in Fetching details from tour code: {e}")
        raise e


def get_airline_iata(carrier_iata):
    try:
        conn = DatabaseConnection.get_instance("api").get_connection()
        query = "SELECT * FROM airline_iata_new WHERE iatacode='{}'".format(carrier_iata)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                iata_data = cursor.fetchall()
                cursor.close()
                return iata_data[0]
    except Exception as e:
        logger.error("Error while fetching data from airline iata")
        raise e


def get_hotel_deal_code(db_type, hotel_id, vendor_id, cwm_id):
    """
    Desc : Fetch the all hotel deal group detail from api db using vendor_id
    Input:
        db_type: master/slave db to connect
    """
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql = """ SELECT
            hdgd.deal,
            CONCAT('[', GROUP_CONCAT(CONCAT('{"deal":"', deal, '","vendor_id":', vm.vendor_id, ',
            "vendor_name":"', vm.name,'"}') ORDER BY priority),']') AS deals
        FROM
            hotel_client_dump hcd
        INNER JOIN hotel_deal_group hdg ON hcd.unique_id = %s AND hdg.id=hcd.deal_group_id
        INNER JOIN hotel_deal_group_detail hdgd ON hdg.id=hdgd.deal_group_id
        INNER JOIN vendor_master vm ON vm.vendor_id=hdgd.vendor_id
        INNER JOIN client_wrapper_mapping cwm ON cwm.client_id = hcd.client_id
        where hcd.unique_id =%s and vm.vendor_id=%s AND cwm.cwm_id=%s
        GROUP BY hcd.unique_id, vm.vendor_id;

        """ % (
            str(hotel_id),
            str(hotel_id),
            str(vendor_id),
            str(cwm_id),
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in get_hotel_tags: {traceback.format_exc()}")


def get_deal_code_for_unica_ids(db_type, hotel_ids, client_id, vendor_id, pref_type, emp_level):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        if pref_type == 1:
            pref_rate = "hcd.preference_rate != 0"
        else:
            pref_rate = "hcd.preference_rate = 0"
        hotel_ids_str = ""
        if len(hotel_ids) == 1:
            hotel_ids_str = str(tuple(hotel_ids)).replace(",", "")
        else:
            hotel_ids_str = str(tuple(hotel_ids))
        query = """ select
                h.unica_id as unica_id,
                hdgd.deal as deal,
                hdgd.deal_group_id as deal_group_id,
                hdgd.vendor_id as vendor_id
            from
                hotel_client_dump hcd
                inner join hotel_vendor_mapping hvm
                ON hcd.client_id = %d
                AND hvm.client_id = %d
                AND hvm.client_dump_id = hcd.unique_id
                AND hcd.status != 0
                AND hcd.property_status=1
                AND %s
                inner join hotel h ON h.unique_id=hvm.unique_id
                AND h.property_status=1
                left join hotel_deal_group hdg ON hcd.deal_group_id = hdg.id
                left join hotel_deal_group_detail hdgd ON hdg.id = hdgd.deal_group_id
            where
                hcd.unica_id in %s
                and hdgd.vendor_id= %d
                AND (
                find_in_set('%s', hcd.eligible_employees)
                OR find_in_set('NA', hcd.eligible_employees)
            )
            ORDER BY
                hcd.preference_order,
                hcd.preference_rate""" % (
            client_id,
            client_id,
            pref_rate,
            hotel_ids_str,
            vendor_id,
            emp_level,
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in hotel_deal_codes: {traceback.format_exc()}")


def get_alliance_details(db_type, client_id):
    try:
        logger.info("Inside alliance Details. Computation started ...")
        temp_salt_key = os.environ["SALT_KEY"]

        conn = DatabaseConnection.get_instance(db_type).get_connection()
        sql1 = (
            "SELECT username, AES_DECRYPT(password, '{0}') as password, end_point FROM"
            " alliance_api_cred WHERE vendor_name = '{1}'".format(temp_salt_key, client_id)
        )

        logger.info(f"----------get_alliance_details sql------- {str(sql1)}")
        logger.info(f"connection---------- {str(conn)}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql1)
                result = cursor.fetchone()
                return result
    except Exception as ex:
        logger.error(f"---------ERROR in get_alliance_details--------: {ex}")
        logger.error(traceback.format_exc())
        return None


def get_seat_details(db_type, vendor_name):
    try:
        logger.info("entered into get_flight_detail_id")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        with conn.cursor() as cursor:
            sql_query = "select * from seat_vendor_details where `vendor`='" + str(vendor_name) + "'limit 1"
            cursor.execute(sql_query)
            record = cursor.fetchall()
            conn.commit()
            result = record[0]
            logger.info(f"result : {result}")
            return result
    except Exception:
        logger.error(f"exception in get_flight_detail_id---------: {traceback.format_exc()}")
        return {}


def get_airline_iata_name(carrier_name):
    try:
        conn = DatabaseConnection.get_instance("api").get_connection()
        query = "SELECT iatacode FROM airline_iata_new WHERE name='{}'".format(carrier_name)
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                iata_data = cursor.fetchall()
                cursor.close()
                if iata_data:
                    return iata_data[0]
                else:
                    return None
    except Exception:
        logger.error("Error while fetching data from airline iata")
        return None


def get_itilite_deal_codes_by_cvwdm_id(cvwdm_id, db_type="api"):
    try:
        logger.info(f"Fetching itilite deal codes with cvwdm_id: {cvwdm_id}")
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        query = f"select * from client_vendor_wrapper_deals where cvwdm_id = {cvwdm_id}"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                deal_codes = [each["account_codes"] for each in result]
                return deal_codes
    except Exception:
        logger.error(f"Error while fetching deal codes. Error: {traceback.format_exc()}")
        return []


def get_deal_name_by_id_and_chain(db_type, client_id, hotel_id, hotel_chain, vendor_id):
    try:
        query_start_time = datetime.now()
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        query = """select
                    h.unica_id as unica_id,
                    h.name as name,
                    h.unique_id as hotel_unique_id,
                    hdgd.deal as deal,
                    hdgd.deal_group_id as deal_group_id,
                    hdgd.vendor_id
                    from
                        hotel_client_dump hcd
                        inner join hotel_vendor_mapping hvm
                        ON hcd.client_id = hvm.client_id
                        AND hvm.client_dump_id = hcd.unique_id
                        AND hcd.status != 0
                        AND hcd.property_status=1
                        AND hcd.preference_rate != 0
                        inner join hotel h ON h.unique_id=hvm.unique_id
                        AND h.property_status=1
                    left join hotel_gal_dump hd on hd.unica_id=h.unica_id
                    left join hotel_deal_group hdg ON hcd.deal_group_id = hdg.id
                    left join hotel_deal_group_detail hdgd ON hdg.id = hdgd.deal_group_id
                    where
                    hd.unique_id='%s' and hd.chain= '%s'
                    and hdgd.vendor_id=%s and hvm.client_id=%s
                    ORDER BY
                        hcd.preference_order,
                        hcd.preference_rate""" % (
            hotel_id,
            hotel_chain,
            str(vendor_id),
            str(client_id),
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                delta = datetime.now() - query_start_time
                logger.info(f"Time taken for fetch deal_name is: {delta.total_seconds()}")
                if len(result) != 0:
                    return result
                else:
                    return []
    except Exception:
        logger.error(f"Error in hotel_deal_codes: {traceback.format_exc()}, query: {query}")


def fetch_hotel_details_by_vendor_name_hotel_ids(vendor_name: str, vendor_id: int, hotel_ids: list):
    """
    Fetch hotel data from mysql database.
    """
    try:
        query_start_time = datetime.now()
        conn = DatabaseConnection.get_instance("api_slave").get_connection()
        table_vendor_mapping = {
            "desiya": "hotel_desiya_dump",
            "desiya_json": "hotel_desiya_dump",
            "zumata": "hotel_zumata_dump",
            "oyo2": "hotel_oyo_dump",
            "galileo": "hotel_gal_dump",
            "gds": "hotel_gal_dump",
            "priceline": "hotel_priceline_dump",
            "agoda": "hotel_priceline_dump",
            "bcom": "hotel_priceline_dump",
        }
        table = table_vendor_mapping.get(vendor_name)
        query = f"""select
                        h.unique_id as id,
                        hvm.vendor_id as provider_id,
                        hd.name,
                        hvm.vendor_unique_id as hotel_unique_id,
                        hd.address,
                        h.city,
                        h.state,
                        h.country,
                        h.pincode,
                        h.category,
                        h.rating,
                        h.reviews,
                        h.rating_provider,
                        h.image_path as image,
                        hd.latitude,
                        hd.longitude,
                        h.chain,
                        '' as il_black_list,
                        h.hashcode,
                        h.created_at,
                        h.updated_at,
                        hd.chain as hotel_chain
                        from hotel_vendor_mapping hvm
                        inner join vendor_master vm on vm.name = '{vendor_name}' and vm.vendor_id =  hvm.vendor_id
                        inner join hotel h on BINARY hvm.vendor_unique_id in {str(tuple(hotel_ids))} and h.unique_id = hvm.unique_id
                        INNER JOIN {table} hd on BINARY hd.unique_id in {str(tuple(hotel_ids))} """
        logger.info(f"Hotel fetch query: {query}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                hotels = cursor.fetchall()
        delta = datetime.now() - query_start_time
        logger.info(f"Time taken for fetch hotels from mysqldb is: {delta.total_seconds()}")
        res = {}
        for hotel in hotels:
            vendor_unique_id = hotel.get("vendor_unique_id")
            res[vendor_unique_id] = hotel
        return res
    except Exception as e:
        logger.error(f"Error while fetching hotel_ids: {hotel_ids} from mysql database. error: {traceback.format_exc()}")
        raise e


def list_hotel_cities(db_type, city: list, provider_id: int):
    """
    Fetch hotel cities from mysql database.
    """
    try:
        if not city:
            return []
        if len(city) == 1 and isinstance(city, list):
            city = city[0]
        cities = "('" + str(city) + "')"

        query_start_time = datetime.now()
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        query = f"""select
                        * from hotel_cities
                        where
                        city_provider_id = '{provider_id}' and
                        name in {cities} """
        logger.info(f"List hotel cities query: {query}")
        hotel_cities = []
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                hotel_cities = cursor.fetchall()
        delta = datetime.now() - query_start_time
        logger.info(f"Time taken for fetch hotel cities from mysqldb is: {delta.total_seconds()}")
        return hotel_cities
    except Exception as e:
        logger.error(f"Error while fetching list_hotel_cities: {city} from mysql database. error: {traceback.format_exc()}")
        raise e


def get_desiya_state_code(db_type, state):
    """
    Fetch hotel cities from mysql database.
    """
    try:
        if not state:
            return {}
        state = state.lower()
        query_start_time = datetime.now()
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        query = """SELECT code FROM gst_state_codes WHERE state = '%s'""" % (state)
        logger.info(f"get_desiya_state_code query: {query}")
        desiya_state = {}
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                desiya_state = cursor.fetchone()
        delta = datetime.now() - query_start_time
        logger.info(f"Time taken for get_desiya_state_code from mysqldb is: {delta.total_seconds()}")
        return desiya_state
    except Exception as e:
        logger.error(f"Error while fetching desiya_state_code: {state} from mysql database. error: {traceback.format_exc()}")
        raise e


def fetch_all_iata_details(iata_list, db_type):
    try:
        conn = DatabaseConnection.get_instance(db_type).get_connection()
        iata_string = ",".join(["'{}'".format(iata) for iata in iata_list])
        query = "SELECT iata, timeZone FROM Airport WHERE iata IN ({})".format(iata_string)
        logger.info(f"fetch_all_iata_details query: {query}")
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                iata_data = cursor.fetchall()
                return iata_data
    except Exception:
        logger.error(f"Error in fetching all iata details: {traceback.format_exc()}")


def get_flight_details(db_type, client_id, cvwdm_id):
    try:
        conn = MysqlConnector.connect_db(db_type)
        sql = """SELECT vm.name, vhd.token_agency_id from
            client_wrapper_mapping as cwm
            left join client_vendor_wrapper_detail_mapping as cvwdm on 1 = 1
            left join vendor_wrapper as vw on vw.vendor_wrapper_id = cvwdm.wrapper_id
            left join vendor_master as vm on vm.vendor_id = vw.vendor_id
            LEFT JOIN vendor_flight_detail as vhd ON vm.vendor_id = vhd.vendor_id
            AND cvwdm.detail_id = vhd.flight_detail_id
            where
            find_in_set(cvwdm.cvwdm_id, cwm.cvwdm_ids)
            AND cwm.mode = 'flight'
            AND cvwdm_id = %d
            AND cwm.client_id = %s
            LIMIT
            1 """ % (
            cvwdm_id,
            client_id,
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return result[0]

    except Exception:
        logger.error(f"Error in get_flight_details {traceback.format_exc()}")


def get_flight_fre_from_pcc(db_type, pcc):
    try:
        salt_key = os.environ["SALT_KEY"]
        conn = MysqlConnector.connect_db(db_type)
        sql = """select vendor_id, terminal_or_client_id,
            uname, AES_DECRYPT(password,'%s') as password,
            end_point,
            end_point_1,
            token_agency_id,
            token_member_id,
            other_details, display_name
            from vendor_flight_detail where token_agency_id = '%s'""" % (
            salt_key,
            pcc,
        )
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                if len(result) != 0:
                    for res in result:
                        if res["uname"] is not None:
                            res["uname"] = aes_encryption_data(res["uname"])
                        if res["password"] is not None:
                            res["password"] = aes_encryption_data(res["password"])
                return result
    except Exception:
        logger.error(f"error in the get_flight_fre_from_pcc: {traceback.format_exc()}")
        return {}


def get_client_osi_remark_data(client_id, carrier_iata):
    try:
        conn = DatabaseConnection.get_instance("api").get_connection()
        query = """
            SELECT airline_code, osi_remark_send, osi_remark, osi_fare, osi_iata_code
            FROM client_osi_remarks
            WHERE client_id = %s AND airline_code = %s
        """

        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (client_id, carrier_iata))
                osi_data = cursor.fetchall()
                if osi_data:
                    return osi_data[0]
                else:
                    return {}
    except Exception as e:
        logger.error(f"Error while fetching OSI data for client_id={client_id}, carrier_iata={carrier_iata}: {str(e)}")
        return {}


def update_hotel_ratings_review(hotel_id, rating, review_count):
    try:
        conn = DatabaseConnection.get_instance("api").get_connection()
        with conn:
            with conn.cursor() as cursor:
                sql = """UPDATE hotel SET rating = %s, reviews = %s WHERE id = %s"""
                cursor.execute(sql, (rating, review_count, hotel_id))
                conn.commit()
                cursor.close()
                return cursor.rowcount
    except Exception as e:
        logger.error(f"Error in updating rating review of hotel: {e}, {traceback.format_exc()}")
    return


def get_carrier_names():
    """
    Fetches all iatacode and carrier names from database.
    :return: dictionary with iatacode as key and carrier name as value for faster fetch.
    """
    try:
        conn = DatabaseConnection.get_instance("api_slave").get_connection()
        sql = "select iatacode,name,id from airline_iata_new"
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                global CARRIER_DATA
                _result = cursor.fetchall()
                cursor.close()
                _carrier_data = {}
                for item in _result:
                    _carrier_data[item["iatacode"]] = item["name"]
                CARRIER_DATA = _carrier_data
                # conn.close()
        logger.info("Iata code fetched successfully from db")

    except Exception as e:
        logger.error(f"Error while fetching airline iata data - {e}")
