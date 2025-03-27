import json
import os
import traceback
from threading import Thread
import zlib
import base64
from confluent_kafka import Producer

_PRODUCER_CONFIGURATIONS = {
    "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
    "sasl.mechanism": os.environ["KAFKA_SASL_MECHANISM"],
    "security.protocol": os.environ["KAFKA_SECURITY_PROTOCOL"],
    "sasl.username": os.environ["KAFKA_SASL_USERNAME"],
    "sasl.password": os.environ["KAFKA_SASL_PASSWORD"],
    "message.max.bytes": 8388608,
    "compression.type": "lz4",
}


def decrypt_data(data):
    try:
        compressed_data = base64.b64decode(data)
        original_log_message = zlib.decompress(compressed_data).decode("utf-8")
        return original_log_message
    except Exception as e:
        print(f"Error while retrieving the original data: {e},{data}")
        return None


class KafkaConnector:
    """
    Kafka connector class
    """

    def __init__(self, pool_size=1):
        self.pool_size = 1  # Enable if the use case arises.
        self.producers = []
        self.__create_producers()

    def __get_producer_connection(self):
        """
        create a kafka producer connection if global connections isn't present.
        :return:
        """
        try:
            self.producers.append(Producer(_PRODUCER_CONFIGURATIONS))
        except Exception as e:
            print(f"Error while creating a Kafka Producer connection: {traceback.format_exc()}")
            raise e

    def __create_producers(self):
        """
        Use this function for creating multiple connections
        :return:
        """
        if self.pool_size == 1:
            self.__get_producer_connection()
        else:
            threads = []
            for i in range(self.pool_size):
                _thread = Thread(target=self.__get_producer_connection, args=())
                threads.append(_thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

    def __single_produce(self, data, producer, topic_name, key, is_raw_data=False):
        try:

            def delivery_callback(error, msg):
                log_data = None
                log_data_size = None
                if error:
                    if is_raw_data:
                        log_data = decrypt_data(data)
                        log_data_size = len(data)
                    print(f"Message delivery failed: {error}, {log_data_size}, {log_data}")

            producer.produce(
                topic_name,
                key=key,
                value=data,
                callback=delivery_callback,
            )
            producer.flush()
        except Exception as e:
            print(f"Error while pushing data to kafka. error: {traceback.format_exc()}")
            raise e

    def produce(self, data, is_parallel_push=False, is_raw_data=False):
        """
        Method which produces the data to kafka.
        :param data: List[dict] or Dict - each dictionary would have data to publish, kafka_topic and key.
        :param is_parallel_push: push the list of json in parallel to kafka
        :return:
        """
        if not is_parallel_push or not isinstance(data, list):
            batch_data = data.get("data") or data.get("batch_data")
            if not batch_data:
                raise ValueError("Empty data to produce")
            if is_raw_data:
                batch_data = batch_data
            else:
                batch_data = json.dumps(json.dumps(batch_data), ensure_ascii=False).encode("utf-8")
            self.__single_produce(
                batch_data,
                self.producers[0],
                data["kafka_topic"],
                data["kafka_key"],
                is_raw_data,
            )
        else:
            threads = []
            for each in data:
                batch_data = each.get("data") or each.get("batch_data")
                if not batch_data:
                    raise ValueError("Empty data to produce")
                if is_raw_data:
                    batch_data = batch_data
                else:
                    batch_data = json.dumps(json.dumps(batch_data), ensure_ascii=False).encode("utf-8")
                producer = self.producers[0]
                topic_name = each["kafka_topic"]
                kafka_key = each["kafka_key"]
                thread = Thread(
                    target=self.__single_produce,
                    args=(
                        batch_data,
                        producer,
                        topic_name,
                        kafka_key,
                        is_raw_data,
                    ),
                )
                threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

    def consume(self):
        pass
