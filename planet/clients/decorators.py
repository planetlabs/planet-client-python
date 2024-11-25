def docstring(s: str):

    def decorator(func):
        func.__doc__ = s
        return func

    return decorator
