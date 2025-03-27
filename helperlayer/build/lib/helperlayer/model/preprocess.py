import bson
import traceback

from . import constants
from opensearchlogger.logging import logger

from .common import operations


class PreProcess:
    def _get_schema(self, mode):
        if mode == constants.MODE_FLIGHT:
            return constants.FLIGHT_PREPROCESS
        elif mode == constants.MODE_HOTEL:
            return constants.HOTEL_PREPROCESS
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def find_one(self, mode, leg_request_id, cache_type_id=None, extra_query={}):
        schema = self._get_schema(mode)
        query = {"leg_request_id": bson.ObjectId(leg_request_id)}
        if cache_type_id:
            query.update({"cache_type_id": cache_type_id})
        if extra_query:
            query.update(extra_query)
        transformation_data = operations.read(schema, query)
        if transformation_data and isinstance(transformation_data, list):
            return transformation_data[0]
        # logger.info("Transformation data: %s", transformation_data)
        return transformation_data

    def find_all(self, mode, leg_request_id, extra_query={}, limit=None):
        schema = self._get_schema(mode)
        query = {"leg_request_id": bson.ObjectId(leg_request_id)}
        if extra_query:
            query.update(extra_query)
        transformation_data = operations.read(schema, query, limit=limit)
        # logger.info("All Transformation data: %s", transformation_data)
        return transformation_data

    def update_one_by_id(self, mode, leg_req_id, cache_type_id, data):
        try:
            schema = self._get_schema(mode)
            filter_data = {
                "$and": [
                    {"leg_request_id": bson.ObjectId(leg_req_id)},
                    {"cache_type_id": cache_type_id},
                ]
            }
            logger.info(f"update_one_by_id--- {filter_data}")
            result = operations.update(schema, filter_data, data, True)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {traceback.format_exc()}")
            raise e
