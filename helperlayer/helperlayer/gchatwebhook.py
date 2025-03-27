import json
import os

from httplib2 import Http

from opensearchlogger.logging import logger

WEBHOOK_URL = os.environ.get("STREAMING_BOT_NOTIFICATION_URI")


# Replace with environment variable later


def push_error_message(message, webhook_url=WEBHOOK_URL):
    try:
        bot_message = {"text": message}
        http_obj = Http()
        message_headers = {"Content-Type": "application/json; charset=UTF-8"}
        response = http_obj.request(
            uri=webhook_url,
            method="POST",
            headers=message_headers,
            body=json.dumps(bot_message),
        )
        logger.info(response)
    except Exception as e:
        logger.error(f"Failed to send error message to webhook: {e}", exc_info=1)


if __name__ == "__main__":
    push_error_message("Hey There. Welcome to Team")
