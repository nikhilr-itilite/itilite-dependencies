import pymysql
import pymysql.cursors
import time
from functools import wraps
import os
from opensearchlogger.logging import logger


def retry_on_error(func):
    MAX_RETRIES = os.getenv("MAX_RETRIES", 3)

    @wraps(func)
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
        key = db_type
        if key not in DatabaseConnection.__instances:
            DatabaseConnection.__instances[key] = DatabaseConnection(db_type)
        return DatabaseConnection.__instances[key]

    def __init__(self, db_type):
        self.connection = pymysql.connect(
            host=os.environ["MYSQL_HOST"],
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PWD"],
            db=os.environ["MYSQL_API_DB"]
            if db_type == "api"
            else os.environ["MYSQL_APP_DB"]
            if db_type == "app"
            else os.environ["MYSQL_API_LOG_DB"]
            if db_type == "log"
            else "api",
            cursorclass=pymysql.cursors.DictCursor,
        )

    @retry_on_error
    def execute_query(self, query):
        cursor = self.connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result

    def __del__(self):
        if self.connection.is_connected():
            self.connection.close()
