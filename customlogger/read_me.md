Env's Required
---------------
CUSTOM_LOGGER_LOG_LEVEL

CUSTOMLOGGER_LOGGER_OPENSEARCH_HOST
CUSTOMLOGGER_LOGGER_OPENSEARCH_PASSWORD
CUSTOMLOGGER_OPENSEARCH_INDEXNAME
CUSTOMLOGGER_OPENSEARCH_USERNAME

OPENSEARCH_LOGGER_ENABLE --> Enable disable Opensearhc logger, If enable above env's of **opensearch** required



How to use Logger?
----------------------
1. First import as below,

    from customlogger import logger</br></br>
2. Initialize logger object,

   logger = logger.Logger("Lambda/Kafka/redis etc", "name-of-the-service-method")</br></br>
3. Usage as below,</br>
   logger.info("check")</br>
   logger.warn("check")</br>
   logger.debug("check")</br>

   logger.info("check", "status", "status_code")</br>
   logger.warn("check", "status", "status_code")</br>
   logger.debug("check", "status", "status_code")</br>
   logger.error("check", "status", "status_code")</br></br>
   logger.info({
        "request_type": "find_recommendation",
        "msg": "info",
        "request_id": "dhdhkkk"
   })</br></br>

   logger.warn({
   "request_type": "find_recommendation",
   "msg": "warn",
   "request_id": "dhdhkkk"
   })</br></br>

   logger.debug({
   "request_type": "find_recommendation",
   "msg": "debug",
   "request_id": "dhdhkkk"
   })</br></br>

    logger.info({}, "status", "status_code")</br></br>
    logger.warn({}, "status", "status_code")</br></br>
    logger.debug({}, "status", "status_code")</br></br>
    logger.error({}, "status", "status_code")</br></br>



Defining instantiation object
--------------------------------
<<custom_logger = logger.Logger("Lambda/kafka/redis etc", "connector-opensearch")>>
Above object creation required 2 variables service name and service type.

=====

streaming_logger.info(message -> dict)
streaming_logger.info(<<status>>, <<status_code>>, message: dict)

same as above for all loggers level