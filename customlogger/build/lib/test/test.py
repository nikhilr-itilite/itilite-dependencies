import os
from customlogger import logger


if __name__ == "__main__":
    os.putenv(
        "CUSTOMLOGGER_LOGGER_OPENSEARCH_HOST",
        "https://search-stream-p7vnbfigrjffehmls3h7rcbl5a.us-east-2.es.amazonaws.com",
    )
    os.putenv("CUSTOMLOGGER_OPENSEARCH_USERNAME", "itilite")
    os.putenv("CUSTOMLOGGER_LOGGER_OPENSEARCH_PASSWORD", "Itilite@123")
    os.putenv("OPENSEARCH_LOGGER_ENABLE", "True")
    logger = logger.Logger("Lambda/Kafka/redis etc", "name-of-the-service-method")
    print(logger.info({"hello": "hi"}))
    logger.info("check")
    logger.warn("check")
    logger.debug("check")

    logger.info("check", "status", "status_code")
    logger.warn("check", "status", "status_code")
    logger.debug("check", "status", "status_code")
    logger.error("check", "status", "status_code")

    logger.warn({"request_type": "find_recommendation", "msg": "warn", "request_id": "dhdhkkk"})

    logger.debug({"request_type": "find_recommendation", "msg": "debug", "request_id": "dhdhkkk"})

    logger.info({}, "status", "status_code")
    logger.warn({}, "status", "status_code")
    logger.debug({}, "status", "status_code")
    logger.error({}, "status", "status_code")

    logger.info("hhhhhhhhhhhhh")
    print(logger)
