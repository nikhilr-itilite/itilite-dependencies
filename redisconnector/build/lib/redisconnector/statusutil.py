import json
import os
import traceback
from redisconnector.lua_scripts import update_min_price_transformer_lua_script
from opensearchlogger.logging import logger
from redis.exceptions import ResponseError
from redisconnector.connector import get_redis_client


def push_transformer_status_to_redis(batch_nums, status, vendor_request_id, leg_request_id, total_batches, mode):
    """
    updates connector status in trip collection.
    :param batch_nums: List of batch numbers
    :param status: transformation status
    :param vendor_request_id:
    :param leg_request_id:
    :param total_batches:
    :param mode:
    :return:
    """
    try:
        push_data = []
        redis_client = get_redis_client()
        for batch_no in batch_nums:  # Loops is a rare case. it should always be single length.
            _data = json.dumps(
                {
                    "leg_request_id": leg_request_id,
                    "vendor_request_id": vendor_request_id,
                    "mode": mode,
                    "status": status,
                    "batch_no": batch_no,
                    "total_batches": total_batches,
                }
            )
            push_data.append(_data)
        key_name = "batch_transformation_" + str(leg_request_id)
        redis_client.lpush(key_name, *push_data)
        logger.info(f"successfully saved {mode} json transformation status in redis.")

    except Exception:
        logger.error(f"Error while updating connector status. error:{traceback.format_exc()}")


def pop_transformation_status_from_redis(leg_request_id):
    """
    :param leg_request_id:
    Pop transformation status of each leg. Initially it tries to pop at once but
    if the redis doesn't support count, it pull one by one.
    """
    redis_client = get_redis_client()
    key_name = "batch_transformation_" + str(leg_request_id)
    try:
        length = redis_client.llen(key_name)
        json_list = redis_client.lpop(name=key_name, count=length)
        return [json.loads(each) for each in json_list] if json_list else []
    except ResponseError as er:
        logger.info(f"Response Error: {str(er)}, retrying element by element")
        data = []
        single_data = redis_client.lpop(name=key_name)
        while single_data:
            data.append(json.loads(single_data))
            single_data = redis_client.lpop(name=key_name)
        logger.info("redis fetch successful")
        return data
    except Exception:
        logger.error(f"Couldn't fetch transformation status for leg_request_id: {leg_request_id}, error: {traceback.format_exc()}")


def update_cabin_class_min_price_redis(leg_request_id, cabin_class, min_price, min_price_tc, retry=3):
    """
    update respective cabin class leg-request id min price
    :param leg_request_id, cabin_class, min_price
    :param cabin_class : lower syntax with strip spaces on left and right
    :param min_price : Minimum of price among current vendor response
    :retry: Set to 3, can be removed in prod
    :There is a change for simultaneous update from different vendors for same leg request id and cabin class, we need
    to handle that
    """
    redis_client = get_redis_client()
    key_name = leg_request_id + "_" + cabin_class.strip().lower()
    # Hash will remain same even if we reload as SHA1 depends on content only
    script_hash = os.getenv("MIN_PRICE_TRANSFORMER_LS_HASH", "")

    try:
        # If scrip is not loaded
        if not redis_client.script_exists(script_hash)[0]:
            # Reloading the script in Redis again
            script_hash_new = redis_client.script_load(update_min_price_transformer_lua_script)
            logger.info(f" New script hash {script_hash_new}, earlier {script_hash} ")
            script_hash = script_hash_new
        logger.info(f" Script hash {script_hash} key {key_name}")
        result = redis_client.evalsha(script_hash, 1, key_name, min_price, min_price_tc)
        return result
    except Exception as ex:
        logger.error(
            f"Error in updating min price transformer : {leg_request_id}, price : {min_price}, "
            f"Retry Attempt remaing : {retry} Error: {str(ex)}"
        )
        if retry > 0:
            update_cabin_class_min_price_redis(leg_request_id, cabin_class, min_price, retry - 1)


def get_values_from_redis(keys):
    """
    You can send any keys you want in list and it will give you the results
    get respective cabin class leg-request id min price
    :param keys
    Format of key will be [
        "leg_request_id_economy",
        "leg_request_id_premium economy",
        "leg_request_id_business",
        "leg_request_id_first",
    ]
    Also there wil be multiple leg_request_id which are subsequent to current legs
    """
    try:
        if not keys:
            return []
        redis_client = get_redis_client()
        pipeline = redis_client.pipeline()

        for key in keys:
            pipeline.get(key)

        # Execute pipeline
        results = pipeline.execute()
        decoded_values = []

        for i, key in enumerate(keys):
            if results[i]:
                logger.info(f" Results {results[i]}")
                data = json.loads(results[i])
                price = data["price"]
                price_tc = data["price_tc"]
                decoded_values.append(
                    {
                        "price": float(price),
                        "price_tc": float(price_tc),
                        "key": key,
                    }
                )
            else:
                decoded_values.append(None)
        return decoded_values

    except Exception as ex:
        logger.error(f"Error in getting min value of all cabin class {str(ex)}, Traceback {traceback.format_exc()}")
