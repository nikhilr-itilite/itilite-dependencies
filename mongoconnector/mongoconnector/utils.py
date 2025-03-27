import json
from opensearchlogger.logging import logger

from mongoconnector.searchbuilder.query_operators import (
    query_operators_conditional,
    query_operators_predicate,
)


def get_field_type_and_cast_value(field_metadata, value):
    try:
        type = field_metadata.get("type")
        if type == "str":
            return str(value)
        elif type == "int":
            return int(value)
        elif type == "float":
            return float(value)
        elif type == "array":
            return get_array_field_value(field_metadata, value)
    except Exception as e:
        logger.error(
            "Error converting data to its doc_description type. Field: "
            + str(field_metadata)
            + ", value: "
            + str(value)
            + ". Error: "
            + str(e)
        )
        raise Exception(
            "Error converting data to its doc_description type. Field: "
            + str(field_metadata)
            + ", value: "
            + str(value)
            + ". Error: "
            + str(e)
        )


def get_array_field_value(field_metadata, value):
    try:
        sub_type = field_metadata.get("sub_type")
        val = value.strip("][").strip().split(",")
        new_converted_values = []
        if sub_type == "str":
            for data in val:
                new_converted_values.append(str(data))
        elif sub_type == "int":
            for data in val:
                new_converted_values.append(int(data))
        elif sub_type == "float":
            for data in val:
                new_converted_values.append(float(data))

        return new_converted_values
    except Exception as e:
        logger.error(
            "Error converting array field value to its doc_description type. Field: "
            + str(field_metadata)
            + ", value: "
            + str(value)
            + ". Error: "
            + str(e)
        )
        raise Exception(
            "Error converting array field value to its doc_description type. Field: "
            + str(field_metadata)
            + ", value: "
            + str(value)
            + ". Error: "
            + str(e)
        )


def convert_list_value(field_metadata, value):
    try:
        type = field_metadata.get("type")
        val = value.strip("][").strip().split(",")
        new_converted_values = []
        if type == "str":
            for data in val:
                new_converted_values.append(str(data.strip()))
        elif type == "int":
            for data in val:
                new_converted_values.append(int(data.strip()))
        elif type == "float":
            for data in val:
                new_converted_values.append(float(data.strip()))

        return new_converted_values
    except Exception as e:
        logger.error(
            "Error converting IN QUERY field value to its doc_description type. Field: "
            + str(field_metadata)
            + ", value: "
            + str(value)
            + ". Error: "
            + str(e)
        )
        raise Exception(
            "Error converting IN QUERY field value to its doc_description type. Field: "
            + str(field_metadata)
            + ", value: "
            + str(value)
            + ". Error: "
            + str(e)
        )


def sub_query_validate(v, doc_description):
    for k, val in v.items():
        for k2, val2 in val.items():
            if k2.lower() not in query_operators_conditional:
                raise ValueError("Provide correct conditional/predicate operators. Query Operator: " + str(k2))
            for query in val2:
                split_query_data = None
                try:
                    split_query_data = query.split(" ")
                    if doc_description[split_query_data[0]] is None:
                        raise ValueError("Schema description does not have field : " + split_query_data[0])
                    if split_query_data[1] not in query_operators_predicate:
                        raise ValueError("Wrong predicate operator: " + split_query_data[1])
                    if split_query_data[2]:
                        meta_data = doc_description[split_query_data[0]]
                        get_field_type_and_cast_value(meta_data, split_query_data[2])
                except Exception as e:
                    raise ValueError("Correct the query. " + str(e))


def load_file_content(file_path):
    with open(file_path) as doc_Schema_file:
        file_contents = doc_Schema_file.read()
    content = json.loads(file_contents)
    return content
