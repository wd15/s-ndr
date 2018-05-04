import numpy as np
import fipy
from toolz.curried import memoize, do, curry, valmap, first
from toolz_ import update, iterate_, rcompose, save
from toolz_ import debug


def get_params():
    return dict(
        diff_sup=9.2e-11,
        diff_cu=2.65e-10,
        cu_inf=240.0,
        sup_inf=0.01,
        delta=1e-6,
        gamma=2.5e-7,
        k_plus=2300.0,
        k_minus=3.79e-6,
        j0=20.0,
        j1=1e-3,
        alpha=0.4,
        n=2,
        omega=7.2e-6,
        faraday=96485.332,
        v0=0,
        vs=-0.325,
        vm=0.01,
        tf=65.0,
        max_sweeps=4,
        max_steps=1,
        theta_ini=0.0,
        sup_ini=0.0,
        nx=100,
        dt=1e-3,
        vel=0.0
    )


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


def calc_mask(mesh):
    return mesh.x > (max(mesh.x) - mesh.dx / 2)


get_mask = rcompose(
    lambda x: fipy.CellVariable(mesh=x),
    do(lambda x: x.setValue(1, where=calc_mask(x.mesh)))
)


@save
def get_eqn(params, mesh):
    print('building equation')
    flux = fipy.CellVariable(mesh, value=0.)
    eqn = fipy.TransientTerm() == fipy.DiffusionTerm(params['diff_sup']) + \
        fipy.ImplicitSourceTerm(flux * get_mask(mesh) / mesh.dx)
    def func(theta):
        flux.setValue(-params['gamma'] * params['k_plus'] * (1 - theta['new']))
        return eqn
    return func


@curry
def sup_eqn(params, sup, theta, **kwargs):
    res = get_eqn(params, sup.mesh)(theta).sweep(sup, dt=params['dt'])
    return (sup, res)


@curry
def output_sweep(params, values):
    print('output sweep')


@curry
def output_step(params, values):
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
                sup=lambda **x: do(lambda x: x.updateOld())(x['sup']),
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


def get_mesh(params):
    return fipy.Grid1D(nx=params['nx'], dx=params['delta'] / params['nx'])


def run(params):
    iterate_(
        step_func(params),
        params['max_steps'],
        dict(theta=dict(new=params['theta_ini'], old=params['theta_ini']),
             sup=fipy.CellVariable(get_mesh(params),
                                   value=params['sup_ini'],
                                   hasOld=True),
             sweeps=0,
             steps=0)
    )


if __name__ == '__main__':
    run(get_params())
