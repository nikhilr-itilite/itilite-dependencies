from functools import wraps
import signal


def timeout(seconds):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise Exception(f"Timed out after : {seconds} seconds")

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator
