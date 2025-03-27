import os

# from helperfunctions import AES_decryption_data  # TODO
from requests import Session
import base64
from zeep import Settings, Client, Transport
from opensearchlogger.logging import logger
import traceback
import xml.etree.ElementTree as ET
from lxml import etree
from io import StringIO

import pyaes

TP_UAPI_VERSION = os.getenv("TP_UAPI_VERSION", "")
TP_UAPI_WSDL_VERSION = os.getenv("TP_UAPI_WSDL_VERSION", "")

HOTEL_GDS_LIB_PATH = "lib/" + TP_UAPI_VERSION + "/"
TP_SERVICE_URL = "http://www.travelport.com/service/"

MAPPINGS = {
    "HotelRulesMap": {
        "xpath": "/x:Envelope/x:Body/y:HotelRulesRsp",
        "fields": {
            # "display_currency": {
            #     "xpath": "y:HotelRateDetail/@Total",
            #     "lambda": lambda s: s[0][0:3] if isinstance(s, list) else s[0:3],
            # },
            # "non_refundable_indicator": {
            #     "xpath": "y:HotelRateDetail/y:CancelInfo/@NonRefundableStayIndicator",
            #     "lambda": lambda s: s[0] if isinstance(s, list) else s,
            # },
            # "offset_time_unit": {"xpath": "y:HotelRateDetail/y:CancelInfo/@OffsetTimeUnit"},
            # "offset_unit_multiplier": {"xpath": "y:HotelRateDetail/y:CancelInfo/@OffsetUnitMultiplier"},
            # "offset_drop_time": {"xpath": "y:HotelRateDetail/y:CancelInfo/@OffsetDropTime"},
            # "date_after": {
            #     "xpath": "y:HotelRateDetail/y:CancelInfo/@CancelDeadline",
            #     "lambda": lambda s: s[0] if isinstance(s, list) else s,
            # },
            # "date_before": {
            #     "xpath": "y:HotelRateDetail/y:CancelInfo/@CancelDeadline",
            #     "lambda": lambda s: s[0] if isinstance(s, list) else s,
            # },
            # "penalty_charges": {
            #     "xpath": "y:HotelRateDetail/y:CancelInfo/@CancelPenaltyAmount",
            #     "lambda": lambda s: s[0] if isinstance(s, list) else s,
            # },
            # "no_of_nights": {
            #     "xpath": "y:HotelRateDetail/y:CancelInfo/@NumberOfNights",
            #     "lambda": lambda s: s[0] if isinstance(s, list) else s,
            # },
            "actual_description": {
                "xpath": "/x:Envelope/x:Body/y:HotelRulesRsp/y:HotelRuleItem[@Name='Cancellation']",
                "iteration": True,
                "fields": {"value": {"xpath": "y:Text", "expand": 1}},
            },
        },
    },
    # "namespaces": {
    #     "x": "http://schemas.xmlsoap.org/soap/envelope/",
    #     "y": "http://www.travelport.com/schema/hotel_v46_0",
    #     "z": "http://www.travelport.com/schema/common_v46_0",
    # },
}

GDS_HOTEL_NAME_SPACES = {
    "x": "http://schemas.xmlsoap.org/soap/envelope/",
    "y": "http://www.travelport.com/schema/hotel_" + TP_UAPI_WSDL_VERSION + "_0",
    "z": "http://www.travelport.com/schema/common_" + TP_UAPI_WSDL_VERSION + "_0",
}

# class GDSRequests:  # For Future
#     def __init__(self, request_type, *args, **kwargs):
#         pass


def AES_decryption_data(encrypted_data):  # TODO: REMOVE Me AFTER TESTING
    # DECRYPTION
    AES_KEY = os.environ["AES_KEY"]
    key = AES_KEY.encode("utf-8")
    aes = pyaes.AESModeOfOperationCTR(key)
    encrypted_data = base64.b64decode(encrypted_data)
    decrypted_data = aes.decrypt(encrypted_data).decode("utf-8")
    return decrypted_data


