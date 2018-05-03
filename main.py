import numpy as np
import fipy
from toolz.curried import memoize, do, curry, valmap, first
from .toolz_ import update, iterate_, rcompose


def get_inf(var):
    return np.array(var[-1])


@curry
def theta_eqn(params, sup, theta, **kwargs):
    def expression1():
        return (theta['old'] + params['dt'] * params['k_plus'] * get_inf(sup))

    def expression2():
        return params['k_plus'] * get_inf(sup) + \
            params['k_minus'] * params['vel']

    @memoize
    def new_value():
        return expression1() / (1 + params['dt'] * expression2())

    return (dict(new=new_value(),
                 old=theta['old']),
            abs(new_value() - theta['new']))


get_mask = rcompose(
    lambda x: fipy.CellVariable(mesh=x),
    do(lambda x: x.setValue(1, where=x.mesh.x > (x.mesh.Lx - x.mesh.dx / 2)))
)


@memoize
def get_eqn_f(params, mesh):
    print('building equation')
    flux = fipy.CellVariable(mesh, value=0.)
    eqn = fipy.TransientTerm() == fipy.DiffusionTerm(params['diff_sup']) + \
        fipy.ImplicitSourceTerm(flux * get_mask(mesh) / mesh.dx)
    def func(theta):
        flux.setValue(-params['gamma'] * params['k_plus'] * (1 - theta))
        return eqn
    return func


@curry
def get_eqn(params, mesh, theta):
    get_eqn_f(params, mesh)(theta)


@curry
def sup_eqn(params, supp, theta, **kwargs):
    res = get_eqn(params, supp.mesh, theta).sweep(supp, dt=params['dt'])
    return (supp, res)


def output_sweep():
    print('output sweep')


def output_step():
    print('output step')


def sweep_func(params):
    return rcompose(
        update(
            dict(
                sup=sup_eqn(params),
                theta=theta_eqn(params),
                steps=lambda **x: (x['steps'], None),
                sweeps=lambda **x: (x['sweeps'] + 1, None)
            )
        ),
        do(output_sweep),
        valmap(first)
    )


@curry
def step_func(params):
    return rcompose(
        update(
            dict(
                sup=lambda **x: do(x['sup'].updateOld()),
                theta=lambda **x: dict(new=x['theta']['old'],
                                       old=x['theta']['old']),
                steps=lambda **x: x['steps'] + 1,
                sweeps=lambda **x: 0
            )
        ),
        iterate_(sweep_func(params), params['max_sweeps']),
        do(output_step(params)),
    )


@curry
def run_values(params, values):
    return iterate_(step_func(params), params['max_steps'], values)


@memoize
def get_mesh(params):
    return fipy.Grid1D(nx=params['nx'], Lx=params['delta'])


def run(params):
    iterate_(
        step_func(params),
        params['max_steps'],
        dict(theta=dict(new=params['theta_ini'], old=params['theta_ini']),
             sup=fipy.CellVariable(get_mesh(params), value=params['sup_ini']),
             sweeps=0,
             steps=0)
    )
