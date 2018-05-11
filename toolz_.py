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


def debug(arg):
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
def update(funcs, values):
    """Apply a dict of funcs to a dict of values

    >>> values = dict(a=1., b=2., c=4.)
    >>> funcs = dict(
    ...     a=lambda a, b, c: a + b + c,
    ...     b=lambda a, b, c: a * b * c,
    ...     c=lambda a, b, c: a - b - c
    ... )
    >>> assert update(funcs, values) == dict(a=7, b=8, c=-5)
    """
    return valmap(lambda f: f(**values), funcs)


def save(func):
    """Save the output from a function.

    Args:
      func: function to save

    Returns:
      caching function

    >>> @save
    ... def test_func(a):
    ...    print('running')
    ...    return 2 * a
    >>> test_func(3)
    running
    6
    >>> test_func(4)
    6

    """
    saved = dict()

    def wrapper(*args, **kwargs):
        """Caching function
        """
        if "result" not in saved:
            saved["result"] = func(*args, **kwargs)
        return saved["result"]

    return wrapper
