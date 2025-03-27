import urllib

from pymongo.errors import CollectionInvalid


class Collection:
    __mongo_client = None

    def __init__(self, client):
        self.__mongo_client = client

    def create_collection(self, db_name, collection_name):
        try:
            self.__mongo_client[urllib.parse.quote(db_name)].create_collection(collection_name)
        except CollectionInvalid as e:
            raise Exception("Collection already exists ." + str(e))
        except Exception as e:
            raise Exception("Error occurred creating collection. Please check collection name. " + str(e))
