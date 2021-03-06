import threading
import functools
from concurrent.futures import Future, ThreadPoolExecutor

from django.db import connection
from django.conf import settings
from djmail import core

from . import base

# TODO: parametrize this
executor = ThreadPoolExecutor(max_workers=1)


def _close_connection_on_finish(function):
    """
    Decorator for future task, that closes
    django database connection when it ends.
    """
    @functools.wraps(function)
    def _decorator(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        finally:
            connection.close()

    return _decorator


class EmailBackend(base.BaseEmailBackend):
    """
    djmail async backend that uses threadpool
    for send emails instead of other async task
    libraries like celery.
    """
    def _send_messages(self, email_messages):
        if len(email_messages) == 0:
            future = Future()
            future.set_result(0)
            return future

        @_close_connection_on_finish
        def _send(messages):
            return core._send_messages(email_messages)

        return executor.submit(_send, email_messages)
