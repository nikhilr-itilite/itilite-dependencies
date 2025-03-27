from mongoconnector.constants import (
    EQUAL,
    NOT_EQUAL,
    GREATER_THAN,
    LESS_THAN,
    LESS_THAN_EQUAL,
    GREATER_THAN_EQUAL,
    IN,
    EXISTS,
    NOT_IN,
    AND_OPERATOR,
    OR_OPERATOR,
    NOR,
    THIS_PROPERTY_PATH,
)
from mongoconnector.searchbuilder import query_operators

from opensearchlogger.logging import logger

from mongoconnector.utils import get_field_type_and_cast_value, convert_list_value


def __check_and_match_operator_and_frame_q(operator: str, field: str, value: str, doc_description: dict) -> dict:
    try:
        query = None
        if operator == EQUAL:
            query = __frame_equal_query(field, value, doc_description)
        elif operator == NOT_EQUAL:
            query = __frame_not_equal_query(field, value, doc_description)
        elif operator == GREATER_THAN:
            query = __frame_greater_than_query(field, value, doc_description)
        elif operator == LESS_THAN:
            query = __frame_less_than_query(field, value, doc_description)
        elif operator == LESS_THAN_EQUAL:
            query = __frame_less_than_query(field, value, doc_description)
        elif operator == GREATER_THAN_EQUAL:
            query = __frame_less_than_query(field, value, doc_description)
        elif operator == IN:
            query = __frame_in_query(field, value, doc_description)
        elif operator == EXISTS:
            query = __frame_exists_query(field, value, doc_description)
        elif operator == NOT_IN:
            query = __frame_not_in_query(field, value, doc_description)

        return query
    except Exception as e:
        logger.error(
            "Error processing operators. Operator:"
            + str(operator)
            + "Field: "
            + str(field)
            + ", value: "
            + str(value)
            + ". Error: "
            + str(e)
        )
        raise Exception(
            "Error processing operators. Operator:"
            + str(operator)
            + "Field: "
            + str(field)
            + ", value: "
            + str(value)
            + ". Error: "
            + str(e)
        )


def frame_and_query(query_list: list, doc_description: dict) -> dict:
    try:
        framed_query_list = []
        for val in query_list:
            split_query_data = val.split(" ")

            if len(split_query_data) > 3:  # Applicable only for String
                split_char = split_query_data[1]
                q_val = val.rsplit(split_char, 1)[1]
                q = __check_and_match_operator_and_frame_q(
                    split_query_data[1],
                    split_query_data[0],
                    q_val.strip(),
                    doc_description,
                )
            else:
                q = __check_and_match_operator_and_frame_q(
                    split_query_data[1],
                    split_query_data[0],
                    split_query_data[2],
                    doc_description,
                )
            framed_query_list.append(q)

        and_query = {query_operators.query_operators[AND_OPERATOR]: framed_query_list}
        return and_query
    except Exception as e:
        logger.error("Error framing AND Query. Query list :  " + str(query_list) + ". Error: " + str(e))
        raise Exception("Error framing AND Query. Query list :  " + str(query_list) + ". Error: " + str(e))


def frame_or_query(query_list: list, doc_description: dict) -> dict:
    try:
        framed_query_list = []
        for val in query_list:
            split_query_data = val.split(" ")
            split_query_data[1]
            q = __check_and_match_operator_and_frame_q(
                split_query_data[1],
                split_query_data[0],
                split_query_data[2],
                doc_description,
            )
            framed_query_list.append(q)

        or_query = {query_operators.query_operators[OR_OPERATOR]: framed_query_list}
        return or_query
    except Exception as e:
        logger.error("Error framing OR Query. Query list :  " + str(query_list) + ". Error: " + str(e))
        raise Exception("Error framing OR Query. Query list :  " + str(query_list) + ". Error: " + str(e))


def frame_nor_query(query_list: list, doc_description: dict) -> dict:
    try:
        framed_query_list = []
        for val in query_list:
            split_query_data = val.split(" ")
            split_query_data[1]
            q = __check_and_match_operator_and_frame_q(
                split_query_data[1],
                split_query_data[0],
                split_query_data[2],
                doc_description,
            )
            framed_query_list.append(q)

        or_query = {query_operators.query_operators[NOR]: framed_query_list}
        return or_query
    except Exception as e:
        logger.error("Error framing NOR Query. Query list :  " + str(query_list) + ". Error: " + str(e))
        raise Exception("Error framing NOR Query. Query list :  " + str(query_list) + ". Error: " + str(e))


def __frame_equal_query(field: str, value, doc_description: dict) -> dict:
    try:
        field_metadata = doc_description[field]
        query = {
            field_metadata.get(THIS_PROPERTY_PATH): {
                query_operators.query_operators[EQUAL]: get_field_type_and_cast_value(field_metadata, value)
            }
        }
        return query
    except Exception as e:
        logger.error("Error converting EQUAL QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))
        raise Exception("Error converting EQUAL QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))


def __frame_not_equal_query(field: str, value, doc_description: dict) -> dict:
    try:
        field_metadata = doc_description[field]
        query = {
            field_metadata.get(THIS_PROPERTY_PATH): {
                query_operators.query_operators[NOT_EQUAL]: get_field_type_and_cast_value(field_metadata, value)
            }
        }
        return query
    except Exception as e:
        logger.error("Error converting NOT EQUAL QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))
        raise Exception("Error converting NOT EQUAL QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))


def __frame_greater_than_query(field: str, value, doc_description: dict) -> dict:
    try:
        field_metadata = doc_description[field]
        query = {
            field_metadata.get(THIS_PROPERTY_PATH): {
                query_operators.query_operators[GREATER_THAN]: get_field_type_and_cast_value(field_metadata, value)
            }
        }
        return query
    except Exception as e:
        logger.error("Error converting GREATER THAN QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))
        raise Exception(
            "Error converting GREATER THAN QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e)
        )


def __frame_less_than_query(field: str, value, doc_description: dict) -> dict:
    try:
        field_metadata = doc_description[field]
        query = {
            field_metadata.get(THIS_PROPERTY_PATH): {
                query_operators.query_operators[LESS_THAN]: get_field_type_and_cast_value(field_metadata, value)
            }
        }
        return query
    except Exception as e:
        logger.error("Error converting LESS THAN QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))
        raise Exception("Error converting LESS THAN QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))


def __frame_less_than_equal_query(field: str, value, doc_description: dict) -> dict:
    try:
        field_metadata = doc_description[field]
        query = {
            field_metadata.get(THIS_PROPERTY_PATH): {
                query_operators.query_operators[LESS_THAN_EQUAL]: get_field_type_and_cast_value(field_metadata, value)
            }
        }
        return query
    except Exception as e:
        logger.error(
            "Error converting LESS THAN EQUAL QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e)
        )
        raise Exception(
            "Error converting LESS THAN EQUAL QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e)
        )


def __frame_greater_than_equal_query(field: str, value, doc_description: dict) -> dict:
    try:
        field_metadata = doc_description[field]
        query = {
            field_metadata.get(THIS_PROPERTY_PATH): {
                query_operators.query_operators[GREATER_THAN_EQUAL]: get_field_type_and_cast_value(field_metadata, value)
            }
        }
        return query
    except Exception as e:
        logger.error(
            "Error converting GREATER THAN EQUAL QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e)
        )
        raise Exception(
            "Error converting GREATER THAN EQUAL QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e)
        )


def __frame_in_query(field: str, value, doc_description: dict) -> dict:
    try:
        field_metadata = doc_description[field]
        query = {
            field_metadata.get(THIS_PROPERTY_PATH): {query_operators.query_operators[IN]: convert_list_value(field_metadata, value)}
        }
        return query
    except Exception as e:
        logger.error("Error converting IN QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))
        raise Exception("Error converting IN QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))


def __frame_not_in_query(field: str, value, doc_description: dict) -> dict:
    try:
        field_metadata = doc_description[field]
        query = {
            field_metadata.get(THIS_PROPERTY_PATH): {
                query_operators.query_operators[NOT_IN]: convert_list_value(field_metadata, value)
            }
        }
        return query
    except Exception as e:
        logger.error("Error converting NOT IN QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))
        raise Exception("Error converting NOT IN QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))


def __frame_exists_query(field: str, value, doc_description: dict) -> dict:
    try:
        field_metadata = doc_description[field]
        val = False
        if value.lower() == "true":
            val = True
        if value.lower() == "false":
            val = False

        query = {field_metadata.get(THIS_PROPERTY_PATH): {query_operators.query_operators[EXISTS]: val}}
        return query
    except Exception as e:
        logger.error("Error converting EXIST QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))
        raise Exception("Error converting EXIST QUERY. Field: " + str(field) + ", value: " + str(value) + ". Error: " + str(e))
