import bson
import json
import jmespath
import uuid
from . import constants
from opensearchlogger.logging import logger
from .common import operations, create_filter_format


class Recommendation:
    def _get_schema(self, mode):
        if mode == constants.MODE_FLIGHT:
            return constants.FLIGHT_RECOMMENDATION
        elif mode == constants.MODE_HOTEL:
            return constants.HOTEL_RECOMMENDATION
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def bulk_write(self, mode, recommendation_data):
        try:
            schema = self._get_schema(mode)
            results = operations.bulk_write(schema, recommendation_data)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def write(self, mode, recommendation_data):
        try:
            schema = self._get_schema(mode)
            results = operations.write(schema, recommendation_data)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def update_many(self, mode, filters, update_data, upsert=False):
        try:
            schema = self._get_schema(mode)
            results = operations.update_many(schema, filters, update_data, upsert)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def delete_many(self, mode, filter_data):
        try:
            schema = self._get_schema(mode)
            results = operations.delete_many(schema, filter_data)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get_recommendation_by_rank(self, mode, leg_request_id, rank=1, mvh_or_huuid=None):
        try:
            filter_data = [
                create_filter_format("leg_request_id", constants.EQUAL, bson.ObjectId(leg_request_id)),
            ]
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                filter_data.append(create_filter_format("rank", constants.EQUAL, rank))
                filter_data.append(create_filter_format("is_recommended", constants.EQUAL, True))
                filter_data.append(create_filter_format("type", constants.EQUAL, "recommendation"))
                if mvh_or_huuid:
                    filter_data.append(create_filter_format("mvh", constants.EQUAL, mvh_or_huuid))
            elif mode == constants.MODE_HOTEL:
                filter_data.append(create_filter_format("rank", constants.EQUAL, str(rank)))
                filter_data.append(create_filter_format("recommended", constants.EQUAL, True))
                filter_data.append(create_filter_format("type", constants.EQUAL, "recommendation"))
                if mvh_or_huuid:
                    filter_data.append(create_filter_format("huuid", constants.EQUAL, mvh_or_huuid))

            results = operations.read_one(schema, filter_data, use_secondary=True)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get_recommendation(self, mode, leg_request_id, lid=None, fare_id=None, hid=None, uid=None, filter={}):
        try:
            filter_data = [
                create_filter_format("leg_request_id", constants.EQUAL, bson.ObjectId(leg_request_id)),
                create_filter_format("type", constants.EQUAL, "recommendation"),
            ]
            if mode == constants.MODE_FLIGHT:
                if lid:
                    filter_data.append(create_filter_format("lid", constants.EQUAL, lid))
                if fare_id:
                    filter_data.append(create_filter_format("fl.fid", constants.IN, [fare_id]))
            elif mode == constants.MODE_HOTEL:
                if not fare_id and not lid:
                    filter_data = {"$match": {"leg_request_id": bson.ObjectId(leg_request_id)}}
                    filter_data["$match"].update(filter)
                if lid:
                    filter_data.append(create_filter_format("huuid", constants.EQUAL, lid))
                if fare_id:
                    filter_data.append(create_filter_format("rms.ruid", constants.IN, [fare_id]))
                if uid:
                    filter_data.append(create_filter_format("uid", constants.EQUAL, lid))
                if hid:
                    filter_data.append(create_filter_format("hid", constants.EQUAL, lid))

            schema = self._get_schema(mode)
            results = operations.read_one(schema, filter_data, use_secondary=True)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get_recommendation_all(self, mode, leg_request_id):
        try:
            filter_data = [
                create_filter_format("leg_request_id", constants.EQUAL, bson.ObjectId(leg_request_id)),
                create_filter_format("type", constants.EQUAL, "recommendation"),
            ]
            if mode == constants.MODE_FLIGHT:
                filter_data.append(create_filter_format("is_recommended", constants.EQUAL, True))
            elif mode == constants.MODE_HOTEL:
                filter_data.append(create_filter_format("recommended", constants.EQUAL, True))
            schema = self._get_schema(mode)
            results = operations.read_all(schema, filter_data, use_secondary=True)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def update_fare_status(self, leg_request_id, flight_uniuqe_id, fare_id):
        try:
            mode = "flight"
            flight_info = self.get_recommendation(mode, leg_request_id, flight_uniuqe_id)
            for fare in flight_info["fl"]:
                if fare["fid"] == fare_id:
                    user_bnh = fare.get("bnh")
                    fare["status"] = "user_selected"
                    break
            for fare in flight_info["fl"]:
                if fare.get("bnh") == user_bnh and fare.get("status") is None:
                    fare["status"] = "ignored"
                    break

            filter_data = [
                create_filter_format("leg_request_id", constants.EQUAL, bson.ObjectId(leg_request_id)),
                create_filter_format("lid", constants.EQUAL, flight_uniuqe_id),
            ]
            schema = self._get_schema(mode)
            results = operations.replace_one(schema, filter_data, flight_info)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get_equivalent_multi_city_selected_fare(self, mode, leg_id, item_id, mc_lid, mc_fid, mc):
        try:
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                aggregate = [
                    # Todo: Uncomment when everything is good from Stream api {"$match": {"lid": leg_details["item_id"]},
                    {"$match": {"leg_request_id": bson.ObjectId(leg_id), "lid": item_id}},
                    {"$unwind": {"path": "$fl"}},
                    {"$match": {"fl.mc_lid": mc_lid, "fl.mc": mc, "fl.mc_fid": mc_fid if mc_fid else ""}},
                    {"$group": {"_id": "$_id", "root": {"$mergeObjects": "$$ROOT"}, "fl": {"$push": "$fl"}}},
                    {"$set": {"root.fl": "$fl"}},
                    {"$replaceRoot": {"newRoot": "$root"}},
                ]
            result = operations.aggregate_data(schema, aggregate)
            return result

        except Exception as ex:
            logger.error(f"An error occurred in get_equivalent_multi_city_selected_fare: {leg_id}, {item_id} {str(ex)}")
            raise ex

    def get_selected_fare(self, mode, leg_id, item_id, multi_city_related_params=None):
        try:
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                aggregate = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_id), "lid": item_id}},
                    {"$unwind": "$fl"},
                    {"$match": {"fl.status": {"$nin": ["ignored", "removed"]}}},
                    {"$group": {"_id": "$_id", "root": {"$mergeObjects": "$$ROOT"}, "fl": {"$push": "$fl"}}},
                    {"$set": {"root.fl": "$fl"}},
                    {"$replaceRoot": {"newRoot": "$root"}},
                ]
                if multi_city_related_params:
                    # Replacing match params for multi_city
                    aggregate[2] = {"$match": {"$or": [{"fl.fid": {"$eq": multi_city_related_params["fid"]}}]}}
                    if multi_city_related_params.get("ref_fid", ""):
                        aggregate[2]["$match"]["$or"].append({"fl.fid": {"$eq": multi_city_related_params["ref_fid"]}})
                    aggregate[2]["$match"]["$or"].append({"mf": {"$ne": 1}, "fl.status": {"$nin": ["ignored", "removed"]}})
            elif mode == constants.MODE_HOTEL:
                aggregate = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_id), "huuid": item_id}},
                    {"$unwind": "$rms"},
                    {"$match": {"rms.ignore": False}},
                    {"$group": {"_id": "$_id", "root": {"$mergeObjects": "$$ROOT"}, "rms": {"$push": "$rms"}}},
                    {"$set": {"root.rms": "$rms"}},
                    {"$replaceRoot": {"newRoot": "$root"}},
                ]
            result = operations.aggregate_data(schema, aggregate)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get_fare_by_leg_hash(self, mode, leg_request_id, leg_hash, cabin_class):
        try:
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                aggregate = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_request_id), "leg.lh": leg_hash, "fl.cc": cabin_class}},
                    {"$unwind": "$fl"},
                    {"$match": {"fl.status": {"$nin": ["ignored", "removed"]}}},
                    {"$group": {"_id": "$_id", "root": {"$mergeObjects": "$$ROOT"}, "fl": {"$push": "$fl"}}},
                    {"$set": {"root.fl": "$fl"}},
                    {"$replaceRoot": {"newRoot": "$root"}},
                ]
            result = operations.aggregate_data(schema, aggregate)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get_all_recommendation(self, mode, leg_request_id, cache_type, huuid=None, recommended=None, non_mc_docs=False):
        try:
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                aggregate = [{"$match": {"leg_request_id": bson.ObjectId(leg_request_id), "type": cache_type}}]
                if non_mc_docs:
                    aggregate[0]["$match"].update({"contains_mc_fare": {"$eq": False}})
                aggregate.extend(
                    [
                        {"$sort": {"rank": 1, "is_recommended": -1}},
                        {"$limit": 5},
                        {"$set": {"mf": "$mf", "mvh": "$mvh"}},
                        {
                            "$group": {
                                "_id": "$_id",
                                "ReqData": {
                                    "$push": {
                                        "_id": "$_id",
                                        "fl": "$fl",
                                        "mf": "$mf",
                                        "mvh": "$mvh",
                                        "flight_unique_id": "$lid",
                                        "in_expanded_window": "$in_expanded_window",
                                        "is_time_duration_inside_maximum_limit": "$is_time_duration_inside_maximum_limit",
                                        "budget_to_beat": "$budget_to_beat",
                                        "leg_req_id": leg_request_id,
                                    }
                                },
                            }
                        },
                    ]
                )
            elif mode == constants.MODE_HOTEL:
                filter = {
                    "leg_request_id": bson.ObjectId(leg_request_id),
                    "type": cache_type,
                    "ignore": False,
                    "rms": {"$ne": None},
                }
                if huuid:
                    filter.update({"huuid": {"$eq": huuid}})
                if recommended:
                    filter.update({"recommended": True})
                aggregate = [{"$match": filter}]
            result = operations.aggregate_data(schema, aggregate)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get_fare_and_leg_data(self, mode, leg_request_id, flight_unique_id):
        try:
            schema = self._get_schema(mode)
            aggregate = [
                {"$match": {"leg_request_id": bson.ObjectId(leg_request_id), "lid": flight_unique_id}},
                {"$set": {"fl": "$fl", "leg": "$leg"}},
                {
                    "$group": {
                        "_id": "$_id",
                        "ReqData": {"$push": {"fl": "$fl", "leg": "$leg"}},
                    }
                },
            ]
            result = operations.aggregate_data(schema, aggregate)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get_fare_data(self, mode, leg_request_id, fare_unique_id=None, huuid=None, ruid=None):
        try:
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                aggregate = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_request_id)}},
                    {"$unwind": {"path": "$fl", "includeArrayIndex": "fl_index", "preserveNullAndEmptyArrays": True}},
                    {"$match": {"fl.fid": fare_unique_id}},
                    {"$group": {"_id": "$_id", "root": {"$mergeObjects": "$$ROOT"}, "fl": {"$push": "$fl"}}},
                    {"$set": {"root.fl": "$fl"}},
                    {"$replaceRoot": {"newRoot": "$root"}},
                ]
            elif mode == constants.MODE_HOTEL:
                aggregate = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_request_id), "rms.huuid": huuid}},
                    {
                        "$project": {
                            "rms": {
                                "$filter": {
                                    "input": "$rms",
                                    "as": "rms",
                                    "cond": {"$and": [{"$eq": ["$$rms.ruid", ruid]}]},
                                }
                            }
                        }
                    },
                ]
            result = operations.aggregate_data(schema, aggregate)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def update_data_to_recommendation(self, mode, leg_request_id, flight_unique_id, data=None, rt_return_leg=False):
        try:
            schema = self._get_schema(mode)
            filter_data = [
                create_filter_format("leg_request_id", constants.EQUAL, bson.ObjectId(leg_request_id)),
                create_filter_format("_id", constants.EQUAL, bson.ObjectId(flight_unique_id)),
            ]
            mf = 2
            if rt_return_leg:
                mf = 1
            if data is not None:
                update_doc_field_set = {"$set": {"fl": data, "mf": mf}}
            else:
                update_doc_field_set = {"$set": {"mf": mf}}
            results = operations.find_one_and_update(schema, filter_data, update_doc_field_set)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def get_matched_flight(self, mode, leg_request_id, selected_hash, cabin_class):
        try:
            schema = self._get_schema(mode)
            filter_data = [
                create_filter_format("leg_request_id", constants.EQUAL, bson.ObjectId(leg_request_id)),
                create_filter_format("leg.0.lh", constants.EQUAL, selected_hash[0]),
                create_filter_format("leg.1.lh", constants.EQUAL, selected_hash[1]),
                create_filter_format("fl.cc", constants.EQUAL, cabin_class),
            ]
            result = operations.read_all(schema, filter_data)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def update_discounted_fare(self, mode, leg_request_id, flight_unique_id, fare_id, discounted_fare=1):
        try:
            schema = self._get_schema(mode)
            filter_data = [
                create_filter_format("leg_request_id", constants.EQUAL, bson.ObjectId(leg_request_id)),
                create_filter_format("lid", constants.EQUAL, flight_unique_id),
                create_filter_format("fl.fid", constants.EQUAL, fare_id),
            ]
            update_doc_field_set = {"$set": {"fl.$.df": discounted_fare}}
            results = operations.find_one_and_update(schema, filter_data, update_doc_field_set)
            return results
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise e

    def recommendation_count(self, mode, leg_request_id):
        try:
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                aggregate = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_request_id), "type": "recommendation"}},
                    {"$count": "flight_count"},
                ]
            elif mode == constants.MODE_HOTEL:
                aggregate = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_request_id), "type": "recommendation"}},
                    {"$group": {"_id": "$ignore", "fieldN": {"$sum": 1}}},
                ]
            result = operations.aggregate_data(schema, aggregate)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {}

    def get_flight_detail_and_unwind_fare(self, leg_request_id, flight_unique_id, fare_id):
        try:
            aggregate = [
                {"$match": {"leg_request_id": bson.ObjectId(leg_request_id), "_id": bson.ObjectId(flight_unique_id)}},
                {"$unwind": "$fl"},
                {"$match": {"fl.fid": fare_id}},
            ]
            schema = self._get_schema("flight")
            result = operations.aggregate_data(schema, aggregate)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {}

    def dataalert_recommendation(self, leg_request_id):
        try:
            aggregate = [
                {"$match": {"leg_request_id": bson.ObjectId(leg_request_id)}},
                {"$unwind": "$fl"},
                {"$match": {"fl.status": "valid", "fl.api": {"$in": ["travelportus", "gds", "pricelinev2"]}}},
            ]
            schema = self._get_schema("flight")
            result = operations.aggregate_data(schema, aggregate)
            return result
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None

    def fetch_multi_city_previous_leg_and_fares(self, mode, leg_id, mc_lid, mc_fid):
        try:
            # We don't have item id here
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                pipeline_to_filter_fare_and_leg = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_id)}},
                    {
                        "$match": {
                            "fl": {
                                "$elemMatch": {
                                    "mc_lid": mc_lid,
                                }
                            }
                        }
                    },
                    {"$unwind": "$fl"},
                    {
                        "$match": {
                            "fl.mc_lid": mc_lid,
                            "fl.mc_fid": mc_fid,
                        }
                    },
                    {"$group": {"_id": "$_id", "leg": {"$first": "$leg"}, "fl": {"$push": "$fl"}}},
                ]
            result = operations.aggregate_data(schema, pipeline_to_filter_fare_and_leg)
            return result

        except Exception as ex:
            logger.error(f"An error occurred in get_equivalent_multi_city_selected_fare: {leg_id}, {mc_lid} {mc_fid}" f" {str(ex)}")
            raise ex

    def aggregate_validated_leg_document(self, mode, leg_id, selected_option, fare_id):
        try:
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                aggregate = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_id)}},
                    {"$match": {"lid": selected_option}},
                    {
                        "$project": {
                            "_id": 1,
                            "fl": {"$filter": {"input": "$fl", "as": "item", "cond": {"$eq": ["$$item.fid", fare_id]}}},
                            "leg.lh": 1,
                        }
                    },
                ]
                result = operations.aggregate_data(schema, aggregate)
                return result
            else:
                return None

        except Exception as ex:
            logger.error(f"An error occurred in aggregate_validated_leg_document: {leg_id}, {selected_option} {fare_id} {str(ex)}")
            raise ex

    def update_matching_document(self, mode, find_query, update_query):
        try:
            schema = self._get_schema(mode)
            result = operations.update_one(schema, find_query, update_query)
            if result.modified_count > 0:
                return True
        except Exception as ex:
            logger.error(f"An error occurred in update_one_with_query_and_update_query: {find_query}, {update_query} {str(ex)}")
        return False

    def push_fares_in_diff_recommendation_legs_multi_city(
        self,
        mode,
        leg_request_id,
        update_query,
        update_set,
        array_filters,
        update_push=None,
    ):
        result_1, result_2 = None, None
        try:
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                update_query.update({"leg_request_id": bson.ObjectId(leg_request_id)})
                result_1 = operations.find_one_and_update(
                    schema, update_query, update_set, generate_query_req=False, array_filters=array_filters, return_document=True
                )
                if update_push:
                    for each_cabin_class in update_push:
                        current_push_query = {"$push": {"fl": {"$each": update_push[each_cabin_class]}}}
                        if each_cabin_class == result_1["fl"][0]["cc"]:
                            result_2 = operations.update_one(schema, update_query, current_push_query)
                        else:
                            # Compute same details hash
                            cc_data = json.dumps([{"cc": each_cabin_class}])
                            multi_vendor_detail = json.dumps(jmespath.search("leg[*].fgt[*].{ci:ci,cid:cid,ddt:ddt}", result_1))
                            multi_vendor_detail += cc_data
                            mvh = str(uuid.uuid3(uuid.NAMESPACE_X500, multi_vendor_detail))
                            find_query = {"leg_request_id": bson.ObjectId(leg_request_id)}
                            find_query.update({"mvh": mvh})
                            result_2 = operations.update_one(schema, find_query, current_push_query)
            return result_1, result_2
        except Exception as ex:
            logger.error(
                f"An error occurred in push_fares_in_diff_recommendation_legs_multi_city: {update_query}, {update_set} "
                f"{array_filters} {str(ex)}"
            )
            raise ex

    def get_one_way_recommendation_rank_one(self, mode, leg_request_id):
        try:
            schema = self._get_schema(mode)
            if mode == constants.MODE_FLIGHT:
                # We have to get mc = 0, or mc can be None or key is not present for old trip
                aggregate = [
                    {"$match": {"leg_request_id": bson.ObjectId(leg_request_id)}},
                    {
                        "$match": {
                            "type": "recommendation",
                            "is_recommended": True,
                            "$or": [
                                {
                                    "fl.mc": 0,
                                },
                                {
                                    "fl.mc": {
                                        "$exists": False,
                                    },
                                },
                            ],
                        }
                    },
                    {"$sort": {"rank": 1}},
                    {"$limit": 1},
                    {"$unwind": {"path": "$fl", "includeArrayIndex": "fl_index", "preserveNullAndEmptyArrays": True}},
                    {"$match": {"fl.mc": {"$nin": [1, 2]}}},
                    {"$sort": {"fl.tf.tp": 1}},
                    {"$group": {"_id": "$_id", "root": {"$mergeObjects": "$$ROOT"}, "fl": {"$push": "$fl"}}},
                    {"$set": {"root.fl": "$fl"}},
                    {"$replaceRoot": {"newRoot": "$root"}},
                ]
                result = operations.aggregate_data(schema, aggregate)
                return result[0]
            else:
                return None

        except Exception as ex:
            logger.error(f"An error occurred in get_one_way_recommendation_rank_one: {leg_request_id}, {mode} {str(ex)}")
            raise None
