import bson

from . import constants
from opensearchlogger.logging import logger
from .common import operations, create_filter_format


class MoreFareCal:
    def _get_schema(self, mode):
        if mode == constants.MODE_FLIGHT:
            return constants.FLIGHT_MORE_FARE_CAL
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def read_more_fare_tracker_status(self, mode, leg_req_id, flight_unique_id):
        try:
            schema = self._get_schema(mode)
            filter_data = [
                create_filter_format("leg_request_id", constants.EQUAL, bson.ObjectId(leg_req_id)),
                create_filter_format("leg_details.flight_unique_id", constants.EQUAL, flight_unique_id),
            ]
            result = operations.read_one(schema, filter_data)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def insert_more_fare_tracker(self, mode, data):
        try:
            schema = self._get_schema(mode)
            result = operations.write(schema, data)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def update_more_fare_data(self, mode, leg_req_id, flight_unique_id, data, mc_lid=None):
        try:
            schema = self._get_schema(mode)
            filter_data = [
                create_filter_format("leg_request_id", constants.EQUAL, bson.ObjectId(leg_req_id)),
            ]
            if mc_lid:
                filter_data.append(
                    create_filter_format("_id", constants.EQUAL, mc_lid),
                )
            else:
                filter_data.append(
                    create_filter_format("_id", constants.EQUAL, bson.ObjectId(flight_unique_id)),
                )

            result = operations.replace_one(schema, filter_data, data, upsert=True)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e
