class Database:
    __mongo_client = None

    def __init__(self, client):
        self.__mongo_client = client
