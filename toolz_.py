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
