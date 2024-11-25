def docstring(s):

    def decorator(func):
        func.__doc__ = s
        return func

    return decorator
