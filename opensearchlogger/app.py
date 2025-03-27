# import json

# from newlogger.handlers import logging_unique_id
# # from itilogging import opensearchlogging
# from newlogger.logging import logger

# logging_unique_id.set({"trip_id": "0307-0001", "farequote_request_id": "", "selection_id": "", "confirmation_id": ""})

# import test
# import check

# def lambda_handler(event, context):
#     # TODO implement
#     # test = opensearchlogging.OSLogging()
#     logger.info("checking")
#     # test.check()
#     check.check()
#     logger.warn({
#         "request_type": "find_recommendation",
#         "msg": "warn",
#         "request_id": "dhdhkkk"
#     })

#     logger.debug({
#         "request_type": "find_recommendation",
#         "msg": "debug",
#         "request_id": "dhdhkkk"
#     })

#     # logger.info({}, "status", "status_code")
#     # logger.warn({}, "status", "status_code")
#     # logger.debug({}, "status", "status_code")
#     # logger.error({}, "status", "status_code")
#     return {
#         'statusCode': 200,
#         'body': json.dumps('Hello from Lambda!')
#     }
#     pass
