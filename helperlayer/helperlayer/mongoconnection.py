import os
import traceback
import urllib
from enum import Enum
from typing import Optional
from opensearchlogger.logging import logger
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, CollectionInvalid

MONGO_DB_USERNAME = os.environ["MONGO_DB_USERNAME"]
MONGO_DB_PASSWORD = os.environ["MONGO_DB_PASSWORD"]
MONGO_HOST = os.environ["MONGO_HOST"]


# https://pymongo.readthedocs.io/en/stable/api/pymongo/errors.html#pymongo.errors.ConnectionFailure


class ConnectionType(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SECONDARY_PREFERRED = "secondaryPreferred"


def get_mongo_client(connection_type: Optional[ConnectionType] = ConnectionType.PRIMARY):
    connection_param = {
        "retryWrites": "true",  # Retry write operations on failure
        "w": "majority",  # Write concern ensures majority acknowledgment
        "readPreference": connection_type.value,
    }

    encoded_username = urllib.parse.quote(MONGO_DB_USERNAME)
    encoded_password = urllib.parse.quote(MONGO_DB_PASSWORD)
    base_uri = f"mongodb+srv://{encoded_username}:{encoded_password}@{MONGO_HOST}/"

    query_string = urllib.parse.urlencode(connection_param)

    final_uri = f"{base_uri}?{query_string}"
    client = MongoClient(final_uri)
    logger.info("Mongo connection is created....")  # for reference
    return client


class PyMongoConnection:
    def __init__(self, prefered_connection: str = "primary"):
        self.__client = None
        try:
            self.__prefered_connection = ConnectionType(prefered_connection)
        except ValueError:
            raise ValueError(
                f"Invalid connection type '{prefered_connection}'. Expected 'primary' or 'secondary' or 'secondaryPreferred'."
            )

    def __enter__(self):
        self.__client = get_mongo_client(self.__prefered_connection)
        return self.__client

    def create_client(self):
        """
        Create the mongo client
        """
        try:
            self.__client = get_mongo_client(self.__prefered_connection)
        except ConnectionFailure as cfe:
            logger.error(f"Couldn't create a connection. retrying once...error: {cfe}")
            self.__client = get_mongo_client()
        except Exception as e:
            logger.error(f"Error while creating the connection. error: {traceback.format_exc()}")
            raise e

    def get_client(self):
        """
        return mongo client
        """
        self.ping()
        if not self.__client:
            self.create_client()
        return self.__client

    def ping(self, count=0):
        """
        mongo_client.alive will return False if there has been an error communicating with the server, else True.
        """
        if not self.__client:
            self.create_client()
        is_alive = False
        try:
            # The ping command is cheap and does not require auth.
            is_alive = self.__client.admin.command("ping")
        except ConnectionFailure as cfe:  # ConnectionFailure is parent of most error
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            self.create_client()
        except Exception as e:
            raise e

        return bool(is_alive)

    def find_one(self, database_name, collection_name, query, counter=0, *args, **kwargs):
        """
        find one data from collection.
        """
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            data = collection.find_one(query, *args, **kwargs)
            return data
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.find_one(database_name, collection_name, query, counter + 1, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error while fetching data from {collection_name}. error: {traceback.format_exc()}")
            raise e

    def find(self, database_name, collection_name, query=None, counter=0, limit=0, offset=0, sort_by=None):
        """
        find one data from collection.
        """
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]

            # Start with a cursor from the find() query
            cursor = collection.find(query or {})

            # Apply sorting if specified
            if sort_by:
                cursor = cursor.sort(sort_by)

            # Apply offset and limit if specified
            if offset:
                cursor = cursor.skip(offset)
            if limit:
                cursor = cursor.limit(limit)

            return list(cursor)
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.find(database_name, collection_name, query, counter + 1, limit, offset, sort_by)
        except Exception as e:
            logger.error(f"Error while fetching data from {collection_name}. error: {traceback.format_exc()}")
            raise e

    def update_many(self, database_name, collection_name, find_query, data, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            ref = collection.update_many(find_query, data)
            return ref
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.update_many(database_name, collection_name, find_query, data, counter + 1)
        except Exception as e:
            raise e

    def find_many(self):
        raise NotImplementedError("")

    def insert_one(self, database_name, collection_name, data, id=None, counter=0):
        """
        Insert one operation of mongo
        """

        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            if id is not None:
                data["_id"] = id
            insert_ref = collection.insert_one(data)
            return insert_ref
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            self.insert_one(database_name, collection_name, data, id, counter + 1)
        except Exception as e:
            raise e

    def find_one_and_update(self, database_name, collection_name, find_query, update_query, counter=0, return_document=False):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            if return_document:
                update_reference = collection.find_one_and_update(find_query, update_query, return_document=True)
            else:
                update_reference = collection.find_one_and_update(find_query, update_query)
            return update_reference
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.find_one_and_update(database_name, collection_name, find_query, update_query, counter + 1)
        except Exception as e:
            raise e

    def upsert_document(
        self,
        database_name,
        collection_name,
        find_query,
        update,
        upsert=False,
        counter=0,
    ):
        update_query = {"$set": update}
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            update_reference = collection.update_one(find_query, update_query, upsert)
            return update_reference
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.upsert_document(database_name, collection_name, find_query, update, upsert, counter + 1)
        except Exception as e:
            raise e

    def upsert_document_with_push(
        self,
        database_name,
        collection_name,
        find_query,
        update,
        upsert=False,
        counter=0,
    ):
        update_query = {"$push": update}
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            update_reference = collection.update_one(find_query, update_query, upsert)
            return update_reference
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.upsert_document_with_push(database_name, collection_name, find_query, update, upsert, counter + 1)
        except Exception as e:
            raise e

    def bulk_write(self, database_name, collection_name, update_requests, counter=0, ordered=True):
        if not update_requests:
            return None
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            ref = collection.bulk_write(update_requests, ordered=ordered)
            logger.info(f"bulk_write completed for {len(update_requests)} entries")
            return ref
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.bulk_write(database_name, collection_name, update_requests, counter + 1, ordered)
        except Exception as e:
            logger.error(f"Error while bulk write data to {collection_name}. error: {traceback.format_exc()}")
            raise e

    def replace_one(self, database_name, collection_name, find_query, data, upsert=True, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            ref = collection.replace_one(find_query, data, upsert=upsert)
            return ref
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.replace_one(database_name, collection_name, find_query, data, upsert, counter + 1)
        except Exception as e:
            raise e

    def aggregate(self, database_name, collection_name, query, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            data = list(collection.aggregate(query))
            return data
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.aggregate(database_name, collection_name, query, counter + 1)
        except Exception as e:
            logger.error(f"Error while fetching data from {collection_name}. error: {traceback.format_exc()}")
            raise e

    def count(self, database_name, collection_name, query, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            data = collection.count_documents(query)
            return data
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.aggregate(database_name, collection_name, query, counter + 1)
        except Exception as e:
            logger.error(f"Error while fetching data from {collection_name}. error: {traceback.format_exc()}")
            raise e

    def update_one(
        self,
        database_name,
        collection_name,
        filter_criteria,
        update_doc_field_set,
        array_filter=None,
        upsert=False,
        counter=0,
    ):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            update_res = collection.update_one(
                filter_criteria,
                update_doc_field_set,
                array_filters=array_filter,
                upsert=upsert,
            )
            return update_res
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.update_one(
                database_name,
                collection_name,
                filter_criteria,
                update_doc_field_set,
                array_filter,
                upsert,
                counter + 1,
            )
        except Exception as e:
            logger.error(f"Error while fetching data from {collection_name}. error: {traceback.format_exc()}")
            raise e

    def delete_many(self, database_name, collection_name, filter_criteria, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            collection.delete_many(filter_criteria)
            return
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.delete_many(database_name, collection_name, filter_criteria, counter + 1)
        except Exception as e:
            logger.error(f"Error while fetching data from {collection_name}. error: {traceback.format_exc()}")
            raise e

    def update_one_by_id(self, database_name, collection_name, doc, id, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            if id is not None:
                doc["_id"] = id
            collection.update_one({"_id": id}, {"$set": doc}, upsert=True)
            return
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.update_one_by_id(database_name, collection_name, doc, id, counter + 1)
        except Exception as e:
            logger.error(f"Error while fetching data from {collection_name}. error: {traceback.format_exc()}")
            raise e

    def close(self):
        if self.__client:
            self.__client.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("__exit__ is being called, we are good to go!!!")
        self.__client.close()

    def __del__(self):
        logger.info("__del__ is being called, we are good to go!!!")
        if self.__client:
            self.__client.close()

    def insert_document_bulk_autogenerate_id(self, database_name: str, collection_name: str, docs: list, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            res = collection.insert_many(docs)
            return {"statusCode": 200, "body": "Bulk docs inserted", "res": res}
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.insert_document_bulk_autogenerate_id(database_name, collection_name, docs, counter + 1)
        except Exception as e:
            logger.error(f"Error while inserting data to {collection_name}. error: {traceback.format_exc()}")
            raise e

    def upsert_specific_fields(
        self,
        database_name,
        collection_name,
        filter_criteria,
        update_doc_field_set,
        counter=0,
    ):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            collection.update_one(filter_criteria, update_doc_field_set, array_filters=None, upsert=True)
            return {"statusCode": 200, "body": "Document inserted / Updated!!!"}
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.upsert_specific_fields(
                database_name,
                collection_name,
                filter_criteria,
                update_doc_field_set,
                counter + 1,
            )
        except Exception as e:
            logger.error(f"Error while updating specific data for {collection_name}. error: {traceback.format_exc()}")
            raise e

    def create_collection(self, database_name, collection_name, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            db.create_collection(collection_name)
        except CollectionInvalid as e:
            raise Exception("Collection already exists ." + str(e))
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.create_collection(database_name, collection_name, counter + 1)
        except Exception as e:
            logger.error(f"Error while updating specific data for {collection_name}. error: {traceback.format_exc()}")
            raise e

    def drop_collection(self, database_name: str, collection_name: str, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            db.drop_collection(collection_name)
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.drop_collection(database_name, collection_name, counter + 1)
        except Exception as e:
            logger.error(f"Error while dropping collection. Error: {traceback.format_exc()}")
            raise e

    def insert_many(self, database_name: str, collection_name: str, docs: list, counter=0):
        if counter >= 5:
            raise ValueError("PyMongo connection is not stable.")
        try:
            self.ping()
            db = self.__client[database_name]
            collection = db[collection_name]
            res = collection.insert_many(docs)
            return res
        except ConnectionFailure as cfe:
            logger.error(f"Pymongo connection failure has occurred, retrying.... error: {cfe}")
            return self.insert_many(database_name, collection_name, docs, counter + 1)
        except Exception as e:
            logger.error(f"Error while inserting data to {collection_name}. error: {traceback.format_exc()}")
            raise e


# mongo_obj = PyMongoConnection()

if __name__ == "__main__":
    mongo_obj = PyMongoConnection()
    mongo_primary = PyMongoConnection(prefered_connection="primary")
    mongo_read = PyMongoConnection(prefered_connection="secondaryPreferred")
    mongo_db_name = "static_content"
    collection_name = "airport"
    query = {"_id": "JFK"}
    mongo_res = mongo_obj.find_one(mongo_db_name, collection_name, query)
    mongo_res = mongo_obj.find_one(mongo_db_name, collection_name, query)
    # print(mongo_obj)
    # print(mongo_obj.ping())
    # print(mongo_obj.get_client())
    # with PyMongoConnection() as mongo_client:
    #     print(mongo_client)
