from pymongo import MongoClient
import os
import urllib

from pymongo.errors import ConnectionFailure

MONGO_CON_RETRY_COUNT = int(os.getenv("CONNECTION_RETRY_MAX_COUNT", 3))


class MongoDBConnection:
    """MongoDB Connection as context"""

    __connection = None
    _instance = None
    __username = None
    __password = None
    __host = None
    __port = None

    def __new__(cls, *args, **kwargs):
        print("I am in new")
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self, config):
        self.__username = config.get("username")
        self.__password = config.get("password")
        self.__host = config.get("host")
        self.__port = config.get("port")
        self.__create_connection()
        print("I am in init")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__connection.close()

    def get_connection(self):
        if self.ping() is False:
            self.__create_connection()
        return self.__connection

    def close_connection(self):
        try:
            if self.__connection is not None:
                self.__connection.close()
        except Exception as e:
            print(f"Pymongo closing connection failure.... error: {e}")

    def __get_mongo_client(self):
        print("I am creating a mongo client")
        if self.__host == "127.0.0.1":
            connection_prefix = "mongodb://"
        else:
            connection_prefix = "mongodb+srv://"
        print(f"{connection_prefix}{urllib.parse.quote(self.__username)}:{urllib.parse.quote(self.__password)}@{self.__host}")
        client = MongoClient(
            connection_prefix + urllib.parse.quote(self.__username) + ":" + urllib.parse.quote(self.__password) + "@" + self.__host,
            retryWrites=True,
            connect=False,
        )
        return client

    def ping(self):
        """
        mongo_client.alive will return False if there has been an error communicating with the server, else True.
        """
        is_alive = False
        try:
            # The ping command is cheap and does not require auth.
            if self.__connection is not None:
                is_alive = self.__connection.admin.command("ping")
        except ConnectionFailure as e:  # ConnectionFailure is parent of most error
            print(f"Pymongo connection failure has occurred, retrying.... error: {e}")

        except Exception as e:
            print(f"Pymongo ping failure.... error: {e}")
            raise Exception("Other ping failiure")

        return bool(is_alive)

    def __create_connection(self):
        max_connection_retry = 0
        is_alive = False
        for max_connection_retry in range(MONGO_CON_RETRY_COUNT):
            is_alive = self.ping()
            if is_alive is True:
                break
            else:
                self.close_connection()
                self.__connection = self.__get_mongo_client()

        if is_alive is False and max_connection_retry == MONGO_CON_RETRY_COUNT:
            raise Exception("max_connection_retry")
