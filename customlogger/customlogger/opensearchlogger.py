from opensearchpy import OpenSearch
import os
import logging


class OpensearchLogger:
    __client: OpenSearch
    __service_name: str
    __service_type: str

    def __init__(self):
        try:
            host = os.environ["CUSTOMLOGGER_LOGGER_OPENSEARCH_HOST"]
            auth = (
                os.environ["CUSTOMLOGGER_OPENSEARCH_USERNAME"],
                os.environ["CUSTOMLOGGER_LOGGER_OPENSEARCH_PASSWORD"],
            )

            self.__client = OpenSearch(
                hosts=host,
                http_auth=auth,
                use_ssl=True,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )
        except Exception as e:
            logging.info("Error Connecting to Opensearch.  " + str(e))

    def __index_doc(self, doc):
        try:
            self.__client.index(
                index=os.environ["CUSTOMLOGGER_OPENSEARCH_INDEXNAME"],
                body=doc,
                refresh=True,
            )
        except Exception as e:
            logging.info("Error pushing log to Opensearch.  " + str(e))

    def push_log(self, message: dict) -> None:
        self.__index_doc(message)
