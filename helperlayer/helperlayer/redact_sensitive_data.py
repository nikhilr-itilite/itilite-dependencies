import re
from opensearchlogger.logging import logger
from copy import deepcopy
from typing import Union

DEFAULT_REDACT_KEY = {"cvv", "cvc", "expiry_date", "expires", "cvc_code"}
DEFAULT_PARTIAL_REDACT_KEY = {"number", "password"}


def redact_the_params(params: dict) -> dict:
    """
    Redacts sensitive information from a dictionary.

    Note: This will increase time complexity: just mentioning
    use this when you know the keys explicitly
    parsing logic: it looks for each key recursively and checks
    which has this default key names and redact them
    """
    try:
        # Create a copy of the params to avoid modifying the original
        params_copy: dict = deepcopy(params)

        for key, value in params_copy.items():
            if isinstance(value, dict):
                params_copy[key] = redact_the_params(value)
            elif (
                isinstance(key, str)
                and isinstance(value, str)
                and (key.lower() in DEFAULT_REDACT_KEY or key.lower() in DEFAULT_PARTIAL_REDACT_KEY)
            ):
                to_redact_whole: bool = True if key.lower() in DEFAULT_REDACT_KEY else False
                params_copy[key] = sanitize_the_value(value, to_redact_whole)
        return params_copy
    except Exception as e:
        logger.error(f"Error in redacting params: {e}", exc_info=True)
        return params


def sanitize_the_value(value: str, to_redact_whole: bool) -> str:
    """
    Redacts a value entirely or partially.
    """
    try:
        if to_redact_whole:
            return "[REDACTED]"
        else:
            # Partially redact, keeping the last 4 digits visible
            return re.sub(r"\d(?=\d{4})", "*", value)
    except Exception as e:
        logger.error(f"Error in sanitizing value: {e}", exc_info=True)
        return value


def sanitize_card_details_from_xml(xml_data: dict) -> dict:
    """
    this takes dict and redacts xml string
    use this when its a dictionary and something like value is a string
    ans contains the sensitive information
    parsing logic: Redacts the 'Number', 'CVV', and 'ExpDate' attributes
    in the XML strings by using regex.
    """
    try:
        copy_xml_data: dict = deepcopy(xml_data)
        for key, xml_string in copy_xml_data.items():
            if isinstance(xml_string, str):
                xml_string = re.sub(
                    r'<ns2:CreditCard[^>]*Number="([^"]*)"[^>]*>',
                    lambda m: re.sub(r'Number="[^"]*"', f'Number="{"*" * (len(m.group(1)) - 4) + m.group(1)[-4:]}"', m.group()),
                    xml_string,
                )
                xml_string = re.sub(r'CVV="[^"]*"', 'CVV="***"', xml_string)
                xml_string = re.sub(r'ExpDate="[^"]*"', 'ExpDate="****"', xml_string)
                copy_xml_data[key] = xml_string  # Reassign sanitized string
        return copy_xml_data
    except Exception as e:
        logger.error(f"Error in sanitizing xml data: {e}", exc_info=True)
        return xml_data


def sanitize_payload(payload: dict) -> Union[dict, None]:
    try:
        redacted_payload = deepcopy(payload)
        if "card_number" in redacted_payload:
            redacted_payload["card_number"] = re.sub(r"\d(?=\d{4})", "*", redacted_payload["card_number"])

        if "cvv" in redacted_payload:
            redacted_payload["cvv"] = "[REDACTED]"
        if "cvc" in redacted_payload:
            redacted_payload["cvc"] = "[REDACTED]"
        if "cvc_code" in redacted_payload:
            redacted_payload["cvc_code"] = "[REDACTED]"
        # Redact expiry date
        if "expiry_date" in redacted_payload:
            redacted_payload["expiry_date"] = "[REDACTED]"
        if "expires" in redacted_payload:
            redacted_payload["expires"] = "[REDACTED]"

        return redacted_payload

    except Exception as e:
        logger.error(f"Couldn't sanitize the payload. Error: {e}")
        return None
