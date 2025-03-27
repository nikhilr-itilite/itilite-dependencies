import os
import time
import traceback

import pymysql
import pymysql.cursors
import pymysqlpool
from opensearchlogger.logging import logger
from pymysql import err


class MysqlConnector:
    def connect_db(db_type):
        """
        Desc : Establish connection to Mysql db and return the connection object
        Input:
            db_type: api/app db slave to connect
        """
        try:
            if db_type == "api":
                conn = pymysql.connect(
                    host=os.environ["MYSQL_HOST"],
                    user=os.environ["MYSQL_USER"],
                    password=os.environ["MYSQL_PWD"],
                    db=os.environ["MYSQL_API_DB"],
                    cursorclass=pymysql.cursors.DictCursor,
                )
                return conn
            if db_type == "api_slave":
                conn = pymysql.connect(
                    host=os.environ["MYSQL_HOST_API_SLAVE"],
                    user=os.environ["MYSQL_USER_API_SLAVE"],
                    password=os.environ["MYSQL_PWD_API_SLAVE"],
                    db=os.environ["MYSQL_API_DB_SLAVE"],
                    cursorclass=pymysql.cursors.DictCursor,
                )
                return conn

            if db_type == "app":
                conn = pymysql.connect(
                    host=os.environ["MYSQL_HOST"],
                    user=os.environ["MYSQL_USER"],
                    password=os.environ["MYSQL_PWD"],
                    db=os.environ["MYSQL_APP_DB"],
                    cursorclass=pymysql.cursors.DictCursor,
                )
                return conn
            if db_type == "app_slave":
                conn = pymysql.connect(
                    host=os.environ["MYSQL_HOST_APP_SLAVE"],
                    user=os.environ["MYSQL_USER_APP_SLAVE"],
                    password=os.environ["MYSQL_PWD_APP_SLAVE"],
                    db=os.environ["MYSQL_APP_DB_SLAVE"],
                    cursorclass=pymysql.cursors.DictCursor,
                )
                return conn

            if db_type == "log":
                conn = pymysql.connect(
                    host=os.environ["MYSQL_API_LOG_HOST"],
                    user=os.environ["MYSQL_API_LOG_USER"],
                    password=os.environ["MYSQL_API_LOG_PWD"],
                    db=os.environ["MYSQL_API_LOG_DB"],
                    cursorclass=pymysql.cursors.DictCursor,
                )
                return conn

        except Exception as ex:
            logger.error(f"ERROR: {ex}")
            logger.error(traceback.format_exc())
            return False


def retry_on_error(func):
    MAX_RETRIES = 3

    def wrapper(*args, **kwargs):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error occurred: {e}")
                retries += 1
                time.sleep(1)
        raise Exception(f"Function {func.__name__} failed after multiple retries.")

    return wrapper


