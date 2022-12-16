# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import functools
import inspect
import logging
import time

logger = logging.getLogger(__name__)


class CommonLogFilter(logging.Formatter):
    def filter(self, record):
        if hasattr(record, "filename_override"):
            record.filename = record.filename_override
        if hasattr(record, "lineno_override"):
            record.lineno = record.lineno_override
        return True


def log_call(
    func: callable = None,
    debug: bool = False,
    called: bool = True,
    params: bool = True,
    returned: bool = True,
    result: bool = True,
    timer: bool = False,
    exception: bool = False,
):
    """
    function decorator that logs the lifecycle of the function. Can be called with or without params.

    Args:
        func (callable, optional): the function to be docrated.
        debug (bool, optional): set to True to log as debug, default is info.
        called (bool, optional): log that the function was called.
        params (bool, optional): log the params the function was called with.
        returned (bool, optional): log that the function returned.
        result (bool, optional): log the retuen value of the function.
        timer (bool, optional): log how long the function took (in seconds).
        exception (bool, optional): log any exception raised by the decorated function, then re-raise.

    Returns:
        callable: decorated function
    """

    level = "debug" if debug else "info"
    frame = inspect.currentframe()
    frame_index = 1
    func_frame = inspect.getouterframes(frame)[frame_index]
    func_lineno = func_frame.lineno

    def decorator(func):
        overrides = {
            "filename_override": func.__module__,
            "lineno_override": func_lineno,
        }

        @functools.wraps(func)
        def inner(*args, **kwargs):
            if timer:
                start_time = time.time()
            if called:
                message = f"{func.__qualname__} called"
                if params:
                    message += f" with args: {args} and kwargs: {kwargs}"
                _logger(
                    message,
                    level,
                    overrides,
                )

            # actual function call
            if exception:
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    _logger(
                        f"{e.__class__.__name__} was raised during call of {func.__qualname__}",
                        "exception",
                        overrides,
                    )
                    raise
            else:
                result = func(*args, **kwargs)

            message = ""
            if timer:
                message += (
                    f"{func.__qualname__} took {time.time() - start_time} seconds."
                )
            elif returned or result:
                message += f"{func.__name__} returned."
            if result:
                message += f" Result: {result}"
            if message:
                _logger(message, level, overrides)
            return result

        return inner

    # if the decorator was used without parameters, we need to force the wrapping here.
    if callable(func):
        return decorator(func)
    return decorator


def _logger(message, level, overrides):
    getattr(logger, level, "info")(message, extra=overrides)
