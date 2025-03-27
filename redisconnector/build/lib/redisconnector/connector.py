from redis import Redis, ConnectionPool
import os

_POOLS = []
_CHANNEL_TO_CLIENT = {}


def init():
    """Create a connection pool and a client object"""
    get()


def get(channel="master"):
    if channel == "master":
        host = os.environ["REDIS_HOST_MASTER"]
    else:
        host = os.environ["REDIS_HOST_SLAVE"]
    pool = ConnectionPool(
        host=host,
        port=os.environ["REDIS_PORT"],
        db=os.environ["REDIS_DB"],
        retry_on_timeout=3,
        health_check_interval=5000,
    )

    _POOLS.append(pool)
    _CHANNEL_TO_CLIENT[channel] = Redis(connection_pool=pool)
    return _CHANNEL_TO_CLIENT[channel]


def get_redis_client(channel="master"):
    """Return the client object"""
    if channel in _CHANNEL_TO_CLIENT:
        return _CHANNEL_TO_CLIENT[channel]

    return get(channel)