class GDSRulesRequest:
    def __init__(self, fre_config: dict, room_details: dict, checkin: str, checkout: str):
        self.mapping = MAPPINGS["HotelRulesMap"]
        self.namespaces = GDS_HOTEL_NAME_SPACES
        self.fre_config = fre_config  # Add Validators
        self.room_details = room_details  # Add Validators
        self.checkin = checkin
        self.checkout = checkout

    def _get_value(self, element, field):
        if "xpath" in field:
            result = element.xpath(field["xpath"], namespaces=self.namespaces)
            if isinstance(result, list):
                if "expand" in field:
                    res = ""
                    if len(result) > 0:
                        for i in range(0, len(result)):
                            res = res + " " + result[i].text
                        result = res
                    else:
                        result = None
                else:
                    if len(result) > 0:
                        result = result[0]
                    else:
                        result = None
            if "value_map" in field and result is not None:
                if result not in field["value_map"]:
                    print(result)
                    print(field)
                    print(field["value_map"])
                result = field["value_map"][result]
            if "lambda" in field and result is not None:
                result = self.run_lambda(field, result)
            if "default_value" in field and not result:
                result = field["default_value"]
            return result
        elif "value" in field:
            return field["value"]
        else:
            return None

    def run_lambda(self, field, value) -> str:
        lambda_func = field.get("lambda")
        if lambda_func:
            return lambda_func(value)
        return value

    def _parse_element(self, element, mapping):
        data = {}
        for field, config in mapping["fields"].items():
            if "iteration" in config and config["iteration"]:
                data[field] = []

                for nested_element in element.xpath(config["xpath"], namespaces=self.namespaces):
                    nested_data = self._parse_element(nested_element, config)
                    if "lambda" in config and nested_data is not None:
                        nested_data = self.run_lambda(config, nested_data)
                    data[field].append(nested_data)
            elif "iteration" in config and not config["iteration"]:
                data[field] = {}
                for nested_element in element.xpath(config["xpath"], namespaces=self.namespaces):
                    nested_data = self._parse_element(nested_element, config)
                    if "lambda" in config and nested_data is not None:
                        nested_data = self.run_lambda(config, nested_data)
                    data[field] = nested_data
            else:
                data[field] = self._get_value(element, config)
        return data

    def transform(self, root):
        result = []
        for element in root.xpath(self.mapping["xpath"], namespaces=self.namespaces):
            data = self._parse_element(element, self.mapping)
            result.append(data)

        return result

    def get_client(self, wsdl_folder, wsdl_file, username, password):
        """
        Fetch zeep client
        """
        try:
            wsdl = os.path.join(f"{HOTEL_GDS_LIB_PATH}{wsdl_folder}/{wsdl_file}")  # TODO: Check path /hotel
            uname = AES_decryption_data(username)
            password = str(AES_decryption_data(password)).lstrip("b").strip(" ' ")
            session = Session()
            auth_bytes = bytes(
                f"{'Universal API/' + uname}:{password}",
                encoding="utf-8",
            )
            auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")
            session.headers = {"Authorization": "Basic " + auth_base64}
            settings = Settings(strict=False, xml_huge_tree=True, raw_response=True)
            client = Client(wsdl, transport=Transport(session=session), settings=settings)
            return client
        except Exception as e:
            logger.error(f"Error while fetching zeep client. error: {traceback.format_exc()}")
            # Retry needed ?
            raise e

    def get_binding_service(self, zeep_client, endpoint, binding_service_name, client_service_name):
        """
        Create zeep binding service
        """
        try:
            # client = self.get_client(wsdl_folder, wsdl_file, username, password)
            binding_service = zeep_client.create_service(
                f"{{{TP_SERVICE_URL}{binding_service_name}}}{client_service_name}", endpoint
            )  # Does it need slashed to be handled ?
            return binding_service
        except Exception as e:
            raise e

    def format_rules_payload(self):
        return {
            "TargetBranch": self.fre_config["token_member_id"],
            "BillingPointOfSaleInfo": {"OriginApplication": "UAPI"},
            "HotelRulesLookup": {
                "Base": self.room_details["ip"]["vc"]["bp"],
                "RatePlanType": self.room_details["rpc"],
                "HotelProperty": {
                    "HotelChain": self.room_details["chn"],
                    "HotelCode": self.room_details["hid"],
                    # "Name": self.room_details["nme"],  # Needed ?
                },
                "HotelStay": {
                    "CheckinDate": self.checkin,
                    "CheckoutDate": self.checkout,
                },
            },
        }

    def make_rule_request(self):
        """
        Make vendor call to fetch GDS hotel Rules
        """
        try:
            zeep_client = self.get_client(
                wsdl_folder="hotel_" + TP_UAPI_WSDL_VERSION + "_0",
                wsdl_file="Hotel.wsdl",
                username=self.fre_config["uname"],  # Why FRE is dictionary
                password=self.fre_config["password"],
            )
            binding_service = self.get_binding_service(
                zeep_client,
                self.fre_config["end_point"],
                binding_service_name="hotel_" + TP_UAPI_WSDL_VERSION + "_0",
                client_service_name="HotelRulesServiceBinding",
            )
            parameters = self.format_rules_payload()
            rules_request = zeep_client.create_message(binding_service, "service", **parameters)
            rules_request = str(
                ET.tostring(rules_request, encoding="utf8", method="xml"),
                "utf-8",
            )  # Just for logging purposes
            logger.info(f"Rules request info: {rules_request}")
            return binding_service.service(**parameters)
        except Exception as e:
            logger.error(f"Vendor call for Rules request is failed. error: {traceback.format_exc()}")
            raise e

    def fetch_cancellation_rules(self):
        """
        Fetch al the rules in xml, transform to json and send
        """
        try:
            rules_response = self.make_rule_request()
            rules_response_text = rules_response.text
            logger.error(f"Vendor response for hotel rules: {str(rules_response_text)}")
            if rules_response.status_code != 200:
                raise Exception("Error while fetching from vendor")

            lx_tree = etree.parse(StringIO(rules_response_text))
            root = lx_tree.getroot()
            error_tag = root.xpath("/x:Envelope/x:Body/x:Fault", namespaces=GDS_HOTEL_NAME_SPACES)
            if len(error_tag) > 0:
                logger.error(f"Error found in the vendor response: {error_tag}")
                raise Exception("Vendor response has fault strings/errors.")

            json_response = self.transform(root)[0]
            actual_desc = json_response["actual_description"]  # Extend for other fields later.
            if actual_desc:
                json_response["actual_description"] = actual_desc[0].get("value", "")
            # Sometimes in description it is coming as 18,273 INR, to handle those we need to replace them
            json_response["actual_description"] = json_response["actual_description"].replace(",", "").strip()

            return json_response["actual_description"]

        except Exception as e:
            raise e
