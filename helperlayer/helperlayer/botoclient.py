import time

import boto3
import os
from helperlayer.gchatwebhook import push_error_message


def boto_retry(service="undefined"):
    def boto_decorator(func):
        def wrapper(*args, **kwargs):
            retry_count = 0
            while retry_count < 5:
                if service in ("stepfunctions", "lambda", "events"):
                    try:
                        boto = boto3.session.Session()
                        client = boto.client(
                            service,
                            region_name=os.environ.get("AWS_REGION_NAME"),
                            aws_access_key_id=os.environ.get("ACCESS_KEY_ID"),
                            aws_secret_access_key=os.environ.get("SECRET_ACCESS_KEY"),
                        )
                        func_response = func(client, *args, **kwargs)
                        return func_response
                    except Exception as ex:
                        retry_count += 1
                        time.sleep(1)
                        if retry_count == 5:
                            push_error_message(f"Retry for boto failed. Attempt {retry_count} {ex}")
                            raise ex

        return wrapper

    return boto_decorator


@boto_retry("stepfunctions")
def trigger_stepfunctions(client, state_machine_arn, state_machine_name, payload):
    # argument "client" will be added by the decorator
    return client.start_execution(stateMachineArn=state_machine_arn, name=state_machine_name, input=payload)


@boto_retry("lambda")
def trigger_lambda(client, lambda_name, payload, invoke_type="Event", qualifier=None):
    # argument "client" will be added by the decorator
    if qualifier:
        return client.invoke(FunctionName=lambda_name, InvocationType=invoke_type, Payload=payload, Qualifier=qualifier)
    else:
        return client.invoke(FunctionName=lambda_name, InvocationType=invoke_type, Payload=payload)


@boto_retry("events")
def get_events_boto_client(client):
    return client


@boto_retry("lambda")
def get_lambda_boto_client(client):
    return client
