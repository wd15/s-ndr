"Helper functions for Toolz"


from toolz.curried import curry, compose, iterate, valmap


def rcompose(*args):
    """Reverse function composition

    >>> assert rcompose(lambda x: x * 2, lambda x: x - 1)(3) == 5
    """
    return compose(*args[::-1])


@curry
def iterate_(func, times, value):
    """Use toolz iterate function to actually iterate

    >>> assert iterate_(lambda x: x * 2, 3, 1) == 8
    """
    iter_ = iterate(func, value)
    for _ in range(times):
        next(iter_)
    return next(iter_)


def debug(arg):  # pragma: no cover
    """Debug for function composition

    Params:
      arg: the input argument

    Returns:
      the input argument
    """
    import ipdb

    ipdb.set_trace()
    return arg


@curry
def update_dict(funcs, values):
    """Apply a dict of funcs to a dict of values

    >>> values = dict(a=1., b=2., c=4.)
    >>> funcs = dict(
    ...     a=lambda a, b, c: a + b + c,
    ...     b=lambda a, b, c: a * b * c,
    ...     c=lambda a, b, c: a - b - c
    ... )
    >>> assert update_dict(funcs, values) == dict(a=7, b=8, c=-5)
    """
    return valmap(lambda f: f(**values), funcs)


@curry
def cache(func):
    """Cache decorator for a function

    Enables caching of a function and adds an `update` keyword
    argument to the funtion so that the function is only reevaluated
    when `update` is `True`.

    Args:
      func: function to save

    Returns:
      caching function

    >>> @cache
    ... def f(a):
    ...    print('running')
    ...    return 2 * a
    >>> f(3)
    running
    6
    >>> f(4)
    6

    >>> f(3, update=True)
    running
    6
    >>> f(4, update=False)
    6
    >>> f(5, update=True)
    running
    10

    """
    saved = dict()

    def wrapper(*args, update=False, **kwargs):
        """Caching function
        """
        if "result" not in saved or update:
            saved["result"] = func(*args, **kwargs)
        return saved["result"]

    return wrapper
