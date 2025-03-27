from opensearchlogger.logging import logger
import urllib

from pydantic import ValidationError

from mongoconnector import constants
from mongoconnector.searchbuilder import search_builder
from mongoconnector.searchbuilder.models.query_model import Query
from mongoconnector.utils import load_file_content, sub_query_validate
from mongoconnector.searchbuilder import query_operators


class Search:
    __mongo_client = None
    __query = None
    __doc_description = None

    def __init__(self, client, schema_file_name, query):
        self.__mongo_client = client
        if schema_file_name and query:
            res = self.__validate(schema_file_name, query)
            self.__query = res[constants.QUERY_VALIDATE]
            self.__doc_description = res[constants.DOC_DESCRIPTION]

    def __search_docs_aggregation(self, db_name, collection_name, query):
        try:
            logger.info("Mongo data search  :" + str(collection_name))
            collection = self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name))
            cursor = collection.aggregate(query)
            list_cur = list(cursor)
            logger.info("Mongo filter result: " + str(list_cur))
            return list_cur

        except Exception as e:
            raise Exception("Error searching documents. Please check query" + str(query) + ". Error: " + str(e))

    def find_docs(self, db_name, collection_name, schema_doc_path=None, query=None):
        try:
            search_docs = []
            if schema_doc_path is None and query is None:
                framed_query = search_builder.frame_query(self.__query, self.__doc_description)
                search_docs = self.__search_docs_aggregation(db_name, collection_name, framed_query)
            else:
                res = self.__validate(schema_doc_path, query)
                query = res[constants.QUERY_VALIDATE]
                doc_description = res[constants.DOC_DESCRIPTION]
                framed_query = search_builder.frame_query(query, doc_description)
                search_docs = self.__search_docs_aggregation(db_name, collection_name, framed_query)
            return {"statusCode": 200, "body": search_docs}
        except ValidationError as e:
            raise Exception("Validate the query input or Object initialized correctly. Error: " + str(e))

    def __validate(self, schema_file_name, query):
        query = Query(**query)
        file_path = f"./resource/{schema_file_name}".format(schema_file_name=schema_file_name)
        doc_description = load_file_content(file_path)
        sub_query_validate(query.query.subquery, doc_description)
        return {
            constants.QUERY_VALIDATE: query,
            constants.DOC_DESCRIPTION: doc_description,
        }

    def find_doc_by_id(self, db_name: str, collection_name: str, id: str) -> dict:
        collection = self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name))
        cursor = collection.find({constants.MONGO_ID: {query_operators.query_operators[constants.EQUAL]: id}})
        list_cur = list(cursor)
        return list_cur

    def mongo_raw_query_find(self, db_name: str, collection_name: str, query: dict) -> dict:
        collection = self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name))
        cursor = collection.find(query)
        list_cur = list(cursor)
        return list_cur

    def mongo_raw_query_aggregate(self, db_name: str, collection_name: str, query_pipeline) -> dict:
        collection = self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name))
        cursor = collection.aggregate(query_pipeline)
        list_cur = list(cursor)
        return list_cur

    def mongo_raw_query_find_with_limit(self, db_name: str, collection_name: str, query: dict, limit_size: int = 50) -> dict:
        collection = self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name))
        cursor = collection.find(query).limit(limit_size)
        list_cur = list(cursor)
        return list_cur

    def mongo_raw_query_find_one(self, db_name: str, collection_name: str, query: dict) -> dict:
        collection = self.__mongo_client[urllib.parse.quote(db_name)].get_collection(urllib.parse.quote(collection_name))
        cursor = collection.find_one(query)
        dict_cursor = cursor
        return dict_cursor
