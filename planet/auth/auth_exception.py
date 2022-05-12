import functools


class AuthException(Exception):

    def __init__(self, message=None, inner_exception=None):
        super().__init__(message)
        self._inner_exception = inner_exception

    @classmethod
    def recast(cls, *exceptions, **params):
        if not exceptions:
            exceptions = (Exception, )
        # params.get('some_arg', 'default')

        def decorator(func):

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    raise cls(str(e), e)

            return wrapper

        return decorator
