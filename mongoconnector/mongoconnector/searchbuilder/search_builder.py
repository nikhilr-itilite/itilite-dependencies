from opensearchlogger.logging import logger

from mongoconnector.constants import RETURN_QUERY_DICT, FRAMED_QUERIES, MATCH, AND_OPERATOR, OR_OPERATOR
from mongoconnector.searchbuilder.models.query_model import Query, SubQuery
from mongoconnector.searchbuilder import (
    operators_predicate_query_builder,
    aggregation_builder,
)
from mongoconnector.searchbuilder import query_operators


def __frame_find_query(query: Query, doc_description: dict):
    try:
        queries_list = {}
        for key, value in query.query.subquery.items():
            query_txt = __detect_operator_and_frame(value, doc_description)
            queries_list[key] = query_txt

        if query.query.compound_query and queries_list and len(queries_list) >= 1:
            q_framed = __frame_compound_query(query.query.compound_query, queries_list)
        else:
            q_framed = __frame_compound_query({}, queries_list)
        return {RETURN_QUERY_DICT: queries_list, FRAMED_QUERIES: q_framed}

    except Exception as e:
        logger.error("Error building find query. Please check query" + str(query) + ". Error: " + str(e))
        raise Exception("Error building find query. Please check query" + str(query) + ". Error: " + str(e))


def frame_query(query: Query, doc_description: dict):
    try:
        pipeline = []
        query_objects = __frame_find_query(query, doc_description)
        framed_find_query = {query_operators.query_operators[MATCH]: query_objects[FRAMED_QUERIES]}
        pipeline.append(framed_find_query)

        if query.query.nested_exact_match:
            frame_exact_match_query = aggregation_builder.frame_exact_match(
                query.query.nested_exact_match,
                query_objects[RETURN_QUERY_DICT],
                doc_description,
            )
            for xact_q in frame_exact_match_query:
                pipeline.append(xact_q)

        if query.sort_by:
            for key, value in query.sort_by.items():
                sort_by_query = aggregation_builder.frame_sort(key, value, doc_description)
                for sort_q in sort_by_query:
                    pipeline.append(sort_q)

        if query.group:
            group_by_query = aggregation_builder.frame_group_by(query.group)
            pipeline.append(group_by_query)

        pipeline = __pagination(pipeline, query)
        logger.info("Final Framed Query: " + str(pipeline))
        return pipeline

    except Exception as e:
        logger.error("Error building find query aggregation pipline. Please check query " + str(query) + ". Error: " + str(e))
        raise Exception("Error building find query aggregation pipline. Please check query " + str(query) + ". Error: " + str(e))


def __detect_operator_and_frame(query: SubQuery, doc_description: dict) -> dict:
    try:
        query_mongo: str = None
        for key, value in query.items():
            if str(key).lower() == AND_OPERATOR:
                query_mongo = operators_predicate_query_builder.frame_and_query(value, doc_description)
            if str(key).lower() == OR_OPERATOR:
                query_mongo = operators_predicate_query_builder.frame_or_query(value, doc_description)
        return query_mongo

    except Exception as e:
        logger.error(
            "Error building find query. And/OR opertor framing error. Please check query " + str(query) + ". Error: " + str(e)
        )
        raise Exception(
            "Error building find query. And/OR opertor framing error. Please check query " + str(query) + ". Error: " + str(e)
        )


def __frame_compound_query(compound_query: dict, queries_list: list):
    try:
        queries = []
        for key, value in queries_list.items():
            queries.append(value)

        query_mongo: str = None
        for key, value in compound_query.items():
            if str(key).lower() == OR_OPERATOR:
                query_mongo = {query_operators.query_operators[OR_OPERATOR]: queries}
            else:
                query_mongo = {query_operators.query_operators[AND_OPERATOR]: queries}
        if query_mongo is None and len(queries) >= 1:
            query_mongo = queries[0]

        return query_mongo
    except Exception as e:
        logger.error(
            "Error building find query. Error combining query object and framing as single query. Please check query "
            + str(compound_query)
            + ". Error: "
            + str(e)
        )
        raise Exception(
            "Error building find query. Error combining query object and framing as single query. Please check query "
            + str(compound_query)
            + ". Error: "
            + str(e)
        )


def __pagination(pipeline: dict, query: Query) -> dict:
    page_no = int(query.page_no[0]) if type(query.page_no) is tuple else int(query.page_no)
    page_size = int(query.page_size[0]) if type(query.page_size) is tuple else int(query.page_size)
    skips = page_size * (page_no - 1)
    pagination = {"$skip": skips}
    pipeline.append(pagination)
    pagination = {"$limit": page_size}
    pipeline.append(pagination)
    return pipeline
