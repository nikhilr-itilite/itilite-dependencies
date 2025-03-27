import bson

from . import constants
from opensearchlogger.logging import logger
from .common import operations


class Transformation:
    def _get_schema(self, mode):
        if mode == constants.MODE_FLIGHT:
            return constants.FLIGHT_TRANSFORMATION
        elif mode == constants.MODE_HOTEL:
            return constants.HOTEL_TRANSFORMATION
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def find_one(self, mode, leg_request_id):
        schema = self._get_schema(mode)
        query = {"leg_request_id": bson.ObjectId(leg_request_id)}
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

    def insert_one(self, mode, data):
        schema = self._get_schema(mode)
        insert_id = operations.write(schema, data)
        logger.info("Inserted document ID in transformation collection: %s, %s", insert_id, data)
        return insert_id

    def aggregate_data(self, mode, leg_request_id, search_type=None, mvh_key=None):
        try:
            schema = self._get_schema(mode)
            match_query = {"$match": {"leg_request_id": bson.ObjectId(leg_request_id)}}
            if mode == "flight":
                match_query["$match"].update({"type": mode})
                aggregate = [
                    match_query,
                    {"$unwind": {"path": "$data.result", "includeArrayIndex": "index", "preserveNullAndEmptyArrays": True}},
                    {
                        "$facet": {
                            "vendor_search_split": [{"$group": {"_id": "$vendor_request_id", "count": {"$sum": 1}}}],
                            "duplicates": [
                                {
                                    "$group": {
                                        "_id": "$data.result.mvh",
                                        "count": {"$sum": 1},
                                        "unique_values": {"$addToSet": "$data.result.mvh"},
                                    }
                                },
                                {
                                    "$project": {
                                        "count": 1,
                                        "unique_count": {"$size": "$unique_values"},
                                        "duplicate_count": {"$subtract": ["$count", 1]},
                                    }
                                },
                                {
                                    "$group": {
                                        "_id": None,
                                        "unique_flights": {"$sum": "$unique_count"},
                                        "duplicate_flights": {"$sum": "$duplicate_count"},
                                    }
                                },
                            ],
                            "count": [{"$count": "total_count"}],
                        }
                    },
                ]
                if search_type and search_type == "farequote":
                    match_query["$match"].update({"type": mode})
                    aggregate = [
                        match_query,
                        {"$unwind": "$data"},
                        {"$unwind": "$data.result"},
                        {"$match": {"data.result.mvh": mvh_key}},
                        {"$replaceRoot": {"newRoot": "$data.result"}},
                    ]
            if mode == "hotel":
                aggregate = [
                    match_query,
                    {"$unwind": {"path": "$data", "includeArrayIndex": "index", "preserveNullAndEmptyArrays": True}},
                    {
                        "$facet": {
                            "vendor_search_split": [{"$group": {"_id": "$vendor_request_id", "count": {"$sum": 1}}}],
                            "duplicates": [
                                {"$group": {"_id": "$data.uid", "count": {"$sum": 1}, "unique_values": {"$addToSet": "$data.uid"}}},
                                {
                                    "$project": {
                                        "count": 1,
                                        "unique_count": {"$size": "$unique_values"},
                                        "duplicate_count": {"$subtract": ["$count", 1]},
                                    }
                                },
                                {
                                    "$group": {
                                        "_id": None,
                                        "unique_hotels": {"$sum": "$unique_count"},
                                        "duplicate_hotels": {"$sum": "$duplicate_count"},
                                    }
                                },
                            ],
                            "count": [{"$count": "total_count"}],
                        }
                    },
                ]
            result = operations.aggregate_data(schema, aggregate)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None

    def aggregate_multi_city_transform_data(self, mode, leg_request_id, batch_request_ids, current_leg_no):
        pipeline = None
        try:
            schema = self._get_schema(mode)
            if mode == "flight":
                limit = 0 if batch_request_ids else 10
                pipeline = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_request_id)}},
                    {"$match": {"_id": {"$nin": batch_request_ids}}},
                    {
                        "$addFields": {
                            "data.result": {
                                "$map": {
                                    "input": "$data.result",
                                    "as": "res",
                                    "in": {
                                        "fl": {
                                            "$cond": [
                                                {"$eq": [{"$size": "$$res.fl"}, 1]},
                                                "$$res.fl",
                                                {
                                                    "$map": {
                                                        "input": {"$range": [0, int(current_leg_no)]},
                                                        "as": "idx",
                                                        "in": {
                                                            "$cond": [
                                                                {"$eq": ["$$idx", int(current_leg_no) - 1]},
                                                                {"$arrayElemAt": ["$$res.fl", "$$idx"]},
                                                                {
                                                                    "bn": {"$arrayElemAt": ["$$res.fl.bn", "$$idx"]},
                                                                    "bnh": {"$arrayElemAt": ["$$res.fl.bnh", "$$idx"]},
                                                                    "fid": {"$arrayElemAt": ["$$res.fl.fid", "$$idx"]},
                                                                    "cc": {"$arrayElemAt": ["$$res.fl.cc", "$$idx"]},
                                                                    "fs": {"$arrayElemAt": ["$$res.fl.fs", "$$idx"]},
                                                                },
                                                            ]
                                                        },
                                                    }
                                                },
                                            ]
                                        },
                                        "leg": {
                                            "$map": {
                                                "input": {"$range": [0, int(current_leg_no)]},
                                                "as": "idx",
                                                "in": {
                                                    "$cond": [
                                                        {"$eq": ["$$idx", int(current_leg_no) - 1]},
                                                        {"$arrayElemAt": ["$$res.leg", "$$idx"]},
                                                        {
                                                            "lh": {"$arrayElemAt": ["$$res.leg.lh", "$$idx"]},
                                                        },
                                                    ]
                                                },
                                            }
                                        },
                                        "mc_doc": 1,
                                        "lid": "$$res.lid",
                                        "mvh": "$$res.mvh",
                                    },
                                }
                            }
                        }
                    },
                ]
                if limit:
                    pipeline.extend([{"$limit": limit}])
                result = operations.aggregate_data(schema, pipeline)
                return result
        except Exception as ex:
            logger.error(f" Error occured in fetching transformed data {str(ex)} {leg_request_id} {current_leg_no} {pipeline}")

    def fetch_particular_transformed_batch_morefarecall(self, mode, leg_request_id, vendor_request_id, batch_no):
        try:
            schema = self._get_schema(mode)
            query = {
                "leg_request_id": bson.ObjectId(leg_request_id),
                "vendor_request_id": vendor_request_id,
                "batch_no": batch_no,
                "type": mode,
            }
            transformation_data = operations.read(schema, query)
            if transformation_data and isinstance(transformation_data, list):
                return transformation_data[0]
        except Exception as ex:
            logger.error(
                f" Error occured while fetch_particular_transformed_batch_morefarecall {mode} {leg_request_id} "
                f"{vendor_request_id} {batch_no} {str(ex)}"
            )

    def fetch_particular_transformed_flight_result(self, mode, leg_request_id, lid, batch_no=None):
        try:
            schema = self._get_schema(mode)

            pipeline_for_fetching_particular_flight_result = [
                {"$match": {"leg_request_id": bson.ObjectId(leg_request_id), "type": "flight"}},
            ]
            if batch_no is not None:
                pipeline_for_fetching_particular_flight_result[0]["$match"].update({"batch_no": batch_no})
            pipeline_for_fetching_particular_flight_result.extend(
                [
                    {"$unwind": {"path": "$data.result", "includeArrayIndex": "string", "preserveNullAndEmptyArrays": True}},
                    {"$match": {"data.result.lid": lid}},
                    {"$project": {"_id": 0, "result": "$data.result.leg"}},
                ]
            )
            result = operations.aggregate_data(schema, pipeline_for_fetching_particular_flight_result)
            if result:
                return [result[0]["result"]]
        except Exception as ex:
            logger.error(
                f" Error occured while fetch_particular_transformed_flight gordian seat {mode} {leg_request_id} " f"{lid} {str(ex)}"
            )
