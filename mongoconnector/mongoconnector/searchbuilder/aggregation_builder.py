from mongoconnector.constants import (
    FIRST,
    PARENT_PATH,
    NESTED,
    TYPE,
    UNWIND,
    PATH,
    DOLLAR,
    THIS_PROPERTY_PATH,
    INCLUDE_ARRAY_INDEX,
    NAME,
    INDEX,
    PRESERVE_NULL_EMPTY_VALUES,
    SORT,
    MONGO_ID,
    PUSH,
)
from mongoconnector.searchbuilder import query_operators
from opensearchlogger.logging import logger


def frame_sort(field: str, order_by: int, doc_description: dict):
    try:
        sort_query = []
        field_metadata = doc_description[field]
        parent = field_metadata.get(PARENT_PATH)
        if parent is not None:
            field_metadata_parent = doc_description[parent]
            if field_metadata_parent.get(TYPE) == NESTED:
                unwind = {
                    query_operators.query_operators[UNWIND]: {
                        PATH: DOLLAR + field_metadata_parent.get(THIS_PROPERTY_PATH),
                        INCLUDE_ARRAY_INDEX: field_metadata_parent.get(NAME) + INDEX,
                        PRESERVE_NULL_EMPTY_VALUES: True,
                    }
                }
                sort_query.append(unwind)

        sort = {query_operators.query_operators[SORT]: {field_metadata.get(THIS_PROPERTY_PATH): order_by}}
        sort_query.append(sort)
        return sort_query
    except Exception as e:
        logger.error("Error processing sort. Field: " + str(field) + ", order_by: " + str(order_by) + ". Error: " + str(e))
        raise Exception("Error processing sort. Field: " + str(field) + ", order_by: " + str(order_by) + ". Error: " + str(e))


def frame_group_by(group_by_text: str):
    try:
        group_by = group_by_text.group_by
        response_fields = group_by_text.doc_response_fields
        res_obj = {}
        res_obj[MONGO_ID] = str(DOLLAR + str(group_by))
        for val in response_fields:
            if bool(val.complete_obj):
                res_obj[val.return_obj_name] = {query_operators.query_operators[PUSH]: str(DOLLAR + val.field_path)}
            else:
                res_obj[response_fields.return_obj_name] = {query_operators.query_operators[FIRST]: str(DOLLAR + val.field_path)}

        group_by_query = {query_operators.query_operators["group"]: res_obj}
        return group_by_query
    except Exception as e:
        logger.error("Error processing group by. Group by query: " + str(group_by_text) + ". Error: " + str(e))
        raise Exception("Error processing group by. Group by query: " + str(group_by_text) + ". Error: " + str(e))


def frame_exact_match(exact_match_obj: dict, queries: dict, doc_description: dict):
    try:
        exact_match = []
        field_metadata = doc_description[exact_match_obj.match_field_path]
        reached_root_parent = False
        parent_path_meta_data = field_metadata

        while not reached_root_parent:
            #     TODO unwind all parent nested obj's
            if parent_path_meta_data and parent_path_meta_data.get(TYPE) == NESTED:
                unwind = {
                    query_operators.query_operators[UNWIND]: {
                        PATH: DOLLAR + parent_path_meta_data.get(THIS_PROPERTY_PATH),
                        INCLUDE_ARRAY_INDEX: parent_path_meta_data.get(NAME) + INDEX,
                        PRESERVE_NULL_EMPTY_VALUES: True,
                    }
                }
                exact_match.append(unwind)

            if parent_path_meta_data.get(PARENT_PATH) is None:
                reached_root_parent = True
            else:
                parent_path_meta_data = doc_description[parent_path_meta_data.get(PARENT_PATH)]

        exact_match.reverse()
        condn = exact_match_obj.condition
        exact_match_condition_query = queries.get(condn)
        exact_match_query = {query_operators.query_operators["match"]: exact_match_condition_query}
        exact_match.append(exact_match_query)
        return exact_match
    except Exception as e:
        logger.error(
            "Error processing Exact match for nested fields. Exact match query: "
            + str(exact_match_obj)
            + ". Queries Framed: "
            + str(queries)
            + ". Error: "
            + str(e)
        )
        raise Exception(
            "Error processing Exact match for nested fields. Exact match query: "
            + str(exact_match_obj)
            + ". Queries Framed: "
            + str(queries)
            + ". Error: "
            + str(e)
        )
