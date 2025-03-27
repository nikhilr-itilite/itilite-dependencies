import os
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Thread
from io import BytesIO

import boto3
import requests
from botocore.config import Config
from bson import json_util
from helperlayer.timeout_decor import timeout
from helperlayer import delete_ephemeral_path
from opensearchlogger.logging import logger
import time


S3_REFRESH_THRESHOLD = 300  # Refresh client if idle for 5 minutes
RETRY_COUNT = 3
MAX_CLIENTS = 50
CONNECT_TIMEOUT = 10  # Explicitly retry in case of connection taking more than 10 seconds, useful for stale
READ_TIMEOUT = 30  # Explicitly retry in case of reading large files, useful where read stalls in midway
MAX_WORKER_FOR_PARALLEL_SAVE = MAX_CLIENTS
last_s3_access = 0


# Each client has a pool of connections, which is shared across all threads.
# If there are 50 threads, it is not necessary to create 50 connection pool.
# Connection timeout and read timeout are added to avoid hanging threads.
def __create_s3_client(count=0, max_clients=MAX_CLIENTS):
    try:
        s3_client = session.client(
            "s3",
            region_name=os.environ["AWS_REGION_NAME"],
            aws_access_key_id=os.environ["ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["SECRET_ACCESS_KEY"],
            config=Config(
                max_pool_connections=max_clients,
                retries={"max_attempts": 3, "mode": "adaptive"},
                connect_timeout=CONNECT_TIMEOUT,
                read_timeout=READ_TIMEOUT,
            ),
        )
        return s3_client
    except Exception as e:
        if count < RETRY_COUNT:
            logger.info("Retrying to create an s3 client")
            return __create_s3_client(count + 1, max_clients)
        else:
            logger.error(f"Could not create an S3 client, More than 5 retries over: error: {traceback.format_exc()}")
        raise e


session = boto3.session.Session()
client = __create_s3_client(max_clients=MAX_CLIENTS)


# Currently this will be tested in booking controller functionality only
def __refresh_s3_client(force_reset=False, max_clients=10):
    """
    Refreshes the global S3 client session.
    """
    global client, session, last_s3_access
    if force_reset or time.time() - last_s3_access > S3_REFRESH_THRESHOLD:
        logger.info(f"Refreshing S3 client {last_s3_access} {force_reset}")
        session = boto3.session.Session()
        client = __create_s3_client(max_clients=max_clients)
        last_s3_access = time.time()


# If refresh_s3_client is successfully tested, then we can add by default refresh_s3_client() in below function
def __get_s3_client():
    return client


def s3_upload_fileobj(s3_bucket_name, s3_file_name, s3_data, is_json=True):
    """
    Uses S3's upload_fileobj which is designed to handle large files efficiently and supports multipart uploads,
     which can be more effective for handling many small files as well.
    """
    try:
        start_time = datetime.now()
        s3_client = __get_s3_client()
        byte_stream = BytesIO(s3_data)
        extra_args = {"ContentType": "application/json"} if is_json else None
        s3_client.upload_fileobj(byte_stream, s3_bucket_name, s3_file_name, ExtraArgs=extra_args)
        logger.info(
            f"Upload time for S3:{s3_file_name} is {(datetime.now()-start_time).total_seconds()}"
        )  # TODO:Change to debug later
    except Exception as e:
        logger.error(f"Error while uploading file: {s3_file_name} to S3. error: {traceback.format_exc()}")
        raise e


def save_to_s3(bucket_name: str, file_name: str, data, content_type="application/json"):
    """
    Function which saves the data in S3.
    :param bucket_name: Name of the S3 bucket.
    :param file_name: Name of the S3 file.
    :param data: Data which is being saved to S3
    :param content_type: Content type of file
    :return: S3 Metadata
    """
    try:
        s3_file = __get_s3_client().put_object(Bucket=bucket_name, Key=file_name, Body=data, ContentType=content_type)
        return {
            "s3_status": True,
            "s3_meta_data": s3_file,
            "s3_bucket_name": bucket_name,
            "s3_file_name": file_name,
        }
    except Exception as e:
        logger.error(
            f"Error while inserting data into S3. bucket: {bucket_name}, file_name: {file_name}, "
            f"error: {traceback.format_exc()}"
        )
        raise e


def s3_parallel_save(inp_dict: dict):
    """
    save objects to S3 in parallel.
    :param inp_dict: Dictionary which contains data, file_name and S3 objects.
    :return:
    """
    s3_publish_start_time = datetime.now()
    published_count = 0
    threads = []
    with ThreadPoolExecutor(
        max_workers=MAX_WORKER_FOR_PARALLEL_SAVE,
    ) as executor:
        for each in inp_dict:
            batch_data = each.get("data") or each.get("batch_data")
            bucket_name = each.get("s3_bucket_name")
            file_name = each.get("s3_file_name")
            if not batch_data:
                # raise ValueError("Empty data to upload")
                logger.error(f"Empty batch_data found, Skipping upload for this batch. File name: {file_name}")
                continue
            threads.append(executor.submit(save_to_s3, bucket_name, file_name, batch_data))

    for t in as_completed(threads):
        # logger.info(f"S3 task result is: {t.result()}")
        if t.result():
            published_count += 1

    s3_time_delta = datetime.now() - s3_publish_start_time
    logger.info(
        f"Time taken for all batches to save to S3 is {s3_time_delta.total_seconds():.6f}, \
        with {MAX_CLIENTS} clients and {MAX_WORKER_FOR_PARALLEL_SAVE} workers for {len(inp_dict)} batches"
    )


def read_from_s3(bucket_name: str, file_name: str):
    """
    Read data from S3 bucket
    :param bucket_name: S3 bucket name
    :param file_name: file name where payload is present
    :return: hotel list from S3
    """
    try:
        s3_start_time = datetime.now()
        client = __get_s3_client()
        resp = client.get_object(Bucket=bucket_name, Key=file_name)
        s3_delta = datetime.now() - s3_start_time
        logger.info(f"Time taken to read file from S3 is {s3_delta.total_seconds()}")
        return resp
    except Exception as e:
        logger.error(f"Error while fetching data from S3. error: {traceback.format_exc()}")
        raise e


@timeout(30)
def fetch_files_with_prefix(bucket_name: str, prefix: str):
    """
    Check if files with a specific prefix exist in the S3 bucket.
    :param str bucket_name: Name of the S3 bucket.
    :param str prefix: Prefix to search for.
    :returns: list: List of matching file keys or an empty list if none found.
    """
    try:
        logger.info(f"Fetching files with prefix {prefix} from bucket {bucket_name}")
        s3_client = __get_s3_client()
        # This will try to connect to s3, based on connection timeout it will timeout and then retry
        paginator = s3_client.get_paginator("list_objects_v2")
        matching_files = []
        for page_num, page in enumerate(paginator.paginate(Bucket=bucket_name, Prefix=prefix)):
            if "Contents" in page:
                new_files = [obj["Key"] for obj in page["Contents"]]
                logger.info(f"Page {page_num} has {len(new_files)} files")
                matching_files.extend(new_files)
            else:
                logger.info(f" Empty page received at iteration {page_num}")
            # Explicitly breaking pagination if no more pages are available
            if not page.get("IsTruncated", False):
                logger.info("Pagination completed. No more pages available.")
                break

        return matching_files
    except Exception as ex:
        logger.error(f"Error fetching files with prefix {prefix} from bucket {bucket_name}. Error: {ex}")
        return []


def save_request_response(request_data, response, layer_name):
    try:
        logger.info("--------save_request_response--------%s,%s,%s", request_data, response, layer_name)
        s3_bucket = os.environ.get("REQUEST_RESPONSE_BUCKET_NAME")
        s3_file_name = get_request_response_file_name(request_data, layer_name)
        logger.info("--------save_request_response file path--------%s,%s", request_data, s3_file_name)
        content = {"request_data": request_data, "response": response}
        content = json_util.dumps(content)
        s3_save_resp = save_to_s3(s3_bucket, s3_file_name, content)
        logger.info("--------save_request_response s3_save_resp--------%s,%s", request_data, s3_save_resp)

    except Exception as ex:
        logger.error(
            "--------Error in save_request_response  %s,%s-------%s,%s",
            request_data,
            response,
            layer_name,
            ex,
            exc_info=True,
        )
        message = f"Error in save_request_response- {request_data}--{response}----{layer_name}----{ex,traceback.format_exc()}"
        send_bot_message(message)


def send_bot_message(msg):
    try:
        logger.info("----------send_bot_message-----%s", msg)
        if not int(os.getenv("ENABLE_BOT_NOTIFICATION")):
            return
        url = os.getenv("BOT_NOTIFICATION_URI")
        bot_message = {"text": msg}
        message_headers = {"Content-Type": "application/json; charset=UTF-8"}
        response = requests.post(url, headers=message_headers, json=bot_message)
        logger.info("----------message notification-----%s,%s", msg, response)
    except Exception as ex:
        logger.error("-----------ERROR in send_bot_message %s-----%s", msg, ex, exc_info=True)


def get_request_response_file_name(request_data, layer_name):
    event = request_data.get("event_data", {})
    query_params = request_data.get("query_params", {})
    file_name = ""
    if (event and "trip_id" in event) or (query_params and "trip_id" in query_params):
        trip_id = None
        if event and "trip_id" in event:
            trip_id = event["trip_id"]
        else:
            trip_id = query_params["trip_id"]
        file_name = f"{layer_name}/{trip_id}-{uuid.uuid4()}.json"
    elif (event and "confirmation_id" in event) or (query_params and "confirmation_id" in query_params):
        confirmation_id = None
        if event and "confirmation_id" in event:
            confirmation_id = event["confirmation_id"]
        else:
            confirmation_id = query_params["confirmation_id"]
        file_name = f"{layer_name}/{confirmation_id}-{uuid.uuid4()}.json"
    return file_name


def download_file_from_s3(bucket_name, key, local_path):
    """
    Downloads a single file from S3.
    """

    # Using single client is not preferable for reads as they will compete for same connection
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    for attempt in range(RETRY_COUNT):
        try:
            s3_client = __get_s3_client()
            s3_client.download_file(bucket_name, key, local_path)
            logger.debug(f"Downloaded {key} to {local_path} from {bucket_name}")
            return True
        except Exception as e:
            if attempt >= RETRY_COUNT - 1:
                logger.error(f"Error downloading {key}: {e}.  Inside final attempt {traceback.format_exc()}")
                return False
            else:
                time.sleep(2**attempt)  # Exponential backoff


def download_files_to_ephemeral_storage(bucket_name, key_prefix):
    """
    Download files from S3 and push to Ephemeral storage.
    """
    logger.info(f" Downloading files from {bucket_name} with prefix {key_prefix}")
    start = datetime.now()

    local_dir = "/tmp/lib"
    key_prefix_path = os.path.join(local_dir, key_prefix)
    if os.path.exists(key_prefix_path) and os.path.isdir(key_prefix_path):
        logger.info(f"Files already downloaded to , skipping download{key_prefix_path}")
        return local_dir
    else:
        # Free up the space before downloading
        delete_ephemeral_path(local_dir)
    os.makedirs(local_dir, exist_ok=True)

    retry_attempts = 3
    matching_files = []
    files_to_download = []
    for attempt in range(retry_attempts):
        try:
            matching_files = fetch_files_with_prefix(bucket_name, key_prefix)
            if matching_files:
                break
        except Exception as e:
            logger.error(f"Error fetching files from S3: {e}. Attempt {attempt + 1}")
            if attempt >= retry_attempts - 1:
                raise Exception(
                    f"Error fetching files from S3, retry attempt succeeded"
                    f" inside download_files_to_ephemeral_storage: {str(e)}"
                )
        # If it is refreshed once, then we don't need to refresh again for this short interval
        # For now, we are adding for all the cases, but we can add a condition to check the last refresh time
        __refresh_s3_client(force_reset=True, max_clients=10)
        time.sleep(2**attempt)  # Exponential backoff

    for key in matching_files:
        local_path = os.path.join(local_dir, key)
        files_to_download.append((bucket_name, key, local_path))
    logger.info(f" Downloading {len(files_to_download)} files")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download_file_from_s3, *args): args for args in files_to_download}
        for future in as_completed(futures):
            try:
                future.result()  # Raises exception if function failed
            except Exception as e:
                logger.error(f"Error downloading {futures[future]}: {e}")

    delta = (datetime.now() - start).total_seconds()
    logger.info(f"Download completed in {delta:.2f} seconds")
    return local_dir


