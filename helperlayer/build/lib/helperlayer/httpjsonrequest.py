import json
import traceback
import helperlayer as helpers

from datetime import datetime

import requests
from opensearchlogger.logging import logger
from requests.exceptions import ChunkedEncodingError, ConnectionError
from helperlayer.helperfunctions import push_newrelic_custom_event, NR_API_EXECUTION_EVENT
from helperlayer.redact_sensitive_data import sanitize_payload


class HTTPJsonRequestMixin:
    """
    HTTPJsonRequestMixin class
    """

    def __init__(self):
        super().__init__()
        self.retry = 1

    def fetch_nested_obj_value(self, obj, nested_path):
        """
        Fetch values from a nested values. eg:obj.attr1.attr2.attr3
        :param obj: source obj
        :param nested_path: path of the field being fetched.
        :return:
        """
        if len(nested_path) == 1:
            return getattr(obj, nested_path[0])
        else:
            return self.fetch_nested_obj_value(getattr(obj, nested_path[0]), nested_path[1:])

    def traverse_body(self, payload):
        """
        Traverse through a dictionary and dynamically replace object values if needed.
        :param payload: a dictionary which could have $ symbols which would be replaced with the obj values.
        :return:
        """
        for key, value in payload.items():
            new_value = None
            if value is None:
                value = ""
            if isinstance(value, dict):
                new_value = self.traverse_body(value)
            elif isinstance(value, int):
                new_value = value
            elif isinstance(value, str):
                if value.startswith("$"):
                    temp_value = value[1:].split(".")
                    if len(temp_value) > 1:
                        new_value = self.fetch_nested_obj_value(self, temp_value)
                    else:
                        new_value = getattr(self, temp_value[0])
                else:
                    new_value = value
            else:
                raise NotImplementedError(f"Dynamic traversal is not implemented for value type: {type(new_value)}. " f"key: {key}")

            payload[key] = new_value

        return payload

    def get_response(self, api_type=None, vendor=None, newrelic_agent=None, param_dict={}):
        """
        This method formulates vendor request url from the config and returns the response.
        :return: Hotel list returned from vendor.
        """
        response_content = None
        desiya_vendor = "desiya_json"
        try:
            start_time = datetime.now()
            http_method = self.request_mapping["http_method"]
            base_url = self.request_mapping["base_url"]
            if base_url.startswith("$fre_config"):
                url = getattr(self.fre_config, base_url.split(".")[1])
            else:
                url = base_url

            path_params = "/" if not url.endswith("/") else ""
            for idx, path_param in enumerate(self.request_mapping["path_params"]):
                path_param = str(path_param)
                if path_param.startswith("$"):
                    temp_value = path_param[1:].split(".")
                    if len(temp_value) > 1:
                        path_param_value = self.fetch_nested_obj_value(self, temp_value)
                    else:
                        path_param_value = getattr(self, temp_value[0])
                elif path_param.startswith("@"):
                    path_param_value = param_dict.get(path_param[1:], path_param)
                else:
                    path_param_value = path_param
                if idx == len(self.request_mapping["path_params"]) - 1:
                    path_params = path_params + str(path_param_value)
                else:
                    path_params = path_params + str(path_param_value) + "/"

            url = url + path_params

            query_params = "?" if self.request_mapping["query_params"] else ""
            for query_param, value in self.request_mapping["query_params"].items():
                value = str(value)
                if value.startswith("$"):
                    temp_value = value[1:].split(".")
                    if len(temp_value) > 1:
                        query_param_value = self.fetch_nested_obj_value(self, temp_value)
                    else:
                        query_param_value = getattr(self, temp_value[0])
                elif value.startswith("@"):
                    query_param_value = param_dict.get(path_param[1:], path_param)
                else:
                    query_param_value = value
                if query_param == "api_key":
                    # Decryption:
                    api_key = helpers.AES_decryption_data(query_param_value)
                    # decrypt here and pass the decrypted value to query_param_value
                    logger.info(f"api_key --> {query_param_value}")
                    query_param_value = api_key
                if query_param == "password":
                    encrypted_password = helpers.AES_decryption_data(query_param_value)
                    query_param_value = encrypted_password

                if not query_param:
                    query_params += str(query_param_value) + "&"
                else:
                    query_params += query_param + "=" + str(query_param_value) + "&"

            if query_params.endswith("&"):
                query_params = query_params[:-1]

            url = url + query_params
            logger.info(f"Final input URL: {url}")

            headers = self.request_mapping["headers"]
            if "x-api-key" in headers:
                headers["x-api-key"] = getattr(self.fre_config, "token_member_id")
            payload = self.traverse_body(self.request_mapping["payload"])
            logger.info(f"Final payload: {sanitize_payload(payload)}")

            response = requests.request(http_method, url, headers=headers, data=payload)
            # need to remove below log
            if self.fre_config.name == desiya_vendor:
                log = {
                    "http_method": http_method,
                    "url": url,
                    "headers": headers,
                    "payload": payload,
                    "response": response.text,
                    "status_code": response.status_code,
                }
                logger.info(f"{desiya_vendor} log {log}")

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Time taken to fetch response is {execution_time}")
            logger.info(f"Vendor response status code: {response}")
            response_content = response.content
            logger.info(f"api_type, {api_type}, newrelic_agent {type(newrelic_agent)}")
            if api_type and newrelic_agent:  # This is an async call
                custom_event = {
                    "api_type": api_type,
                    "execution_time": round(execution_time, 6),
                    "api_status_code": response.status_code,
                    "vendor": vendor,
                }
                push_newrelic_custom_event(newrelic_agent, NR_API_EXECUTION_EVENT, custom_event)
            if self.request_mapping.get("request_type") in ("booking", "lookup"):
                logger.info(f"Raw vendor response is: {response_content}")
            response_data = json.loads(response_content) if response_content else {}
            if self.fre_config.name == desiya_vendor:
                response_data["status_code"] = response.status_code
            return response_data
        except ChunkedEncodingError as ce:  # This occurs with connection reset
            logger.error(f"ChunkedEncodingError occured, retrying.. error: {ce}")
            self.retry = self.retry - 1
            if self.retry > 0:
                return self.get_response()
            else:
                raise ce
        except ConnectionError as coe:
            logger.error(f"ConnectionError occured, retrying.. error: {coe}")
            self.retry = self.retry - 1
            if self.retry > 0:
                return self.get_response()
            else:
                raise coe
        except Exception as e:
            logger.info(f"Response content in exception: {response_content}")
            logger.error(f"Error while fetching vendor response, error: {traceback.format_exc()}")
            self.retry = self.retry - 1
            if self.retry > 0:
                return self.get_response()
            else:
                raise e
