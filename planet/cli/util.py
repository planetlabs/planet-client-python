import click
import functools
import logging


logger = logging.getLogger(__name__)


def recast_exceptions_to_click(*exceptions, **params):
    if not exceptions:
        exceptions = (Exception,)
    # params.get('some_arg', 'default')

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                raise click.ClickException(str(e))
        return wrapper
    return decorator