class S3Threading:
    """
    This is mainly for the multithreading of S3.
    We are creating a connection and reusing the same connection for multiple threads.
    This provides better performance than creating a new connection for each thread.
    Maximum recommended 10 threads parallel (https://github.com/boto/botocore/issues/619)
    """

    def __init__(self) -> None:
        # Use boto3.session.Session() for multithreading
        # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/resources.html#multithreading-or-multiprocessing-with-resources
        self.s3_resource = session.resource(
            "s3",
            region_name=os.environ["AWS_REGION_NAME"],
            aws_access_key_id=os.environ["ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["SECRET_ACCESS_KEY"],
        )
        self.s3_client = session.client(
            "s3",
            region_name=os.environ["AWS_REGION_NAME"],
            aws_access_key_id=os.environ["ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["SECRET_ACCESS_KEY"],
        )

    def save_to_s3(self, bucket_name: str, file_name: str, data: dict):
        """
        Function which saves the data in S3.
        :param bucket_name: Name of the S3 bucket.
        :param file_name: Name of the S3 file.
        :param data: Data which is being saved to S3
        :return: S3 Metadata
        """
        try:
            s3_publish_start_time = datetime.now()
            s3_file = self.s3_resource.Object(bucket_name, file_name).put(Body=data)
            s3_time_delta = datetime.now() - s3_publish_start_time
            logger.info(f"Time taken to save in S3 is {s3_time_delta.total_seconds()} (In Sec)")
            return {
                "s3_status": True,
                "s3_meta_data": s3_file,
                "s3_bucket_name": bucket_name,
                "s3_file_name": file_name,
            }
        except Exception as e:
            logger.error(
                f"Error while inserting data into S3. bucket: {bucket_name}, file_name: {file_name}, "
                f"error: {traceback.format_exc()}"
            )
            raise e

    def read_from_s3(self, bucket_name: str, file_name: str):
        """
        Read data from S3 bucket
        :param bucket_name: S3 bucket name
        :param file_name: file name where payload is present
        :return: hotel list from S3
        """
        try:
            s3_start_time = datetime.now()
            resp = self.s3_client.get_object(Bucket=bucket_name, Key=file_name)
            s3_delta = datetime.now() - s3_start_time
            logger.info(f"Time taken to read file from S3 is {s3_delta.total_seconds()}")
            return resp
        except Exception as e:
            logger.error(f"Error while fetching data from S3. error: {traceback.format_exc()}")
            raise e

    def s3_parallel_save(self, inp_list, threads=None, wait=1):
        """
        save objects to S3 in parallel.
        :param inp_dict: Dictionary which contains data, file_name and S3 objects.
        :return:
        """
        if not threads:
            threads = list()
        s3_publish_start_time = datetime.now()
        # threads = []
        for each in inp_list:
            batch_data = each.get("data") or each.get("batch_data")
            bucket_name = each.get("s3_bucket_name")
            file_name = each.get("s3_file_name")
            thread = Thread(
                target=self.save_to_s3,
                args=(
                    bucket_name,
                    file_name,
                    batch_data,
                ),
            )
            threads.append(thread)

        for thread in threads:
            thread.start()
        if wait:
            for thread in threads:
                thread.join()

        s3_time_delta = datetime.now() - s3_publish_start_time
        logger.info(f"Time taken for all batches to save to S3 is {s3_time_delta.total_seconds()}")
