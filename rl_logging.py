from types import FunctionType
from functools import wraps
import logging as log
from inspect import getcallargs
from inspect import getsource


def decorate_all_in_module(module, decorator):
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, FunctionType):
            setattr(module, name, decorator(obj))


def log_decorator(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        log.info(
            "Called "
            + str(fun)
            + " with args: "
            + str(getcallargs(fun, *args, **kwargs))
        )
        retval = fun(*args, **kwargs)
        log.info("Returned " + str(retval))
        return retval

    return wrapper


def log_on_fail(fun, retval_check=lambda x: None):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        try:
            retval = fun(*args, **kwargs)
        except Exception as e:
            log_call(fun, args, kwargs, exception=e)
            raise
        retval_check(retval)
        return retval

    return wrapper


def fun_name(fun):
    return getsource(fun) if fun.func_name == "<lambda>" else str(fun) + " failed"


def log_call(fun, args, kwargs, exception):
    log.warning(
        "{fun} failed with exception {e} on arguments {args}, {kwargs}".format(
            fun=fun_name(fun), args=args, kwargs=kwargs, e=exception
        )
    )
