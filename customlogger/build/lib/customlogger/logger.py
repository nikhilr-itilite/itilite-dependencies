import os
import datetime
import uuid

from customlogger import constants
from customlogger.loggermodel import LoggerModel
import logging

from customlogger.opensearchlogger import OpensearchLogger


class Logger:
    __service_type = None
    __service_name = None
    __LOG_LEVEL = constants.INFO
    __enable_opensearch_logger = None
    __opensearch_client = None
    __request_id = None

    def __init__(self, service_type, service_name):
        self.__service_type = service_type
        self.__service_name = service_name
        self.__request_id = str(uuid.uuid1())
        self.__LOG_LEVEL = constants.INFO
        if os.environ["CUSTOM_LOGGER_LOG_LEVEL"] is not None:
            self.__LOG_LEVEL = os.environ["CUSTOM_LOGGER_LOG_LEVEL"]
        # self.__enable_opensearch_logger = os.environ["OPENSEARCH_LOGGER_ENABLE")
        # if (self.__enable_opensearch_logger is not None) and bool(self.__enable_opensearch_logger):
        self.__opensearch_client = OpensearchLogger()

    def debug(self, message: dict, status=None, status_code=None):
        try:
            if self.__LOG_LEVEL == constants.DEBUG:
                log_message = self.__set_obj(message, constants.DEBUG, status, status_code)
                log_msg_json = log_message.json()
                logging.debug(log_msg_json)
                self.__push_log(log_msg_json)
        except Exception as e:
            logging.info("Error in DEBUG Logger.  " + str(e))

    def info(self, message: dict, status=None, status_code=None):
        try:
            if self.__LOG_LEVEL == constants.DEBUG or self.__LOG_LEVEL == constants.INFO:
                log_message = self.__set_obj(message, constants.INFO, status, status_code)
                log_msg_json = log_message.json()
                logging.info(log_msg_json)
                self.__push_log(log_msg_json)
        except Exception as e:
            logging.info("Error in INFO Logger.  " + str(e))

    def warn(self, message: dict, status=None, status_code=None):
        try:
            if self.__LOG_LEVEL == constants.DEBUG or self.__LOG_LEVEL == constants.INFO or self.__LOG_LEVEL == constants.WARN:
                log_message = self.__set_obj(message, constants.WARN, status, status_code)
                log_msg_json = log_message.json()
                logging.warning(log_msg_json)
                self.__push_log(log_msg_json)
        except Exception as e:
            logging.info("Error in WARN Logger.  " + str(e))

    def error(self, message: dict, status=None, status_code=None):
        try:
            log_message = self.__set_obj(message, constants.ERROR, status, status_code)
            log_msg_json = log_message.json()
            logging.error(log_msg_json)
            self.__push_log(log_msg_json)
        except Exception as e:
            logging.info("Error in ERROR Logger.  " + str(e))

    def __set_obj(self, message, level, status, status_code):
        msg = None
        detailed_msg = None
        if type(message) is dict:
            detailed_msg = message
        else:
            msg = message
        log_message = LoggerModel(
            service_type=self.__service_type,
            service_name=self.__service_name,
            request_id=self.__request_id,
            log_level=level,
            status=status,
            status_code=status_code,
            message=msg,
            message_detailed=detailed_msg,
            created_ts=datetime.datetime.now(),
        )
        return log_message

    def __push_log(self, msg):
        self.__opensearch_client.push_log(msg)
