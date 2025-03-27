from opensearchlogger.logging import logger
from datetime import datetime
from pymongo import WriteConcern, ReadPreference, UpdateOne, InsertOne, ReplaceOne


class MongoDBOperations:
    def __init__(self, connection):
        self.connection = connection

    def generate_query(self, filter_data):
        mongo_filter = {}

        for filter_item in filter_data:
            field = filter_item.get("field")
            operator = filter_item.get("operator").lower()
            value = filter_item.get("value")

            # Define how to handle each operator
            if operator == "eq":
                mongo_filter[field] = value  # Equality operator
            elif operator == "in":
                mongo_filter[field] = {"$in": value}  # In operator
            elif operator == "notin":
                mongo_filter[field] = {"$nin": value}  # Not in operator
            elif operator == "ne":
                mongo_filter[field] = {"$ne": value}  # Not equal
            elif operator == "gt":
                mongo_filter[field] = {"$gt": value}  # Greater than
            elif operator == "lt":
                mongo_filter[field] = {"$lt": value}  # Less than
            elif operator == "gte":
                mongo_filter[field] = {"$gte": value}  # Greater than or equal
            elif operator == "lte":
                mongo_filter[field] = {"$lte": value}  # Less than or equal
            elif operator == "regex":
                mongo_filter[field] = {"$regex": value, "$options": "i"}  # Case-insensitive regex
            elif operator == "exists":
                mongo_filter[field] = {"$exists": value}  # Field existence
            elif operator == "or":
                # Handle OR condition between multiple fields/values
                or_conditions = []
                for sub_filter in value:
                    or_conditions.append(self.generate_query([sub_filter]))
                mongo_filter["$or"] = or_conditions
            elif operator == "and":
                # Handle AND condition between multiple fields/values
                and_conditions = []
                for sub_filter in value:
                    and_conditions.append(self.generate_query([sub_filter]))
                mongo_filter["$and"] = and_conditions
            else:
                raise ValueError(f"Invalid condition '{operator}' for MongoDB.")

        return mongo_filter

    def write(self, database_name, collection, data):
        try:
            write_concern = WriteConcern("majority")
            db = self.connection[database_name]

            result = db[collection].with_options(write_concern=write_concern).insert_one(data)
            return {"_id": str(result.inserted_id)}
        except Exception as e:
            logger.error(f"Error writing to MongoDB: {e}")
            raise e

    def create_bulk_operations(self, bulk_data):
        bulk_operations = []
        for each_data in bulk_data:
            operation = each_data.get("operation")
            filter_conditions = each_data.get("filter")
            data = each_data.get("data")
            insert_or_update = each_data.get("insert_or_update", False)

            if operation == "update":
                bulk_operations.append(
                    UpdateOne(
                        {**filter_conditions},  # Use the provided filter conditions
                        {"$set": data},  # Update the fields with the data
                        upsert=insert_or_update,
                    )
                )
            elif operation == "insert":
                bulk_operations.append(InsertOne(data))  # Wrap the document in InsertOne
            elif operation == "replace":
                bulk_operations.append(
                    ReplaceOne(
                        filter_conditions,  # Use the provided filter conditions
                        data,  # Replace the document with the provided data
                        upsert=insert_or_update,
                    )
                )
            else:
                raise ValueError("Invalid operation type. Must be 'insert', 'replace', or 'update'.")
        return bulk_operations

    def bulk_write(self, database_name, collection, data):
        try:
            write_concern = WriteConcern("majority")
            db = self.connection[database_name]
            bulk_operations = self.create_bulk_operations(data)
            result = db[collection].with_options(write_concern=write_concern).bulk_write(bulk_operations)
            return result
        except Exception as e:
            logger.error(f"Error writing to MongoDB: {e}")
            raise e

    def read(self, database_name, collection, query, use_secondary=False, limit=None):
        try:
            read_preference = ReadPreference.PRIMARY
            if use_secondary:
                read_preference = ReadPreference.SECONDARY_PREFERRED
            db = self.connection[database_name]
            # print(f"Query: {query}, DB {database_name}, Collection {collection}")
            cursor = db[collection].with_options(read_preference=read_preference).find(query)
            if limit:
                cursor = cursor.limit(limit)
            result = [doc for doc in cursor]
            # print(f"Result: {result}")
            # logger.info(f"Read from MongoDB: {result}")
            return result
        except Exception as e:
            logger.error(f"Error reading from MongoDB: {e}")
            raise e

    def read_one(self, database_name, collection, filter_data, use_secondary=False):
        try:
            read_preference = ReadPreference.PRIMARY
            if use_secondary:
                read_preference = ReadPreference.SECONDARY_PREFERRED
            db = self.connection[database_name]
            query = self.generate_query(filter_data)
            cursor = db[collection].with_options(read_preference=read_preference).find_one(query)
            logger.info(f"Read from MongoDB: {cursor}")
            return cursor
        except Exception as e:
            logger.error(f"Error reading from MongoDB: {e}")
            raise e

    def read_all(self, database_name, collection, filter_data, use_secondary=False):
        try:
            read_preference = ReadPreference.PRIMARY
            if use_secondary:
                read_preference = ReadPreference.SECONDARY_PREFERRED
            db = self.connection[database_name]
            query = self.generate_query(filter_data)
            cursor = db[collection].with_options(read_preference=read_preference).find(query)
            result = [doc for doc in cursor]
            logger.info(f"Read from MongoDB: {result}")
            return result
        except Exception as e:
            logger.error(f"Error reading from MongoDB: {e}")
            raise e

    def update(self, database_name, collection, query, update, insert_or_update=False):
        try:
            current_ts = datetime.now()
            db = self.connection[database_name]
            update["updated_tn"] = current_ts
            update_fields = {
                "$set": update,
                "$setOnInsert": {"inserted_tn": current_ts},
            }
            result = db[collection].update_many(query, update_fields, insert_or_update)
            return {"modified_count": result.modified_count}
        except Exception as e:
            logger.error(f"Error updating MongoDB: {e}")
            raise e

    def aggregate_data(self, database_name, collection, pipeline):
        try:
            db = self.connection[database_name]
            result = db[collection].aggregate(pipeline)
            return [doc for doc in result]
        except Exception as e:
            logger.error(f"Error aggregating MongoDB: {e}")
            raise e

    def delete_many(self, database_name, collection, filter_data):
        try:
            write_concern = WriteConcern("majority")
            db = self.connection[database_name]
            query = self.generate_query(filter_data)
            result = db[collection].with_options(write_concern=write_concern).delete_many(query)
            return {"deleted_count": result.deleted_count}
        except Exception as e:
            logger.error(f"Error deleting from MongoDB: {e}")
            raise e

    def replace_one(self, database_name, collection, filter_data, data, insert_or_update=False):
        try:
            db = self.connection[database_name]
            query = self.generate_query(filter_data)
            result = db[collection].replace_one(query, data, upsert=insert_or_update)
            return {"modified_count": result.modified_count}
        except Exception as e:
            logger.error(f"Error replacing in MongoDB: {e}")
            raise e

    def find_one_and_update(
        self,
        database_name,
        collection,
        filter_data,
        update_data,
        upsert=False,
        generate_query_req=True,
        array_filters=None,
        return_document=False,
    ):
        try:
            db = self.connection[database_name]
            if generate_query_req:
                filter_data = self.generate_query(filter_data)
            result = db[collection].find_one_and_update(
                filter_data, update_data, upsert=upsert, array_filters=array_filters, return_document=return_document
            )
            return result
        except Exception as e:
            logger.error(f"Error finding and updating in MongoDB: {e}")
            raise e

    def update_one(self, database_name, collection, filter_criteria, update_doc_field_set, array_filters=None, upsert=False):
        try:
            db = self.connection[database_name]
            result = db[collection].update_one(filter_criteria, update_doc_field_set, array_filters=array_filters, upsert=upsert)
            return result
        except Exception as e:
            logger.error(f"Error finding and updating in MongoDB: {e}")
            raise e
