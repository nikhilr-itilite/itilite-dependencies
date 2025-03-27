from opensearchlogger.logging import logger
from .config import config
from .mongo.connect import MongoDBConnection
from .mongo.operation import MongoDBOperations

# from redisdb.connect import RedisConnection
# from redisdb.operation import RedisOperations


class DBConfig:
    def __init__(self):
        self.config = config
        self.active_databases = self.config.get("active_databases", [])
        self.data_mappings = self.config.get("data_mappings", {})

    def get_db_config(self, db_name):
        return self.config["databases"].get(db_name, {})

    def get_data_mapping(self, store_type):
        return self.data_mappings.get(store_type, {})


class OperationWrapper:
    def __init__(self, config):
        self.config = config
        self.connections = {}
        self.operations = {}

    def _initialize_operations(self, store_name):
        if store_name not in self.operations:
            if "mongodb" in self.config.active_databases and store_name == "mongodb":
                mongo_connect = MongoDBConnection(self.config.get_db_config("mongodb"))
                mongo_connection = mongo_connect.get_connection()
                self.connections["mongodb"] = mongo_connection
                self.operations["mongodb"] = MongoDBOperations(mongo_connection)

        # if "redis" in self.config.active_databases:
        #     redis_connect = RedisConnection(self.config.get_db_config("redis"))
        #     self.connections["redis"] = redis_connect
        #     self.operations["redis"] = RedisOperations(redis_connect)

    def _get_db_operation(self, store_type):
        mapping = self.config.get_data_mapping(store_type)
        store_name = mapping.get("store")
        database = mapping.get("database")
        schema = mapping.get("schema")
        primary_key = mapping.get("primary_key")

        self._initialize_operations(store_name)
        operation = self.operations.get(store_name)

        return mapping, database, schema, primary_key, operation

    def write(self, store_type, data):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        # if primary_key in data:
        return operation.write(database, schema, data)
        # raise ValueError(f"Primary key '{primary_key}' missing in data")

    def read(self, store_type, keys, use_secondary=False, limit=None):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.read(database, schema, keys, use_secondary, limit)

    def read_one(self, store_type, keys, use_secondary=False):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.read_one(database, schema, keys, use_secondary)

    def read_all(self, store_type, keys, use_secondary=False):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.read_all(database, schema, keys, use_secondary)

    def update(self, store_type, keys, data, upsert=False):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.update(database, schema, keys, data, upsert)

    def update_many(self, store_type, filters, update_data, upsert=False):
        # Retrieve the necessary configuration (mapping, database, schema, etc.)
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)

        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        try:
            return operation.update(database, schema, filters, update_data, upsert)
        except Exception as e:
            logger.error(f"Error updating documents for {store_type}: {e}")
            raise

    def bulk_write(self, store_type, data):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.bulk_write(database, schema, data)

    def delete_many(self, store_type, filter_data):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.delete_many(database, schema, filter_data)

    def replace_one(self, store_type, filter_data, update_data, upsert=False):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.replace_one(database, schema, filter_data, update_data, upsert)

    def aggregate_data(self, store_type, pipeline):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.aggregate_data(database, schema, pipeline)

    def find_one_and_update(
        self, store_type, filter_data, update_data, upsert=False, generate_query_req=True, array_filters=None, return_document=False
    ):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.find_one_and_update(
            database,
            schema,
            filter_data,
            update_data,
            upsert=upsert,
            generate_query_req=generate_query_req,
            array_filters=array_filters,
            return_document=return_document,
        )

    def update_one(self, store_type, filter_criteria, update_doc_field_set, array_filters=None, upsert=False):
        mapping, database, schema, primary_key, operation = self._get_db_operation(store_type)
        if not operation or not mapping:
            logger.error(f"No configuration found for data type: {store_type}")
            raise ValueError(f"No configuration found for data type: {store_type}")
        return operation.update_one(
            database, schema, filter_criteria, update_doc_field_set, array_filters=array_filters, upsert=upsert
        )
