from datetime import datetime
import bson
from .common import operations
from opensearchlogger.logging import logger


class Farequote:
    def insert_farequote(self, mode, farequote_data, farequote_request_id):
        farequote_data["_id"] = bson.ObjectId(farequote_request_id)
        if mode == "flight":
            schema = "flight_farequote"
        elif mode == "hotel":
            schema = "hotel_farequote"
        farequote_data["insert_tn"] = datetime.now()
        farequote_data["upsert_tn"] = datetime.now()
        insert_id = operations.write(schema, farequote_data)
        logger.info("Inserted document ID in farequote collection: %s, %s", insert_id, farequote_data)
        return insert_id

    def find_farequote(self, mode, farequote_request_id):
        if mode == "flight":
            schema = "flight_farequote"
        elif mode == "hotel":
            schema = "hotel_farequote"
        query = {"_id": bson.ObjectId(farequote_request_id)}
        farequote_data = operations.read(schema, query)
        if farequote_data:
            return farequote_data[0]
        logger.info("Farequote data: %s", farequote_data)
        return farequote_data
