"""OpenSearch logging Handler facility."""
import contextvars

import copy
import logging
import os
import socket
import traceback
import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import Lock, Timer
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from opensearchpy import OpenSearch
from opensearchpy import helpers

from .serializers import OpenSearchLoggerSerializer
from .version import __version__

logging_request_uuid = contextvars.ContextVar("request_id", default=None)
logging_unique_id = contextvars.ContextVar("logging_unique_id", default=None)


class RotateFrequency(Enum):
    """Index rotation frequency."""

    DAILY = 0
    WEEKLY = 1
    MONTHLY = 2
    YEARLY = 3
    NEVER = 4


class OpenSearchHandler(logging.Handler):
    """OpenSearch logging handler.

    Allows to log to OpenSearch in json format.
    All LogRecord fields are serialised and inserted
    """

    DAILY = RotateFrequency.DAILY
    WEEKLY = RotateFrequency.WEEKLY
    MONTHLY = RotateFrequency.MONTHLY
    YEARLY = RotateFrequency.YEARLY
    NEVER = RotateFrequency.NEVER

    _LOGGING_FILTER_FIELDS = ["msecs", "relativeCreated", "levelno", "exc_text", "msg"]
    _AGENT_TYPE = "opensearch-logger"
    _AGENT_VERSION = __version__
    _ECS_VERSION = "1.4.0"

    def __init__(
        self,
        index_name: str = "python-logs",
        index_rotate: Union[RotateFrequency, str] = RotateFrequency.DAILY,
        index_date_format: str = "%Y.%m.%d",
        index_name_sep: str = "-",
        buffer_size: int = 1,
        flush_frequency: float = 1.0,
        extra_fields: Optional[Dict[str, Any]] = None,
        raise_on_index_exc: bool = False,
        **kwargs: Any,
    ):
        """Initialize OpenSearch logging handler.
        Examples:
            The configuration below is suitable for connection to an OpenSearch docker
            container running locally.

            >>> import logging
            >>> from opensearch_logger import OpenSearchHandler
            >>> handler = OpenSearchHandler
            >>> handler = OpenSearchHandler(
            >>>     index_name="my-logs",
            >>>     hosts=["https://localhost:9200"],
            >>>     http_auth=("admin", "admin"),
            >>>     use_ssl=True,
            >>>     verify_certs=False,
            >>>     ssl_assert_hostname=False,
            >>>     ssl_show_warn=False,
            >>> )
            >>> logger = logging.getLogger(__name__)
            >>> logger.setLevel(logging.INFO)
            >>> logger.addHandler(handler)
            >>> logger.info("This message will be indexed in OpenSearch")
            >>> logger.info(f"This one will have extra fields", extra={"topic": "dev"})
        """
        logging.Handler.__init__(self)

        # Throw an exception if connection arguments for Openserach client are empty
        if not kwargs:
            raise TypeError("Missing OpenSearch connection parameters.")

        # Arguments that will be passed to OpenSearch client object
        self.opensearch_kwargs = kwargs

        # Bufferization and flush settings
        self.buffer_size = buffer_size
        self.flush_frequency = flush_frequency

        # Index name
        self.index_name = index_name
        if isinstance(index_rotate, str):
            self.index_rotate = RotateFrequency[index_rotate]
        else:
            self.index_rotate = index_rotate
        self.index_date_format = index_date_format
        self.index_name_sep = index_name_sep

        if extra_fields is None:
            extra_fields = {}
        self.extra_fields = copy.deepcopy(extra_fields.copy())
        self.extra_fields.setdefault("ecs", {})["version"] = OpenSearchHandler._ECS_VERSION

        self._client: Optional[OpenSearch] = None
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_lock: Lock = Lock()
        self._timer: Optional[Timer] = None
        self.serializer = OpenSearchLoggerSerializer()

        self.raise_on_index_exc: bool = raise_on_index_exc

        # agent_dict = self.extra_fields.setdefault('agent', {})
        # agent_dict['ephemeral_id'] = uuid4()
        # agent_dict['type'] = OpenSearchHandler._AGENT_TYPE
        # agent_dict['version'] = OpenSearchHandler._AGENT_VERSION

        host_dict = self.extra_fields.setdefault("host", {})
        host_name = socket.gethostname()
        host_dict["hostname"] = host_name
        host_dict["name"] = host_name
        host_dict["id"] = host_name
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:  # pragma: no cover
            ip = ""
        host_dict["ip"] = ip

    def test_opensearch_connection(self) -> bool:
        """Returns True if the handler can ping the OpenSearch servers.

        Can be used to confirm the setup of a handler has been properly done and confirm
        that things like the authentication are working properly.

        Returns:
            bool: True if the connection against elasticserach host was successful.
        """
        return self._get_opensearch_client().ping()

    def flush(self) -> None:
        """Flush the buffer into OpenSearch."""
        if hasattr(self, "_timer") and self._timer is not None and self._timer.is_alive():
            print("*alive**********************", self._timer.is_alive())
            self._timer.cancel()
        self._timer = None
        # print("*buffer**********************", self._buffer)
        if self._buffer:
            try:
                with self._buffer_lock:
                    logs_buffer = self._buffer
                    self._buffer = []

                index = self._get_index()
                # print(f" Index Name : {index}")
                actions = [{"_index": index, "_source": record} for record in logs_buffer]

                res = helpers.bulk(
                    client=self._get_opensearch_client(),
                    actions=actions,
                    stats_only=True,
                )

                if int(res[1]):
                    print(f"Bulk Insert failed response: {res}")

            except Exception as exception:  # noqa: B902
                if self.raise_on_index_exc:
                    raise exception

    def close(self) -> None:
        """Flush the buffer and release any outstanding resource."""
        self.flush()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit overrides the abstract logging.Handler logRecord emit method.

        Formats and emits the log record.

        Args:
            record: A record.
        """
        self.format(record)
        doc = self._convert_log_record_to_doc(record)
        with self._buffer_lock:
            self._buffer.append(doc)
        # print(
        #     "*sizecheck****************************",
        #     len(self._buffer),
        #     self.buffer_size,
        # )
        if len(self._buffer) >= self.buffer_size:
            self.flush()
        else:
            self._schedule_flush()

    def _get_opensearch_client(self) -> OpenSearch:
        if self._client is None:
            self._client = OpenSearch(**self.opensearch_kwargs)
        return self._client

    def _schedule_flush(self) -> None:
        print("*_schedule_flush****************************", self._timer)
        if self._timer is None:
            self._timer = Timer(self.flush_frequency, self.flush)
            self._timer.setDaemon(True)
            self._timer.start()

    def _get_index(self) -> str:
        if RotateFrequency.DAILY == self.index_rotate:
            return self._get_daily_index_name()
        elif RotateFrequency.WEEKLY == self.index_rotate:  # pragma: no cover
            return self._get_weekly_index_name()
        elif RotateFrequency.MONTHLY == self.index_rotate:  # pragma: no cover
            return self._get_monthly_index_name()
        elif RotateFrequency.YEARLY == self.index_rotate:  # pragma: no cover
            return self._get_yearly_index_name()
        else:  # pragma: no cover
            return self._get_never_index_name()

    def _convert_log_record_to_doc(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Take the original logging.LogRecord and map its attributes to ecs fields.

        Args:
            record: The original LogRecord.

        Returns:
            Dict[str, Any]: OpenSearch ECS compliant document with all the proper meta data fields.
        """
        log_record_dict = record.__dict__.copy()
        doc = copy.deepcopy(self.extra_fields)

        doc["request_id"] = None
        doc["logging_unique_data"] = None
        try:
            if logging_unique_id.get():
                doc["request_id"] = logging_unique_id.get()
                doc["logging_unique_data"] = logging_unique_id.get()
            elif os.environ.get("logging_unique_data"):
                doc["request_id"] = json.loads(os.environ.get("logging_unique_data"))
                doc["logging_unique_data"] = json.loads(os.environ.get("logging_unique_data"))
            else:
                doc["request_id"] = {"service": "undefined"}
        except Exception as e:
            print(f"context requestid not set. Error: {e}")
            pass

        if "created" in log_record_dict:  # pragma: no cover
            doc["@timestamp"] = self._get_opensearch_datetime_str(log_record_dict.pop("created"))

        if "message" in log_record_dict:  # pragma: no cover
            message = log_record_dict.pop("message")
            doc["message"] = message
            # doc.setdefault('log', {})['original'] = message

        if "levelname" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {})["level"] = log_record_dict.pop("levelname")

        if "name" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {})["logger"] = log_record_dict.pop("name")

        if "lineno" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {}).setdefault("origin", {}).setdefault("file", {})["line"] = log_record_dict.pop("lineno")

        if "filename" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {}).setdefault("origin", {}).setdefault("file", {})["name"] = log_record_dict.pop("filename")

        if "pathname" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {}).setdefault("origin", {}).setdefault("file", {})["path"] = log_record_dict.pop("pathname")

        if "funcName" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {}).setdefault("origin", {})["function"] = log_record_dict.pop("funcName")

        if "module" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {}).setdefault("origin", {})["module"] = log_record_dict.pop("module")

        if "processName" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {}).setdefault("process", {})["name"] = log_record_dict.pop("processName")

        if "process" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {}).setdefault("process", {})["pid"] = log_record_dict.pop("process")

        if "threadName" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {}).setdefault("thread", {})["name"] = log_record_dict.pop("threadName")

        if "thread" in log_record_dict:  # pragma: no cover
            doc.setdefault("log", {}).setdefault("thread", {})["id"] = log_record_dict.pop("thread")

        if "exc_info" in log_record_dict:  # pragma: no cover
            exc_info = log_record_dict.pop("exc_info")
            if exc_info:
                exc_type, exc_value, traceback_object = exc_info
                doc["error"] = {
                    "code": exc_type.__name__,
                    "id": uuid4(),
                    "type": exc_type.__name__,
                    "message": str(exc_value),
                    "stack_trace": "".join(traceback.format_exception(exc_type, exc_value, traceback_object)),
                }

        # Copy unknown attributes of the log_record object.
        for key, value in log_record_dict.items():
            if key not in OpenSearchHandler._LOGGING_FILTER_FIELDS:
                if key == "args" and value:
                    value = tuple(str(arg) for arg in value)
                doc[key] = "" if value is None else value

        return doc

    def _get_daily_index_name(self, current_date: Optional[datetime] = None) -> str:
        if current_date is None:
            current_date = datetime.now(tz=timezone.utc)  # pragma: no cover
        return f"{self.index_name}{self.index_name_sep}{current_date.strftime(self.index_date_format)}"

    def _get_weekly_index_name(self, current_date: Optional[datetime] = None) -> str:
        if current_date is None:
            current_date = datetime.now(tz=timezone.utc)  # pragma: no cover
        start_of_the_week = current_date - timedelta(days=current_date.weekday())
        return f"{self.index_name}{self.index_name_sep}{start_of_the_week.strftime(self.index_date_format)}"

    def _get_monthly_index_name(self, current_date: Optional[datetime] = None) -> str:
        if current_date is None:
            current_date = datetime.now(tz=timezone.utc)  # pragma: no cover
        first_date_of_month = datetime(current_date.year, current_date.month, 1)
        return f"{self.index_name}{self.index_name_sep}{first_date_of_month.strftime(self.index_date_format)}"

    def _get_yearly_index_name(self, current_date: Optional[datetime] = None) -> str:
        if current_date is None:
            current_date = datetime.now(tz=timezone.utc)  # pragma: no cover
        first_date_of_year = datetime(current_date.year, 1, 1)
        return f"{self.index_name}{self.index_name_sep}{first_date_of_year.strftime(self.index_date_format)}"

    def _get_never_index_name(self, current_date: Optional[datetime] = None) -> str:
        return self.index_name

    @staticmethod
    def _get_opensearch_datetime_str(timestamp: float) -> str:
        """Return OpenSearch utc formatted time for an epoch timestamp.

        Args:
            timestamp (float): Timestamp, including milliseconds.

        Returns:
            str: A string valid for OpenSearch record such "2021-11-08T10:04:06.122Z".
        """
        dt = datetime.utcfromtimestamp(timestamp)
        fmt = "%Y-%m-%dT%H:%M:%S"
        return f"{dt.strftime(fmt)}.{int(dt.microsecond / 1000):03d}Z"