class DatabaseConnection:
    __instances = {}

    @staticmethod
    def get_instance(db_type):
        """
        Retrieve the singleton instance of the class based on the specified database type.

        Args:
            db_type (str): The type of the database.

        Returns:
            DatabaseConnection: The singleton instance of the class.

        """

        key = db_type
        if key not in DatabaseConnection.__instances:
            DatabaseConnection.__instances[key] = DatabaseConnection(db_type)
        return DatabaseConnection.__instances[key]

    def __init__(self, db_type):
        """
        Initialize the DatabaseConnection object.

        Args:
            db_type (str): The type of the database.

        Attributes:
            connection (pymysql.connections.Connection): MySQL database connection object.
            connected (bool): Connection status.
        """
        db_type_config_mapping = {
            "api": {
                "database": os.environ.get("MYSQL_API_DB"),
                "host": os.environ.get("MYSQL_HOST"),
                "user": os.environ.get("MYSQL_USER"),
                "password": os.environ.get("MYSQL_PWD"),
            },
            "api_slave": {
                "database": os.environ.get("MYSQL_API_DB_SLAVE"),
                "host": os.environ.get("MYSQL_HOST_API_SLAVE"),
                "user": os.environ.get("MYSQL_USER_API_SLAVE"),
                "password": os.environ.get("MYSQL_PWD_API_SLAVE"),
            },
            "app": {
                "database": os.environ.get("MYSQL_APP_DB"),
                "host": os.environ.get("MYSQL_HOST"),
                "user": os.environ.get("MYSQL_USER"),
                "password": os.environ.get("MYSQL_PWD"),
            },
            "app_slave": {
                "database": os.environ.get("MYSQL_APP_DB_SLAVE"),
                "host": os.environ.get("MYSQL_HOST_APP_SLAVE"),
                "user": os.environ.get("MYSQL_USER_APP_SLAVE"),
                "password": os.environ.get("MYSQL_PWD_APP_SLAVE"),
            },
            "log": {
                "database": os.environ.get("MYSQL_API_LOG_DB"),
                "host": os.environ.get("MYSQL_API_LOG_HOST"),
                "user": os.environ.get("MYSQL_API_LOG_USER"),
                "password": os.environ.get("MYSQL_API_LOG_PWD"),
            },
            "itilite_user": {
                "database": os.environ.get("MYSQL_ITILITE_USER_DB"),
                "host": os.environ.get("MYSQL_HOST_ITILITE_USER"),
                "user": os.environ.get("MYSQL_USER_ITILITE_USER"),
                "password": os.environ.get("MYSQL_PWD_ITILITE_USER"),
            },
        }

        self.db_config = {
            "host": db_type_config_mapping.get(db_type, {}).get("host"),
            "user": db_type_config_mapping.get(db_type, {}).get("user"),
            "password": db_type_config_mapping.get(db_type, {}).get("password"),
            "database": db_type_config_mapping.get(db_type, {}).get("database"),
            "cursorclass": pymysql.cursors.DictCursor,
            "size": int(os.getenv("MYSQL_MAXIMIMUL_POOL_SIZE", 25)),
            "con_lifetime": int(os.getenv("MYSQL_MAX_CONNECTION_LIFETIME", 10)),
        }
        # logger.info("----------db config---------%s", self.db_config)
        self.connection_pool = pymysqlpool.ConnectionPool(**self.db_config)

        # self.connection = pymysql.connect(
        #     host=os.environ["MYSQL_HOST"],
        #     user=os.environ["MYSQL_USER"],
        #     password=os.environ["MYSQL_PWD"],
        #     db=os.environ["MYSQL_API_DB"]
        #     if db_type == "api"
        #     else os.environ["MYSQL_APP_DB"]
        #     if db_type == "app"
        #     else os.environ["MYSQL_API_LOG_DB"]
        #     if db_type == "log"
        #     else "api",
        #     cursorclass=pymysql.cursors.DictCursor,
        # )

        # self.test_connection()

    def get_connection(self):
        """
        Get the database connection.

        Returns:
            pymysql.connections.Connection: The database connection object.
        """

        logger.debug(f"--------------get connection pool----------- {self.connection_pool}")
        try:
            connection = self.connection_pool.get_connection(retry_num=5, retry_interval=1, pre_ping=True)
            return connection
        except Exception:
            logger.error(f"Error in getting connections=========>{traceback.format_exc()}")
            try:
                self.connection_pool = pymysqlpool.ConnectionPool(**self.db_config)
                connection = self.connection_pool.get_connection(retry_num=5, retry_interval=1, pre_ping=True)
                return connection
            except Exception:
                logger.error(f"Error in getting connections while retrying=========>{traceback.format_exc()}")

    @retry_on_error
    def test_connection(self):
        """
        Test the database connection.

        Raises:
            Exception: If the database connection fails.
        """
        try:
            if self.connection_pool.get_connection():
                logger.info("-------Connection is connected and operational--------")
            else:
                logger.info("--------Connection is not connected----------")
            # if not self.connection.open:
            #     self.connection.connect()
            # else:
            #     self.connection.ping()

        except (err.OperationalError, err.InterfaceError) as e:
            logger.error(f"Connection error occurred: {e}")
            raise Exception("Database connection failed.")

    @retry_on_error
    def execute_query(self, query):
        """
        Execute a database query.

        Args:
            query (str): The SQL query to execute.

        Returns:
            list: The result of the query as a list of dictionaries.

        Raises:
            Exception: If the database connection fails.
        """

        result = list()
        conn = self.connection_pool.get_connection()
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()

        return result
