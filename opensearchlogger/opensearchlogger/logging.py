import json
import traceback

from opensearchlogger.handlers import OpenSearchHandler
import os
import queue
from logging import handlers, getLogger
import logging
import zlib
import base64
from kafkaconnector import KafkaConnector
from concurrent.futures import ThreadPoolExecutor

# ------------------------------------
# import boto3
# from requests_aws4auth import AWS4Auth
# from opensearchpy import RequestsHttpConnection
# ------------------------------------

OPENSEARCH_LOGGING = 0
KAFKA_LOGGING = 1


host = os.environ["LOGGER_OPENSEARCH_HOST"]
port = os.environ["LOGGER_OPENSEARCH_HOST_PORT"]
auth = (
    os.environ["LOGGER_OPENSEARCH_USERNAME"],
    os.environ["LOGGER_OPENSEARCH_PASSWORD"],
)
index_rotate = os.environ["LOGGER_OPENSEARCH_INDEX_ROTATE"]
index_name = os.environ["LOGGER_OPENSEARCH_INDEX_NAME"]
log_level = os.environ["LOGGER_OPENSEARCH_LOG_LEVEL"]
logging_strategy = int(os.environ.get("LOGGING_STRATEGY") or 2)
local_log = int(os.environ.get("LOCAL_LOG") or 0)  # Use opensearch only if set
kafka_topic = os.getenv("KAFKA_APPLICATION_LOGS_TOPIC")
environment = os.getenv("ENVIRONMENT")


# ------------------------------------
# AWS region # region= "us-east-1"
# service = "es"
# creds = boto3.Session().get_credentials()
# ------------------------------------
class KafkaLogHandler(logging.Handler):
    def __init__(self, kafka_connector, topic):
        super().__init__()
        self.kafka_connector = kafka_connector
        self.topic = topic
        self.executor = ThreadPoolExecutor(max_workers=10)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_message = self.format(record)
            compressed_data = zlib.compress(log_message.encode("utf-8"))
            encoded_data = base64.b64encode(compressed_data).decode("utf-8")
            log_data = {"data": encoded_data, "kafka_topic": self.topic, "kafka_key": None}
            self.executor.submit(self._produce_log_to_kafka, log_data)
        except Exception as e:
            print(f"Error while preparing the logs data to push into Kafka: {str(e)},{record}")

    def _produce_log_to_kafka(self, log_data):
        try:
            self.kafka_connector.produce(log_data, is_raw_data=True)
        except Exception as e:
            print(f"Error while producing to Kafka: {str(e)},{traceback.format_exc()}")
            print(f"Log Data:\n{log_data}")


class CustomLogger(logging.Logger):
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None):
        extra = extra or {}
        logging_unique_data = os.environ.get("logging_unique_data") or '{"service": "undefined"}'
        common_custom_info = json.loads(logging_unique_data)
        extra.update(common_custom_info)
        if "message" in extra:
            print(f"message key removed from extra {extra} LogRecord")
            del extra["message"]
        return super().makeRecord(name, level, fn, lno, msg, args, exc_info, func=func, extra=extra, sinfo=sinfo)


class KeyValueFormatter(logging.Formatter):
    def format(self, record):
        logging_unique_data = os.environ.get("logging_unique_data") or '{"service": "undefined"}'
        log_message = record.getMessage()

        # Calculate byte size of the log message
        log_push_size = len(log_message.encode("utf-8"))

        log_data = {
            "log": {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger_name": record.name,
                "file_name": record.filename,
                "line_number": record.lineno,
                "function_name": record.funcName,
                "process": {"name": record.processName, "pid": record.process},
                "thread": {"name": record.threadName, "id": record.thread},
            },
            "message": log_message,
            "logging_unique_data": json.loads(logging_unique_data),
            "environment": environment,
            "logpushsize": log_push_size,  # Add the logpushsize field
        }
        return json.dumps(log_data)


if logging_strategy == OPENSEARCH_LOGGING:
    logger = getLogger(__name__)
    logger.setLevel(log_level)
    log_queue = queue.Queue(-1)
    # Queue handler will write all logs into this queue.
    queue_handler = handlers.QueueHandler(log_queue)
    logger.addHandler(queue_handler)
    opensearch_handler = OpenSearchHandler(
        index_name=index_name,
        hosts=[host],
        # ------------------------------------
        # http_auth=AWS4Auth(creds.access_key, creds.secret_key, region, service, session_token=creds.token),
        # ------------------------------------
        http_auth=auth,
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        index_rotate=index_rotate
        # connection_class=RequestsHttpConnection
    )

    # Queue listener will get all these logs and perform emit using our opensearch handler.
    try:
        opensearch_listener = handlers.QueueListener(log_queue, opensearch_handler)
        opensearch_listener.start()
    except Exception:
        print(traceback.format_exc())
elif logging_strategy == KAFKA_LOGGING:
    logger = CustomLogger(__name__)
    logger.setLevel(log_level)
    formatter = KeyValueFormatter()
    kafka_handler = KafkaLogHandler(KafkaConnector(), kafka_topic)
    kafka_handler.setLevel(log_level)
    kafka_handler.setFormatter(formatter)
    logger.addHandler(kafka_handler)
else:
    logger = CustomLogger(__name__)
    logger.setLevel(log_level)
    formatter = KeyValueFormatter()
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if local_log == 1:
        file_handler = logging.FileHandler("storage/logs/app.log")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def opensearch_logger_noparam(func):
    def wrapper(*args, **kwargs):
        func_response = func(*args, **kwargs)
        restart_listener()
        return func_response

    return wrapper


def opensearch_logger(service="undefined"):
    def decorator(func):
        def execute_function(*args, **kwargs):
            func_response = None
            try:
                func_response = func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception {e} occurred while execution")

            return func_response

        def wrapper(*args, **kwargs):
            os.environ["logging_unique_data"] = json.dumps({"service": service})
            if logging_strategy == OPENSEARCH_LOGGING:
                func_response = execute_function(*args, **kwargs)
                logger.info("flushing logs before shutdown")
                restart_listener()
            else:
                func_response = execute_function(*args, **kwargs)
            return func_response

        return wrapper

    return decorator


def restart_listener():
    global opensearch_listener
    opensearch_listener.stop()
    opensearch_listener.start()


if __name__ == "__main__":
    logger.info("We are testing opensearch logs....")
