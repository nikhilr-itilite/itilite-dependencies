import json
import os
from enum import Enum

import requests

from opensearchlogger.logging import logger

API_CONSTANT = "/api/v1/user/custominfo"
GET_INFO_API_CONSTANT = "/api/v1/user/getcustominfo"

AUTH_HEADERS = {
    "Content-Type": "application/json; charset=UTF-8",
    "cache-control": "no-cache",
}


class CustomTypeEnum(Enum):
    TSA_VAL = "tsa_val"
    KTN_VAL = "ktn_val"
    MEMBERSHIP_VAL = "membership"


class Mode(Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"


class UserType(Enum):
    STAFF = "STAFF"
    GUEST = "GUEST"


def save_or_update_usm_data(
    is_ktn,
    is_tsa,
    is_membership,
    auth_token,
    tsa_val=None,
    ktn_val=None,
    membership_val=None,
    guest_id=None,
    staff_id=None,
):
    try:
        payload = list()
        if is_ktn and ktn_val and len(ktn_val.strip()) > 0:
            ktn_dict = {
                "user_id": guest_id if guest_id is not None else staff_id,
                "user_type": UserType.GUEST.value if guest_id is not None else UserType.STAFF.value,
                "type": CustomTypeEnum.KTN_VAL.value,
                "value": ktn_val,
                "mode": Mode.FLIGHT.value,
            }
            payload.append(ktn_dict)
        elif is_ktn:
            delete_custom_id(
                auth_token,
                guest_id if guest_id else staff_id,
                UserType.GUEST.value if guest_id is not None else UserType.STAFF.value,
                CustomTypeEnum.KTN_VAL.value,
            )
        if is_tsa and tsa_val and len(tsa_val.strip()) > 0:
            tsa_dict = {
                "user_id": guest_id if guest_id is not None else staff_id,
                "user_type": UserType.GUEST.value if guest_id is not None else UserType.STAFF.value,
                "type": CustomTypeEnum.TSA_VAL.value,
                "value": tsa_val,
                "mode": Mode.FLIGHT.value,
            }
            payload.append(tsa_dict)
        elif is_tsa:
            delete_custom_id(
                auth_token,
                guest_id if guest_id else staff_id,
                UserType.GUEST.value if guest_id is not None else UserType.STAFF.value,
                CustomTypeEnum.TSA_VAL.value,
            )
        if is_membership:
            for membership in membership_val:
                membership_dict = {
                    "user_id": guest_id if guest_id is not None else staff_id,
                    "user_type": UserType.GUEST.value if guest_id is not None else UserType.STAFF.value,
                    "type": CustomTypeEnum.MEMBERSHIP_VAL.value,
                    "mode": membership["membership_type"],
                    "membership_details": {
                        "name": membership["name"],
                        "number": membership["number"],
                        "code": membership.get("iata_code", "None"),
                        "loyalty_program_id": membership.get("loyalty_program_id"),
                    },
                }
                if membership.get("id", None):
                    if not (isinstance(membership.get("id"), int) and len(str(membership.get("id"))) == 13):
                        membership_dict["custom_info_id"] = membership["id"]
                payload.append(membership_dict)
        if len(payload) > 0:
            url = os.environ.get("APP_URL") + API_CONSTANT
            AUTH_HEADERS["Authorization"] = auth_token
            response = requests.post(url, headers=AUTH_HEADERS, json=payload)
            if response and response.status_code == 200:
                result = json.loads(response.text)
            else:
                result = {
                    "status": False,
                    "message": "profile updation failed",
                    "usm_response": response.text,
                }
            logger.info(f"-----------update profile response for user result: {result}")
            return response
        return {}
    except Exception as e:
        logger.error(f"Error While updating user details in USM : {e}")
        return {}


def get_custom_info_details(is_tsa, is_ktn, is_membership, auth_token, staff_ids=None, guest_ids=None):
    try:
        attribute_name_list = list()
        payload = {"user_ids": {}}
        if is_tsa and is_ktn and is_membership:
            payload["attribute_names"] = [
                CustomTypeEnum.TSA_VAL.value,
                CustomTypeEnum.KTN_VAL.value,
                CustomTypeEnum.MEMBERSHIP_VAL.value,
            ]
        else:
            if is_ktn:
                attribute_name_list.append(CustomTypeEnum.KTN_VAL.value)
            if is_tsa:
                attribute_name_list.append(CustomTypeEnum.TSA_VAL.value)
            if is_membership:
                attribute_name_list.append(CustomTypeEnum.MEMBERSHIP_VAL.value)
            payload["attribute_names"] = attribute_name_list

        if staff_ids is not None and len(staff_ids) > 0 and guest_ids is not None and len(guest_ids) > 0:
            staff_ids.append(guest_ids)
            payload["user_ids"]["guest_ids"] = staff_ids
        else:
            payload["user_ids"]["guest_ids"] = staff_ids if staff_ids is not None and len(staff_ids) > 0 else guest_ids

        url = os.environ.get("APP_URL") + GET_INFO_API_CONSTANT

        AUTH_HEADERS["Authorization"] = auth_token
        response = requests.post(url, headers=AUTH_HEADERS, json=payload)
        if response and response.status_code == 200:
            result = json.loads(response.text)
        else:
            result = {
                "status": False,
                "message": "profile updation failed",
                "usm_response": response.text,
            }
        logger.info(f"-----------Fetching user profile response for user result : {result}")
        return result

    except Exception as e:
        logger.error(f"Exception while fetching user details :{e}")
        return {}


def delete_custom_id(auth_token, user_id, user_type, att_type):
    try:
        url = f"{os.environ.get('APP_URL')}{API_CONSTANT}?user_type={user_type}&user_id={user_id}&attribute_type={att_type}"
        AUTH_HEADERS["Authorization"] = auth_token
        response = requests.delete(url, headers=AUTH_HEADERS)
        return response
    except Exception as e:
        logger.error(f"Exception while removing custom info details : {e}")
        return {}
