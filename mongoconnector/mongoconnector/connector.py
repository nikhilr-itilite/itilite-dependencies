import os

from pymongo import MongoClient
import urllib

from mongoconnector.mongo_adminer.collection import Collection
from mongoconnector.mongo_adminer.database import Database
from mongoconnector.mongo_adminer.document import Documents
from mongoconnector.mongo_adminer.search import Search

MONGO_DB_PASSWORD = os.environ["MONGO_DB_PASSWORD"]
MONGO_DB_USERNAME = os.environ["MONGO_DB_USERNAME"]
MONGO_HOST = os.environ["MONGO_HOST"]


def get_mongo_client():
    client = MongoClient(
        "mongodb+srv://" + urllib.parse.quote(MONGO_DB_USERNAME) + ":" + urllib.parse.quote(MONGO_DB_PASSWORD) + "@" + MONGO_HOST
    )
    return client


class Connector:
    __mongo_client = None
    __query = None
    __doc_description = None

    document_service = None
    collection_service = None
    search_service = None
    database_service = None

    # TODO Document schema validation
    # TODO query validation
    # TODO Text search like , =
    def __init__(self, schema_file_name=None, query=None):
        self.__client = self.__create_client()
        self.__make_connections()

    def __make_connections(self, schema_file_name=None, query=None):
        try:
            client = MongoClient(
                "mongodb+srv://"
                + urllib.parse.quote(MONGO_DB_USERNAME)
                + ":"
                + urllib.parse.quote(MONGO_DB_PASSWORD)
                + "@"
                + MONGO_HOST
            )

            self.__mongo_client = client
            self.document_service = Documents(client)
            self.collection_service = Collection(client)
            self.search_service = Search(client, schema_file_name, query)
            self.database_service = Database(client)

        except Exception as e:
            print(str(e))
            raise Exception("Error getting mongo connection" + ". Error: " + str(e))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__mongo_client.close()

    def __del__(self):
        self.__mongo_client.close()

    def get_connector(self):
        return self.__mongo_client
